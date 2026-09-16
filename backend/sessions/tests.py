from datetime import date, time

from django.test import TestCase

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
