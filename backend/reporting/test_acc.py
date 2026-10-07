import json
from unittest.mock import patch

from django.test import TestCase, override_settings
from rest_framework.test import APIClient
from rest_framework.exceptions import ValidationError

from audit.models import AuditEvent
from participants.models import Feedback, Participant
from users.models import Branch, UserAccount
from .models import ACCAnalysisJob
from .prompts.acc import SECTION_TITLES, build_acc_prompt
from .services.acc import render_acc_draft
from .tasks import generate_acc_analysis


@override_settings(DEFAULT_LLM_MODEL="test-model", REPORT_LLM_MODELS=["test-model"])
class ACCReportTests(TestCase):
    def setUp(self):
        self.admin = UserAccount.objects.create_user(username="acc-admin", email="acc@example.com", role="super_admin")
        self.branch = Branch.objects.create(name="Selected branch")
        self.other_branch = Branch.objects.create(name="Other branch")
        self.person = Participant.objects.create(first_name="PRIVATE", last_name="PERSON", branch=self.branch, joined_on="2026-01-05")
        self.feedback = Feedback.objects.create(branch=self.branch, participant=self.person, quote="PRIVATE says: Classes help.",
                                                source="PRIVATE PERSON", date="2026-01-10", consent=True, recorded_by=self.admin)
        self.unconsented = Feedback.objects.create(branch=self.branch, participant=self.person, quote="Not consented",
                                                   source="PRIVATE PERSON", date="2026-01-10", recorded_by=self.admin)
        other_person = Participant.objects.create(first_name="Other", last_name="Person", branch=self.other_branch)
        self.other_feedback = Feedback.objects.create(branch=self.other_branch, participant=other_person, quote="Other branch text",
                                                      source="Other", date="2026-01-10", consent=True, recorded_by=self.admin)
        self.client = APIClient()
        self.client.force_authenticate(self.admin)
        self.scope = {"start_date": "2026-01-01", "end_date": "2026-03-31", "branch_id": str(self.branch.pk)}
        self.payload = {**self.scope, "model": "test-model", "approved_for_acc_and_ai": True,
                        "sources": [{"id": str(self.feedback.pk), "text": "Classes help.", "speaker": "unknown"}]}
        self.source_id = f"F-{self.feedback.pk}"
        self.draft = {"sections": [{"title": SECTION_TITLES[0], "text": "Feedback describes a positive experience.",
                                   "source_ids": [self.source_id]}],
                      "quotes": [{"text": "Classes help.", "source_id": self.source_id}],
                      "review_notes": ["Speaker attribution was not reported."]}

    def queue(self):
        with patch("reporting.views.generate_acc_analysis.apply_async") as enqueue:
            response = self.client.post("/api/reporting/acc/analyse/", self.payload, format="json")
        self.assertEqual(response.status_code, 202, response.data)
        enqueue.assert_called_once()
        return ACCAnalysisJob.objects.get(pk=response.data["job_id"])

    def test_sources_filter_scope_consent_dates_and_do_not_infer_speaker(self):
        response = self.client.get("/api/reporting/acc/sources/", self.scope)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["speaker"], "unknown")
        outside_period = {**self.scope, "start_date": "2026-02-01"}
        self.assertEqual(self.client.get("/api/reporting/acc/sources/", outside_period).data["count"], 0)

    def test_generation_snapshot_privacy_history_and_editing(self):
        job = self.queue()
        prompt = build_acc_prompt(job.statistics)
        self.assertNotIn("PRIVATE", prompt)
        self.assertNotIn("original_text", prompt)
        self.assertNotIn("engagement", prompt)
        self.assertNotIn("attendance_rate", prompt)
        self.assertNotIn("walking_aid", prompt)
        self.assertEqual(job.statistics["aggregates"]["S-enrolments"]["new_enrolments"], 1)
        with patch("reporting.services.acc.get_client", return_value=object()), \
             patch("reporting.services.acc.generate", return_value=json.dumps(self.draft)) as provider:
            generate_acc_analysis.run(str(job.pk))
            generate_acc_analysis.run(str(job.pk))
        provider.assert_called_once()
        self.assertEqual(provider.call_args.kwargs["model"], "test-model")
        job.refresh_from_db()
        self.assertEqual(job.status, "succeeded")
        self.assertIn(f"#acc-source-{self.source_id}", job.narrative)
        self.assertIn("Classes help", job.narrative)
        self.assertEqual(AuditEvent.objects.get(action="report.succeeded", target_id=str(job.pk)).details["report_type"], "acc")
        other_admin = UserAccount.objects.create_user(username="reviewer", email="reviewer@example.com", role="super_admin")
        self.client.force_authenticate(other_admin)
        self.assertEqual(self.client.get("/api/reporting/acc/history/").data["count"], 1)
        url = f"/api/reporting/acc/history/{job.pk}/"
        self.assertEqual(self.client.get(url).data["statistics"], job.statistics)
        self.feedback.quote = "Changed later"
        self.feedback.save()
        self.assertEqual(self.client.get(url).data["statistics"]["sources"][0]["original_text"], "PRIVATE says: Classes help.")
        response = self.client.patch(f"/api/reporting/acc/jobs/{job.pk}/", {"narrative": "Reviewed draft"}, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.client.get(url).data["narrative"], "Reviewed draft")
        self.assertEqual(self.client.get(url).data["statistics"], job.statistics)

    def test_rejects_invalid_source_approval_and_input_before_queueing(self):
        changes = [
            {"approved_for_acc_and_ai": False}, {"sources": []},
            {"sources": [self.payload["sources"][0]] * 2},
            {"sources": [{**self.payload["sources"][0], "text": "   "}]},
            {"sources": [{**self.payload["sources"][0], "speaker": "guessed"}]},
            {"sources": [{**self.payload["sources"][0], "text": "x" * 4001}]},
            {"sources": [{**self.payload["sources"][0], "id": str(self.unconsented.pk)}]},
            {"sources": [{**self.payload["sources"][0], "id": str(self.other_feedback.pk)}]},
            {"start_date": "2026-02-01"}, {"model": "unavailable"},
        ]
        with patch("reporting.views.generate_acc_analysis.apply_async") as enqueue:
            for change in changes:
                with self.subTest(change=change):
                    response = self.client.post("/api/reporting/acc/analyse/", {**self.payload, **change}, format="json")
                    self.assertEqual(response.status_code, 400, response.data)
        enqueue.assert_not_called()
        self.assertFalse(ACCAnalysisJob.objects.exists())

    def test_only_super_admins_can_access_acc_endpoints(self):
        job = self.queue()
        for role in ("branch_manager", "instructor"):
            self.admin.role = role
            self.admin.branch = self.branch
            for path in ("sources/", "history/", f"history/{job.pk}/", f"jobs/{job.pk}/"):
                self.assertEqual(self.client.get(f"/api/reporting/acc/{path}", self.scope).status_code, 403)
            self.assertEqual(self.client.post("/api/reporting/acc/analyse/", self.payload, format="json").status_code, 403)
            self.assertEqual(self.client.patch(f"/api/reporting/acc/jobs/{job.pk}/", {"narrative": "No"}, format="json").status_code, 403)
        self.client.force_authenticate(None)
        self.assertEqual(self.client.get("/api/reporting/acc/history/").status_code, 403)

    def test_worker_rechecks_consent_and_role_before_provider_call(self):
        for changed in ("consent", "role"):
            self.admin.role = "super_admin"
            self.admin.save()
            self.feedback.consent = True
            self.feedback.save()
            job = self.queue()
            if changed == "consent":
                self.feedback.consent = False
                self.feedback.save()
            else:
                self.admin.role = "branch_manager"
                self.admin.branch = self.branch
                self.admin.save()
            with patch("reporting.services.acc.generate") as provider:
                from django.core.exceptions import PermissionDenied
                with self.assertRaises(PermissionDenied):
                    generate_acc_analysis.run(str(job.pk))
                provider.assert_not_called()
            job.refresh_from_db()
            self.assertEqual(job.status, "failed")

    def test_invalid_json_invented_quotes_and_unknown_sources_fail_safely(self):
        job = self.queue()
        invalid = ["not json", "{}", json.dumps({**self.draft, "quotes": [{"text": "Invented", "source_id": self.source_id}]}),
                   json.dumps({**self.draft, "sections": [{**self.draft["sections"][0], "source_ids": ["missing"]}]})]
        for raw in invalid:
            with self.subTest(raw=raw), self.assertRaises((ValueError, ValidationError)):
                render_acc_draft(raw, job.statistics)
        with patch("reporting.services.acc.get_client", return_value=object()), \
             patch("reporting.services.acc.generate", return_value=invalid[-1]):
            with self.assertRaises(ValueError):
                generate_acc_analysis.run(str(job.pk))
        job.refresh_from_db()
        self.assertEqual(job.status, "failed")
        self.assertIsNone(job.narrative)

    def test_uncited_sections_are_omitted_with_review_notes_without_losing_supported_draft(self):
        job = self.queue()
        sections = [
            {"title": title, "text": "Uncited claim that must not appear." if i in (2, 3, 5) else "Supported feedback summary.",
             "source_ids": [] if i in (2, 3, 5) else [self.source_id]}
            for i, title in enumerate(SECTION_TITLES)
        ]
        raw = json.dumps({**self.draft, "sections": sections, "review_notes": []})
        with patch("reporting.services.acc.get_client", return_value=object()), \
             patch("reporting.services.acc.generate", return_value=raw) as provider:
            generate_acc_analysis.run(str(job.pk))
        provider.assert_called_once()
        job.refresh_from_db()
        self.assertEqual(job.status, "succeeded")
        self.assertIn("Supported feedback summary.", job.narrative)
        self.assertNotIn("Uncited claim", job.narrative)
        self.assertIn("## Review notes", job.narrative)
        for index in (2, 3, 5):
            self.assertNotIn(f"## {SECTION_TITLES[index]}", job.narrative)
            self.assertIn(f"{SECTION_TITLES[index]}: section omitted", job.narrative)
        self.assertIn(f"#acc-source-{self.source_id}", job.narrative)

    def test_uncited_sections_do_not_bypass_evidence_validation(self):
        job = self.queue()
        uncited = {**self.draft["sections"][0], "source_ids": []}
        with self.assertRaisesRegex(ValueError, "no sections with source references"):
            render_acc_draft(json.dumps({**self.draft, "sections": [uncited]}), job.statistics)
        unknown = {"title": SECTION_TITLES[1], "text": "Claim", "source_ids": ["invented"]}
        with self.assertRaisesRegex(ValueError, "Unknown source"):
            render_acc_draft(json.dumps({**self.draft, "sections": [uncited, unknown]}), job.statistics)
        for invalid_refs in (None, "not a list"):
            with self.subTest(invalid_refs=invalid_refs), self.assertRaises(ValidationError):
                render_acc_draft(json.dumps({**self.draft, "sections": [{**uncited, "source_ids": invalid_refs}]}), job.statistics)
