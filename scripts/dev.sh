#!/usr/bin/env bash
# Development launcher for Linux: keep service lifetimes tied to this terminal.
set -Eeuo pipefail
PROJECT_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"
PYTHON="$PROJECT_ROOT/.venv/bin/python"
pids=()
redis_container=""

fail() { echo "Error: $*" >&2; exit 1; }
cleanup() {
    trap - EXIT INT TERM
    echo 'Stopping development services…'
    for pid in "${pids[@]}"; do kill -TERM -- "-$pid" 2>/dev/null || true; done
    # Give Celery time for a warm shutdown before stopping Redis.
    for pid in "${pids[@]}"; do wait "$pid" 2>/dev/null || true; done
    if [[ -n "$redis_container" ]]; then docker stop "$redis_container" >/dev/null || true; fi
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

[[ -x "$PYTHON" ]] || fail 'Create .venv and install backend/requirements.txt first.'
command -v npm >/dev/null || fail 'Install Node.js and npm first.'
command -v setsid >/dev/null || fail 'This script requires Linux setsid (util-linux).'
[[ -d frontend/node_modules ]] || fail 'Run npm ci in frontend first.'
"$PYTHON" -c 'import django, celery, redis, dotenv' || fail 'Install backend/requirements.txt into .venv first.'

# Read .env as configuration, never execute it as shell code or print credentials.
# Exit 2 means the unreachable broker can safely be supplied by local Docker Redis.
redis_check() {
    "$PYTHON" - <<'PY'
import os
from urllib.parse import urlsplit
from dotenv import load_dotenv
from redis import Redis
load_dotenv('.env')
url = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0')
try:
    Redis.from_url(url, socket_connect_timeout=1, socket_timeout=1).ping()
except Exception:
    parsed = urlsplit(url)
    local = (parsed.scheme == 'redis' and parsed.hostname in ('localhost', '127.0.0.1')
             and (parsed.port or 6379) == 6379 and not parsed.username and not parsed.password)
    raise SystemExit(2 if local else 1)
PY
}
if redis_check; then
    echo 'Using the existing Redis broker.'
else
    result=$?
    [[ "$result" == 2 ]] || fail 'Configured Redis broker is unavailable. Check CELERY_BROKER_URL and start that service.'
    command -v docker >/dev/null || fail 'Start Redis on localhost:6379 or install Docker.'
    docker info >/dev/null 2>&1 || fail 'Start Docker and ensure your account can access it.'
    echo 'Starting local Redis…'
    redis_container=$(docker run --rm -d -p 127.0.0.1:6379:6379 \
        -v taurite-dev-redis:/data redis:7-alpine redis-server --appendonly yes)
    ready=false
    for attempt in {1..20}; do
        if redis_check; then ready=true; break; fi
        sleep 0.5
    done
    [[ "$ready" == true ]] || fail 'Redis did not become ready.'
fi

# Existing .env values take precedence; supply only the missing local cache default.
if "$PYTHON" - <<'PY'
import os
from dotenv import load_dotenv
load_dotenv('.env')
raise SystemExit(0 if os.getenv('DJANGO_CACHE') else 1)
PY
then :; else export DJANGO_CACHE=redis://localhost:6379/3; fi
"$PYTHON" - <<'PY'
import os
from dotenv import load_dotenv
from redis import Redis
load_dotenv('.env')
try:
    Redis.from_url(os.environ['DJANGO_CACHE'], socket_connect_timeout=2, socket_timeout=2).ping()
except Exception:
    raise SystemExit('Django cache is unavailable. Check DJANGO_CACHE in .env.')
PY

cd "$PROJECT_ROOT/backend"
"$PYTHON" manage.py migrate --noinput
setsid "$PYTHON" manage.py runserver 127.0.0.1:8000 &
pids+=("$!")
setsid "$PYTHON" -m celery -A config worker --loglevel=info --concurrency=1 &
pids+=("$!")
cd "$PROJECT_ROOT/frontend"
setsid npm run dev -- --host localhost --port 5173 --strictPort &
pids+=("$!")
echo 'Starting services. Open http://localhost:5173 once Vite is ready. Press Ctrl+C to stop.'
# If any service exits, clean up the others instead of leaving a partial system running.
set +e
wait -n "${pids[@]}"
result=$?
set -e
echo 'A development service exited; shutting down the remaining services.' >&2
exit "$result"
