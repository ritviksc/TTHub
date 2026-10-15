from datetime import date, time, datetime, timezone as datetime_timezone
from unittest.mock import patch

from django.test import TestCase
from rest_framework.test import APIClient

from participants.models import Participant
from users.models import Branch, UserAccount

from .models import AttendanceRecord, ProgrammeSession
from .serializers import AttendanceRecordSerializer


class SessionModelTests(TestCase):
    def setUp(self):
        self.branch = Branch.objects.create(name="Dunedin")
        self.instructor = UserAccount.objects.create_user(
            username="instructor@example.com",
            email="instructor@example.com",
            password="SafePass123!",
            role=UserAccount.Role.INSTRUCTOR,
            branch=self.branch,
        )
        self.participant = Participant.objects.create(
            first_name="Aroha", last_name="Ngata", branch=self.branch
        )
        self.session = ProgrammeSession.objects.create(
            branch=self.branch,
            created_by=self.instructor,
            date=date.today(),
            time=time(10, 0),
            activity="Strength and mobility",
        )

    def test_marking_present_clears_an_absence_reason(self):
        AttendanceRecord.objects.create(session=self.session, participant=self.participant)
        serializer = AttendanceRecordSerializer(
            data={"status": "present", "absence_reason": "no_show"}
        )

        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data["absence_reason"], "")


class SessionDateTests(TestCase):
    def setUp(self):
        branch = Branch.objects.create(name="Dunedin")
        instructor = UserAccount.objects.create_user(
            username="instructor@example.com", email="instructor@example.com",
            role=UserAccount.Role.INSTRUCTOR, branch=branch,
        )
        self.client = APIClient()
        self.client.force_authenticate(instructor)

    @patch("django.utils.timezone.now", return_value=datetime(2026, 9, 20, 13, tzinfo=datetime_timezone.utc))
    def test_rejects_previous_day_using_new_zealand_date(self, now):
        response = self.client.post("/api/sessions/", {
            "date": "2026-09-20", "time": "23:59", "activity": "Class",
        }, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertIn("date", response.data)
        self.assertFalse(ProgrammeSession.objects.exists())
        self.assertFalse(AttendanceRecord.objects.exists())

    @patch("django.utils.timezone.now", return_value=datetime(2026, 9, 20, 13, tzinfo=datetime_timezone.utc))
    def test_accepts_today_and_future_dates(self, now):
        for day in ("2026-09-21", "2026-09-22"):
            with self.subTest(day=day):
                response = self.client.post("/api/sessions/", {
                    "date": day, "time": "09:00", "activity": "Class",
                }, format="json")
                self.assertEqual(response.status_code, 201, response.data)


class SessionCreationTests(TestCase):
    def setUp(self):
        self.branch = Branch.objects.create(name="Own branch")
        self.other = Branch.objects.create(name="Other branch")
        self.participant = Participant.objects.create(first_name="Active", last_name="Person", branch=self.branch)
        Participant.objects.create(first_name="Inactive", last_name="Person", branch=self.branch, is_active=False)
        Participant.objects.create(first_name="Foreign", last_name="Person", branch=self.other)
        self.client = APIClient()

    def test_instructors_and_managers_create_only_in_their_branch_with_active_roster(self):
        from django.utils import timezone
        for role in (UserAccount.Role.INSTRUCTOR, UserAccount.Role.BRANCH_MANAGER):
            with self.subTest(role=role):
                user = UserAccount.objects.create_user(username=role, email=f"{role}@example.com", role=role, branch=self.branch)
                self.client.force_authenticate(user)
                response = self.client.post("/api/sessions/", {
                    "date": timezone.localdate(), "time": "09:00", "activity": "Class",
                    "branch": str(self.other.pk), "created_by": str(user.pk),
                }, format="json")
                self.assertEqual(response.status_code, 201, response.data)
                session = ProgrammeSession.objects.get(pk=response.data["id"])
                self.assertEqual(session.branch_id, self.branch.pk)
                self.assertEqual(session.created_by_id, user.pk)
                self.assertEqual(list(session.attendance.values_list("participant_id", flat=True)), [self.participant.pk])

    def test_unassigned_staff_and_super_admin_without_selected_branch_cannot_create_sessions(self):
        from django.utils import timezone
        for role in UserAccount.Role.values:
            with self.subTest(role=role):
                user = UserAccount.objects.create_user(
                    username=role, email=f"{role}@example.com", role=role,
                    branch=self.branch if role == UserAccount.Role.SUPER_ADMIN else None,
                )
                self.client.force_authenticate(user)
                response = self.client.post("/api/sessions/", {
                    "date": timezone.localdate(), "time": "09:00", "activity": "Class",
                }, format="json")
                self.assertEqual(response.status_code, 400, response.data)
        self.assertFalse(ProgrammeSession.objects.exists())
        self.assertFalse(AttendanceRecord.objects.exists())

    def test_super_admin_creates_in_selected_branch_with_only_its_active_roster(self):
        from django.utils import timezone
        admin = UserAccount.objects.create_user(username="national", email="national@example.nz", role="super_admin")
        Participant.objects.create(first_name="Inactive", last_name="Foreign", branch=self.other, is_active=False)
        self.client.force_authenticate(admin)
        for branch in (self.branch, self.other):
            with self.subTest(branch=branch):
                response = self.client.post("/api/sessions/", {
                    "date": timezone.localdate(), "time": "09:00", "activity": "Class",
                    "branch": str(branch.pk), "created_by": "forged",
                }, format="json")
                self.assertEqual(response.status_code, 201, response.data)
                self.assertEqual(response.json()["branch"], str(branch.pk))
                self.assertEqual(response.data["branch_name"], branch.name)
                session = ProgrammeSession.objects.get(pk=response.data["id"])
                self.assertEqual(session.created_by_id, admin.pk)
                self.assertEqual(session.branch_id, branch.pk)
                self.assertEqual(set(session.attendance.values_list("participant_id", flat=True)),
                                 set(Participant.objects.filter(branch=branch, is_active=True).values_list("pk", flat=True)))

    def test_super_admin_branch_selection_must_be_a_real_branch_and_date_cannot_be_past(self):
        from django.utils import timezone
        from datetime import timedelta
        from uuid import uuid4
        admin = UserAccount.objects.create_user(username="national", email="national@example.nz", role="super_admin")
        self.client.force_authenticate(admin)
        for branch in (None, "", "not-a-uuid", str(uuid4())):
            with self.subTest(branch=branch):
                response = self.client.post("/api/sessions/", {
                    "date": timezone.localdate(), "time": "09:00", "activity": "Class", "branch": branch,
                }, format="json")
                self.assertEqual(response.status_code, 400, response.data)
                self.assertIn("branch", response.data)
        response = self.client.post("/api/sessions/", {
            "date": timezone.localdate() - timedelta(days=1), "time": "09:00", "activity": "Class", "branch": str(self.branch.pk),
        }, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertIn("date", response.data)
        self.assertFalse(ProgrammeSession.objects.exists())
        self.assertFalse(AttendanceRecord.objects.exists())


class AttendanceFinalisationTests(TestCase):
    def setUp(self):
        SessionModelTests.setUp(self)
        from rest_framework.test import APIClient
        self.client = APIClient()
        self.client.force_authenticate(self.instructor)
        self.record = AttendanceRecord.objects.create(
            session=self.session, participant=self.participant,
        )
        self.state_url = f"/api/sessions/{self.session.pk}/attendance-state/"
        self.record_url = f"/api/sessions/{self.session.pk}/attendance/{self.record.pk}/"

    def test_empty_session_can_be_finalised_and_reopened(self):
        self.assertFalse(self.session.attendance_finalised)
        response = self.client.patch(self.state_url, {"attendance_finalised": True}, format="json")
        self.assertEqual(response.status_code, 200)
        self.session.refresh_from_db()
        self.assertTrue(self.session.attendance_finalised)
        detail = self.client.get(f"/api/sessions/{self.session.pk}/")
        self.assertTrue(detail.data["attendance_finalised"])
        self.assertEqual(detail.data["present_count"], 0)
        self.assertEqual(self.client.patch(self.record_url, {"status": "present"}, format="json").status_code, 409)
        self.record.refresh_from_db()
        self.assertEqual(self.record.status, "absent")
        self.assertEqual(self.client.patch(self.state_url, {"attendance_finalised": False}, format="json").status_code, 200)
        self.assertEqual(self.client.patch(self.record_url, {"status": "present"}, format="json").status_code, 200)
        self.session.refresh_from_db()
        self.assertFalse(self.session.attendance_finalised)

    def test_other_branch_cannot_finalise(self):
        self.instructor.branch = Branch.objects.create(name="Other branch")
        self.instructor.save()
        self.assertEqual(self.client.patch(self.state_url, {"attendance_finalised": True}, format="json").status_code, 404)
        self.session.refresh_from_db()
        self.assertFalse(self.session.attendance_finalised)

    def test_manager_can_mark_finalise_and_reopen_instructor_session(self):
        manager = UserAccount.objects.create_user(
            username="manager", email="manager@example.com", role="branch_manager", branch=self.branch,
        )
        self.client.force_authenticate(manager)
        response = self.client.patch(self.record_url, {"status": "absent", "absence_reason": "transport_issue"}, format="json")
        self.assertEqual(response.status_code, 200, response.data)
        self.record.refresh_from_db()
        self.assertEqual(self.record.absence_reason, "transport_issue")
        self.assertEqual(self.client.patch(self.state_url, {"attendance_finalised": True}, format="json").status_code, 200)
        self.assertEqual(self.client.patch(self.record_url, {"status": "present"}, format="json").status_code, 409)
        self.assertEqual(self.client.patch(self.state_url, {"attendance_finalised": False}, format="json").status_code, 200)
        self.assertEqual(self.client.patch(self.record_url, {"status": "present"}, format="json").status_code, 200)
        self.record.refresh_from_db()
        self.session.refresh_from_db()
        self.assertEqual(self.record.status, "present")
        self.assertEqual(self.record.absence_reason, "")
        self.assertFalse(self.session.attendance_finalised)

    def test_foreign_and_unassigned_managers_cannot_change_attendance(self):
        other = Branch.objects.create(name="Other branch")
        for branch in (other, None):
            with self.subTest(branch=branch):
                manager = UserAccount.objects.create_user(
                    username=f"manager-{branch}", email=f"manager-{branch.pk if branch else 'none'}@example.com",
                    role="branch_manager", branch=branch,
                )
                self.client.force_authenticate(manager)
                self.assertEqual(self.client.get(f"/api/sessions/{self.session.pk}/").status_code, 404)
                self.assertEqual(self.client.patch(self.state_url, {"attendance_finalised": True}, format="json").status_code, 404)
                self.assertEqual(self.client.patch(self.record_url, {"status": "present"}, format="json").status_code, 404)
        self.record.refresh_from_db()
        self.session.refresh_from_db()
        self.assertEqual(self.record.status, "absent")
        self.assertFalse(self.session.attendance_finalised)

    def test_super_admin_and_anonymous_users_cannot_change_attendance(self):
        admin = UserAccount.objects.create_user(username="admin", email="admin@example.com", role="super_admin", branch=self.branch)
        for user in (admin, None):
            with self.subTest(user=user):
                self.client.force_authenticate(user)
                self.assertEqual(self.client.patch(self.state_url, {"attendance_finalised": True}, format="json").status_code, 403)
                self.assertEqual(self.client.patch(self.record_url, {"status": "present"}, format="json").status_code, 403)

    def test_state_is_required(self):
        self.assertEqual(self.client.patch(self.state_url, {}, format="json").status_code, 400)

    def test_finalised_absence_reasons_can_be_reviewed_by_both_branch_roles(self):
        self.session.attendance_finalised = True
        self.session.save()
        for role in (UserAccount.Role.INSTRUCTOR, UserAccount.Role.BRANCH_MANAGER):
            with self.subTest(role=role):
                user = UserAccount.objects.create_user(username=f"review-{role}", email=f"review-{role}@example.com", role=role, branch=self.branch)
                self.client.force_authenticate(user)
                response = self.client.patch(self.record_url, {
                    "absence_reason": "other", "absence_reason_other": "Family commitment",
                }, format="json")
                self.assertEqual(response.status_code, 200, response.data)
                self.record.refresh_from_db()
                self.session.refresh_from_db()
                self.assertEqual(self.record.status, "absent")
                self.assertEqual(self.record.absence_reason_other, "Family commitment")
                self.assertTrue(self.session.attendance_finalised)
                self.assertEqual(self.client.patch(self.record_url, {
                    "absence_reason": "other", "absence_reason_other": "",
                }, format="json").status_code, 400)
                self.assertEqual(self.client.patch(self.record_url, {
                    "status": "present", "absence_reason": "",
                }, format="json").status_code, 409)

    def test_finalised_present_record_cannot_be_given_an_absence_reason(self):
        self.session.attendance_finalised = True
        self.session.save()
        self.record.status = "present"
        self.record.save()
        self.assertEqual(self.client.patch(self.record_url, {
            "absence_reason": "no_show",
        }, format="json").status_code, 409)
        self.record.refresh_from_db()
        self.assertEqual(self.record.absence_reason, "")
