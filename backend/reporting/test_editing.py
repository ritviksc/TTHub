from django.test import TestCase
from rest_framework.test import APIClient

from audit.models import AuditEvent
from users.models import UserAccount
from .models import AttendanceAnalysisJob, PhysicalAnalysisJob


class ReportEditingTests(TestCase):
    def test_editing_both_report_types_preserves_statistics_and_checks_permissions(self):
        admin = UserAccount.objects.create_user(username="editor", email="editor@example.com", role="super_admin")
        other = UserAccount.objects.create_user(username="other-editor", email="other@example.com", role="super_admin")
        client = APIClient()
        for kind, model in (("attendance", AttendanceAnalysisJob), ("physical", PhysicalAnalysisJob)):
            with self.subTest(kind=kind):
                client.force_authenticate(admin)
                job = model.objects.create(requested_by=admin, status="succeeded", narrative="Original",
                                           statistics={"totals": {"count": 3}}, model_name="test-model")
                url = f"/api/reporting/{kind}/jobs/{job.pk}/"
                response = client.patch(url, {"narrative": "## Reviewed\nUpdated explanation", "statistics": {}}, format="json")
                self.assertEqual(response.status_code, 200)
                job.refresh_from_db()
                self.assertEqual(job.narrative, "## Reviewed\nUpdated explanation")
                self.assertEqual(job.statistics, {"totals": {"count": 3}})
                self.assertEqual(job.model_name, "test-model")
                self.assertEqual(client.get(url).data["narrative"], job.narrative)
                self.assertTrue(AuditEvent.objects.filter(action="report.edited", target_id=str(job.pk)).exists())
                for payload in ({}, {"narrative": "   "}, {"narrative": None}, {"narrative": "x" * 100001}):
                    self.assertEqual(client.patch(url, payload, format="json").status_code, 400)
                client.force_authenticate(other)
                self.assertEqual(client.patch(url, {"narrative": "Forbidden"}, format="json").status_code, 404)
                for role in ("branch_manager", "instructor"):
                    admin.role = role
                    client.force_authenticate(admin)
                    self.assertEqual(client.patch(url, {"narrative": "Forbidden"}, format="json").status_code, 403)
                client.force_authenticate(None)
                self.assertEqual(client.patch(url, {"narrative": "Forbidden"}, format="json").status_code, 403)
                admin.role = "super_admin"
                client.force_authenticate(admin)
                for status in ("queued", "running", "failed"):
                    job.status = status
                    job.save(update_fields=["status"])
                    self.assertEqual(client.patch(url, {"narrative": "Too early"}, format="json").status_code, 409)
                job.status, job.narrative = "succeeded", None
                job.save(update_fields=["status", "narrative"])
                self.assertEqual(client.patch(url, {"narrative": "No AI output"}, format="json").status_code, 409)
