from datetime import timedelta
from unittest.mock import Mock, patch

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient, APIRequestFactory, force_authenticate

from users.models import Branch, UserAccount
from users.views import StaffCreateView
from reporting.models import AttendanceAnalysisJob, PhysicalAnalysisJob
from reporting.tasks import run_analysis_job
from reporting.views import queue_analysis
from .models import AuditEvent
from .services import record, transition_job


class AuditTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.branch = Branch.objects.create(name="Harbour")
        cls.other = Branch.objects.create(name="Hills")
        cls.admin = UserAccount.objects.create_user(username="admin", email="admin@example.nz", role="super_admin")
        cls.manager = UserAccount.objects.create_user(username="manager", email="manager@example.nz", role="branch_manager", branch=cls.branch)
        cls.instructor = UserAccount.objects.create_user(username="instructor", email="instructor@example.nz", role="instructor", branch=cls.branch)

    def setUp(self):
        self.client = APIClient()
        self.client.force_authenticate(self.admin)

    def test_staff_creation_promotion_and_deactivation_capture_actor_and_changes(self):
        response = self.client.post('/api/auth/staff/', {
            'email': 'new@example.nz', 'first_name': 'New', 'last_name': 'Staff',
            'role': 'instructor', 'branch': str(self.branch.pk), 'password': 'SecretPassword123!'
        }, format='json')
        self.assertEqual(response.status_code, 201, response.data)
        created = AuditEvent.objects.get(action='staff.created')
        self.assertEqual(created.actor_id, self.admin.pk)
        self.assertEqual(created.details['changes']['role']['after'], 'instructor')
        self.assertNotIn('password', str(created.details).lower())
        self.assertNotIn('SecretPassword', str(list(AuditEvent.objects.values())))
        self.assertEqual(created.target_id, str(response.data['id']))
        self.assertTrue(AuditEvent.objects.filter(action='api.write', request_id=created.request_id).exists())
        response = self.client.post(f'/api/branches/{self.branch.pk}/managers/',
                                   {'user_id': str(self.instructor.pk)}, format='json')
        self.assertEqual(response.status_code, 200)
        promoted = AuditEvent.objects.get(action='staff.role_changed')
        self.assertEqual(promoted.details['changes']['role'], {'before': 'instructor', 'after': 'branch_manager'})
        response = self.client.post(f'/api/auth/staff/{self.instructor.pk}/deactivate/')
        self.assertEqual(response.status_code, 200)
        event = AuditEvent.objects.get(action='staff.deactivated')
        self.assertEqual(event.details['changes']['is_active'], {'before': True, 'after': False})

    def test_staff_edit_transfer_and_unassignment(self):
        self.client.patch(f'/api/auth/staff/{self.instructor.pk}/',
                          {'branch': str(self.other.pk)}, format='json')
        event = AuditEvent.objects.get(action='staff.branch_changed')
        self.assertEqual(event.details['changes']['branch_id'], {'before': str(self.branch.pk), 'after': str(self.other.pk)})
        self.client.post(f'/api/auth/staff/{self.instructor.pk}/deactivate/')
        self.client.patch(f'/api/auth/staff/{self.instructor.pk}/', {'is_active': True}, format='json')
        # Account reactivation is not an existing API capability. Ignored fields
        # must not create a fictional change event.
        self.assertFalse(AuditEvent.objects.filter(action='staff.reactivated').exists())
        response = self.client.delete(f'/api/branches/{self.other.pk}/instructors/{self.instructor.pk}/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(AuditEvent.objects.filter(action='staff.branch_changed').first().details['changes']['branch_id']['after'], None)

    def test_denied_write_is_not_a_successful_staff_change(self):
        self.client.force_authenticate(self.manager)
        response = self.client.post(f'/api/branches/{self.branch.pk}/managers/',
                                   {'user_id': str(self.instructor.pk)}, format='json')
        self.assertEqual(response.status_code, 403)
        self.assertFalse(AuditEvent.objects.filter(action='staff.role_changed').exists())
        event = AuditEvent.objects.get(action='api.write')
        self.assertEqual(event.outcome, 'denied')
        self.assertEqual(event.actor_id, self.manager.pk)

    def test_atomic_staff_create_rolls_back_if_audit_fails(self):
        request = APIRequestFactory().post('/api/auth/staff/', {
            'email': 'rollback@example.nz', 'role': 'instructor',
            'branch': str(self.branch.pk), 'password': 'SecretPassword123!'
        }, format='json')
        force_authenticate(request, self.admin)
        with patch('audit.services.record', side_effect=RuntimeError('Audit unavailable')):
            with self.assertRaises(RuntimeError):
                StaffCreateView.as_view()(request)
        self.assertFalse(UserAccount.objects.filter(email='rollback@example.nz').exists())

    def test_log_permissions_read_only_and_filters(self):
        event = record('staff.created', actor=self.admin, branch_id=self.branch.pk, target_label='Test target')
        record('report.failed', actor=self.manager, outcome='failed', branch_id=self.other.pk)
        for user in (self.instructor, None):
            self.client.force_authenticate(user)
            self.assertIn(self.client.get('/api/audit/').status_code, (401, 403))
        self.client.force_authenticate(self.admin)
        response = self.client.get('/api/audit/', {'q': 'Test target', 'branch_id': str(self.branch.pk),
            'actor_id': str(self.admin.pk), 'action': 'staff.created', 'outcome': 'success',
            'start_date': timezone.localdate().isoformat(), 'end_date': timezone.localdate().isoformat()})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['id'], str(event.pk))
        self.assertEqual(self.client.post('/api/audit/', {}, format='json').status_code, 405)
        self.assertEqual(self.client.get('/api/audit/', {'branch_id': 'invalid'}).status_code, 400)
        self.assertEqual(self.client.get('/api/audit/', {'start_date': '2026-02-01', 'end_date': '2026-01-01'}).status_code, 400)

    def test_pagination_and_model_guards(self):
        AuditEvent.objects.bulk_create([AuditEvent(action='test') for _ in range(51)])
        response = self.client.get('/api/audit/')
        self.assertEqual(len(response.data['results']), 50)
        self.assertIsNotNone(response.data['next'])
        self.assertEqual(len(self.client.get('/api/audit/', {'page': 2}).data['results']), 1)
        event = AuditEvent.objects.first()
        for operation in (event.save, event.delete, lambda: AuditEvent.objects.filter(pk=event.pk).delete(),
                          lambda: AuditEvent.objects.filter(pk=event.pk).update(action='changed')):
            with self.assertRaises(ValueError):
                operation()

    def test_identity_snapshots_survive_account_and_branch_deletion(self):
        user = UserAccount.objects.create_user(username='temp', email='temp@example.nz', role='super_admin')
        branch = Branch.objects.create(name='Temporary')
        event = record('test', actor=user, branch_id=branch.pk)
        user.delete(); branch.delete()
        event.refresh_from_db()
        self.assertEqual(event.actor_email, 'temp@example.nz')
        self.assertIsNotNone(event.actor_id)
        self.assertIsNotNone(event.branch_id)

    def test_both_report_types_record_lifecycle_once_without_content(self):
        for model in (AttendanceAnalysisJob, PhysicalAnalysisJob):
            with self.subTest(model=model):
                task = Mock()
                statistics = {'scope': {'branch_id': str(self.branch.pk), 'start_date': '2026-01-01', 'end_date': '2026-03-31'},
                              'private_notes': 'Never copy these notes'}
                response = queue_analysis(self.admin, statistics, model, task, True)
                job_id = response.data['job_id']
                explain = Mock(return_value='Private narrative')
                run_analysis_job(model, explain, job_id)
                run_analysis_job(model, explain, job_id)
                explain.assert_called_once()
                events = AuditEvent.objects.filter(target_id=job_id)
                self.assertEqual(set(events.values_list('action', flat=True)), {'report.requested', 'report.running', 'report.succeeded'})
                self.assertEqual(events.count(), 3)
                self.assertNotIn('Private narrative', str(list(events.values())))
                self.assertNotIn('Never copy', str(list(events.values())))
                self.assertEqual(events.get(action='report.succeeded').actor_id, self.admin.pk)

    def test_queue_failure_expiry_and_worker_failure(self):
        task = Mock()
        task.apply_async.side_effect = OSError('secret connection string')
        response = queue_analysis(self.admin, {'scope': {'branch_id': None}}, AttendanceAnalysisJob, task, True)
        self.assertEqual(response.status_code, 503)
        self.assertEqual(AuditEvent.objects.get(action='report.failed').details['reason'], 'queue_unavailable')
        job = PhysicalAnalysisJob.objects.create(requested_by=self.admin, statistics={}, expires_at=timezone.now() - timedelta(seconds=1))
        job.expire_if_needed(); job.expire_if_needed()
        self.assertEqual(AuditEvent.objects.filter(target_id=str(job.pk), action='report.failed').count(), 1)
        job = PhysicalAnalysisJob.objects.create(requested_by=self.admin, statistics={})
        with self.assertRaises(RuntimeError):
            run_analysis_job(PhysicalAnalysisJob, Mock(side_effect=RuntimeError('Private error')), job.pk)
        event = AuditEvent.objects.get(target_id=str(job.pk), action='report.failed')
        self.assertEqual(event.details['reason'], 'generation_failed')
        self.assertNotIn('Private error', str(event.details))

    def test_job_transition_rolls_back_if_audit_fails(self):
        job = AttendanceAnalysisJob.objects.create(requested_by=self.admin, statistics={})
        with patch('audit.services.record', side_effect=RuntimeError('Audit unavailable')):
            with self.assertRaises(RuntimeError):
                transition_job(job, AttendanceAnalysisJob.objects.filter(pk=job.pk), 'running')
        job.refresh_from_db()
        self.assertEqual(job.status, 'queued')

    def test_branch_and_quarter_events_and_statistics_scope(self):
        response = self.client.post('/api/branches/', {'name': 'Created'}, format='json')
        self.assertEqual(response.status_code, 201)
        branch_id = response.data['id']
        self.client.patch(f'/api/branches/{branch_id}/', {'name': 'Renamed'}, format='json')
        self.client.delete(f'/api/branches/{branch_id}/')
        self.assertTrue(AuditEvent.objects.filter(action='branch.created', target_id=branch_id).exists())
        self.assertTrue(AuditEvent.objects.filter(action='branch.updated', target_id=branch_id).exists())
        self.assertTrue(AuditEvent.objects.filter(action='branch.deleted', target_id=branch_id).exists())
        url = f'/api/branches/{self.branch.pk}/quarters/2026/'
        payload = self.client.get(url).data
        payload['quarters'][0]['start_date'] = '2026-02-01'
        self.assertEqual(self.client.put(url, payload, format='json').status_code, 200)
        event = AuditEvent.objects.get(action='branch.quarters_updated')
        self.assertEqual(event.details['before'][0]['start_date'], '2026-01-01')
        self.assertEqual(event.details['after'][0]['start_date'], '2026-02-01')
        response = self.client.get('/api/reporting/attendance/', {'start_date': '2026-01-01', 'end_date': '2026-03-31', 'branch_id': str(self.branch.pk)})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(AuditEvent.objects.get(action='report.statistics_viewed').branch_id, self.branch.pk)

    def test_login_logout_keep_identity_but_not_credentials(self):
        self.admin.username = self.admin.email
        self.admin.set_password('LoginSecret123!')
        self.admin.save()
        self.client.force_authenticate(None)
        response = self.client.post('/api/auth/login/', {'email': self.admin.email, 'password': 'LoginSecret123!'}, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(AuditEvent.objects.get(action='auth.login').actor_id, self.admin.pk)
        self.assertEqual(self.client.post('/api/auth/logout/').status_code, 200)
        self.assertEqual(AuditEvent.objects.get(action='auth.logout').actor_id, self.admin.pk)
        self.client.post('/api/auth/login/', {'email': 'private-input@example.nz', 'password': 'WrongSecret123!'}, format='json')
        event = AuditEvent.objects.filter(action='auth.login', outcome='denied').get()
        self.assertIsNone(event.actor_id)
        serialized = str(list(AuditEvent.objects.values()))
        self.assertNotIn('private-input@example.nz', serialized)
        self.assertNotIn('Secret123!', serialized)

    def test_empty_report_and_polling_do_not_duplicate_events(self):
        task = Mock()
        response = queue_analysis(self.admin, {'scope': {'branch_id': None}}, AttendanceAnalysisJob, task, False)
        task.apply_async.assert_not_called()
        job_id = response.data['job_id']
        for _ in range(2):
            self.assertEqual(self.client.get(f'/api/reporting/attendance/jobs/{job_id}/').status_code, 200)
        self.assertEqual(AuditEvent.objects.filter(target_id=job_id).count(), 2)

    def test_branch_update_preserves_detail_response(self):
        response = self.client.patch(f'/api/branches/{self.branch.pk}/', {'name': 'Updated'}, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['instructor_count'], 1)
        self.assertEqual(response.data['participant_count'], 0)
        self.assertEqual(response.data['managers'][0]['id'], str(self.manager.pk))
        self.assertEqual(response.data['instructors'][0]['id'], str(self.instructor.pk))

    def test_manager_scope_cannot_be_widened_and_includes_departures(self):
        own = record('report.requested', actor=self.admin, branch_id=self.branch.pk)
        departure = record('staff.branch_changed', actor=self.admin, branch_id=self.other.pk,
            details={'changes': {'branch_id': {'before': str(self.branch.pk), 'after': str(self.other.pk)}}})
        record('report.requested', actor=self.admin, branch_id=self.other.pk)
        record('report.requested', actor=self.admin)
        self.client.force_authenticate(self.manager)
        response = self.client.get('/api/audit/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual({row['id'] for row in response.data['results']}, {str(own.pk), str(departure.pk)})
        response = self.client.get('/api/audit/', {'branch_id': str(self.other.pk)})
        self.assertEqual({row['id'] for row in response.data['results']}, {str(departure.pk)})
        self.manager.branch = None
        self.manager.save()
        self.assertEqual(self.client.get('/api/audit/').data['count'], 0)

    def test_super_admin_resource_writes_are_visible_to_own_branch_including_delete(self):
        from documents.models import Folder
        folder = Folder.objects.create(branch=self.branch, created_by=self.admin, name='Folder')
        url = f'/api/folders/{folder.pk}/'
        response = self.client.patch(url, {'name': 'Updated folder'}, format='json')
        self.assertEqual(response.status_code, 200, response.data)
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 204, getattr(response, 'data', None))
        self.client.force_authenticate(self.manager)
        events = self.client.get('/api/audit/').data['results']
        self.assertEqual(len(events), 2)
        self.assertEqual({event['description'] for event in events}, {'Updated folder', 'Removed folder'})
        self.assertTrue(all(event['branch'] == self.branch.name for event in events))

    def test_public_log_hides_metadata_and_other_branch_information(self):
        event = record('staff.branch_changed', actor=self.admin, branch_id=self.other.pk,
            target_label='staff@example.nz', target_id=str(self.instructor.pk),
            details={'changes': {'branch_id': {'before': str(self.branch.pk), 'after': str(self.other.pk)}},
                     'secret': 'private diagnostic content', 'route': '/private/internal/'})
        self.client.force_authenticate(self.manager)
        row = self.client.get('/api/audit/').data['results'][0]
        self.assertEqual(set(row), {'id', 'created_at', 'person', 'description', 'branch', 'result'})
        self.assertEqual(row['description'], 'Staff member left your branch — staff@example.nz')
        self.assertNotIn('private diagnostic content', str(row))
        self.assertNotIn(str(self.other.pk), str(row))
        self.assertNotIn(self.other.name, str(row))
        self.assertNotIn(str(self.instructor.pk), str(row))

    def test_readable_log_omits_duplicate_requests_and_worker_progress(self):
        import uuid
        from types import SimpleNamespace
        request = SimpleNamespace(user=self.admin, audit_request_id=uuid.uuid4())
        record('staff.created', request=request, branch_id=self.branch.pk, target_label='staff@example.nz')
        record('api.write', request=request, branch_id=self.branch.pk)
        record('report.running', actor=self.admin, branch_id=self.branch.pk)
        self.assertEqual(AuditEvent.objects.count(), 3)
        response = self.client.get('/api/audit/')
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['description'], 'Created a staff account — staff@example.nz')
        self.assertEqual(self.client.get('/api/audit/', {'category': 'staff'}).data['count'], 1)
        self.assertEqual(self.client.get('/api/audit/', {'category': 'reports'}).data['count'], 0)

    def test_staff_history_is_not_relabelled_when_email_is_reused(self):
        original_email = self.instructor.email
        event = record('staff.created', actor=self.admin, branch_id=self.branch.pk,
                       target_type='staff', target_id=self.instructor.pk, target_label=original_email)
        self.instructor.first_name = 'Original'
        self.instructor.email = 'changed@example.nz'
        self.instructor.save()
        UserAccount.objects.create_user(username='replacement', email=original_email,
            first_name='Replacement', role='instructor', branch=self.branch)
        row = self.client.get('/api/audit/').data['results'][0]
        self.assertEqual(row['id'], str(event.pk))
        self.assertIn('Original', row['description'])
        self.assertNotIn('Replacement', row['description'])
        self.instructor.delete()
        row = self.client.get('/api/audit/').data['results'][0]
        self.assertIn(original_email, row['description'])
        self.assertNotIn('Replacement', row['description'])
