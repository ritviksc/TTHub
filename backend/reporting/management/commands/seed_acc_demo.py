"""Sample ACC reporting records; reference excerpts are not real participant testimony."""
from datetime import date, time, timedelta

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from participants.models import Feedback, Participant
from sessions.models import AttendanceRecord, ProgrammeSession
from users.models import Branch
from .seed_reporting_demo import Command as ReportingDemoCommand, demo_id


# Image/item labels preserve provenance; branch and participant associations are fictional.
BRANCHES = [
    ("whangarei", "Whangārei", 20, 6, 0.60, [
        (1, "2", "participant", "Favourite day of the week."),
        (1, "5", "participant", "I find the group to be very uplifting and a great connection with whānau and keeps me motivated."),
        (2, "26", "participant", "After classes I feel energised and able to do more around the home. Being limited in my mobility, this has improved my mental health and motivation."),
        (2, "27", "participant", "Enjoy the exercises every week, they are keeping me independent at home."),
        (3, "41", "kaimahi", "Wānanga was amazing and I loved the whanaungatanga with the new kaimahi."),
        (3, "46", "kaimahi", "Kaumātua are enjoying the new exercises."),
        (4, "74", "kaimahi", 'We have found that inviting in "special" guests to tautoko with the class and kai has made the kaumātua feel very special and valued. We will keep doing this.'),
        (4, "79", "kaimahi", "Our term has been very busy; I simply ran out of time to complete testing this term."),
        (5, "Requests for change 2", "participant", "Improvements to the program: Easier visual for other attendees that may need. To have access to exercises when not in class."),
        (5, "Missed classes 2", "participant", "Classes are great, but I've had too many absences to benefit as much as I'd like."),
    ]),
    ("heretaunga", "Heretaunga", 25, 5, 0.75, [
        (1, "3", "participant", "Has been fun. Enjoy the company and the banter. Would be a shame if this was to stop. I look forward to my Thursdays."),
        (2, "25", "kaimahi", "Whanaungatanga is enjoyed over morning tea, the social aspect of Taurite Tu is just as important as exercises."),
        (2, "32", "participant", "Is helping me with balance and stability."),
        (3, "44", "participant", "Very excited about new exercises and doing harder exercises."),
        (3, "51", "kaimahi", "New exercises are great, kaumātua love them, however they are very wordy."),
        (4, "63", "kaimahi", "Kaumātua enjoyed the regional get togethers and a great opportunity to build connections between kapa in the same area."),
        (4, "70", "kaimahi", "The connections that have been made and how they support each other is amazing."),
        (4, "78", "kaimahi", "Our kaumātua have been resistant to testing for the last couple of years, however I intend to raise the possibility again in the new year, possibly with a new twist."),
        (5, "84", "kaimahi", "Whānau are seeing results and feeling empowered by this."),
        (5, "Requests for change 1", "participant", "More balance moves. Mau rākau, warm-ups. Happy to do more."),
    ]),
    ("otepoti", "Ōtepoti", 30, 8, 0.85, [
        (1, "7", "participant", "I have enjoyed the year exercising, and the group is a nice bunch."),
        (1, "8", "participant", "I love it. I find it really fun, and I realise it is starting to help my balance."),
        (2, "31", "participant", "The gentle exercises I have been doing have increased my strength, stamina, my breathing has improved and I now have the confidence to go for short walks alone."),
        (4, "64", "kaimahi", "Kaumātua loved the Regional Kaumātua Hui. They enjoyed catching up with our other roopū, and coming together for the new roll out of the exercises."),
        (3, "47", "kaimahi", "Kaumātua are loving learning the new exercises and having fun doing it."),
        (3, "50", "kaimahi", "Kaumātua love the three new developments we've introduced so far (Matatini, te timataka karakia and mindful breathing)."),
        (4, "69", "kaimahi", "Our physio has been a huge asset in our space."),
        (4, "77", "kaimahi", "I have noticed if I say we have testing the following week our kaumātua don't turn up."),
        (5, "Missed classes 3", "kaimahi", "Medical appointments, surgeries, mahi, mauiui, tangi, whānau commitments, holiday"),
        (6, "Kaimahi", "kaimahi", "After a fall, I was more comfortable to reach out to my GP to get checked out, and covered by ACC. In the past, I have been too whakamā to let anyone know I was injured. I let our kaimahi know as well and they supported me and my whānau to a full recovery."),
    ]),
]


class Command(BaseCommand):
    help = "Add three clearly labelled ACC sample branches, 75 participants, 36 sessions and 30 reference feedback examples; preserves existing records."

    def add_arguments(self, parser):
        parser.add_argument("--as-of", type=date.fromisoformat, help="Initial last-session date, YYYY-MM-DD; defaults to today.")

    @transaction.atomic
    def handle(self, *args, **options):
        if not settings.ALLOW_DEMO_SEEDING:
            raise CommandError("Demo seeding is disabled. Set ALLOW_DEMO_SEEDING=True to enable it.")
        end = options["as_of"] or timezone.localdate()
        if end > timezone.localdate():
            raise CommandError("The demo date cannot be in the future.")
        existing = ProgrammeSession.objects.filter(pk=demo_id("acc-whangarei-session-11")).first()
        if existing:
            if options["as_of"] and end != existing.date:
                raise CommandError("This ACC demo already exists with a different date. Existing records are preserved.")
            end = existing.date
        recorder = ReportingDemoCommand(stdout=self.stdout).staff("admin", "super_admin", None)
        for slug, location, count, new_count, rate, feedback in BRANCHES:
            branch, _ = Branch.objects.get_or_create(pk=demo_id(f"acc-{slug}"), defaults={
                "name": f"DEMO {location}", "region": location,
            })
            people = []
            for index in range(count):
                joined_on = end - timedelta(days=110) if index < count - new_count else end - timedelta(weeks=count - index)
                person, _ = Participant.objects.get_or_create(pk=demo_id(f"acc-{slug}-person-{index}"), defaults={
                    "first_name": "Demo", "last_name": f"{location} {index + 1:02d}",
                    "date_of_birth": date(end.year - 60 - index % 18, 1, 15), "branch": branch,
                    "joined_on": joined_on, "notes": "FICTIONAL ACC reporting sample. Identity and enrolment dates are synthetic.",
                })
                people.append(person)
            sessions = []
            for week in range(12):
                day = end - timedelta(weeks=11 - week)
                session, created = ProgrammeSession.objects.get_or_create(pk=demo_id(f"acc-{slug}-session-{week}"), defaults={
                    "branch": branch, "created_by": recorder, "date": day, "time": time(10),
                    "activity": "DEMO Taurite Tū — strength, balance and whanaungatanga", "attendance_finalised": True,
                })
                if created:
                    roster = [person for person in people if person.is_active and (person.joined_on is None or person.joined_on <= day)]
                    present_count = round(len(roster) * (rate + (week % 3 - 1) * 0.05))
                    for index, person in enumerate(roster):
                        present = (index + week) % len(roster) < present_count
                        reason = AttendanceRecord.AbsenceReason.values[(index + week) % 4]
                        AttendanceRecord.objects.create(session=session, participant=person,
                            status="present" if present else "absent", absence_reason="" if present else reason,
                            absence_reason_other="DEMO whānau commitments or tangi" if not present and reason == "other" else "")
                sessions.append(session)
            for index, (image, item, speaker, quote) in enumerate(feedback):
                session = sessions[index + 2]
                person = session.attendance.filter(status="present").order_by("participant_id").first()
                Feedback.objects.get_or_create(pk=demo_id(f"acc-{slug}-feedback-{index}"), defaults={
                    "branch": branch, "session": session,
                    "participant": person.participant if speaker == "participant" and person else None,
                    "quote": quote, "date": session.date, "recorded_by": recorder, "consent": True,
                    "speaker": Feedback.Speaker.KAUMATUA if speaker == "participant" else speaker,
                    "source": f"DEMO {speaker} example — supplied image {image}, item {item}. Reference excerpt; fictional attribution and simulated reporting consent.",
                })
            self.stdout.write(f"{branch.name}: {count} sample participants, {new_count} joined during the report period, 12 sessions and 10 feedback examples.")
        self.stdout.write(self.style.SUCCESS(f"ACC sample data ready. Report dates: {end - timedelta(weeks=11)} to {end}."))
        self.stdout.write("These are sample associations and simulated consent, not real participant statements or verified clinical outcomes. Reruns preserve edits.")
