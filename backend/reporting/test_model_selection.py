from unittest.mock import Mock, patch
from django.test import TestCase, override_settings
from rest_framework.test import APIClient
from django.core.cache import cache
from users.models import UserAccount, Branch
from reporting.models import AttendanceAnalysisJob, PhysicalAnalysisJob
from reporting.tasks import run_analysis_job
from audit.models import AuditEvent
from llm.services.catalog import report_models


@override_settings(DEFAULT_LLM_MODEL='first-model', REPORT_LLM_MODELS=['first-model', 'chosen-model'],
                   CACHES={'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'}})
class ReportModelTests(TestCase):
    def setUp(self):
        self.branch = Branch.objects.create(name='Branch')
        self.user = UserAccount.objects.create_user(username='admin', email='admin@example.nz', role='super_admin')
        self.client = APIClient()
        self.client.force_authenticate(self.user)
        self.statistics = {'scope': {'branch_id': str(self.branch.pk), 'start_date': '2026-01-01', 'end_date': '2026-03-31'},
                           'totals': {'finalised_sessions': 1, 'completed_assessments': 1}}
        self.payload = {'start_date': '2026-01-01', 'end_date': '2026-03-31', 'model': 'chosen-model'}

    def test_catalogue_permissions(self):
        response = self.client.get('/api/reporting/models/')
        self.assertEqual(response.data, {'models': ['first-model', 'chosen-model'], 'default': 'first-model'})
        self.user.role = 'branch_manager'; self.user.branch = self.branch; self.user.save()
        self.assertEqual(self.client.get('/api/reporting/models/').status_code, 200)
        self.user.role = 'instructor'; self.user.save()
        self.assertEqual(self.client.get('/api/reporting/models/').status_code, 403)

    def test_both_reports_pin_selection_and_audit_it(self):
        for kind, model, view in [('attendance', AttendanceAnalysisJob, 'AttendanceAnalysisView'),
                                  ('physical', PhysicalAnalysisJob, 'PhysicalAnalysisView')]:
            with self.subTest(kind=kind), patch(f'reporting.views.{view}.report_statistics', return_value=self.statistics), \
                 patch(f'reporting.views.generate_{kind}_analysis.apply_async'):
                response = self.client.post(f'/api/reporting/{kind}/analyse/', self.payload, format='json')
                self.assertEqual(response.status_code, 202, response.data)
                job = model.objects.get(pk=response.data['job_id'])
                self.assertEqual(job.model_name, 'chosen-model')
                explain = Mock(return_value='A report')
                with override_settings(DEFAULT_LLM_MODEL='changed-default'):
                    run_analysis_job(model, explain, job.pk)
                explain.assert_called_once_with(self.statistics, model='chosen-model')
                event = AuditEvent.objects.get(target_id=str(job.pk), action='report.succeeded')
                self.assertEqual(event.details['model'], 'chosen-model')
                status = self.client.get(f'/api/reporting/{kind}/jobs/{job.pk}/')
                self.assertEqual(status.data['model'], 'chosen-model')
        rows = self.client.get('/api/audit/', {'action': 'report.succeeded'}).data['results']
        self.assertTrue(all('Model: chosen-model' in row['description'] for row in rows))

    def test_rejects_unknown_model_before_creating_or_queueing_job(self):
        with patch('reporting.views.AttendanceAnalysisView.report_statistics', return_value=self.statistics), \
             patch('reporting.views.generate_attendance_analysis.apply_async') as enqueue:
            response = self.client.post('/api/reporting/attendance/analyse/', {**self.payload, 'model': 'unknown'}, format='json')
        self.assertEqual(response.status_code, 400)
        enqueue.assert_not_called()
        self.assertFalse(AttendanceAnalysisJob.objects.exists())

    @override_settings(REPORT_LLM_MODELS=[])
    def test_catalogue_uses_provider_cache_and_falls_back_on_outage(self):
        cache.delete('llm:models')
        self.addCleanup(cache.delete, 'llm:models')
        with patch('llm.services.catalog.get_available_models', return_value=['chosen-model']) as provider:
            self.assertEqual(report_models()['models'], ['first-model', 'chosen-model'])
            report_models()
            provider.assert_called_once()
        cache.delete('llm:models')
        with patch('llm.services.catalog.get_available_models', side_effect=RuntimeError('private connection detail')):
            self.assertEqual(report_models(), {'models': ['first-model'], 'default': 'first-model'})

    @override_settings(REPORT_LLM_MODELS=[])
    def test_catalogue_survives_cache_outage(self):
        from redis.exceptions import ConnectionError
        with patch('llm.services.catalog.cache.get', side_effect=ConnectionError()), \
             patch('llm.services.catalog.cache.set', side_effect=ConnectionError()), \
             patch('llm.services.catalog.get_available_models', return_value=['chosen-model']):
            self.assertEqual(report_models()['models'], ['first-model', 'chosen-model'])

    @override_settings(REPORT_LLM_MODELS=[])
    def test_embedding_model_is_not_offered_or_accepted_even_from_old_cache(self):
        cache.set('llm:models', ['ONCAMPUS/BAAI/bge-m3', 'ONCAMPUS/gemma-4-12B-it'])
        self.addCleanup(cache.delete, 'llm:models')
        self.assertNotIn('ONCAMPUS/BAAI/bge-m3', report_models()['models'])
        self.assertIn('ONCAMPUS/gemma-4-12B-it', report_models()['models'])
        with patch('reporting.views.AttendanceAnalysisView.report_statistics', return_value=self.statistics), \
             patch('reporting.views.generate_attendance_analysis.apply_async') as enqueue:
            response = self.client.post('/api/reporting/attendance/analyse/',
                {**self.payload, 'model': 'ONCAMPUS/BAAI/bge-m3'}, format='json')
        self.assertEqual(response.status_code, 400)
        enqueue.assert_not_called()

    @override_settings(REPORT_LLM_MODELS=[])
    def test_provider_failure_does_not_hide_models_for_five_minutes(self):
        cache.delete('llm:models')
        self.addCleanup(cache.delete, 'llm:models')
        with patch('llm.services.catalog.get_available_models', side_effect=[RuntimeError(), ['recovered-model']]) as provider:
            self.assertEqual(report_models()['models'], ['first-model'])
            self.assertIn('recovered-model', report_models()['models'])
            self.assertEqual(provider.call_count, 2)
