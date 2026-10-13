import io
import json
from datetime import date, timedelta
from unittest.mock import patch

from django.core.management import call_command
from django.test import TestCase, TransactionTestCase, override_settings
from django.utils import timezone
from rest_framework.test import APIClient

from participants.models import Participant
from physical_tests.models import Assessment, ExerciseResult
from sessions.models import ProgrammeSession
from users.models import Branch, UserAccount
from .models import PhysicalAnalysisJob
from .prompts.physical import build_physical_prompt
from .services.physical import physical_statistics


@override_settings(DEFAULT_LLM_MODEL="test-model", REPORT_LLM_MODELS=["test-model"])
class PhysicalReportTests(TestCase):
    def setUp(self):
        self.branch = Branch.objects.create(name="Report branch")
        self.other = Branch.objects.create(name="Other report branch")
        self.user = UserAccount.objects.create_user(username="physical-manager", email="physical-manager@example.com", role="branch_manager", branch=self.branch)
        self.person = Participant.objects.create(first_name="Private", last_name="Name", branch=self.branch, joined_on=date(2025, 1, 1))
        self.no_tests = Participant.objects.create(first_name="No", last_name="Tests", branch=self.branch)
        self.scope = {"start_date": date(2026, 1, 1), "end_date": date(2026, 3, 31)}
        self.client = APIClient()
        self.client.force_authenticate(self.user)
        self.url = "/api/reporting/physical/"

    def assessment(self, day, value, *, person=None, completed=True, outcome="measured", aid=""):
        result = Assessment.objects.create(participant=person or self.person, branch=(person or self.person).branch,
            recorded_by=self.user, assessed_on=day, completed_at=timezone.now() if completed else None)
        ExerciseResult.objects.create(assessment=result, exercise="tug", outcome=outcome, value=value,
            walking_aid=aid, notes="Private clinical note", recorded_by=self.user)
        return result

    def stats(self):
        return physical_statistics(user=self.user, **self.scope)

    def test_no_test_people_are_in_denominator_and_drafts_excluded(self):
        self.assessment(date(2026, 1, 1), 15)
        self.assessment(date(2026, 3, 31), 12)
        self.assessment(date(2026, 2, 1), 999, person=self.no_tests, completed=False)
        stats = self.stats()
        self.assertEqual(stats["totals"], {"eligible_participants": 2, "tested_participants": 1, "untested_participants": 1,
            "completion_percent": 50, "completed_assessments": 2, "draft_assessments": 1})
        self.assertEqual(stats["metrics"][0]["mean"], 13.5)
        self.assertEqual(stats["paired_changes"][0], {"exercise": "tug", "participants": 1, "mean_change": -3})
        self.assertEqual(stats["monthly"][1]["metrics"][0]["mean"], None)
        self.assertEqual(len(stats["monthly"]), 3)

    def test_inclusive_dates_and_other_branch_are_enforced(self):
        self.assessment(date(2025, 12, 31), 99)
        self.assessment(date(2026, 4, 1), 99)
        self.assessment(date(2026, 1, 1), 10)
        self.assessment(date(2026, 3, 31), 8)
        other = Participant.objects.create(first_name="Other", last_name="Person", branch=self.other)
        self.assessment(date(2026, 2, 1), 99, person=other)
        self.assertEqual(self.stats()["metrics"][0]["mean"], 9)
        response = self.client.get(self.url, {**self.scope, "branch_id": str(self.other.pk)})
        self.assertEqual(response.status_code, 403)
        self.user.role = "super_admin"
        self.user.save()
        national = self.client.get(self.url, self.scope)
        self.assertEqual(national.status_code, 200)
        self.assertEqual(national.data["totals"]["eligible_participants"], 3)

    def test_missing_is_not_zero_but_chair_arms_score_is_zero(self):
        first = self.assessment(date(2026, 1, 1), None, outcome="unable")
        ExerciseResult.objects.create(assessment=first, exercise="chair", outcome="arms_used", value=0, recorded_by=self.user)
        ExerciseResult.objects.create(assessment=first, exercise="one_foot", outcome="skipped", value=None, recorded_by=self.user)
        stats = self.stats()
        self.assertEqual(stats["totals"]["tested_participants"], 1)
        metrics = {r["exercise"]: r for r in stats["metrics"]}
        self.assertIsNone(metrics["tug"]["mean"])
        self.assertEqual(metrics["tug"]["outcomes"]["unable"], 1)
        self.assertEqual(metrics["chair"]["mean"], 0)
        self.assertEqual(metrics["chair"]["outcomes"]["arms_used"], 1)
        self.assertIsNone(metrics["one_foot"]["mean"])

    def test_changed_aid_and_same_day_cannot_form_pair(self):
        first = self.assessment(date(2026, 1, 1), 12, aid="Stick")
        last = self.assessment(date(2026, 2, 1), 10, aid="")
        self.assertEqual(self.stats()["paired_changes"][0]["participants"], 0)
        last.results.update(walking_aid="stick")
        self.assertEqual(self.stats()["paired_changes"][0]["mean_change"], -2)
        last.assessed_on = first.assessed_on
        last.save()
        self.assertEqual(self.stats()["paired_changes"][0]["participants"], 0)

    def test_roster_rule_and_transfers_are_explicit(self):
        self.person.is_active = False
        self.person.save()
        Participant.objects.create(first_name="Later", last_name="Join", branch=self.branch, joined_on=date(2026, 4, 1))
        self.assertEqual(self.stats()["totals"]["eligible_participants"], 1)
        self.assessment(date(2026, 2, 1), 10)
        self.assertEqual(self.stats()["totals"]["eligible_participants"], 2)
        self.person.branch = self.other
        self.person.save()
        self.assertEqual(self.stats()["totals"]["tested_participants"], 0)

    def test_prompt_contains_only_aggregates(self):
        self.assessment(date(2026, 2, 1), 10, aid="Private aid description")
        payload = build_physical_prompt(self.stats())
        for private in ("Private", str(self.person.pk), str(self.branch.pk), "walking_aid", "participants\": [", "history", "notes"):
            self.assertNotIn(private, payload)
        self.assertIn("paired_changes", json.loads(payload))

    def test_report_queries_do_not_grow_per_participant(self):
        self.assessment(date(2026, 2, 1), 10)
        with self.assertNumQueries(4):
            self.stats()
        for index in range(5):
            person = Participant.objects.create(first_name=f"Person {index}", last_name="Report", branch=self.branch)
            self.assessment(date(2026, 2, 1), 10, person=person)
        with self.assertNumQueries(4):
            self.stats()

    @patch("reporting.views.generate_physical_analysis.apply_async")
    def test_empty_report_never_calls_provider_or_queue(self, enqueue):
        response = self.client.post(self.url + "analyse/", self.scope, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["status"], "succeeded")
        self.assertIsNone(response.data["narrative"])
        enqueue.assert_not_called()

    @patch("reporting.views.generate_physical_analysis.apply_async")
    @patch("reporting.tasks.explain_physical", return_value="Saved analysis")
    def test_async_job_snapshot_status_and_ownership(self, explain, enqueue):
        from .tasks import generate_physical_analysis
        self.assessment(date(2026, 2, 1), 10)
        response = self.client.post(self.url + "analyse/", self.scope, format="json")
        self.assertEqual(response.status_code, 202)
        enqueue.assert_called_once()
        explain.assert_not_called()
        job_id = response.data["job_id"]
        generate_physical_analysis.run(job_id)
        generate_physical_analysis.run(job_id)
        explain.assert_called_once()
        status_url = self.url + f"jobs/{job_id}/"
        response = self.client.get(status_url)
        self.assertEqual(response.data["narrative"], "Saved analysis")
        self.assertEqual(response.data["statistics"]["totals"]["completed_assessments"], 1)
        other = UserAccount.objects.create_user(username="other-admin", email="other-admin@example.com", role="super_admin")
        self.client.force_authenticate(other)
        self.assertEqual(self.client.get(status_url).status_code, 404)
        self.client.force_authenticate(self.user)
        self.user.branch = self.other
        self.user.save()
        self.assertEqual(self.client.get(status_url).status_code, 403)

    @patch("reporting.views.generate_physical_analysis.apply_async")
    def test_queue_failure_is_safe(self, enqueue):
        from kombu.exceptions import OperationalError
        self.assessment(date(2026, 2, 1), 10)
        enqueue.side_effect = OperationalError("Secret Redis credentials")
        response = self.client.post(self.url + "analyse/", self.scope, format="json")
        self.assertEqual(response.status_code, 503)
        self.assertNotIn("Secret", str(response.data))
        self.assertEqual(PhysicalAnalysisJob.objects.get().status, "failed")

    @patch("reporting.tasks.explain_physical", side_effect=ValueError("private provider failure"))
    def test_worker_failure_and_expiry_are_visible(self, explain):
        from .tasks import generate_physical_analysis
        job = PhysicalAnalysisJob.objects.create(requested_by=self.user, branch=self.branch, statistics=self.stats())
        with self.assertRaises(ValueError):
            generate_physical_analysis.run(str(job.pk))
        job.refresh_from_db()
        self.assertEqual(job.status, "failed")
        self.assertNotIn("private", job.error)
        job.status = "queued"
        job.expires_at = timezone.now() - timedelta(seconds=1)
        job.save()
        generate_physical_analysis.run(str(job.pk))
        self.assertEqual(explain.call_count, 1)
        job.refresh_from_db()
        self.assertEqual(job.status, "failed")

    def test_permissions_and_invalid_dates(self):
        for payload in ({"start_date": "bad", "end_date": "2026-03-01"},
                        {"start_date": "2026-04-01", "end_date": "2026-03-01"}):
            self.assertEqual(self.client.get(self.url, payload).status_code, 400)
        self.user.role = "instructor"
        self.user.save()
        self.assertEqual(self.client.get(self.url, self.scope).status_code, 403)
        self.assertEqual(self.client.post(self.url + "analyse/", self.scope, format="json").status_code, 403)
        self.client.force_authenticate(None)
        self.assertEqual(self.client.get(self.url, self.scope).status_code, 403)


@override_settings(DEFAULT_LLM_MODEL="test-model", REPORT_LLM_MODELS=["test-model"])
class PhysicalWorkerTests(TransactionTestCase):
    @patch("reporting.tasks.explain_physical", return_value="Physical worker narrative")
    def test_real_worker_consumes_physical_task(self, explain):
        import os
        import time
        from celery.contrib.testing.worker import start_worker
        from config.celery import app
        from .tasks import generate_physical_analysis
        user = UserAccount.objects.create_user(username="physical-worker", email="physical-worker@example.com", role="super_admin")
        job = PhysicalAnalysisJob.objects.create(requested_by=user, statistics={"totals": {"completed_assessments": 1}})
        with patch.dict(os.environ, {"CELERY_BROKER_URL": "memory://"}), self.settings(CELERY_TASK_ALWAYS_EAGER=False):
            with start_worker(app, pool="solo", perform_ping_check=False, queues=["physical-test"]):
                generate_physical_analysis.apply_async(args=[str(job.pk)], queue="physical-test")
                deadline = time.monotonic() + 8
                while time.monotonic() < deadline:
                    job.refresh_from_db()
                    if job.status in ("succeeded", "failed"):
                        break
                    time.sleep(0.1)
                self.assertEqual(job.status, "succeeded")
                self.assertEqual(job.narrative, "Physical worker narrative")


@override_settings(DEBUG=False, ALLOW_DEMO_SEEDING=True)
class ReportingDemoTests(TestCase):
    def test_seed_is_repeatable_preserves_edits_and_generates_valid_cases(self):
        from .management.commands.seed_reporting_demo import demo_id
        from physical_tests.serializers import GroupSerializer, GROUPS
        call_command("seed_reporting_demo", as_of=date(2026, 3, 31), stdout=io.StringIO())
        self.assertEqual(Branch.objects.count(), 2)
        self.assertEqual(UserAccount.objects.count(), 5)
        self.assertEqual(Participant.objects.count(), 24)
        self.assertEqual(ProgrammeSession.objects.count(), 24)
        self.assertEqual(Assessment.objects.filter(completed_at__isnull=False).count(), 50)
        self.assertEqual(Assessment.objects.filter(completed_at__isnull=True).count(), 2)
        self.assertFalse(Participant.objects.filter(date_of_birth__gt=date(1976, 3, 31)).exists())
        self.assertTrue(ProgrammeSession.objects.filter(attendance_finalised=False).exists())
        empty = ProgrammeSession.objects.get(pk=demo_id("harbour-session-4"))
        self.assertTrue(empty.attendance_finalised)
        self.assertFalse(empty.attendance.filter(status="present").exists())
        admin = UserAccount.objects.get(role="super_admin")
        admin.set_password("ChangedDemoPassword")
        admin.save()
        call_command("seed_reporting_demo", stdout=io.StringIO())
        self.assertEqual(Assessment.objects.count(), 52)
        admin.refresh_from_db()
        self.assertTrue(admin.check_password("ChangedDemoPassword"))
        report = physical_statistics(user=admin, start_date=date(2026, 1, 1), end_date=date(2026, 3, 31))
        self.assertEqual(report["totals"]["completion_percent"], 75)
        for assessment in Assessment.objects.filter(completed_at__isnull=False).prefetch_related("results"):
            for group, exercises in GROUPS.items():
                rows = [{"exercise": r.exercise, "outcome": r.outcome, "value": r.value, "notes": r.notes, "walking_aid": r.walking_aid}
                        for r in assessment.results.all() if r.exercise in exercises]
                serializer = GroupSerializer(data={"version": 0, "results": rows}, context={"group": group})
                self.assertTrue(serializer.is_valid(), serializer.errors)

    @override_settings(DEBUG=True, ALLOW_DEMO_SEEDING=False)
    def test_disabled_without_explicit_opt_in_even_in_debug(self):
        from django.core.management.base import CommandError
        with self.assertRaises(CommandError):
            call_command("seed_reporting_demo", stdout=io.StringIO())
        self.assertFalse(Branch.objects.exists())
