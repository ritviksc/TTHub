"""Fixed text and layout used by the `seed_test_data` command.

Kept apart from the command so the command reads as the order of steps, and
this file as the data it draws from. Everything here is fictional.
"""
import unicodedata

# (slug, display name, region, participants, managers, instructors)
# Two branches share a region so the branch switcher has something to group.
BRANCHES = [
    ("dunedin", "Dunedin", "Otago", 34, 1, 2),
    ("christchurch", "Christchurch", "Canterbury", 30, 1, 2),
    ("wellington", "Wellington", "Wellington", 28, 1, 2),
    ("auckland-central", "Auckland Central", "Auckland", 40, 2, 3),
    ("north-shore", "North Shore", "Auckland", 26, 1, 2),
]

# Branches that get custom reporting quarters; the rest keep calendar quarters.
CUSTOM_QUARTER_BRANCHES = ["dunedin", "auckland-central"]

# The branch whose extra instructor has left and been deactivated.
DEACTIVATED_INSTRUCTOR_BRANCH = "christchurch"

SUPER_ADMINS = [
    ("superadmin1", "Aroha", "Whaanga"),
    ("superadmin2", "Graham", "Fletcher"),
]

# Split so each participant gets a photo that fits their name; see
# seed_photos/CREDITS.md for which photos are which.
FEMALE_FIRST_NAMES = [
    "Margaret", "Patricia", "Barbara", "Elizabeth", "Susan", "Jennifer", "Linda",
    "Karen", "Nancy", "Betty", "Sandra", "Carol", "Ruth", "Sharon", "Colleen",
    "Janice", "Judith", "Diane", "Marilyn", "Aroha", "Ngaio", "Mere", "Ana",
    "Huia", "Malia", "Fatu", "Ilaisaane", "Losalini", "Mei", "Priya", "Lan",
]
MALE_FIRST_NAMES = [
    "John", "Robert", "Michael", "William", "David", "Richard", "Joseph",
    "Thomas", "Charles", "Christopher", "Peter", "Paul", "Graeme", "Bruce",
    "Trevor", "Kevin", "Gary", "Wayne", "Hemi", "Rawiri", "Wiremu", "Tane",
    "Manaia", "Tamati", "Siosaia", "Sione", "Wei", "Hyun", "Arjun", "Minh", "Rajesh",
]
FIRST_NAMES = FEMALE_FIRST_NAMES + MALE_FIRST_NAMES

# Participant photos in seed_photos/: photo_01-09 are women, photo_10-23 men.
FEMALE_PHOTOS = [f"photo_{n:02d}.jpg" for n in range(1, 10)]
MALE_PHOTOS = [f"photo_{n:02d}.jpg" for n in range(10, 24)]

LAST_NAMES = [
    "Smith", "Jones", "Williams", "Brown", "Taylor", "Wilson", "Johnson",
    "White", "Martin", "Anderson", "Thompson", "Nguyen", "Clarke", "Walker",
    "Robinson", "Wright", "Roberts", "King", "Baker", "Green", "Adams",
    "Hill", "Campbell", "Mitchell", "Carter", "Evans", "Turner", "Phillips",
    "Ngata", "Wikaira", "Rangi", "Waititi", "Paraone", "Tipene", "Horomona",
    "Tuilagi", "Fifita", "Havili", "Faleolo", "Patel", "Singh", "Kim", "Park",
    "Chen", "Lee", "Wong", "Reid", "Fraser", "Stewart", "Douglas", "McKenzie",
]

MANAGER_FIRST_NAMES = ["Fiona", "Grant", "Alison", "Craig", "Denise", "Shane", "Vicki", "Mereana"]
INSTRUCTOR_FIRST_NAMES = [
    "Hana", "Tyler", "Leilani", "Josh", "Amber", "Cody", "Renee", "Blake",
    "Anahera", "Kane", "Tui", "Reuben", "Marama", "Levi", "Kiri", "Nadia",
]

ACTIVITIES = [
    "Strength and balance",
    "Gentle movement",
    "Seated exercise",
    "Falls prevention circuit",
    "Balance and mobility",
    "Tai chi for balance",
]

# (hour, minute) options for class start times.
SESSION_TIMES = [(9, 30), (10, 0), (10, 30), (13, 30)]

OTHER_ABSENCE_TEXTS = [
    "Feeling unwell today.",
    "Family visiting from out of town.",
    "Weather kept them home.",
    "Recovering from a cold.",
    "Caring for a grandchild.",
    "Hospital visit for a family member.",
]

PARTICIPANT_NOTES = [
    "Prefers a chair near the door.",
    "Hard of hearing on the left side; stand on the right when giving instructions.",
    "Brings own water bottle and towel.",
    "Usually gets a lift with a neighbour.",
    "Likes to be called by preferred name.",
    "Mild arthritis in both knees; modify floor work.",
]

WALKING_AIDS = ["Walking stick", "Walker frame"]

TUG_UNABLE_NOTES = ["Stopped for safety: felt light-headed.", "Stopped for safety: unsteady on the turn."]
CHAIR_NOT_ATTEMPTED_NOTES = ["Knee pain on the day.", "Declined today: tired after a hospital visit."]
BALANCE_NOT_ATTEMPTED_NOTES = ["Not confident to try without support today.", "Dizzy on standing; balance tests skipped."]

# ---------------------------------------------------------------------------
# Feedback. Each shape has its own pool so the wording fits what it is about.
# ---------------------------------------------------------------------------

# About one participant, no particular session.
PARTICIPANT_QUOTES = [
    "I can get up out of my chair without using my hands now. I couldn't do that in summer.",
    "My daughter noticed I'm walking much more steadily to the letterbox.",
    "I was frightened of falling again after my hip. Coming here has given me my confidence back.",
    "I've started doing the heel raises while the jug boils, like you showed us.",
    "Walking up the hill to the shops is easier. I don't have to stop halfway any more.",
    "I look forward to Tuesdays. It's the only time I see some of these people.",
    "My GP said my balance has improved and to keep coming.",
    "I can carry the washing basket down the steps again.",
    "Kei te pai ahau. I feel stronger in my legs since I started.",
    "I haven't had a fall since I joined, and I used to have one every couple of months.",
    "The exercises are easy to remember so I do them at home on the days in between.",
    "I was nervous on the first day but everyone made me feel welcome.",
    "I can stand on the bus now while it moves without grabbing the pole.",
    "My knees still ache but I'm moving better than I have in years.",
    "Being able to get down to the garden again means a lot to me.",
    "I feel safer in the shower now my balance is better.",
]

# About one session as a whole.
SESSION_QUOTES = [
    "The new circuit was a good challenge without being too much.",
    "The group really enjoyed the music today; lots of laughter.",
    "Too cold in the hall this morning. Could the heaters go on earlier?",
    "The seated version helped those of us with sore backs.",
    "Great turnout today and a lovely cup of tea afterwards.",
    "The tai chi was relaxing; several people asked for it again.",
    "It was a bit crowded today. Hard to hear the instructions at the back.",
    "Really liked practising getting up from the floor safely.",
    "Pace was just right, and the instructor checked on everyone.",
    "The kōrero at the start about medication and dizziness was useful.",
]

# About one participant at one session.
PARTICIPANT_SESSION_QUOTES = [
    "Today was the first time I did the whole class standing.",
    "I managed ten seconds on one foot today. I was so pleased.",
    "I felt a bit wobbly today, but the instructor gave me an easier option.",
    "First class back after my operation and it went really well.",
    "I brought my neighbour along today and she loved it.",
    "My legs were tired after the step-ups but in a good way.",
    "I needed a rest partway through today but I finished the class.",
    "I didn't need my stick for the walking part today.",
]

PARTICIPANT_SOURCES = [
    "Participant, spoken to instructor",
    "Participant, written card",
    "Participant, phone call",
    "Family member (daughter)",
    "Family member (husband)",
    "Family member (son)",
    "End-of-term survey",
]
SESSION_SOURCES = [
    "Group discussion after class",
    "Instructor observation",
    "End-of-term survey",
    "Participant, spoken to instructor",
]
PARTICIPANT_SESSION_SOURCES = [
    "Participant, spoken to instructor",
    "Instructor observation",
    "Family member (daughter)",
]

# ---------------------------------------------------------------------------
# Documents. Each level is a dict: "_files" lists files at that level and
# every other key is a subfolder. "{year}" / "{last_year}" are filled in.
# ---------------------------------------------------------------------------

ORG_TREE = {
    "_files": ["Taurite Tu Programme Overview.pdf"],
    "Policies": {"_files": [
        "Health and Safety Policy.pdf", "Privacy Policy.pdf", "Code of Conduct.pdf",
        "Incident Reporting Procedure.pdf",
    ]},
    "Training": {
        "_files": ["Instructor Induction Guide.pdf", "First Aid Refresher Schedule.pdf"],
        "Falls Prevention Modules": {"_files": [
            "Module 1 - Strength.pdf", "Module 2 - Balance.pdf", "Module 3 - Getting Up From the Floor.pdf",
        ]},
    },
    "ACC Reporting": {"_files": ["ACC Reporting Guidelines.pdf", "Quarterly Report Template.pdf"]},
}

BRANCH_TREE = {
    "_files": ["Venue Hire Agreement.pdf", "Emergency Contacts.pdf"],
    "Rosters": {"_files": ["Instructor Roster Term 1.pdf", "Instructor Roster Term 2.pdf"]},
    "Risk Assessments": {"_files": ["Hall Risk Assessment.pdf", "Fire Evacuation Plan.pdf"]},
    "Newsletters": {
        "{last_year}": {"_files": ["Spring Newsletter.pdf", "Summer Newsletter.pdf"]},
        "{year}": {"_files": ["Autumn Newsletter.pdf", "Winter Newsletter.pdf"]},
    },
}

PARTICIPANT_DOCUMENTS = [
    "GP Referral Letter.pdf",
    "Physiotherapy Report.pdf",
    "Medication List.pdf",
    "Hospital Discharge Summary.pdf",
]

# ---------------------------------------------------------------------------
# Report summaries for seeded report history. Filled with real statistics.
# ---------------------------------------------------------------------------

SEEDED_NOTE = "This summary was written by the seed data command for demonstration. It was not generated by AI."

ATTENDANCE_SUMMARY = """Attendance summary: {scope}, {start} to {end}

Across {finalised} finalised sessions there were {attendances} attendances from {distinct} different people. That is {rate}% of roster places, or an average of {average} people per session. {incomplete} session register(s) were not finalised and are left out of these figures.

The most common recorded absence reason was "{top_reason}" ({top_percent}% of absences).

{note}"""

PHYSICAL_SUMMARY = """Physical testing summary: {scope}, {start} to {end}

{tested} of {eligible} eligible participants ({completion}%) completed at least one assessment, with {completed} completed assessments in total and {drafts} still in draft.

Mean timed up and go was {tug} seconds and mean 30-second chair stands was {chair}. Where people had two comparable results, the average change in timed up and go was {tug_change} seconds across {tug_pairs} people.

{note}"""

FAILED_REPORT_ERROR = "The AI provider did not respond in time. Please try again."


# ---------------------------------------------------------------------------
# Placeholder PDFs
# ---------------------------------------------------------------------------

def _pdf_text(value):
    # The built-in Helvetica font only covers Latin-1, so drop macrons and
    # anything else outside it, and escape PDF string delimiters.
    plain = unicodedata.normalize("NFKD", value).encode("latin-1", "ignore").decode("latin-1")
    plain = "".join(ch for ch in plain if not unicodedata.combining(ch))
    return plain.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def make_pdf(title, lines=()):
    """Return the bytes of a small, valid one-page PDF showing a title and lines."""
    text = [f"BT /F1 18 Tf 60 770 Td ({_pdf_text(title)}) Tj ET"]
    y = 740
    for line in ("Fictional demonstration document.", *lines):
        text.append(f"BT /F1 11 Tf 60 {y} Td ({_pdf_text(line)}) Tj ET")
        y -= 18
    stream = "\n".join(text).encode("latin-1")
    objects = [
        b"<</Type/Catalog/Pages 2 0 R>>",
        b"<</Type/Pages/Kids[3 0 R]/Count 1>>",
        b"<</Type/Page/Parent 2 0 R/MediaBox[0 0 595 842]/Resources<</Font<</F1 5 0 R>>>>/Contents 4 0 R>>",
        b"<</Length " + str(len(stream)).encode() + b">>stream\n" + stream + b"\nendstream",
        b"<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>",
    ]
    out = bytearray(b"%PDF-1.4\n")
    offsets = []
    for number, body in enumerate(objects, start=1):
        offsets.append(len(out))
        out += f"{number} 0 obj".encode() + body + b"endobj\n"
    xref = len(out)
    out += f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n".encode()
    for offset in offsets:
        out += f"{offset:010d} 00000 n \n".encode()
    out += f"trailer<</Size {len(objects) + 1}/Root 1 0 R>>\nstartxref\n{xref}\n%%EOF\n".encode()
    return bytes(out)
