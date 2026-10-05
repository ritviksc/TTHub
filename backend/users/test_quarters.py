from copy import deepcopy
from datetime import date, time

from django.test import TestCase
from rest_framework.test import APIClient

from sessions.models import ProgrammeSession
from .models import Branch, BranchQuarter, UserAccount
from .quarters import calendar_quarters, QuarterSerializer


class BranchQuarterTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.branch = Branch.objects.create(name="Harbour")
        cls.other = Branch.objects.create(name="Hills")
        cls.manager = UserAccount.objects.create_user(username="manager", email="manager@test.nz",
            role="branch_manager", branch=cls.branch)
        cls.admin = UserAccount.objects.create_user(username="admin", email="admin@test.nz", role="super_admin")
        cls.instructor = UserAccount.objects.create_user(username="instructor", email="instructor@test.nz",
            role="instructor", branch=cls.branch)

    def setUp(self):
        self.client = APIClient()
        self.client.force_authenticate(self.manager)
        self.url = f"/api/branches/{self.branch.pk}/quarters/2026/"
        self.payload = {"quarters": list(QuarterSerializer(calendar_quarters(2026), many=True).data)}

    def test_defaults_do_not_write_rows(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["is_default"])
        self.assertEqual(response.data["quarters"], self.payload["quarters"])
        self.assertEqual(BranchQuarter.objects.count(), 0)

    def test_save_is_isolated_by_branch_and_year(self):
        self.payload["quarters"][0]["start_date"] = "2026-02-01"
        result = self.client.put(self.url, self.payload, format="json")
        self.assertEqual(result.status_code, 200, result.data)
        self.assertFalse(result.data["is_default"])
        self.assertEqual(self.client.get(self.url).data["quarters"][0]["start_date"], "2026-02-01")
        self.assertTrue(self.client.get(self.url.replace("2026", "2027")).data["is_default"])
        self.client.force_authenticate(self.admin)
        other_url = f"/api/branches/{self.other.pk}/quarters/2026/"
        self.assertTrue(self.client.get(other_url).data["is_default"])
        self.assertEqual(self.client.put(other_url, self.payload, format="json").status_code, 200)

    def test_permissions(self):
        other_url = f"/api/branches/{self.other.pk}/quarters/2026/"
        self.assertEqual(self.client.get(other_url).status_code, 404)
        self.assertEqual(self.client.put(other_url, self.payload, format="json").status_code, 404)
        for user in (self.instructor, None):
            self.client.force_authenticate(user)
            self.assertIn(self.client.get(self.url).status_code, (401, 403))
            self.assertIn(self.client.put(self.url, self.payload, format="json").status_code, (401, 403))
        self.assertEqual(BranchQuarter.objects.count(), 0)

    def test_invalid_settings_leave_existing_year_unchanged(self):
        self.client.put(self.url, self.payload, format="json")
        invalid = []
        for key, value in (("start_date", "2026-04-01"), ("start_date", "2025-12-31"),
                           ("end_date", "2026-04-01"), ("start_date", "invalid"), ("quarter", 2)):
            data = deepcopy(self.payload)
            data["quarters"][0][key] = value
            invalid.append(data)
        invalid.append({"quarters": self.payload["quarters"][:3]})
        for data in invalid:
            with self.subTest(data=data):
                self.assertEqual(self.client.put(self.url, data, format="json").status_code, 400)
                self.assertEqual(self.client.get(self.url).data["quarters"], self.payload["quarters"])
        self.assertEqual(BranchQuarter.objects.count(), 4)

    def test_saved_dates_filter_both_report_types(self):
        self.payload["quarters"][0].update(start_date="2026-02-01", end_date="2026-02-21")
        saved = self.client.put(self.url, self.payload, format="json").data["quarters"][0]
        for day in (date(2026, 1, 31), date(2026, 2, 1), date(2026, 2, 21), date(2026, 2, 22)):
            ProgrammeSession.objects.create(branch=self.branch, created_by=self.manager,
                date=day, time=time(10), activity="Class", attendance_finalised=True)
        params = {key: saved[key] for key in ("start_date", "end_date")}
        for report_type in ("attendance", "physical"):
            result = self.client.get(f"/api/reporting/{report_type}/", params)
            self.assertEqual(result.status_code, 200, result.data)
            self.assertEqual(result.data["scope"]["start_date"], saved["start_date"])
            self.assertEqual(result.data["scope"]["end_date"], saved["end_date"])
            if report_type == "attendance":
                self.assertEqual(result.data["totals"]["total_sessions"], 2)

    def test_invalid_year(self):
        for year in (0, 1899, 9999):
            url = self.url.replace("2026", str(year))
            self.assertEqual(self.client.get(url).status_code, 400)
