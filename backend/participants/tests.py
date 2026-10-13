from datetime import date, datetime, timedelta, timezone as datetime_timezone
from unittest.mock import patch
from io import BytesIO
from tempfile import TemporaryDirectory

from PIL import Image
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from sessions.models import ProgrammeSession
from users.models import Branch, UserAccount

from .models import Feedback, Participant


class ConsentDateTests(TestCase):
    @patch("django.utils.timezone.now", return_value=datetime(2026, 9, 20, 13, tzinfo=datetime_timezone.utc))
    def test_consent_dates_for_each_authorized_role_use_new_zealand_today(self, now):
        branch = Branch.objects.create(name="Dunedin")
        participant = Participant.objects.create(first_name="Aroha", last_name="Ngata", branch=branch)
        client = APIClient()
        for role in ("super_admin", "branch_manager", "instructor"):
            user = UserAccount.objects.create_user(
                username=f"{role}@example.com", email=f"{role}@example.com", role=role, branch=branch,
            )
            client.force_authenticate(user)
            for consent in (["photo"] if role == "instructor" else ["gp", "photo"]):
                for day, expected in (("2026-09-20", 200), ("2026-09-21", 200), ("2026-09-22", 400)):
                    with self.subTest(role=role, consent=consent, day=day):
                        response = client.patch(f"/api/participants/{participant.pk}/", {
                            f"{consent}_consent_given": "true", f"{consent}_consent_date": day,
                        }, format="multipart")
                        self.assertEqual(response.status_code, expected, response.data)
                        if expected == 400:
                            self.assertIn(f"{consent}_consent_date", response.data)
                            participant.refresh_from_db()
                            self.assertEqual(getattr(participant, f"{consent}_consent_date"), date(2026, 9, 21))


class ParticipantConsentTests(TestCase):
    def setUp(self):
        self.branch = Branch.objects.create(name="Dunedin")
        self.manager = UserAccount.objects.create_user(
            username="manager@example.com",
            email="manager@example.com",
            password="SafePass123!",
            role=UserAccount.Role.BRANCH_MANAGER,
            branch=self.branch,
        )
        self.instructor = UserAccount.objects.create_user(
            username="instructor@example.com",
            email="instructor@example.com",
            password="SafePass123!",
            role=UserAccount.Role.INSTRUCTOR,
            branch=self.branch,
        )
        self.participant = Participant.objects.create(
            first_name="Aroha", last_name="Ngata", branch=self.branch,
        )
        self.client = APIClient()

    def test_instructor_cannot_record_gp_consent(self):
        self.client.force_authenticate(self.instructor)

        response = self.client.patch(
            f"/api/participants/{self.participant.id}/",
            {"gp_consent_given": True, "gp_consent_date": str(date.today())},
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("gp_consent_given", response.data)

    def test_manager_must_record_date_with_gp_consent(self):
        self.client.force_authenticate(self.manager)

        response = self.client.patch(
            f"/api/participants/{self.participant.id}/",
            {"gp_consent_given": True},
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("gp_consent_date", response.data)

    def test_list_hides_photo_without_consent(self):
        self.participant.photo.name = "participant_photos/aroha.jpg"
        self.participant.save(update_fields=["photo"])
        self.client.force_authenticate(self.instructor)

        response = self.client.get("/api/participants/")

        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.data[0]["photo"])

        self.participant.photo_consent_given = True
        self.participant.photo_consent_date = date.today()
        self.participant.save(update_fields=["photo_consent_given", "photo_consent_date"])

        response = self.client.get("/api/participants/")

        self.assertTrue(response.data[0]["photo"].endswith(f"/api/participants/{self.participant.pk}/photo/"))


class ParticipantDocumentTests(ParticipantConsentTests):
    def setUp(self):
        super().setUp()
        directory = TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        settings = override_settings(STORAGES={
            "default": {"BACKEND": "django.core.files.storage.InMemoryStorage"},
            "private": {"BACKEND": "django.core.files.storage.FileSystemStorage", "OPTIONS": {"location": directory.name}},
        })
        settings.enable()
        self.addCleanup(settings.disable)
        self.admin = UserAccount.objects.create_user(
            username="admin@example.com", email="admin@example.com", role="super_admin",
        )
        self.other_branch = Branch.objects.create(name="Other branch")
        self.other_manager = UserAccount.objects.create_user(
            username="other@example.com", email="other@example.com",
            role="branch_manager", branch=self.other_branch,
        )
        self.url = f"/api/participants/{self.participant.pk}/"

    def upload(self, user, name="consent.pdf", content=b"%PDF-1.4\n%%EOF"):
        self.client.force_authenticate(user)
        return self.client.patch(self.url, {
            "gp_consent_document": SimpleUploadedFile(name, content),
        }, format="multipart")

    def test_manager_and_admin_can_upload_and_download_without_setting_consent(self):
        for user in (self.manager, self.admin):
            with self.subTest(role=user.role):
                response = self.upload(user)
                self.assertEqual(response.status_code, 200, response.data)
                self.assertTrue(response.data["gp_document_available"])
                self.assertNotIn("gp_consent_document", response.data)
                self.assertFalse(response.data["gp_consent_given"])
                self.participant.refresh_from_db()
                self.assertEqual(self.participant.gp_document_uploaded_by, user)
                self.assertIsNotNone(self.participant.gp_document_uploaded_at)
                download = self.client.get(self.url + "gp-document/")
                self.assertEqual(download.status_code, 200)
                self.assertEqual(b"".join(download.streaming_content), b"%PDF-1.4\n%%EOF")
                self.assertEqual(download["Cache-Control"], "private, no-store")
                self.assertIn("attachment", download["Content-Disposition"])
                download.close()

    def test_document_access_is_role_and_branch_scoped(self):
        self.upload(self.manager)
        for user, expected in ((self.instructor, 403), (self.other_manager, 404), (None, 403)):
            self.client.force_authenticate(user)
            self.assertEqual(self.client.get(self.url + "gp-document/").status_code, expected)
        self.assertEqual(self.upload(self.instructor).status_code, 400)
        self.assertNotIn("gp_document_available", self.client.get(self.url).data)
        self.assertEqual(self.upload(self.other_manager).status_code, 404)

    def test_rejects_bad_type_content_and_oversize_without_replacing_document(self):
        self.upload(self.manager)
        self.participant.refresh_from_db()
        original = self.participant.gp_consent_document.name
        for name, content in (("file.svg", b"<svg/>"), ("file.pdf", b"not PDF"),
                              ("file.jpg", b"not JPEG"), ("file.pdf", b"%PDF-" + b"x" * (10 * 1024 * 1024))):
            self.assertEqual(self.upload(self.manager, name, content).status_code, 400)
        self.participant.refresh_from_db()
        self.assertEqual(self.participant.gp_consent_document.name, original)

    def test_accepts_png_and_jpeg_documents(self):
        for extension, format in (("png", "PNG"), ("jpg", "JPEG")):
            content = BytesIO()
            Image.new("RGB", (2, 2)).save(content, format=format)
            self.assertEqual(self.upload(self.manager, f"consent.{extension}", content.getvalue()).status_code, 200)

    def test_optional_dates_and_consent_remain_editable_with_multipart(self):
        self.client.force_authenticate(self.manager)
        response = self.client.patch(self.url, {
            "first_name": "New name", "date_of_birth": "", "joined_on": "",
            "gp_consent_given": "false", "gp_consent_date": "",
            "photo_consent_given": "false", "photo_consent_date": "",
        }, format="multipart")
        self.assertEqual(response.status_code, 200, response.data)
        self.assertIsNone(response.data["gp_consent_date"])

    def test_photo_requests_check_consent_and_branch_and_have_no_public_route(self):
        self.participant.photo.save("photo.jpg", SimpleUploadedFile("photo.jpg", b"image"))
        self.participant.photo_consent_given = True
        self.participant.save()
        photo_url = self.url + "photo/"
        self.client.force_authenticate(self.instructor)
        response = self.client.get(photo_url)
        self.assertEqual(response.status_code, 200)
        response.close()
        self.assertEqual(self.client.get(self.participant.photo.url).status_code, 404)
        self.client.force_authenticate(self.other_manager)
        self.assertEqual(self.client.get(photo_url).status_code, 404)
        self.client.force_authenticate(None)
        self.assertEqual(self.client.get(photo_url).status_code, 403)
        self.participant.photo_consent_given = False
        self.participant.save()
        self.client.force_authenticate(self.instructor)
        self.assertEqual(self.client.get(photo_url).status_code, 404)

    def test_history_preserves_inactive_participant_and_scopes_session_branch(self):
        from sessions.models import AttendanceRecord, ProgrammeSession
        for branch in (self.branch, self.other_branch):
            session = ProgrammeSession.objects.create(
                branch=branch, created_by=self.instructor, date=date.today(), time="09:00", activity="Class",
            )
            AttendanceRecord.objects.create(session=session, participant=self.participant, status="present")
        self.participant.is_active = False
        self.participant.save()
        self.client.force_authenticate(self.manager)
        response = self.client.get(self.url + "attendance/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["status"], "present")
        self.client.force_authenticate(self.admin)
        self.assertEqual(len(self.client.get(self.url + "attendance/").data), 2)
        self.client.force_authenticate(self.other_manager)
        self.assertEqual(self.client.get(self.url + "attendance/").status_code, 404)


class ParticipantAccessTests(TestCase):
    def setUp(self):
        import tempfile
        from django.test import override_settings
        from django.core.files.base import ContentFile
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.settings_override = override_settings(MEDIA_ROOT=self.directory.name)
        self.settings_override.enable()
        self.addCleanup(self.settings_override.disable)
        self.branch = Branch.objects.create(name="Photo branch")
        self.other = Branch.objects.create(name="Other branch")
        self.instructor = UserAccount.objects.create_user(
            username="photo@example.com", email="photo@example.com",
            role=UserAccount.Role.INSTRUCTOR, branch=self.branch,
        )
        self.participant = Participant.objects.create(
            first_name="Test", last_name="Participant", branch=self.branch,
            photo_consent_given=True, photo_consent_date=date.today(),
        )
        self.participant.photo.save("test.gif", ContentFile(b"test-image-bytes"))
        self.photo_url = f"/api/participants/{self.participant.pk}/photo/"
        self.client = APIClient()

    def test_direct_photo_requires_login_branch_access_and_consent(self):
        self.assertEqual(self.client.get(self.photo_url).status_code, 403)
        self.client.force_authenticate(self.instructor)
        response = self.client.get(self.photo_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(b"".join(response.streaming_content), b"test-image-bytes")
        response.close()
        self.assertIn("no-store", response["Cache-Control"])
        self.instructor.branch = self.other
        self.instructor.save()
        self.assertEqual(self.client.get(self.photo_url).status_code, 404)
        self.instructor.branch = self.branch
        self.instructor.save()
        self.participant.photo_consent_given = False
        self.participant.save()
        self.assertEqual(self.client.get(self.photo_url).status_code, 404)

    def test_unassigned_staff_cannot_create_participant(self):
        self.instructor.branch = None
        self.instructor.save()
        self.client.force_authenticate(self.instructor)
        response = self.client.post("/api/participants/", {
            "first_name": "New", "last_name": "Person",
        }, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertIn("branch", response.data)


class ParticipantEnrolmentTests(TestCase):
    def test_both_branch_roles_enrol_in_own_branch_and_new_session_includes_participant(self):
        from django.utils import timezone
        from sessions.models import ProgrammeSession
        other = Branch.objects.create(name="Other branch")
        client = APIClient()
        for role in (UserAccount.Role.INSTRUCTOR, UserAccount.Role.BRANCH_MANAGER):
            with self.subTest(role=role):
                branch = Branch.objects.create(name=role)
                user = UserAccount.objects.create_user(username=role, email=f"{role}@example.com", role=role, branch=branch)
                client.force_authenticate(user)
                response = client.post("/api/participants/", {
                    "first_name": "Aroha", "last_name": "Example", "date_of_birth": None,
                    "joined_on": timezone.localdate(), "branch": str(other.pk),
                }, format="json")
                self.assertEqual(response.status_code, 201, response.data)
                participant = Participant.objects.get(pk=response.data["id"])
                self.assertEqual(participant.branch_id, branch.pk)
                self.assertTrue(participant.is_active)
                self.assertEqual(client.get(f"/api/participants/{participant.pk}/").status_code, 200)
                created = client.post("/api/sessions/", {
                    "date": timezone.localdate(), "time": "09:00", "activity": "Class",
                }, format="json")
                self.assertEqual(created.status_code, 201, created.data)
                session = ProgrammeSession.objects.get(pk=created.data["id"])
                self.assertEqual(list(session.attendance.values_list("participant_id", flat=True)), [participant.pk])


class ParticipantHistoryRegressionTests(TestCase):
    def setUp(self):
        self.branch = Branch.objects.create(name="History regressions")
        self.user = UserAccount.objects.create_user(username="history-user", email="history-user@example.com", role="instructor", branch=self.branch)
        self.participant = Participant.objects.create(first_name="History", last_name="Person", branch=self.branch)
        self.client = APIClient()
        self.client.force_authenticate(self.user)
        self.url = f"/api/participants/{self.participant.pk}/"

    def test_history_exposes_finalisation_to_distinguish_default_absences(self):
        from sessions.models import AttendanceRecord, ProgrammeSession
        for finalised in (True, False):
            session = ProgrammeSession.objects.create(branch=self.branch, created_by=self.user, date=date(2026, 1, 1), time="10:00", activity="Class", attendance_finalised=finalised)
            AttendanceRecord.objects.create(session=session, participant=self.participant, status="absent")
        response = self.client.get(self.url + "attendance/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(sorted(row["attendance_finalised"] for row in response.data), [False, True])

    @patch("participants.serializers.timezone.localdate", return_value=date(2030, 1, 2))
    def test_birth_date_uses_programme_today(self, localdate):
        for value, expected in [("2030-01-02", 200), ("2030-01-03", 400)]:
            response = self.client.patch(self.url, {"date_of_birth": value}, format="json")
            self.assertEqual(response.status_code, expected, response.data)


class FeedbackTests(TestCase):
    def setUp(self):
        self.a = Branch.objects.create(name='A')
        self.b = Branch.objects.create(name='B')
        self.manager = self.user('manager', 'branch_manager', self.a)
        self.other = self.user('other', 'branch_manager', self.b)
        self.instructor = self.user('instructor', 'instructor', self.a)
        self.admin = self.user('admin', 'super_admin', None)
        self.person = Participant.objects.create(branch=self.a, first_name='Aroha', last_name='Example',
                                                gp_consent_given=True, gp_consent_date=timezone.localdate())
        self.foreign_person = Participant.objects.create(branch=self.b, first_name='Other', last_name='Person')
        self.session = ProgrammeSession.objects.create(branch=self.a, created_by=self.instructor,
                                                       date=timezone.localdate(), time='10:00', activity='Movement')
        self.client = APIClient()
        self.client.force_authenticate(self.manager)
        self.payload = {'participant': str(self.person.pk), 'quote': 'Feeling steadier',
                        'date': timezone.localdate().isoformat(), 'consent': True}

    def user(self, name, role, branch):
        return UserAccount.objects.create_user(username=name, email=f'{name}@example.org', role=role, branch=branch)

    def test_persists_between_clients_with_server_owned_scope_and_author(self):
        response = self.client.post('/api/participants/feedback/', {
            **self.payload, 'branch': str(self.b.pk), 'recorded_by': str(self.admin.pk), 'source': 'Forged',
        }, format='json')
        self.assertEqual(response.status_code, 201, response.data)
        entry = Feedback.objects.get()
        self.assertEqual(entry.branch, self.a)
        self.assertEqual(entry.recorded_by, self.manager)
        self.assertEqual(entry.source, self.person.full_name)
        second_device = APIClient()
        second_device.force_authenticate(self.instructor)
        self.assertEqual(second_device.get('/api/participants/feedback/').data[0]['id'], str(entry.pk))
        self.client.force_authenticate(self.other)
        self.assertEqual(self.client.get('/api/participants/feedback/').data, [])
        self.client.force_authenticate(self.admin)
        self.assertEqual(len(self.client.get('/api/participants/feedback/').data), 1)

    def test_empty_database_has_no_demo_feedback_and_requires_auth(self):
        self.assertEqual(self.client.get('/api/participants/feedback/').data, [])
        self.client.force_authenticate(None)
        self.assertEqual(self.client.get('/api/participants/feedback/').status_code, 403)
        self.assertEqual(self.client.post('/api/participants/feedback/', self.payload, format='json').status_code, 403)

    def test_rejects_foreign_subjects_and_missing_subject(self):
        foreign_session = ProgrammeSession.objects.create(branch=self.b, created_by=self.other,
                                                          date=timezone.localdate(), time='10:00', activity='Other')
        for subject in ({'participant': str(self.foreign_person.pk)},
                        {'participant': None, 'session': str(foreign_session.pk)},
                        {'participant': None, 'session': None}):
            with self.subTest(subject=subject):
                response = self.client.post('/api/participants/feedback/', {**self.payload, **subject}, format='json')
                self.assertEqual(response.status_code, 400, response.data)
        self.assertFalse(Feedback.objects.exists())

    def test_session_feedback_defaults_to_no_consent(self):
        response = self.client.post('/api/participants/feedback/', {
            'session': str(self.session.pk), 'quote': 'Enjoyed the class', 'date': timezone.localdate(),
        }, format='json')
        self.assertEqual(response.status_code, 201, response.data)
        self.assertFalse(response.data['consent'])
        self.assertEqual(response.data['session'], self.session.pk)

    def test_all_roles_save_subject_combinations_with_server_owned_identity_and_reload(self):
        for user in (self.manager, self.instructor, self.admin):
            for participant, session in ((self.person, None), (None, self.session), (self.person, self.session)):
                with self.subTest(role=user.role, participant=participant, session=session):
                    self.client.force_authenticate(user)
                    response = self.client.post('/api/participants/feedback/', {
                        'participant': str(participant.pk) if participant else None,
                        'session': str(session.pk) if session else None,
                        'quote': '  A short story about the class.  ', 'date': timezone.localdate(),
                        'branch': str(self.b.pk), 'recorded_by': str(self.other.pk), 'source': 'Forged',
                    }, format='json')
                    self.assertEqual(response.status_code, 201, response.data)
                    entry = Feedback.objects.get(pk=response.data['id'])
                    self.assertEqual(entry.branch, self.a)
                    self.assertEqual(entry.recorded_by, user)
                    self.assertEqual(entry.source, participant.full_name if participant else session.activity)
                    self.assertEqual(entry.quote, 'A short story about the class.')
                    self.assertFalse(entry.consent)
                    fresh_client = APIClient()
                    fresh_client.force_authenticate(user)
                    saved = next(row for row in fresh_client.get('/api/participants/feedback/').data if row['id'] == str(entry.pk))
                    self.assertEqual(saved['quote'], entry.quote)
                    fresh_client.force_authenticate(self.other)
                    self.assertEqual(fresh_client.get('/api/participants/feedback/').data, [])

    def test_super_admin_records_feedback_in_any_branch_without_bypassing_consent(self):
        self.client.force_authenticate(self.admin)
        response = self.client.post('/api/participants/feedback/', {
            **self.payload, 'participant': str(self.foreign_person.pk), 'consent': False,
        }, format='json')
        self.assertEqual(response.status_code, 201, response.data)
        entry = Feedback.objects.get(pk=response.data['id'])
        self.assertEqual(entry.branch, self.b)
        self.assertEqual(entry.recorded_by, self.admin)
        self.assertFalse(entry.consent)
        self.client.force_authenticate(self.manager)
        self.assertEqual(self.client.get('/api/participants/feedback/').data, [])
        self.client.force_authenticate(self.other)
        self.assertEqual(self.client.get('/api/participants/feedback/').data[0]['id'], str(entry.pk))

    def test_admin_cannot_mix_branches_and_future_dates_are_rejected(self):
        self.client.force_authenticate(self.admin)
        response = self.client.post('/api/participants/feedback/', {
            **self.payload, 'participant': str(self.foreign_person.pk), 'session': str(self.session.pk),
        }, format='json')
        self.assertEqual(response.status_code, 400)
        response = self.client.post('/api/participants/feedback/', {
            **self.payload, 'date': (timezone.localdate() + timedelta(days=1)).isoformat(),
        }, format='json')
        self.assertEqual(response.status_code, 400)

    def test_transfer_preserves_original_branch_evidence_without_live_name_leak(self):
        self.client.post('/api/participants/feedback/', self.payload, format='json')
        original_name = self.person.full_name
        self.person.branch = self.b
        self.person.first_name = 'Changed elsewhere'
        self.person.save()
        self.assertEqual(self.client.get('/api/participants/feedback/').data[0]['source'], original_name)
        self.client.force_authenticate(self.other)
        self.assertEqual(self.client.get('/api/participants/feedback/').data, [])

    def test_dashboard_contracts_and_manager_attendance_access(self):
        people = self.client.get('/api/participants/').data
        self.assertTrue(people[0]['gp_consent_given'])
        self.person.gp_consent_given = False
        self.person.save()
        self.assertFalse(self.client.get('/api/participants/').data[0]['gp_consent_given'])
        sessions = self.client.get('/api/sessions/').data
        self.assertEqual(sessions[0]['created_by'], self.instructor.pk)
        self.assertEqual(self.client.get(f'/api/sessions/{self.session.pk}/').status_code, 200)
        self.assertEqual(self.client.patch(f'/api/sessions/{self.session.pk}/attendance-state/',
                                          {'attendance_finalised': True}, format='json').status_code, 200)

    def test_feedback_blocks_branch_deletion_after_all_people_transfer(self):
        self.client.post('/api/participants/feedback/', self.payload, format='json')
        self.session.delete()
        self.person.branch = self.b
        self.person.save()
        UserAccount.objects.filter(branch=self.a).update(branch=self.b)
        self.client.force_authenticate(self.admin)
        response = self.client.delete(f'/api/branches/{self.a.pk}/')
        self.assertEqual(response.status_code, 409, response.data)
        self.assertIn('feedback', response.data['detail'])
        self.assertTrue(Feedback.objects.exists())
