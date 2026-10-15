# LLM integration

The `llm` app connects the system to an OpenAI-compatible model server (the university vLLM server). It is used for three things:

- **Report explanations**: attendance, physical-testing and ACC report drafts. Django calculates the statistics, and the model only explains the figures it is given.
- **Help chatbot**: answers questions from the help articles. See [help-chatbot.md](../setup/help-chatbot.md).
- **Model catalogue**: the list of models admins can choose from. See [report-model-selection.md](report-model-selection.md).

```
report scope --> authorised data --> verified statistics --> model explains them --> response validated --> report shown
```

Statistics never depend on the model. If the provider is down, every report still loads its figures and only the AI explanation fails.

## Configuration

Set in the repo-root `.env`:

| Setting | Purpose |
| --- | --- |
| `LLM_API_ENDPOINT` | Provider base URL. Required. |
| `OPENAI_API_KEY` | Provider key. Required. |
| `DEFAULT_LLM_MODEL` | Model used when the caller doesn't choose one. |
| `REPORT_LLM_MODELS` | Optional comma-separated list of models admins may choose for reports. |
| `HELP_LLM_MODEL`, `HELP_EMBED_MODEL`, `HELP_MIN_SCORE` | Help chatbot settings (see [help-chatbot.md](../setup/help-chatbot.md)). |

The provider is only reachable on the university network, so connect to the VPN when you're off campus.

## Provider client

[`backend/llm/services/client.py`](../../backend/llm/services/client.py)

| Function | What it does |
| --- | --- |
| `get_client()` | Creates the OpenAI SDK client on first use and reuses it. Raises `ImproperlyConfigured` if `LLM_API_ENDPOINT` or `OPENAI_API_KEY` is missing. It uses a 200-second timeout and no automatic retries, so a paid generation is never repeated. |
| `chat(client, messages, …)` | Sends a full message list and returns the reply text. Accepts `model`, `max_tokens`, `temperature` and provider-specific `extra_body`. |
| `generate(client, prompt, sys_prompt, …)` | The single-prompt form of `chat()`, used by the report services. |
| `chat_stream(client, messages, …)` | The streaming form of `chat()`, used by the help chatbot. It returns the text in pieces as the model writes them. |
| `get_available_models()` | Lists the provider's model IDs, with a 4-second timeout. |

The model passed in takes precedence over `DEFAULT_LLM_MODEL`. If neither is set, the call raises `ImproperlyConfigured`. The defaults are 100 output tokens and temperature 0.2, and each caller sets its own limits:

| Caller | Max tokens |
| --- | --- |
| Attendance explanation (`reporting/services/attendance.py`) | 1,000 |
| Physical-testing explanation (`reporting/services/physical.py`) | 1,200 |
| ACC report draft (`reporting/services/acc.py`) | 6,000 |

Responses are rejected with `ValueError` when there are no choices, when the reply was cut off at the token limit or didn't finish normally, or when the text is empty. These checks don't verify that the content is accurate. Provider errors are passed up to the caller. The report tasks save a safe failure message on the job, and the chatbot returns a 503 or an error event.

## Background jobs

Report explanations run as Celery tasks in [`backend/reporting/tasks.py`](../../backend/reporting/tasks.py): `generate_attendance_analysis`, `generate_physical_analysis` and `generate_acc_analysis`. Each one has a 240-second soft limit and a 270-second hard limit. See [celery-setup.md](../setup/celery-setup.md) for the job lifecycle.

[`backend/llm/tasks.py`](../../backend/llm/tasks.py) defines `get_models()`, which stores the provider's model list in the Django cache under `llm:models`. It is not scheduled. The model catalogue fetches and caches the list for five minutes when it needs one (see [report-model-selection.md](report-model-selection.md)).

Redis has two separate jobs:

| Setting | Job |
| --- | --- |
| `CELERY_BROKER_URL` | Queues tasks for the Celery worker |
| `DJANGO_CACHE` | Django's cache, which holds the model list and the help chat throttle |

## Tests

From `backend/`, with the virtual environment active:

```bash
python manage.py test llm
```

The tests use a fake provider and an in-memory cache. They check that a missing model fails before any request is sent, that the chosen model and prompts reach the provider, and that a failed model-list refresh keeps the previously cached list. The report and help tests (`reporting`, `help`) cover the callers.

## Key files

- `backend/llm/services/client.py`: provider client
- `backend/llm/services/catalog.py`: report model catalogue
- `backend/llm/tasks.py`: model-list cache task
- `backend/reporting/services/{attendance,physical,acc}.py` and `backend/reporting/prompts/`: report prompts and calls
- `backend/help/services/chat.py`: help chatbot calls
