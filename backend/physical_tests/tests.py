from datetime import timedelta

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from participants.models import Participant
from users.models import Branch, UserAccount
from .models import Assessment
from .serializers import BALANCE


class AssessmentTests(TestCase):
    def setUp(self):
        self.branch = Branch.objects.create(name="Testing branch")
        self.other = Branch.objects.create(name="Other branch")
        self.user = UserAccount.objects.create_user(username="tester", email="tester@example.com", role="instructor", branch=self.branch)
        self.participant = Participant.objects.create(first_name="Test", last_name="Participant", branch=self.branch)
        self.client = APIClient()
        self.client.force_authenticate(self.user)
        self.list_url = f"/api/physical-tests/participants/{self.participant.pk}/"
        self.job = self.client.post(self.list_url).data
        self.url = f"/api/physical-tests/{self.job['id']}/"

    def save_group(self, group, results, expected=200):
        response = self.client.put(self.url + f"results/{group}/", {"version": self.job["version"], "results": results}, format="json")
        self.assertEqual(response.status_code, expected, response.data)
        if expected == 200:
            self.job = response.data
        return response

    def measured(self, exercise, value):
        return {"exercise": exercise, "outcome": "measured", "value": value}

    def complete(self):
        return self.client.post(self.url + "complete/", {"version": self.job["version"]}, format="json")

    def test_repeated_start_resumes_one_draft_and_binds_owner(self):
        response = self.client.post(self.list_url, {"recorded_by": "fake", "branch": str(self.other.pk)}, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["id"], self.job["id"])
        self.assertEqual(Assessment.objects.count(), 1)
        self.assertEqual(str(Assessment.objects.get().recorded_by_id), str(self.user.pk))
        self.assertEqual(Assessment.objects.get().branch_id, self.branch.pk)

    def test_complete_roundtrip_is_read_only_and_next_assessment_keeps_history(self):
        self.save_group("tug", [self.measured("tug", "12.35")])
        self.save_group("chair", [self.measured("chair", 9)])
        self.save_group("balance", [self.measured(exercise, 10) for exercise in BALANCE])
        response = self.complete()
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data["status"], "completed")
        self.save_group("tug", [self.measured("tug", 20)], expected=400)
        self.assertEqual(self.client.patch(self.url, {"version": response.data["version"], "assessed_on": str(timezone.localdate())}, format="json").status_code, 400)
        created = self.client.post(self.list_url)
        self.assertEqual(created.status_code, 201)
        self.assertNotEqual(created.data["id"], self.job["id"])
        self.assertEqual(len(self.client.get(self.list_url).data), 2)

    def test_protocol_stopping_preserves_zero_and_skipped_values(self):
        self.save_group("tug", [{"exercise": "tug", "outcome": "unable", "notes": "Stopped for safety", "value": None}])
        self.save_group("chair", [{"exercise": "chair", "outcome": "arms_used", "value": 0}])
        rows = [self.measured(BALANCE[0], "4.25")] + [{"exercise": e, "outcome": "skipped", "value": None} for e in BALANCE[1:]]
        self.save_group("balance", rows)
        response = self.complete()
        self.assertEqual(response.status_code, 200, response.data)
        results = {row["exercise"]: row for row in response.data["results"]}
        self.assertEqual(results["chair"]["value"], "0.00")
        self.assertIsNone(results["one_foot"]["value"])
        self.assertEqual(results["tug"]["notes"], "Stopped for safety")

    def test_incomplete_attempts_do_not_complete_and_version_rolls_back(self):
        self.assertEqual(self.complete().status_code, 400)
        self.assertEqual(self.client.get(self.url).data["version"], 0)
        self.save_group("tug", [{"exercise": "tug", "outcome": "not_attempted", "notes": "Deferred", "value": None}])
        self.save_group("chair", [self.measured("chair", 10)])
        self.save_group("balance", [self.measured(e, 10) for e in BALANCE])
        self.assertEqual(self.complete().status_code, 400)

    def test_bad_measurements_are_rejected(self):
        for exercise, values in [("tug", [0, -1, None, "NaN", "Infinity"]), ("chair", [1.5, -1, None])]:
            for value in values:
                with self.subTest(exercise=exercise, value=value):
                    self.save_group(exercise, [self.measured(exercise, value)], expected=400)
        self.save_group("chair", [{"exercise": "chair", "outcome": "arms_used", "value": 3}], expected=400)
        self.save_group("tug", [{"exercise": "tug", "outcome": "unable", "value": 0, "notes": "Stopped"}], expected=400)
        self.save_group("tug", [{"exercise": "tug", "outcome": "unable", "value": None}], expected=400)
        self.save_group("tug", [self.measured("chair", 10)], expected=400)
        self.save_group("tug", [self.measured("tug", 10)] * 2, expected=400)

    def test_balance_requires_ordered_progression(self):
        for values in ([5, 10, 10, 10], [10, 11, 10, 10]):
            self.save_group("balance", [self.measured(e, v) for e, v in zip(BALANCE, values)], expected=400)
        self.save_group("balance", [{"exercise": e, "outcome": "skipped"} for e in BALANCE], expected=400)
        self.save_group("balance", [self.measured(BALANCE[0], 10)], expected=400)

    def test_conflicting_tab_cannot_overwrite_saved_result(self):
        self.save_group("tug", [self.measured("tug", 12)])
        response = self.client.put(self.url + "results/tug/", {"version": 0, "results": [self.measured("tug", 99)]}, format="json")
        self.assertEqual(response.status_code, 409)
        self.assertEqual(self.client.get(self.url).data["results"][0]["value"], "12.00")

    def test_branch_isolation_covers_every_endpoint(self):
        self.user.branch = self.other
        self.user.save()
        for response in [self.client.get(self.list_url), self.client.post(self.list_url), self.client.get(self.url),
                         self.client.patch(self.url, {}, format="json"), self.client.put(self.url + "results/tug/", {}, format="json"), self.complete()]:
            self.assertEqual(response.status_code, 404)
        self.client.force_authenticate(None)
        self.assertEqual(self.client.get(self.url).status_code, 403)

    def test_all_staff_roles_have_access_only_with_scope(self):
        for role in ("branch_manager", "super_admin"):
            self.user.role = role
            self.user.save()
            self.assertEqual(self.client.get(self.url).status_code, 200)
        self.user.role = "instructor"
        self.user.branch = None
        self.user.save()
        self.assertEqual(self.client.get(self.url).status_code, 404)

    def test_date_validation_and_inactive_participant(self):
        future = timezone.localdate() + timedelta(days=1)
        response = self.client.patch(self.url, {"assessed_on": str(future), "version": 0}, format="json")
        self.assertEqual(response.status_code, 400)
        self.participant.date_of_birth = timezone.localdate() - timedelta(days=100)
        self.participant.save()
        before_birth = self.participant.date_of_birth - timedelta(days=1)
        self.assertEqual(self.client.patch(self.url, {"assessed_on": str(before_birth), "version": 0}, format="json").status_code, 400)
        self.assertEqual(self.client.patch(self.url, {"assessed_on": str(timezone.localdate()), "version": 0}, format="json").status_code, 200)
        self.participant.is_active = False
        self.participant.save()
        self.assertEqual(self.client.post(self.list_url).status_code, 400)
        self.assertEqual(self.client.get(self.url).status_code, 200)

    def test_branch_with_historic_assessment_cannot_be_deleted_after_move(self):
        self.participant.branch = self.other
        self.participant.save()
        self.user.role = "super_admin"
        self.user.branch = None
        self.user.save()
        response = self.client.delete(f"/api/branches/{self.branch.pk}/")
        self.assertEqual(response.status_code, 409)
        self.assertIn("physical", response.data["detail"])

    def test_completion_rechecks_date_after_birth_date_correction(self):
        self.save_group("tug", [self.measured("tug", 12)])
        self.save_group("chair", [self.measured("chair", 10)])
        self.save_group("balance", [self.measured(e, 10) for e in BALANCE])
        from datetime import date
        response = self.client.patch(self.url, {"assessed_on": "1950-01-01", "version": self.job["version"]}, format="json")
        self.assertEqual(response.status_code, 200)
        self.job = response.data
        self.participant.date_of_birth = date(1960, 1, 1)
        self.participant.save()
        response = self.complete()
        self.assertEqual(response.status_code, 400)
        self.assertIn("assessed_on", response.data)
        saved = self.client.get(self.url).data
        self.assertEqual(saved["status"], "draft")
        self.assertEqual(saved["version"], self.job["version"])
