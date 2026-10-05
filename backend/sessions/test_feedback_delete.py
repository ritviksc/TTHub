from datetime import date, time
from django.test import TestCase
from rest_framework.test import APIClient
from participants.models import Feedback
from users.models import Branch, UserAccount
from .models import ProgrammeSession


class SessionFeedbackDeletionTests(TestCase):
    def test_session_with_feedback_returns_conflict_and_preserves_evidence(self):
        branch = Branch.objects.create(name='Branch')
        user = UserAccount.objects.create_user(username='teacher', email='teacher@example.nz', role='instructor', branch=branch)
        session = ProgrammeSession.objects.create(branch=branch, created_by=user, date=date(2026, 1, 1), time=time(10), activity='Class')
        feedback = Feedback.objects.create(branch=branch, session=session, quote='Feedback', source='Class', date=session.date, recorded_by=user)
        client = APIClient()
        client.force_authenticate(user)
        client.raise_request_exception = False
        response = client.delete(f'/api/sessions/{session.pk}/')
        self.assertEqual(response.status_code, 409)
        self.assertTrue(ProgrammeSession.objects.filter(pk=session.pk).exists())
        self.assertTrue(Feedback.objects.filter(pk=feedback.pk).exists())
