# Seeding test data

For the complete staff-to-reporting demo, use **`seed_reporting_demo`** instead. It includes a super admin, adult participants, sessions and assessments, and preserves existing records on reruns. See [physical-reporting.md](physical-reporting.md). The older command below is retained unchanged.

## ACC reporting samples

From `backend/`, run `ALLOW_DEMO_SEEDING=True .venv/bin/python manage.py seed_acc_demo` against your local demo database. An optional `--as-of YYYY-MM-DD` sets the initial last-session date; reruns keep that date and preserve existing data, edits, passwords and consent flags.

This adds three branches: **DEMO Whangārei** (20 participants), **DEMO Heretaunga** (25), and **DEMO Ōtepoti** (30). Each has 12 finalised weekly sessions, varied attendance and absence reasons, and 10 feedback examples. The report period spans 77 days through the initial last-session date. Six, five and eight participants respectively have joined dates inside that period; the remaining sample registrations predate it. Rosters only include participants registered by the session date.

Feedback excerpts come from the supplied ACC reference images and cover connection, reported wellbeing, cultural delivery, training/hui, testing barriers, requests for change, missed classes and an ACC experience. Branch/participant associations and reporting consent are simulated; `source` labels record the image/item and identify the examples as **DEMO**. They are not real testimony or verified health outcomes. No AI call is made, and the ACC report layout is unchanged by seeding.

Select **All branches** (or one sample branch), use the dates printed by the command, and load consented feedback in **Prepare an ACC report**. Existing saved reports retain their original statistics snapshots.

`seed_test_data` is a Django management command that populates the database
with fixed test data for local testing / demoing. It always creates the same
shape of data — no options to tweak counts:

- 2 branches: Dunedin, Christchurch
- 60 participants total, 30 per branch
- 4 staff accounts: 1 Branch Manager + 1 Instructor per branch

## Prerequisites

From `backend/`, with your virtualenv active and migrations applied:

```
pip install -r requirements.txt
python manage.py migrate
```

## Usage

```
python manage.py seed_test_data
```

Branches and staff accounts are looked up with `get_or_create` (by name /
email), so running it again won't duplicate them. Participants aren't
deduplicated, so running it again adds another 30 participants to each
branch.

### Removing seeded data

```
python manage.py seed_test_data --clear
```

Deletes the seeded participants and staff accounts, then the branches
themselves (in that order — both `Participant.branch` and
`UserAccount.branch` are `on_delete=PROTECT`, so Django refuses to delete a
branch that's still referenced). Combine with a plain run to wipe and
reseed in one go:

```
python manage.py seed_test_data --clear && python manage.py seed_test_data
```

## Staff accounts

| Role | Email | Password |
| --- | --- | --- |
| Branch Manager | `manager.dunedin@example.com` | `TestPass123!` |
| Instructor | `instructor.dunedin@example.com` | `TestPass123!` |
| Branch Manager | `manager.christchurch@example.com` | `TestPass123!` |
| Instructor | `instructor.christchurch@example.com` | `TestPass123!` |

Each Branch Manager owns their branch via `UserAccount.branch`, the same FK
the app uses everywhere else to scope a manager/instructor to a branch —
there's no separate "ownership" field.

It does not create a Super Admin account. If you need one, create it
separately (e.g. `python manage.py createsuperuser` plus setting
`role="super_admin"`).

## Where it lives, and why the extra files

```
backend/participants/management/__init__.py
backend/participants/management/commands/__init__.py
backend/participants/management/commands/seed_test_data.py
```

This is Django's required layout for a custom `manage.py` subcommand, not
project-specific structure:

- Django looks for commands inside a `management/commands/` directory in each
  installed app. Every `.py` file in there (other than `__init__.py`) is
  registered as a subcommand named after the file — `seed_test_data.py`
  becomes `python manage.py seed_test_data`.
- The two `__init__.py` files just mark `management/` and
  `management/commands/` as regular Python packages so Django's command
  loader can import them reliably. They're empty on purpose — nothing needs
  to go in them.
- You may also see `__pycache__/` folders appear alongside these files after
  running the command. Those are auto-generated, compiled-bytecode caches
  Python creates on import to speed up the next run. They aren't source code,
  aren't required, and are already covered by `.gitignore` — safe to ignore
  or delete; Python recreates them as needed.
