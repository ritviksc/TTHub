# Help chatbot setup

How to get the Help page (`/help`) and its chatbot working on a development machine. Do the [quickstart](../quickstart/guide.md) first, so that Django, Redis and the frontend already run.

The article list works without any of this. The chatbot only answers once its index is built.

## 1. Check `.env`

These values in the repo-root `.env` are required (ask the team for them):

```ini
LLM_API_ENDPOINT=
OPENAI_API_KEY=
DEFAULT_LLM_MODEL=
```

These are optional and can usually stay unset:

| Setting | Default | Change it when |
| --- | --- | --- |
| `HELP_LLM_MODEL` | `DEFAULT_LLM_MODEL` | You want the chatbot on a different chat model from reports. |
| `HELP_EMBED_MODEL` | `ONCAMPUS/BAAI/bge-m3` | Rarely. Rebuild the index after changing it. |
| `HELP_MIN_SCORE` | `0.40` | Real questions get "couldn't find that" (lower it) or off-topic ones get answered (raise it). |

## 2. Connect to the LLM server

Off campus, connect to the university VPN. Both building the index and answering questions call the LLM server.

## 3. Build the index

With the virtual environment active, from `backend/`:

```bash
python manage.py migrate
python manage.py build_help_index
```

When it works, it prints a line like `Indexed N chunks from M articles (N embedded, 0 reused).`

## 4. Run it and check it works

Start the system as usual, then:

1. Sign in with any account and open **Help** in the nav.
2. Ask a question that one of the articles answers, such as "How do I take attendance?". The answer should stream in and list its sources.
3. Ask something off-topic, such as "What's the weather?". It should say it couldn't find that in the help docs.

The chatbot's requests go straight to Django, so the Celery worker doesn't need to be running.

## Adding or editing articles

Articles are Markdown files in `backend/help/content/`. The folder an article sits in decides who can read it:

| Folder | Readers |
| --- | --- |
| `general/` | Everyone |
| `kaimahi/` | Kaimahi, branch managers, super admins |
| `branch-manager/` | Branch managers, super admins |
| `super-admin/` | Super admins |

Each file needs front-matter, and the file name (its slug) must be unique across all folders:

```markdown
---
title: Recording feedback
section: Feedback
order: 50
---
## A section heading
...
```

Edits show on the Help page straight away. **Run `python manage.py build_help_index` again before the chatbot can see them.** It only re-embeds the parts that changed.

If an article has a missing title or section, an unknown key, a duplicate slug or a wrong folder, loading fails with an error that names the file.

## Tests

```bash
# from backend/
python manage.py test help llm audit
```

```bash
# from frontend/
node --test tests/help.test.js
```

The LLM is mocked in these tests, so they don't need the VPN.

## Troubleshooting

| Problem | Fix |
| --- | --- |
| `build_help_index` times out or fails to connect | Connect to the VPN and check `LLM_API_ENDPOINT` and `OPENAI_API_KEY`. |
| Every question gets "couldn't find that in the help docs" | The index is empty or out of date. Run `build_help_index`. |
| A new or edited article is never used in answers | Run `build_help_index` again. |
| The chat returns a 503 error | The LLM server can't be reached. Check the VPN and `.env`. |
| "Too many requests" after many questions | The chat allows 20 questions per user per hour. Wait, or clear the cache with `docker restart taurite-redis`. |
| Questions go through but the 20-an-hour limit is ignored, with a cache warning in the logs | Redis isn't running. Start it with `docker start taurite-redis`. |
