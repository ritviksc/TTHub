# LLM Reporting/Analysing

The subsystem will be responsible for analysing data and using a LLM model
to explain trends/statisics and present them.

```
report scope --> retrieve authorised data --> calculate verified statistics --> ask the model to explain them --> validate the response --> present the report.
```

## Planned capabilities

##### Dashboard trends 

Attendance, sessions delivered, and participation over time. The backend can calculate these and display charts directly; an LLM could optionally explain the trends.

##### Formal reports

Privileged users select a period and scope, then generate a report using verified statistics and an AI-assisted narrative.

##### Physical outcomes

Measurements collected over time, which could eventually support reporting on participant progress.

##### Participant wellbeing and experience reports

Kaumātua fill out surveys which the llm uses to summarise the feedback and authorised staff can see the findings and take appropriate decesions

### Areas of reporting

```
Area	What we might want to understand	Current system
Participation	Are people attending regularly?	Sessions and attendance exist
Physical function	Are participants’ strength, balance, or mobility changing?	Assessment records are missing
Participant experience	Do people report connection, confidence, and wellbeing?	Needs agreed questions and a collection process
```

## Current implementation

The provider client and model-list caching task are implemented. The reporting
flow above is the intended design: report endpoints, data aggregation, surveys,
and report presentation are not implemented in the LLM app yet.

### Provider client

[`backend/llm/services/client.py`](../../../backend/llm/services/client.py) handles
communication with an OpenAI-compatible provider.

- `get_client()` creates the SDK client on first use and reuses it within the
  process. It checks that `LLM_API_ENDPOINT` and `OPENAI_API_KEY` are configured
  before construction, raising `ImproperlyConfigured` if either is missing.
- The client uses a 30-second network timeout and permits two SDK retries for
  retryable failures. This timeout is not a total deadline including retries.
- `generate()` accepts a client, a user prompt, and a system prompt. The caller
  owns the instructions; the provider client does not prescribe a report type.
- An explicit model takes precedence over `DEFAULT_LLM_MODEL`. If no usable
  model name is supplied or configured, generation raises `ImproperlyConfigured`.
- Generation defaults to 100 output tokens and temperature 0.2; callers can
  override both values.
- The current code rejects missing response choices, finish reasons other than
  `stop` (including token-limit truncation), and empty or whitespace-only text
  with `ValueError`. These checks do not verify factual accuracy.
- Provider exceptions propagate to the caller rather than being converted to
  `None`. A future view or task must decide how to present or handle failures.
- `get_available_models()` fetches model identifiers from the provider. It does
  not read the cache and does not require a default generation model.

Passing a client into `generate()` lets tests supply a fake provider without
network access. This is dependency injection: the caller supplies a dependency
instead of the function constructing it internally.

### Model-list cache task

[`backend/llm/tasks.py`](../../../backend/llm/tasks.py) defines `get_models()`:

```text
Task executes --> fetch model identifiers --> store list in Django cache
```

The cache key is `llm:models`. The list is stored directly using `timeout=None`,
so it has no automatic expiry. This is a cache, not durable storage: Redis
eviction, clearing, or loss of stored data can still remove the entry.

If fetching fails, execution stops before the cache write, preserving any
previous value. A successful empty list replaces the old list. Without expiry,
the last successful result can remain stale until another successful refresh.

Redis has two separate responsibilities in this project:

| Configuration | Responsibility |
| --- | --- |
| `CELERY_BROKER_URL` | Queue tasks for Celery workers |
| `DJANGO_CACHE` | Configure Django's Redis cache for stored values |

The `@shared_task` decorator registers the task; it does not schedule it.
No startup trigger or periodic refresh schedule is currently configured.
Calling `get_models.delay()` queues it for a worker; `get_models.run()` executes
the body directly, as used in tests. No task-level automatic retries are configured.

### Verification

[`backend/llm/tests.py`](../../../backend/llm/tests.py) currently tests:

1. Missing model configuration fails before a provider request is made.
2. An explicit model and request arguments reach the provider, and returned text
   reaches the caller.
3. A failed model-list fetch propagates its error and preserves cached models.

Run from `backend/` with the project's virtual environment activated:

```bash
python manage.py test llm
```

All three tests passed during this review. They use mocks and an in-memory cache;
they do not verify live provider connectivity, Redis, or Celery worker execution.
Client initialisation, successful cache refresh, and response rejection paths
still need dedicated tests.
