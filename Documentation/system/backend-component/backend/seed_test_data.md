# Seeding test data

`seed_test_data` is a Django management command that fills the database with
a year of fictional data, so every page and feature has something to show. It
covers the last 365 days plus three weeks of upcoming sessions, which is
enough to prepare a yearly ACC report.

`seed_reporting_demo` is a separate, smaller fixture with stable IDs (see
[physical-reporting.md](physical-reporting.md)), and `seed_acc_demo` adds ACC
reporting samples (see [ACC reporting samples](#acc-reporting-samples)). The
commands don't share any data and none of them touches another's records.

## What it creates

| Area | Data |
| --- | --- |
| Branches | Dunedin (Otago), Christchurch (Canterbury), Wellington (Wellington), Auckland Central and North Shore (both Auckland). |
| Staff | 2 super admins. Each branch has 1 manager (2 at Auckland Central) and 2 instructors (3 at Auckland Central). Christchurch also has a deactivated instructor who left partway through the year. |
| Participants | 158 people aged 60–92. Some records are complete, some partial and some minimal. About 60% joined before the year started and the rest joined during it. 12 are inactive (for reactivation). |
| Photos and consent | Every participant has a real profile photo from `participants/management/seed_photos/`: 23 free-licence Unsplash portraits, matched to the participant's name and reused across participants. Every participant has photo consent. GP consent varies: some have a consent date and most of those have a GP consent PDF. |
| Sessions | 1–2 classes a week per branch for the whole year, with a break over Christmas. A few recent registers are left open, and each branch has upcoming sessions. |
| Attendance | Each person has their own attendance rate, with a dip in winter. Absences use every reason, including "Other" with a note, and a few have no reason recorded. |
| Physical tests | A baseline and then roughly quarterly follow-ups that show improvement, no change or decline. Every outcome appears (measured, unable, arms used, not attempted, skipped), along with walking aids and a few drafts in progress. Every result is checked through the app's own `GroupSerializer` rules. |
| Feedback | About 190 entries across the year, covering all three shapes: about a participant, about a session, and about a participant at a session. About 75% have reporting consent, so they can be picked for an ACC report. |
| Quarters | Dunedin and Auckland Central have custom reporting quarters for this year and last year. The other branches use calendar quarters. |
| Documents | Organisation folders (Policies, Training with a subfolder, ACC Reporting) and branch folders (Rosters, Risk Assessments, Newsletters by year), all holding readable placeholder PDFs. Some participants also have their own documents. |
| Report history | Saved attendance and physical reports for the last three calendar quarters (national and per branch), a branch manager's report, and one failed job. Their statistics are real; the written summaries come from templates. ACC reports aren't pre-made, so you can generate them yourself. |

Audit events can't be deleted, so the command doesn't create any. The audit
log fills up as the app is used.

## Usage

From `backend/`, with your virtualenv active and migrations applied:

```
ALLOW_DEMO_SEEDING=True python manage.py seed_test_data
```

The command refuses to run unless `ALLOW_DEMO_SEEDING=True`, which can be set
in the environment or in `.env`. That's the same flag `seed_reporting_demo`
uses, so the command can also seed the deployed demo site. It takes about 30
seconds.

If the seeded branches already exist, it stops. To wipe them and seed again:

```
ALLOW_DEMO_SEEDING=True python manage.py seed_test_data --reset
```

`--reset` deletes everything attached to the five seeded branches and the
seeded staff accounts, including their uploaded files. It finds them by their
fixed IDs, never by name, so other branches and accounts are left alone. Using
the same `--seed N` (default 345) gives the same data every time.

## Logins

Every account uses the password `TestPass123!`. The command prints the full
list when it finishes.

| Role | Email |
| --- | --- |
| Super Admin | `superadmin1@example.com`, `superadmin2@example.com` |
| Branch Manager | `manager1.<branch>@example.com`, plus `manager2.auckland-central@example.com` |
| Instructor | `instructor1.<branch>@example.com`, `instructor2.<branch>@example.com`, plus `instructor3.auckland-central@example.com` |
| Deactivated instructor | `instructor3.christchurch@example.com` |

`<branch>` is one of `dunedin`, `christchurch`, `wellington`,
`auckland-central` or `north-shore`.

## ACC reporting samples

From `backend/`, run `ALLOW_DEMO_SEEDING=True .venv/bin/python manage.py seed_acc_demo` against your local demo database. An optional `--as-of YYYY-MM-DD` sets the initial last-session date; reruns keep that date and preserve existing data, edits, passwords and consent flags.

This adds three branches: **DEMO Whangārei** (20 participants), **DEMO Heretaunga** (25), and **DEMO Ōtepoti** (30). Each has 12 finalised weekly sessions, varied attendance and absence reasons, and 10 feedback examples. The report period spans 77 days through the initial last-session date. Six, five and eight participants respectively have joined dates inside that period; the remaining sample registrations predate it. Rosters only include participants registered by the session date.

Feedback excerpts come from the supplied ACC reference images and cover connection, reported wellbeing, cultural delivery, training/hui, testing barriers, requests for change, missed classes and an ACC experience. Branch/participant associations and reporting consent are simulated; `source` labels record the image/item and identify the examples as **DEMO**. They are not real testimony or verified health outcomes. No AI call is made, and the ACC report layout is unchanged by seeding.

Select **All branches** (or one sample branch), use the dates printed by the command, and load consented feedback in **Prepare an ACC report**. Existing saved reports retain their original statistics snapshots.

## Where it lives

```
backend/participants/management/commands/seed_test_data.py   the command
backend/participants/management/seed_content.py              names, quotes, folder layout, PDF helper
backend/participants/management/seed_photos/                 participant photos (sources in CREDITS.md)
```

Django registers every `.py` file in an app's `management/commands/`
directory as a `manage.py` subcommand named after the file. The fixed text is
kept in `seed_content.py` so the command reads as a list of steps.
