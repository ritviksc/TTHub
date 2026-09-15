import random
from datetime import date, timedelta

from django.core.management.base import BaseCommand

from participants.models import Participant
from users.models import Branch, UserAccount

FIRST_NAMES = [
    "Olivia", "Liam", "Emma", "Noah", "Ava", "Ethan", "Sophia", "Mason",
    "Isabella", "Lucas", "Mia", "Aiden", "Amelia", "Jack", "Harper", "Logan",
    "Evelyn", "James", "Charlotte", "Benjamin", "Grace", "Henry", "Chloe",
    "Oliver", "Zoe", "William", "Lily", "Elijah", "Ella", "Alexander",
]

LAST_NAMES = [
    "Smith", "Jones", "Williams", "Brown", "Taylor", "Wilson", "Johnson",
    "White", "Martin", "Anderson", "Thompson", "Nguyen", "Clarke", "Walker",
    "Robinson", "Wright", "Thomas", "Roberts", "King", "Baker", "Green",
    "Adams", "Nelson", "Hill", "Campbell", "Mitchell", "Carter", "Evans",
    "Turner", "Phillips",
]

BRANCH_NAMES = ["Dunedin", "Christchurch"]
PARTICIPANTS_PER_BRANCH = 30

# Password set on every seeded staff account (manager + instructor).
STAFF_PASSWORD = "TestPass123!"


class Command(BaseCommand):
    help = "Populate the database with 2 branches, 60 participants, and 4 staff accounts."

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear", action="store_true",
            help="Delete the seeded branches, staff accounts, and participants first.",
        )

    def handle(self, *args, **options):
        if options["clear"]:
            # Participant.branch and UserAccount.branch are both
            # on_delete=PROTECT, so both have to go before the branches
            # they belong to.
            Participant.objects.filter(branch__name__in=BRANCH_NAMES).delete()
            UserAccount.objects.filter(branch__name__in=BRANCH_NAMES).delete()
            Branch.objects.filter(name__in=BRANCH_NAMES).delete()
            self.stdout.write(f"Cleared seeded data for {BRANCH_NAMES}.")

        today = date.today()

        for branch_name in BRANCH_NAMES:
            branch, _ = Branch.objects.get_or_create(
                name=branch_name, defaults={"region": "Test Region"}
            )

            slug = branch_name.lower()
            manager = self._get_or_create_staff(
                email=f"manager.{slug}@example.com",
                first_name=branch_name,
                last_name="Manager",
                role=UserAccount.Role.BRANCH_MANAGER,
                branch=branch,
            )
            instructor = self._get_or_create_staff(
                email=f"instructor.{slug}@example.com",
                first_name=branch_name,
                last_name="Instructor",
                role=UserAccount.Role.INSTRUCTOR,
                branch=branch,
            )

            for i in range(PARTICIPANTS_PER_BRANCH):
                first_name = random.choice(FIRST_NAMES)
                last_name = random.choice(LAST_NAMES)
                dob = today - timedelta(days=random.randint(6 * 365, 17 * 365))
                joined_on = today - timedelta(days=random.randint(0, 365))

                Participant.objects.create(
                    first_name=first_name,
                    last_name=last_name,
                    date_of_birth=dob,
                    email=f"{first_name.lower()}.{last_name.lower()}{i}@example.com",
                    branch=branch,
                    joined_on=joined_on,
                )

            self.stdout.write(
                f"{branch.name}: manager {manager.email}, instructor {instructor.email}, "
                f"{PARTICIPANTS_PER_BRANCH} participants."
            )

        self.stdout.write(self.style.SUCCESS(f"Done. Staff password: {STAFF_PASSWORD}"))

    def _get_or_create_staff(self, *, email, first_name, last_name, role, branch):
        account, created = UserAccount.objects.get_or_create(
            email=email,
            defaults={
                "username": email,
                "first_name": first_name,
                "last_name": last_name,
                "role": role,
                "branch": branch,
            },
        )
        if created:
            account.set_password(STAFF_PASSWORD)
            account.save()
        return account
