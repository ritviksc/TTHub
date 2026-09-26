# AI reporting worker

Attendance and physical-testing statistics are calculated by Django. AI explanations run in a separate Celery worker so the web request does not wait for the model.

## One-command development startup

From the repository root, run:

```sh
./scripts/dev.sh
```

The Linux/Bash launcher uses the existing `.venv` and `frontend/node_modules`; install the project dependencies first. It reads the root `.env`, reuses a reachable Redis broker, or starts Docker Redis for the default local broker. Docker must be installed and running for that fallback; its first run may download `redis:7-alpine`. Custom remote/authenticated brokers must already be available. `DJANGO_CACHE` is respected, with `redis://localhost:6379/3` used only when unset.

It applies migrations, starts Django on port 8000, Celery with one worker process, and Vite on port 5173. Open <http://localhost:5173>. Output from all services shares the terminal. A service exit stops the others. Ctrl+C stops its application processes and any Redis container it created; existing Redis services are left running. Celery is allowed to finish its current task during shutdown, so stopping can take time. Docker Redis data remains in the `taurite-dev-redis` volume between runs.

The script does not create accounts or configure LLM credentials. Keep the existing LLM configuration in `.env`. Restart the launcher after changing Celery task code.

## Local setup (separate terminals)

Use the existing Python environment and dependencies. Start Redis (the default broker is `redis://localhost:6379/0`), or set `CELERY_BROKER_URL` to your Redis service in the backend environment. For a local Docker installation you can start Redis with:

```sh
docker run --name taurite-redis -p 127.0.0.1:6379:6379 -d redis:7-alpine
```

From the repository root:

```sh
source .venv/bin/activate
cd backend
python manage.py migrate
celery -A config worker --loglevel=info --concurrency=1
```

Run Django and the frontend in separate terminals as usual. The worker needs the same database, broker and LLM environment configuration as Django. Restart the worker after changing task code. One worker process avoids unnecessary write contention with the development SQLite database. Celery Beat is not needed: these jobs are requested by users.

## Request lifecycle

1. `POST /api/reporting/attendance/analyse/` validates report scope and saves a statistics snapshot and job owner in Django.
2. Django sends only the job UUID to Redis and responds with HTTP 202 and `job_id`/`status`.
3. `reporting/tasks.py` claims the job, checks the owner's current permissions, calls the LLM service and saves the explanation. Duplicate deliveries cannot claim the same job twice.
4. The frontend polls `GET /api/reporting/attendance/jobs/<job_id>/` until it succeeds or fails. Only the requesting user, with continuing report access, can read the result.

No finalised sessions means an immediate completed response without an LLM request. Statistics remain available if Redis or the LLM is unavailable. Broker failures return 503; worker failures save a safe error. Pending jobs expire after 15 minutes when checked, and tasks have worker execution limits. There are no automatic task retries that could repeat a paid model call. Leaving the page stops polling; it does not cancel the worker job.

Job snapshots and explanations are stored in the database, not the Django cache or a Celery result backend. Existing jobs protect their referenced branch from deletion. There is currently no automatic job retention/cleanup policy. These snapshots capture the figures used for an explanation; they are not an approved quarterly-report workflow.

## Manual check

Log in as a super admin or branch manager. Open Reporting, select a period with finalised attendance, and click the AI analysis button. The page should show queued/running progress and then a Markdown explanation. Check the worker terminal for the completed task. Stop Redis and request another analysis to verify a queue error while ordinary statistics still load.

Automated tests use a real Celery worker with an in-memory broker and a stubbed LLM, plus tests for permissions, failures, duplicate delivery and frontend polling. This does not verify a deployed Redis service or a live model response.


## Physical-testing analysis

Physical reporting uses the same worker and job lifecycle. Its endpoints are `/api/reporting/physical/`, `/api/reporting/physical/analyse/` and `/api/reporting/physical/jobs/<job_id>/`. The task is `reporting.tasks.generate_physical_analysis`; results are saved in `PhysicalAnalysisJob`. Restart existing workers to register the new task. Only aggregate statistics are sent to the model. See [physical-reporting.md](physical-reporting.md) for reporting rules and demo accounts.
