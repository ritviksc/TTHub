from datetime import timedelta
from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone
from users.models import UserAccount
from .models import AttendanceAnalysisJob, PhysicalAnalysisJob
from .tasks import run_analysis_job


class JobDeadlineTests(TestCase):
    def test_late_provider_result_is_not_saved_even_without_status_polling(self):
        user = UserAccount.objects.create_user(username="deadline", email="deadline@example.com", role="super_admin")
        started = timezone.now()
        finished = started + timedelta(minutes=2)
        for model in (AttendanceAnalysisJob, PhysicalAnalysisJob):
            with self.subTest(model=model.__name__):
                job = model.objects.create(requested_by=user, statistics={}, expires_at=started + timedelta(minutes=1))
                with patch('django.utils.timezone.now', return_value=started) as now:
                    def explain(statistics, **kwargs):
                        now.return_value = finished
                        return "Late response"
                    run_analysis_job(model, explain, str(job.pk))
                job.refresh_from_db()
                self.assertEqual(job.status, 'failed')
                self.assertIsNone(job.narrative)
                self.assertIn('timed out', job.error)
