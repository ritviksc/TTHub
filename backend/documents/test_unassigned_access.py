from io import BytesIO
from unittest.mock import patch
from django.test import TestCase
from rest_framework.test import APIClient
from participants.models import Participant
from users.models import Branch, UserAccount
from .models import Document


class UnassignedDocumentTests(TestCase):
    def test_unassigned_staff_cannot_list_retrieve_or_download_participant_files(self):
        branch = Branch.objects.create(name='Branch')
        participant = Participant.objects.create(first_name='Private', last_name='Person', branch=branch)
        private = Document.objects.create(name='Private.pdf', file='private.pdf', size=1, participant=participant)
        public = Document.objects.create(name='Policy.pdf', file='policy.pdf', size=1)
        client = APIClient()
        for role in ('instructor', 'branch_manager'):
            with self.subTest(role=role):
                user = UserAccount.objects.create_user(username=role, email=f'{role}@example.nz', role=role)
                client.force_authenticate(user)
                response = client.get('/api/documents/')
                self.assertEqual([row['id'] for row in response.data], [str(public.pk)])
                self.assertEqual(client.get(f'/api/documents/{private.pk}/').status_code, 404)
                with patch.object(private.file.storage, 'open', return_value=BytesIO(b'private content')) as opened:
                    self.assertEqual(client.get(f'/api/documents/{private.pk}/download/').status_code, 404)
                    opened.assert_not_called()
