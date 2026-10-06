from django.test import TestCase
from rest_framework.test import APIClient

from users.models import Branch, UserAccount
from .models import AttendanceAnalysisJob, PhysicalAnalysisJob


class ReportHistoryTests(TestCase):
    def test_history_is_paginated_separated_and_super_admin_only(self):
        admin = UserAccount.objects.create_user(username="history-admin", email="admin@example.com", role="super_admin")
        branch = Branch.objects.create(name="History branch")
        manager = UserAccount.objects.create_user(username="history-manager", email="manager@example.com", role="branch_manager", branch=branch)
        client = APIClient()
        for kind, model in (("attendance", AttendanceAnalysisJob), ("physical", PhysicalAnalysisJob)):
            with self.subTest(kind=kind):
                scope = {"start_date": "2026-01-01", "end_date": "2026-03-31", "branch_id": str(branch.pk)}
                jobs = [model.objects.create(requested_by=manager, branch=branch, status="succeeded",
                        narrative=f"Report {i}", statistics={"scope": scope, "totals": {"count": i}}) for i in range(21)]
                for status, narrative in (("queued", None), ("failed", None), ("succeeded", None), ("succeeded", "")):
                    excluded = model.objects.create(requested_by=admin, status=status, narrative=narrative, statistics={})
                url = f"/api/reporting/{kind}/history/"
                client.force_authenticate(admin)
                first = client.get(url)
                self.assertEqual(first.status_code, 200)
                self.assertEqual(client.get(f"{url}{excluded.pk}/").status_code, 404)
                self.assertEqual(first.data["count"], 21)
                self.assertEqual(len(first.data["results"]), 20)
                latest = first.data["results"][0]
                self.assertEqual(latest["job_id"], str(jobs[-1].pk))
                self.assertEqual(latest["scope"], scope)
                self.assertEqual(latest["branch_name"], branch.name)
                self.assertEqual(latest["requested_by"], manager.email)
                self.assertNotIn("statistics", latest)
                second = client.get(url, {"page": 2})
                self.assertEqual([row["job_id"] for row in second.data["results"]], [str(jobs[0].pk)])
                detail_url = f"{url}{jobs[-1].pk}/"
                detail = client.get(detail_url)
                self.assertEqual(detail.data["statistics"], jobs[-1].statistics)
                edit = client.patch(f"/api/reporting/{kind}/jobs/{jobs[-1].pk}/", {"narrative": "Reviewed"}, format="json")
                self.assertEqual(edit.status_code, 200)
                self.assertEqual(client.get(detail_url).data["narrative"], "Reviewed")
                self.assertEqual(client.get(detail_url).data["statistics"], jobs[-1].statistics)
                for user in (manager, None):
                    client.force_authenticate(user)
                    self.assertEqual(client.get(url).status_code, 403)
                    self.assertEqual(client.get(detail_url).status_code, 403)
                client.force_authenticate(manager)
                self.assertEqual(client.patch(f"/api/reporting/{kind}/jobs/{jobs[-1].pk}/", {"narrative": "No"}, format="json").status_code, 403)
