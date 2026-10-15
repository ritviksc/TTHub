# Taurite Tū

A web app for running Taurite Tū, a strength and balance programme for kaumātua (older adults). Staff use it to manage branches (kapa), participants, classes and attendance, record physical assessments, and produce reports for ACC, with optional AI-written summaries.

Built by COSC345 Group 4, University of Otago.

## Features

- **Participants**: profiles, contact and emergency details, photo and GP consent, documents.
- **Sessions and attendance**: plan classes, take the register, record absence reasons.
- **Physical assessments**: chair stand, timed up-and-go and balance tests, compared quarter to quarter.
- **Reporting**: attendance and physical-testing statistics by branch and quarter, AI explanations, and ACC report drafts.
- **Documents**: shared organisation and branch folders.
- **Help**: role-specific help articles and a help chatbot that answers from them.
- **Audit log**: a record of who changed what.

Three roles use the app: **kaimahi** (instructors), **branch managers** and **super admins**. Each one sees only what their role allows.

## Tech stack

| Part | Technology |
| --- | --- |
| Frontend | Vue 3, Vue Router, Vite, Axios |
| Backend | Django 5.2, Django REST Framework |
| Background jobs | Celery, with Redis as the broker |
| Cache | Redis |
| Database | SQLite |
| AI | University vLLM server through the OpenAI client |

## Getting started

**[docs/quickstart](docs/quickstart/guide.md)** walks through the whole setup, from installing the prerequisites to signing in. In short:

```bash
# 1. Configuration: copy the template, then fill in SECRET_KEY and the LLM values
cp backend/.env_skeleton .env

# 2. Python environment and backend dependencies
python -m venv .venv
source .venv/bin/activate          # Windows PowerShell: .\.venv\Scripts\Activate.ps1
python -m pip install -r backend/requirements.txt

# 3. Frontend dependencies
npm ci --prefix frontend

# 4. Redis
docker run --name taurite-redis -p 127.0.0.1:6379:6379 -d redis:7-alpine

# 5. Database and demo data
cd backend
python manage.py migrate
python manage.py seed_test_data    # needs ALLOW_DEMO_SEEDING=True in .env
```

Then start everything. On Linux, `./scripts/dev.sh` runs it all in one terminal. On Windows or macOS, open three terminals:

```bash
# from backend/: Django
python manage.py runserver

# from backend/: Celery worker (Windows: use --pool=solo in place of --concurrency=1)
celery -A config worker --loglevel=info --concurrency=1

# from frontend/: Vite dev server
npm run dev
```

Open <http://localhost:5173> and sign in as `superadmin1@example.com` with the password `TestPass123!`.

## Testing

```bash
# from backend/
python manage.py test
```

```bash
# from frontend/
node --test tests/*.test.js
```

## Project structure

```
Group_4/
├── backend/        Django project (config/) and apps: users, participants, sessions,
│                   physical_tests, reporting, documents, help, llm, audit
├── frontend/       Vue app (src/views, src/components, src/apis.js)
├── docs/           Developer documentation
├── scripts/        dev.sh, the Linux development launcher
└── .env            Local configuration (not committed; copy backend/.env_skeleton)
```

## Documentation

| Folder | What's in it |
| --- | --- |
| [quickstart](docs/quickstart/guide.md) | Full setup guide |
| [setup](docs/setup) | Python environment, Celery, demo data, help chatbot |
| [overview](docs/overview) | System overview and te reo Māori terms used in the app |
| [features](docs/features) | How each feature behaves |
| [backend](docs/backend) | Audit log, document storage, LLM integration |
| [frontend](docs/frontend) | Frontend coding conventions |
| [bug-scans](docs/bug-scans) | Past code review findings |
