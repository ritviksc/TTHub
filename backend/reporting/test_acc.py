import json
from datetime import time
from unittest.mock import patch

from django.test import TestCase, override_settings
from rest_framework.test import APIClient
from rest_framework.exceptions import ValidationError

from audit.models import AuditEvent
from participants.models import Feedback, Participant
from sessions.models import AttendanceRecord, ProgrammeSession
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
                                   "source_ids": [self.source_id],
                                   "quotes": [{"text": "Classes help.", "source_id": self.source_id}]}],
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

    def test_feedback_created_by_each_role_enters_report_sources_only_with_consent(self):
        included = {str(self.feedback.pk)}
        speakers = {str(self.feedback.pk): Feedback.Speaker.UNKNOWN}
        for index, role in enumerate(UserAccount.Role.values):
            user = self.admin if role == 'super_admin' else UserAccount.objects.create_user(
                username=f"feedback-{role}", email=f"feedback-{role}@example.com", role=role, branch=self.branch,
            )
            self.client.force_authenticate(user)
            for consent in (False, True):
                response = self.client.post('/api/participants/feedback/', {
                    'participant': str(self.person.pk), 'quote': 'A recorded experience.',
                    'date': '2026-01-12', 'consent': consent,
                    'speaker': Feedback.Speaker.values[index],
                }, format='json')
                self.assertEqual(response.status_code, 201, response.data)
                if consent:
                    included.add(str(response.data['id']))
                    speakers[str(response.data['id'])] = response.data['speaker']
        self.client.force_authenticate(self.admin)
        response = self.client.get('/api/reporting/acc/sources/', self.scope)
        self.assertEqual(response.status_code, 200)
        self.assertEqual({row['id'] for row in response.data['results']}, included)
        self.assertEqual(response.data['count'], len(included))
        self.assertEqual({row['id']: row['speaker'] for row in response.data['results']}, speakers)

    def test_report_carries_recorded_speaker_without_review_attribution_and_ignores_overrides(self):
        self.feedback.speaker = Feedback.Speaker.KAUMATUA
        self.feedback.save(update_fields=['speaker'])
        response = self.client.get('/api/reporting/acc/sources/', self.scope)
        self.assertEqual(response.data['results'][0]['speaker'], 'kaumātua')
        self.payload['sources'][0].pop('speaker')
        job = self.queue()
        self.assertEqual(job.statistics['sources'][0]['speaker'], 'kaumātua')
        self.assertEqual(json.loads(build_acc_prompt(job.statistics))['feedback'][0]['speaker'], 'kaumātua')
        self.payload['sources'][0]['speaker'] = 'kaimahi'
        self.assertEqual(self.queue().statistics['sources'][0]['speaker'], 'kaumātua')

    def test_generation_snapshot_privacy_history_and_editing(self):
        job = self.queue()
        prompt = build_acc_prompt(job.statistics)
        self.assertNotIn("PRIVATE", prompt)
        self.assertNotIn("original_text", prompt)
        self.assertEqual(json.loads(prompt)["statistics"]["S-engagement"], job.statistics["aggregates"]["S-engagement"])
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

    def test_engagement_uses_branch_registrations_and_weighted_finalised_attendance(self):
        self.branch.region = "Ōtepoti"
        self.branch.save()
        existing = Participant.objects.create(first_name="Existing", last_name="Private", branch=self.branch, joined_on="2025-12-31")
        unknown = Participant.objects.create(first_name="Unknown", last_name="Private", branch=self.branch)
        inactive = Participant.objects.create(first_name="Inactive", last_name="Private", branch=self.branch,
                                             joined_on="2026-03-31", is_active=False)
        Participant.objects.create(first_name="Later", last_name="Private", branch=self.branch, joined_on="2026-04-01")

        def session(day, statuses, finalised=True, branch=None):
            record = ProgrammeSession.objects.create(branch=branch or self.branch, created_by=self.admin, date=day,
                                                     time=time(10), activity="Class", attendance_finalised=finalised)
            AttendanceRecord.objects.bulk_create([
                AttendanceRecord(session=record, participant=person, status=status)
                for person, status in statuses
            ])

        session("2026-01-01", [(self.person, "present"), (existing, "absent"), (unknown, "absent")])
        session("2026-03-31", [(self.person, "present")])
        session("2026-02-01", [(self.person, "absent"), (inactive, "absent")], finalised=False)
        session("2025-12-31", [(self.person, "absent")])
        session("2026-04-01", [(self.person, "absent")])
        job = self.queue()
        rows = job.statistics["aggregates"]["S-engagement"]["branches"]
        self.assertEqual(len(rows), 1)
        row = rows[0]
        self.assertEqual(row["entity"], self.branch.name)
        self.assertEqual(row["location"], "Ōtepoti")
        self.assertEqual(row["participants"], 3)  # Active, joined by end date; unknown join date included.
        self.assertEqual(row["new_participants"], 2)  # Inclusive period, including a now-inactive registration.
        self.assertEqual(row["total_sessions"], 3)
        self.assertEqual(row["finalised_sessions"], 2)
        self.assertEqual(row["total_attendances"], 2)
        self.assertEqual(row["total_roster_places"], 4)
        self.assertEqual(row["engagement_percent"], 50)  # Weighted, not the mean of 33.33% and 100%.
        with patch("reporting.services.acc.generate", return_value=json.dumps({
            **self.draft, "sections": [{**self.draft["sections"][0], "source_ids": ["S-engagement", self.source_id]}],
        })), patch("reporting.services.acc.get_client", return_value=object()):
            generate_acc_analysis.run(str(job.pk))
        job.refresh_from_db()
        self.assertEqual(job.status, "succeeded")

    def test_all_branches_include_zero_and_missing_engagement_without_source_selection_bias(self):
        absent_branch = Branch.objects.create(name="Absent branch", region="Whangārei")
        empty_branch = Branch.objects.create(name="Empty branch")
        empty_register = Branch.objects.create(name="Empty register")
        incomplete_branch = Branch.objects.create(name="Incomplete branch")
        record = ProgrammeSession.objects.create(branch=absent_branch, created_by=self.admin, date="2026-02-01",
                                                time=time(10), activity="Class", attendance_finalised=True)
        person = Participant.objects.create(first_name="Absent", last_name="Private", branch=absent_branch, joined_on="2026-01-01")
        AttendanceRecord.objects.create(session=record, participant=person, status="absent")
        ProgrammeSession.objects.create(branch=empty_register, created_by=self.admin, date="2026-02-01",
                                        time=time(10), activity="Class", attendance_finalised=True)
        incomplete = ProgrammeSession.objects.create(branch=incomplete_branch, created_by=self.admin, date="2026-02-01",
                                                     time=time(10), activity="Class", attendance_finalised=False)
        AttendanceRecord.objects.create(session=incomplete, participant=person, status="present")
        self.payload.pop("branch_id")
        job = self.queue()
        rows = job.statistics["aggregates"]["S-engagement"]["branches"]
        self.assertEqual([row["entity"] for row in rows], sorted(branch.name for branch in Branch.objects.all()))
        by_branch = {row["branch_id"]: row for row in rows}
        self.assertEqual(by_branch[str(absent_branch.pk)]["engagement_percent"], 0)
        self.assertEqual(by_branch[str(absent_branch.pk)]["new_participants"], 1)
        for branch in (empty_branch, empty_register, incomplete_branch, self.other_branch):
            self.assertIsNone(by_branch[str(branch.pk)]["engagement_percent"])
        self.assertEqual(by_branch[str(empty_branch.pk)]["participants"], 0)
        self.assertIsNone(by_branch[str(empty_branch.pk)]["location"])
        self.assertEqual(by_branch[str(incomplete_branch.pk)]["total_roster_places"], 0)
        self.assertEqual(by_branch[str(self.other_branch.pk)]["participants"], 1)
        self.assertEqual(by_branch[str(self.other_branch.pk)]["new_participants"], 0)
        prompt_rows = json.loads(build_acc_prompt(job.statistics))["statistics"]["S-engagement"]["branches"]
        self.assertEqual(prompt_rows, rows)

    def test_rejects_invalid_source_approval_and_input_before_queueing(self):
        changes = [
            {"approved_for_acc_and_ai": False}, {"sources": []},
            {"sources": [self.payload["sources"][0]] * 2},
            {"sources": [{**self.payload["sources"][0], "text": "   "}]},
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
        invalid = ["not json", "{}", json.dumps({**self.draft, "sections": [{**self.draft["sections"][0],
                   "quotes": [{"text": "Invented", "source_id": self.source_id}]}]}),
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
             "source_ids": [] if i in (2, 3, 5) else [self.source_id],
             "quotes": [] if i in (2, 3, 5) else self.draft["sections"][0]["quotes"]}
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
        unknown = {"title": SECTION_TITLES[1], "text": "Claim", "source_ids": ["invented"], "quotes": []}
        with self.assertRaisesRegex(ValueError, "Unknown source"):
            render_acc_draft(json.dumps({**self.draft, "sections": [uncited, unknown]}), job.statistics)
        for invalid_refs in (None, "not a list"):
            with self.subTest(invalid_refs=invalid_refs), self.assertRaises(ValidationError):
                render_acc_draft(json.dumps({**self.draft, "sections": [{**uncited, "source_ids": invalid_refs}]}), job.statistics)

    def test_engagement_rounds_to_nearest_five_with_halfway_values_up(self):
        people = [self.person] + [Participant.objects.create(
            first_name="Sample", last_name=str(index), branch=self.branch,
        ) for index in range(40)]
        session = ProgrammeSession.objects.create(branch=self.branch, created_by=self.admin, date="2026-01-10",
                                                 time=time(10), activity="Class", attendance_finalised=True)
        for present, roster, expected in [(17, 20, 85), (18, 21, 85), (35, 40, 90), (1, 40, 5), (1, 41, 0), (0, 20, 0), (20, 20, 100), (0, 0, None)]:
            with self.subTest(present=present, roster=roster):
                session.attendance.all().delete()
                AttendanceRecord.objects.bulk_create([
                    AttendanceRecord(session=session, participant=person, status="present" if index < present else "absent")
                    for index, person in enumerate(people[:roster])
                ])
                row = self.queue().statistics["aggregates"]["S-engagement"]["branches"][0]
                self.assertEqual(row["engagement_percent"], expected)
                self.assertEqual(row["total_attendances"], present)
                self.assertEqual(row["total_roster_places"], roster)

    def test_each_section_renders_its_own_exact_quotations_before_its_summary(self):
        job = self.queue()
        second_source = {"id": "F-second", "text": "New exercises are great, however they are very wordy."}
        job.statistics["sources"].append(second_source)
        second_section = {
            "title": SECTION_TITLES[3], "text": "Feedback requests clearer exercise instructions.",
            "source_ids": [second_source["id"]], "quotes": [{"text": second_source["text"], "source_id": second_source["id"]}],
        }
        narrative = render_acc_draft(json.dumps({**self.draft, "sections": [self.draft["sections"][0], second_section]}), job.statistics)
        first_block, second_block = narrative.split(f"## {second_section['title']}")
        self.assertLess(first_block.index("> Classes help"), first_block.index("**Summary**"))
        self.assertLess(first_block.index("**Summary**"), first_block.index(self.draft["sections"][0]["text"]))
        self.assertLess(second_block.index("> New exercises"), second_block.index("**Summary**"))
        self.assertLess(second_block.index("**Summary**"), second_block.index(second_section["text"]))
        self.assertNotIn(second_source["text"], first_block)
        self.assertNotIn("Classes help", second_block)
        self.assertNotIn("## Supporting quotations", narrative)
        with self.assertRaisesRegex(ValueError, "no supporting quotations"):
            render_acc_draft(json.dumps({**self.draft, "sections": [{**second_section, "quotes": []}]}), job.statistics)
        mismatched = {**self.draft["sections"][0], "quotes": second_section["quotes"]}
        with self.assertRaisesRegex(ValueError, "not a supporting source for its section"):
            render_acc_draft(json.dumps({**self.draft, "sections": [mismatched]}), job.statistics)
        quoted_markup = "**Māori** [text](https://example.com)\nA second line."
        job.statistics["sources"][0]["text"] = quoted_markup
        section = {**self.draft["sections"][0], "quotes": [{"text": quoted_markup, "source_id": self.source_id}]}
        escaped = render_acc_draft(json.dumps({**self.draft, "sections": [section]}), job.statistics)
        self.assertIn("> \\*\\*Māori\\*\\*", escaped)
        self.assertIn("\n> A second line", escaped)

    def test_worker_accepts_more_than_four_verified_quotes_and_checks_the_last_quote(self):
        model = "ONCAMPUS/gemma-4-12B-kt"
        for index in range(5):
            feedback = Feedback.objects.create(branch=self.branch, participant=self.person, recorded_by=self.admin,
                                              date="2026-01-10", consent=True, source="Sample kaimahi feedback",
                                              quote=f"Attendance barrier {index + 1}: whānau commitments.")
            self.payload["sources"].append({"id": str(feedback.pk), "text": feedback.quote, "speaker": "kaimahi"})
        self.payload["model"] = model
        with override_settings(REPORT_LLM_MODELS=[model]):
            job = self.queue()
        section = {
            "title": SECTION_TITLES[4], "text": "Selected feedback describes attendance barriers.",
            "source_ids": [source["id"] for source in job.statistics["sources"]],
            "quotes": [{"text": source["text"], "source_id": source["id"]} for source in job.statistics["sources"]],
        }
        draft = {"sections": [section], "review_notes": []}
        with patch("reporting.services.acc.get_client", return_value=object()), \
             patch("reporting.services.acc.generate", return_value=json.dumps(draft)) as provider:
            generate_acc_analysis.run(str(job.pk))
        job.refresh_from_db()
        self.assertEqual(job.status, "succeeded")
        self.assertEqual(provider.call_args.kwargs["model"], model)
        self.assertEqual(job.narrative.count("> "), 6)
        for quote in section["quotes"]:
            text = quote["text"].removesuffix(".")  # The renderer escapes Markdown punctuation.
            self.assertIn(text, job.narrative)
            self.assertLess(job.narrative.index(text), job.narrative.index("**Summary**"))
        for change in ({"text": "Invented quotation"}, {"source_id": "missing"}):
            invalid = {**section, "quotes": [*section["quotes"][:-1], {**section["quotes"][-1], **change}]}
            with self.subTest(change=change), self.assertRaisesRegex(ValueError, "does not match its reviewed source"):
                render_acc_draft(json.dumps({**draft, "sections": [invalid]}), job.statistics)
        uncited = {**section, "source_ids": section["source_ids"][:-1]}
        with self.assertRaisesRegex(ValueError, "not a supporting source for its section"):
            render_acc_draft(json.dumps({**draft, "sections": [uncited]}), job.statistics)
