import json
from datetime import date, time
from unittest.mock import Mock, patch

from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import PermissionDenied, ValidationError
from django.test import TestCase

from participants.models import Participant
from reporting.services.attendance import analyse_attendance, attendance_statistics
from sessions.models import AttendanceRecord, ProgrammeSession
from users.models import Branch, UserAccount


class AttendanceReportingTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.branch = Branch.objects.create(name="Dunedin")
        cls.other_branch = Branch.objects.create(name="Other")
        cls.manager = UserAccount.objects.create_user(
            username="manager", email="manager@example.com",
            role=UserAccount.Role.BRANCH_MANAGER, branch=cls.branch,
        )
        cls.admin = UserAccount.objects.create_user(
            username="admin", email="admin@example.com", role=UserAccount.Role.SUPER_ADMIN,
        )
        cls.people = [Participant.objects.create(
            first_name=f"Person {i}", last_name="Private", branch=cls.branch,
        ) for i in range(3)]

    def session(self, day, statuses, finalised=True, branch=None):
        session = ProgrammeSession.objects.create(
            branch=branch or self.branch, created_by=self.manager,
            date=day, time=time(10), activity="Class",
            attendance_finalised=finalised,
        )
        AttendanceRecord.objects.bulk_create([
            AttendanceRecord(session=session, participant=person, status=status)
            for person, status in zip(self.people, statuses)
        ])
        return session

    def statistics(self, **kwargs):
        return attendance_statistics(**{
            "user": self.manager, "start_date": date(2026, 1, 1),
            "end_date": date(2026, 3, 31), **kwargs,
        })

    def test_finalised_empty_and_incomplete_sessions_have_distinct_meanings(self):
        self.session(date(2026, 1, 1), ["present", "present", "absent"])
        self.session(date(2026, 1, 2), ["absent", "absent", "absent"])
        self.session(date(2026, 2, 1), ["present", "absent"])
        self.session(date(2026, 2, 2), ["present"], finalised=False)
        result = self.statistics()
        self.assertEqual(result["totals"], {
            "total_sessions": 4, "finalised_sessions": 3,
            "incomplete_sessions": 1, "empty_sessions": 1,
            "total_attendances": 3, "total_roster_places": 8,
            "distinct_attendees": 2, "attendance_rate_percent": 37.5,
            "average_attendance": 1.0,
        })
        self.assertEqual(len(result["sessions"]), 3)
        january, february, march = result["monthly"]
        self.assertEqual(january["attendance_rate_percent"], 33.33)
        self.assertEqual(february["attendances_change"], -1)
        self.assertEqual(february["attendance_rate_change_percentage_points"], 16.67)
        self.assertIsNone(march["attendance_rate_percent"])
        self.assertIsNone(march["attendances_change"])

    def test_dates_are_inclusive_and_branch_scope_is_enforced(self):
        self.session(date(2025, 12, 31), ["present"])
        self.session(date(2026, 1, 1), ["present"])
        self.session(date(2026, 3, 31), ["present"])
        self.session(date(2026, 4, 1), ["present"])
        self.session(date(2026, 1, 2), [], branch=self.other_branch)
        self.assertEqual(self.statistics()["totals"]["total_sessions"], 2)
        self.assertEqual(self.statistics(user=self.admin)["totals"]["total_sessions"], 3)
        self.assertEqual(self.statistics(user=self.admin, branch_id=self.other_branch.pk)["totals"]["total_sessions"], 1)
        with self.assertRaises(PermissionDenied):
            self.statistics(branch_id=self.other_branch.pk)

    def test_invalid_scope_fails_before_provider_call(self):
        with self.assertRaises(PermissionDenied):
            self.statistics(user=AnonymousUser())
        self.manager.branch = None
        with self.assertRaises(PermissionDenied):
            self.statistics()
        self.manager.branch = self.branch
        with self.assertRaises(ValidationError):
            self.statistics(start_date=date(2027, 1, 1))
        with self.assertRaises(ValidationError):
            self.statistics(branch_id="not-a-uuid")

    def test_zero_denominators_and_no_finalised_data(self):
        result = self.statistics()
        self.assertIsNone(result["totals"]["average_attendance"])
        self.assertIsNone(result["totals"]["attendance_rate_percent"])
        self.session(date(2026, 1, 1), [])
        result = self.statistics()
        self.assertEqual(result["totals"]["empty_sessions"], 1)
        self.assertEqual(result["totals"]["average_attendance"], 0)
        self.assertIsNone(result["totals"]["attendance_rate_percent"])

    def test_no_query_per_session(self):
        for day in range(1, 11):
            self.session(date(2026, 1, day), ["present", "absent"])
        # Branch existence, grouped sessions, distinct attendees.
        with self.assertNumQueries(3):
            self.statistics()

    @patch("reporting.services.attendance.generate", return_value="A summary.")
    def test_narrative_receives_aggregates_only(self, generate):
        session = self.session(date(2026, 1, 1), ["present"])
        client = Mock()
        result = analyse_attendance(
            user=self.manager, start_date=date(2026, 1, 1),
            end_date=date(2026, 3, 31), client=client, model="test-model",
        )
        self.assertEqual(result["narrative"], "A summary.")
        generate.assert_called_once()
        arguments = generate.call_args.kwargs
        self.assertIs(arguments["client"], client)
        self.assertEqual(arguments["model"], "test-model")
        payload = json.loads(arguments["prompt"])
        self.assertEqual(payload["totals"]["total_attendances"], 1)
        self.assertNotIn("sessions", payload)
        for private_value in (str(session.pk), str(self.people[0].pk), "Private"):
            self.assertNotIn(private_value, arguments["prompt"])

    @patch("reporting.services.attendance.get_client")
    @patch("reporting.services.attendance.generate")
    def test_incomplete_only_report_skips_provider(self, generate, get_client):
        self.session(date(2026, 1, 1), ["present"], finalised=False)
        result = analyse_attendance(
            user=self.manager, start_date=date(2026, 1, 1), end_date=date(2026, 3, 31),
        )
        self.assertEqual(result["statistics"]["totals"]["incomplete_sessions"], 1)
        self.assertIsNone(result["narrative"])
        generate.assert_not_called()
        get_client.assert_not_called()

    @patch("reporting.services.attendance.generate", side_effect=RuntimeError("Unavailable"))
    def test_provider_errors_remain_visible(self, generate):
        self.session(date(2026, 1, 1), ["present"])
        with self.assertRaises(RuntimeError):
            analyse_attendance(
                user=self.manager, start_date=date(2026, 1, 1),
                end_date=date(2026, 3, 31), client=Mock(),
            )
        self.assertEqual(self.statistics()["totals"]["total_attendances"], 1)


class AttendanceReportAPITests(TestCase):
    def setUp(self):
        from rest_framework.test import APIClient
        self.client = APIClient()
        self.branch = Branch.objects.create(name="Reporting branch")
        self.other = Branch.objects.create(name="Another branch")
        self.user = UserAccount.objects.create_user(
            username="report-manager", email="report-manager@example.com",
            role=UserAccount.Role.BRANCH_MANAGER, branch=self.branch,
        )
        self.client.force_authenticate(self.user)
        self.scope = {"start_date": "2026-01-01", "end_date": "2026-03-31"}
        self.url = "/api/reporting/attendance/"
        self.analysis_url = self.url + "analyse/"
        ProgrammeSession.objects.create(
            branch=self.branch, created_by=self.user, date=date(2026, 1, 1),
            time=time(10), activity="Empty finalised class", attendance_finalised=True,
        )

    @patch("reporting.services.attendance.generate")
    def test_get_statistics_never_generates_narrative(self, generate):
        response = self.client.get(self.url, self.scope)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["totals"]["empty_sessions"], 1)
        self.assertEqual(response.data["scope"]["branch_id"], str(self.branch.pk))
        generate.assert_not_called()

    def test_filters_are_validated(self):
        for payload in (
            {}, {**self.scope, "start_date": "invalid"},
            {**self.scope, "end_date": "2025-01-01"},
            {**self.scope, "end_date": "2050-01-01"},
            {**self.scope, "branch_id": "invalid"},
        ):
            with self.subTest(payload=payload):
                self.assertEqual(self.client.get(self.url, payload).status_code, 400)
                self.assertEqual(self.client.post(self.analysis_url, payload, format="json").status_code, 400)

    @patch("reporting.services.attendance.generate")
    def test_manager_cannot_request_another_branch(self, generate):
        payload = {**self.scope, "branch_id": str(self.other.pk)}
        self.assertEqual(self.client.get(self.url, payload).status_code, 403)
        self.assertEqual(self.client.post(self.analysis_url, payload, format="json").status_code, 403)
        generate.assert_not_called()

    def test_instructors_and_anonymous_users_cannot_access_reports(self):
        self.user.role = UserAccount.Role.INSTRUCTOR
        self.user.save()
        for user in (self.user, None):
            self.client.force_authenticate(user)
            self.assertEqual(self.client.get(self.url, self.scope).status_code, 403)
            self.assertEqual(self.client.post(self.analysis_url, self.scope, format="json").status_code, 403)

    @patch("reporting.services.attendance.get_client", return_value=Mock())
    @patch("reporting.services.attendance.generate", return_value="One empty session.")
    def test_post_returns_narrative_and_its_statistics(self, generate, get_client):
        response = self.client.post(self.analysis_url, self.scope, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["narrative"], "One empty session.")
        self.assertEqual(response.data["statistics"]["totals"]["finalised_sessions"], 1)
        generate.assert_called_once()

    @patch("reporting.views.analyse_attendance", side_effect=ValueError("private provider response"))
    def test_provider_failure_does_not_expose_details_or_break_statistics(self, analyse):
        response = self.client.post(self.analysis_url, self.scope, format="json")
        self.assertEqual(response.status_code, 502)
        self.assertNotIn("private", str(response.data))
        self.assertEqual(self.client.get(self.url, self.scope).status_code, 200)

    def test_super_admin_can_select_all_or_one_branch(self):
        self.user.role = UserAccount.Role.SUPER_ADMIN
        self.user.save()
        self.assertIsNone(self.client.get(self.url, self.scope).data["scope"]["branch_id"])
        response = self.client.get(self.url, {**self.scope, "branch_id": str(self.other.pk)})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["totals"]["total_sessions"], 0)
