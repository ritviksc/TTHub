# Help page and chatbot

Every role has a **Help** item in the nav (`/help`). The page is two equal halves:

- **Left: documentation.** A file-explorer tree (role folder › section › article). Opening an article switches the panel to a reader with a breadcrumb, **← All articles**, and Previous/Next within the section.
- **Right: the help assistant.** A chatbot that answers using only the articles this user can read. Answers stream in as they are written. It is built with retrieval-augmented generation (RAG) on the university vLLM server.

```
article Markdown --> chunks --> bge-m3 vectors (HelpChunk table)              [once, per docs change]
question --> bge-m3 vector --> closest chunks this role may read --> streamed LLM answer with [slug] citations
```

## Who reads what

Articles live in `backend/help/content/<audience>/`. The folder decides who may read them, both on the page and in the chatbot:

| Folder | Label | Readers |
| --- | --- | --- |
| `general/` | General | everyone |
| `kaimahi/` | Kaimahi | kaimahi, branch managers, super admins |
| `branch-manager/` | Branch Manager | branch managers, super admins |
| `super-admin/` | Super Admin | super admins |

Branch managers and super admins can read the docs for the roles they support. Every folder in the explorer starts collapsed; users open the ones they need, and searching opens the ones with matches. `AUDIENCES` in `help/services/docs.py` defines who reads what.

## Writing help articles

One Markdown file per topic. The file name is the slug and must be unique across all folders. By convention, prefix role articles: `kaimahi-`, `bm-`, `sa-`. Each file starts with front-matter:

```markdown
---
title: Recording feedback
section: Feedback
order: 50
---
## A section heading
...
```

- `section` groups articles into folders inside the role folder. Sections appear in order of their first article's `order`.
- Unknown keys, a missing title or section, a file outside an audience folder, an unknown folder, or a duplicate slug all make loading fail loudly.
- Split articles with `##` headings. Each section becomes a chunk prefixed with "Audience › Title › Heading", so write each section so it makes sense on its own. The audience prefix lets the bot say which role does a task ("only kaimahi take attendance").
- Use the app's words (kaumātua, kapa, kaimahi). `general/terminology.md` maps them to participant, branch and instructor.
- Check every label against the real screen. The current articles were written from the Vue templates and backend permission rules (October 2026).

Articles appear on the page as soon as they are saved. **The chatbot only sees them after rebuilding the index:**

```
python manage.py build_help_index
```

This needs the LLM provider (university VPN off campus). Only article text is sent. Unchanged chunks reuse their stored vector.

## How an answer is produced

1. `retrieve()` (`help/services/retrieval.py`) keeps only chunks this role may read, **before** scoring, then ranks them by cosine similarity to the question. The index is held in memory and reloads when the table changes.
2. Chunks below `HELP_MIN_SCORE` are dropped. If none are left, a fixed "couldn't find that in the help docs" reply is streamed **without calling the LLM**.
3. `start_answer()` (`help/services/chat.py`) builds the system rules (`help/prompts.py`), the chunks, up to six earlier turns and the question. It then opens a streamed request with `llm.services.client.chat_stream()`. Qwen models get `enable_thinking: False`.
4. The view returns the answer as **NDJSON** (one JSON object per line):
   - `{"type":"delta","text":"…"}`: the next piece of the answer
   - `{"type":"done","sources":[{"slug","title"}]}`: the end. Sources are the retrieved articles the answer cited; a refusal cites nothing, so it gets no sources.
   - `{"type":"error","detail":"…"}`: the end, if generation failed part-way (e.g. hit the token limit)

Retrieval and opening the provider stream happen before the response starts. Their failures still return a normal 503 JSON response. If the reader stops (the Stop button closes the connection), the upstream stream is closed too.

The bot never sees participant data or queries the database. The role always comes from the session. Help questions are not written to the audit log (`audit/middleware.py` skips `api/help/chat/`), because they change no records.

## API (`/api/help/`, any signed-in staff role)

| Endpoint | Purpose |
| --- | --- |
| `GET articles/` | `[{slug, title, section, order, audience, audience_label}]` the user may read, in explorer order |
| `GET articles/<slug>/` | `{slug, title, section, audience, audience_label, body}`, or 404 when missing or not readable |
| `POST chat/` | `{question (≤500 chars), history: [{role: user\|assistant, content}]}`. Streams NDJSON as above; only the last 6 history turns are used. |

`chat/` is throttled at `help_chat: 20/hour` per user (Redis cache). If the cache is unavailable, the request is allowed and a warning logged.

## Configuration

| Setting | Default | Purpose |
| --- | --- | --- |
| `HELP_LLM_MODEL` | `DEFAULT_LLM_MODEL` | Chat model that writes answers |
| `HELP_EMBED_MODEL` | `ONCAMPUS/BAAI/bge-m3` | Embedding model. Changing it needs `build_help_index`. |
| `HELP_MIN_SCORE` | `0.40` | Similarity cut-off. With the 32-article set, off-topic questions scored ≤0.32 and real questions ≥0.48. Retune after big content changes. |

## Frontend

| File | Purpose |
| --- | --- |
| `src/views/Help.vue` | Two equal, window-height halves (stacked below 900px). The open article lives in `?article=`. |
| `src/components/help/HelpExplorer.vue` | Search, tree, and reader mode (breadcrumb, back, Previous/Next) |
| `src/components/help/HelpTree.vue` | Folder/article tree, drawn as flat rows like `documents/FolderTree.vue` |
| `src/components/help/HelpChat.vue` | Chat. Typing dots, then streamed text with a caret; Stop, New chat, Copy, Retry, times, source chips; follows new text unless scrolled up ("Jump to latest"); auto-growing input. |
| `src/utils/help.js` | Pure helpers: tree building, search rows, siblings, citation stripping (including a half-written `[slug` while streaming), NDJSON parsing, history, error messages |
| `src/apis.js` | `listHelpArticles`, `getHelpArticle`, and `streamHelp()`. `streamHelp()` uses `fetch` (axios can't read a response while it is arriving), with the CSRF cookie, never retried. The chat aborts after 200 s without any new data. |

## Tests

- Backend: `python manage.py test help llm audit`. The LLM and embeddings are mocked. Covers audience visibility and loader validation, chunk labels, role filtering before ranking, streamed events and sources, the no-LLM refusal, part-way failure, `chat_stream`, API scoping, input limits, throttling, cache outage, 503 before streaming, the audit skip, and index reuse.
- Frontend: `node --test tests/help.test.js` (tree, search, siblings, NDJSON, citation stripping, history, route access).
- Manual: build the index, sign in as each role. Check the folders shown, search, reader and Previous/Next. Ask an in-scope question (streams, cited), an off-topic one (declines), and another role's task (names the right role). Also check Stop mid-answer and the mobile layout.
