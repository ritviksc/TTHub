# Quickstart

This guide gets the whole system running on a development machine: the Django backend, the Vue frontend, Redis and the Celery worker. It also covers accounts, demo data, tests and resetting. It includes everything in the root `README.md`.

Commands are run from the repo root (`Group_4/`) unless a step says otherwise.

## What runs where

| Part | What it does | Address |
| --- | --- | --- |
| Frontend (Vue + Vite) | The web app you open in the browser | <http://localhost:5173> |
| Backend (Django) | The API and the database | <http://localhost:8000/api> |
| Redis (Docker) | Celery's message broker and Django's cache | `localhost:6379` |
| Celery worker | Runs AI report explanations in the background | n/a |

The development database is SQLite (`backend/db.sqlite3`), so you don't need a database server.

## 1. Install the prerequisites

- **Python 3.10 or newer**: check with `python --version` (Windows: `py --version`).
- **Node.js 22.18+ or 24.12+**: check with `node --version`. The frontend's `package.json` rejects older versions.
- **Docker Desktop**: needed for Redis. Start it before step 5.
- **Git**.
- **University VPN** when you're off campus. Without it the AI features can't reach the LLM server, though everything else still works.

## 2. Create the `.env` file

Django and Vite both read a single `.env` file at the repo root. Git ignores it, so every developer makes their own. The quickest way is to copy the template, `cp backend/.env_skeleton .env`, and fill in the blanks. At minimum, `Group_4/.env` needs:

```ini
# Django
SECRET_KEY=<generate one, see below>
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Redis: database 0 is Celery's broker (the default), database 3 is Django's cache
DJANGO_CACHE=redis://localhost:6379/3

# Allows the demo data commands in step 7
ALLOW_DEMO_SEEDING=True

# LLM provider: ask the team for these values
LLM_API_ENDPOINT=
OPENAI_API_KEY=
DEFAULT_LLM_MODEL=
```

Generate a secret key once the virtual environment from step 3 is set up:

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Notes:

- `SECRET_KEY` is required, and Django won't start without it.
- `DJANGO_CACHE` must point at a running Redis, because Django uses it for its cache.
- Optional settings: `CELERY_BROKER_URL` (default `redis://localhost:6379/0`), `CORS_ALLOWED_ORIGINS` and `CSRF_TRUSTED_ORIGINS` (both default to `http://localhost:5173`), and `VITE_API_BASE_URL` (default `http://localhost:8000/api`). The help chatbot also reads `HELP_LLM_MODEL`, `HELP_EMBED_MODEL` and `HELP_MIN_SCORE` (see [help-chatbot.md](../setup/help-chatbot.md)).
- Never commit `.env` and never paste the API key anywhere public.

## 3. Set up the Python environment

The full guide, with every shell and the common problems, is in [venv-setup.md](../setup/venv-setup.md). The short version:

```bash
# Windows: py -m venv .venv    Linux/macOS: python3 -m venv .venv
python -m venv .venv
```

Activate it:

| Shell | Command |
| --- | --- |
| Linux/macOS | `source .venv/bin/activate` |
| Windows PowerShell | `.\.venv\Scripts\Activate.ps1` |
| Git Bash on Windows | `source .venv/Scripts/activate` |

Install the backend dependencies:

```bash
python -m pip install -r backend/requirements.txt
```

## 4. Install the frontend dependencies

```bash
cd frontend
npm ci
cd ..
```

`npm ci` installs the exact versions in `package-lock.json`. Use `npm install` only when you are adding or upgrading a package.

## 5. Start Redis

The first time, create the container:

```bash
docker run --name taurite-redis -p 127.0.0.1:6379:6379 -d redis:7-alpine
```

After that, Docker keeps the container. Start and stop it with:

```bash
docker start taurite-redis
```

```bash
docker stop taurite-redis
```

If you see *the container name is already in use*, the container already exists, so use `docker start`.

## 6. Set up the database

With the virtual environment active:

```bash
cd backend
python manage.py migrate
```

Run `migrate` again whenever you pull changes that include new migrations.

## 7. Create accounts

### Option A: load demo data (recommended)

This fills the database with a year of fictional branches, staff, participants, sessions, attendance, physical tests, feedback and documents. From `backend/`:

```bash
python manage.py seed_test_data
```

It needs `ALLOW_DEMO_SEEDING=True` in `.env` and takes about 30 seconds. Every account it creates uses the password `TestPass123!`, for example `superadmin1@example.com`, `manager1.dunedin@example.com` and `instructor1.dunedin@example.com`. It prints the full list when it finishes. To wipe the demo data and seed again, add `--reset`.

There are two smaller fixtures: `seed_reporting_demo` and `seed_acc_demo`. See [seed-test-data.md](../setup/seed-test-data.md) for what each one creates.

### Option B: create a super user yourself

`role` is required on `UserAccount`, so use the Django shell instead of `createsuperuser`. From `backend/`:

```bash
python manage.py shell
```

```python
from getpass import getpass
from users.models import UserAccount
UserAccount.objects.create_superuser(
    username="admin@example.com",
    email="admin@example.com",
    password=getpass("Admin password: "),
    role=UserAccount.Role.SUPER_ADMIN,
)
exit()
```

### Option C: create a temporary test user

```bash
python manage.py shell
```

```python
from users.models import UserAccount
UserAccount.objects.create_user(
    username="testuser@example.com",
    email="testuser@example.com",
    password="TestPass123!",
    role=UserAccount.Role.SUPER_ADMIN,
)
exit()
```

## 8. Build the help chatbot index (optional)

The help chatbot answers from the articles in `backend/help/content/`. It needs an index of them, built through the LLM server, so connect to the VPN first if you're off campus. From `backend/`:

```bash
python manage.py build_help_index
```

Run it again after editing any help article. Re-runs only process the articles that changed.

## 9. Run the system

### Linux: one command

```bash
./scripts/dev.sh
```

This applies migrations, reuses a running Redis or starts one in Docker, and then starts Django on port 8000, Celery and Vite on port 5173. Open <http://localhost:5173>. Press Ctrl+C to stop everything. It needs Linux's `setsid`, so it does not run on Windows, including Git Bash. On Windows, use the separate terminals below or WSL.

### Windows, macOS or Linux: separate terminals

Make sure Redis is running (step 5). Then open three terminals, each starting at the repo root.

**Terminal 1: Django**

```bash
# activate .venv first (step 3)
cd backend
python manage.py runserver
```

**Terminal 2: Celery worker**

```bash
# activate .venv first (step 3)
cd backend

# Linux/macOS
celery -A config worker --loglevel=info --concurrency=1

# Windows
celery -A config worker --loglevel=info --pool=solo
```

**Terminal 3: frontend**

```bash
cd frontend
npm run dev
```

Open <http://localhost:5173> and sign in with an account from step 7.

Restart the Celery worker after changing any task code, because it doesn't reload by itself. Django and Vite reload automatically.

## Everyday commands

| Task | Command | Run from |
| --- | --- | --- |
| Start the frontend dev server | `npm run dev` | `frontend/` |
| Build the frontend for production | `npm run build` | `frontend/` |
| Preview the production build | `npm run preview` | `frontend/` |
| Start Django | `python manage.py runserver` | `backend/` |
| Apply migrations | `python manage.py migrate` | `backend/` |
| Start Celery (Windows) | `celery -A config worker --loglevel=info --pool=solo` | `backend/` |
| Start Celery (Linux/macOS) | `celery -A config worker --loglevel=info --concurrency=1` | `backend/` |
| Start Redis | `docker start taurite-redis` | anywhere |

## Testing

**Frontend**, from `frontend/`:

```bash
node --test tests/*.test.js
```

**Backend**, from `backend/` with the virtual environment active:

```bash
python manage.py test
```

The backend tests use an in-memory Celery broker and a stubbed LLM, so they don't need the VPN. Keep Redis running anyway, because Django's cache still uses it.

## Resetting

Wipe all data from the backend database while keeping the tables:

```bash
cd backend
python manage.py flush
```

To start completely fresh, delete `backend/db.sqlite3` and run `python manage.py migrate` again. Uploaded files live in `backend/media/` and `backend/private_media/`, and they are not removed by either command.

## Troubleshooting

| Problem | Fix |
| --- | --- |
| `KeyError: 'SECRET_KEY'` when Django starts | `.env` is missing, not at the repo root, or has no `SECRET_KEY`. |
| `ModuleNotFoundError: No module named 'django'` | The virtual environment isn't active in this terminal, or step 3's install was skipped. |
| `Error 10061` / `Connection refused` on port 6379 | Redis isn't running. Start Docker Desktop, then `docker start taurite-redis`. |
| AI analysis stays on "queued" | The Celery worker isn't running, or it was started before Redis. Restart it. |
| AI analysis or the chatbot fails, but statistics load | The LLM server can't be reached. Connect to the VPN and check the LLM values in `.env`. |
| Frontend loads but every request fails | Django isn't running on port 8000, or `VITE_API_BASE_URL` points somewhere else. |
| `npm ci` fails with an engine error | Node.js is too old. Install 22.18+ or 24.12+. |
| Celery crashes straight away on Windows | Use `--pool=solo`. The default pool doesn't work on Windows. |

## Further reading

- [System overview](../overview/system-overview.md)
- [Celery setup](../setup/celery-setup.md): how AI jobs move through Redis and the worker
- [Seed test data](../setup/seed-test-data.md)
- [Help chatbot setup](../setup/help-chatbot.md)
- [Frontend conventions](../frontend/conventions.md)
- [LLM integration](../backend/llm.md)
