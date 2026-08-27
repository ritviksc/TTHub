from django.db.models import Count
from django.db.models.deletion import ProtectedError
from django.test import TestCase

from users.models import Branch

from .models import Participant


class ParticipantModelTests(TestCase):
    def setUp(self):
        self.kapa = Branch.objects.create(name="Ngā Hau e Whā", region="Rotorua")

    def test_str_uses_full_name(self):
        p = Participant.objects.create(
            first_name="Materoa", last_name="Ngātai", branch=self.kapa
        )
        self.assertEqual(str(p), "Materoa Ngātai")

    def test_optional_fields_may_be_left_blank(self):
        p = Participant.objects.create(
            first_name="Hēmi", last_name="Rangitāua", branch=self.kapa
        )
        p.full_clean()  # raises if a blank field is actually required
        self.assertTrue(p.is_active)
        self.assertIsNone(p.date_of_birth)

    def test_ordered_by_last_then_first_name(self):
        for first, last in [("Ana", "Ngata"), ("Mere", "Toko"), ("Wiremu", "Ngata")]:
            Participant.objects.create(first_name=first, last_name=last, branch=self.kapa)

        self.assertEqual(
            [p.full_name for p in Participant.objects.all()],
            ["Ana Ngata", "Wiremu Ngata", "Mere Toko"],
        )

    def test_reverse_accessor_counts_participants_per_kapa(self):
        other = Branch.objects.create(name="Te Puna Ora", region="Kirikiriroa")
        Participant.objects.create(first_name="Rāhera", last_name="Tuhi", branch=self.kapa)
        Participant.objects.create(first_name="Piripi", last_name="Kereama", branch=other)
        Participant.objects.create(first_name="Aroha", last_name="Bell", branch=other)

        # The count the Kapa table needs, in one query rather than N.
        counts = {
            b.name: b.n
            for b in Branch.objects.annotate(n=Count("participants"))
        }
        self.assertEqual(counts, {"Ngā Hau e Whā": 1, "Te Puna Ora": 2})

    def test_kapa_with_participants_cannot_be_deleted(self):
        Participant.objects.create(first_name="Mere", last_name="Toko", branch=self.kapa)
        with self.assertRaises(ProtectedError):
            self.kapa.delete()
