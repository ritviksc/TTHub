# Celery and AI report jobs

Attendance and physical-testing statistics are calculated by Django. AI explanations and ACC drafts run in a separate Celery worker, so the web request doesn't wait for the model. Redis carries the job messages between Django and the worker.

## Running it locally

### Linux: one command

From the repo root:

```bash
./scripts/dev.sh
```

It uses `.venv` and `frontend/node_modules` (install both first) and reads the root `.env`. It uses a Redis that is already running, or starts one in Docker when the broker is the default local one. Docker must be running for that, and the first run downloads `redis:7-alpine`. A remote or password-protected broker must already be available. `DJANGO_CACHE` defaults to `redis://localhost:6379/3` if unset.

The script applies migrations and starts Django on port 8000, one Celery worker and Vite on port 5173. Open <http://localhost:5173>. All output shares the terminal, and if one service exits the others stop. Ctrl+C stops everything, including any Redis container it started; a Redis that was already running is left alone. Celery finishes its current job before stopping, so this can take a moment. Docker Redis data is kept in the `taurite-dev-redis` volume.

The script doesn't create accounts or set LLM credentials; those come from `.env`.

### Any OS: separate terminals

Start Redis (the default broker is `redis://localhost:6379/0`, or set `CELERY_BROKER_URL`):

```bash
docker run --name taurite-redis -p 127.0.0.1:6379:6379 -d redis:7-alpine
```

Then, from `backend/` with the virtual environment active, start the worker:

```bash
# Linux/macOS
celery -A config worker --loglevel=info --concurrency=1
```

```bash
# Windows
celery -A config worker --loglevel=info --pool=solo
```

Run Django and the frontend in their own terminals as usual (see the [quickstart](../quickstart/guide.md)). The worker needs the same database, broker and LLM settings as Django. It doesn't reload by itself, so restart it after changing task code. One worker process avoids write contention on the SQLite database. Celery Beat isn't used: every job is started by a user.

### Without a worker

Setting `CELERY_TASK_ALWAYS_EAGER=True` in `.env` runs jobs inside the web request instead of on a worker, so neither Redis as a broker nor the worker is needed. The request then waits for the model to finish. Django's cache still uses Redis through `DJANGO_CACHE`.

## Job lifecycle

1. The analyse endpoint (for example `POST /api/reporting/attendance/analyse/`) checks the report scope, saves a statistics snapshot with the requesting user, and returns HTTP 202 with `job_id` and `status`.
2. Django sends only the job ID to Redis.
3. The worker (`reporting/tasks.py`) claims the job, checks the requester's permissions again, calls the LLM and saves the explanation. A job delivered twice can't be claimed twice.
4. The page polls the job endpoint (for example `GET /api/reporting/attendance/jobs/<job_id>/`) until it succeeds or fails. Only the requester, if they still have access, can read the result.

| Report | Analyse endpoint | Task |
| --- | --- | --- |
| Attendance | `/api/reporting/attendance/analyse/` | `generate_attendance_analysis` |
| Physical testing | `/api/reporting/physical/analyse/` | `generate_physical_analysis` |
| ACC draft | `/api/reporting/acc/analyse/` | `generate_acc_analysis` |

If there is no data (for example no finalised sessions), the job completes straight away without calling the LLM. Statistics still load when Redis or the LLM is down. A broker failure returns 503, and a worker failure saves a safe error message. Pending jobs expire after 15 minutes when checked, and tasks have time limits. Tasks are never retried automatically, so a paid model call isn't repeated. Leaving the page stops polling but doesn't cancel the job.

Snapshots and explanations are stored in the database, not in the cache or a Celery result backend. Jobs are kept indefinitely, and a branch with saved jobs can't be deleted. A snapshot records the figures used for an explanation; it isn't an approved quarterly report.

See [physical-reporting.md](../features/physical-reporting.md) and [acc-reporting.md](../features/acc-reporting.md) for what each report sends to the model.

## How to check it

Sign in as a super admin or branch manager, open Reporting, choose a period with finalised attendance and click the AI analysis button. The page shows queued and running, then the explanation, and the worker terminal logs the finished task. Stop Redis and request again: you get a queue error, but the statistics still load.

The automated tests run a real Celery worker against an in-memory broker with a stubbed LLM, plus tests for permissions, failures, duplicate delivery and polling. They don't test a real Redis or a live model.
