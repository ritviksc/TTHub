# Help Chatbot Feature Plan (Role-scoped Docs + RAG)

## Context
There is no in-app help for users. Each role (Super Admin, Branch Manager, Instructor) gets a **Help page** with two parts:
1. Written documentation for that role.
2. A **help chatbot** that answers questions using only those docs. It is built with **RAG** (Retrieval-Augmented Generation) on the university's local LLM server.

What already exists and will be reused:
- The university's vLLM server is OpenAI-compatible and is already called by `backend/llm/services/client.py` (`get_client()`, `generate()`).
- `ONCAMPUS/BAAI/bge-m3` is already on that server and unused. It is an embedding model: it turns text into vectors.
- `/api/llm/` is mounted, but `backend/llm/views.py` and `urls.py` are empty stubs.
- The frontend already has:
  - role-based routing with `meta.roles` (`frontend/src/router/index.js`, `router/access.js`)
  - a per-role sidebar (`DashboardNav.vue`, `NAV_ITEMS`)
  - safe Markdown rendering (`MarkdownResponse.vue`, `utils/markdown.js`)
- The database is SQLite, with Redis as the Django cache.

---

## How RAG works (plain explanation)

An LLM only knows what it was trained on, plus whatever you put in the prompt. It knows nothing about our app. RAG fixes this by **finding the relevant parts of our docs and pasting them into the prompt** before the model answers.

The key idea is the **embedding**. An embedding model (bge-m3) turns any piece of text into a list of 1024 numbers (a vector). Texts that *mean* similar things get vectors that point in similar directions, even with no shared words. For example, "how do I add a new kaumātua" and "registering a participant" end up close together. Closeness is measured with **cosine similarity**: 1.0 means the same meaning, around 0 means unrelated.

RAG has two phases:

### Phase 1: Indexing (offline, once per docs change)
```
docs/*.md ──► split into chunks ──► bge-m3 embeds each chunk ──► store (chunk text + vector + roles)
```
- The docs are embedded **once**, not on every question. Your assumption is right.
- The stored result is the "vector database". At our scale (tens of docs, a few hundred chunks) this is just a **SQLite table** where each row is a chunk plus its vector. We don't need pgvector, FAISS or Chroma: 300 × 1024 floats is about 1.2 MB, which fits easily in memory.
- When the docs change, re-run the index command. It can skip chunks whose text hash hasn't changed.

### Phase 2: Querying (online, every question)
```
question ──► bge-m3 embeds the question (1 fast call)
         ──► keep only chunks the user's role may see
         ──► cosine-similarity against those chunk vectors (numpy dot product, < 1 ms)
         ──► take top 5 chunks (drop any below a score threshold)
         ──► build prompt: system rules + those chunks + chat history + question
         ──► LLM (Qwen) writes the answer, citing which chunks it used
         ──► return answer + source links
```
- Each question costs **one embedding call** (milliseconds) and **one LLM call** (a few seconds).
- If no chunk scores above the threshold, the bot says it doesn't know instead of guessing. This is the main defence against made-up answers.

Why not paste all the docs into every prompt? It works while the docs are small. RAG keeps prompts small and fast as the docs grow, and gives exact citations.

---

## Code flow / pipeline

### Content: `backend/help/content/*.md`
One topic per file, with front-matter:
```markdown
---
title: Generating an attendance report
roles: [super_admin, branch_manager]
order: 20
---
## Choosing a date range
...
## Picking a model
...
```
The same files feed both the docs pages and the RAG index, so there is one source of truth.

### Indexing: `python manage.py build_help_index`
`backend/help/management/commands/build_help_index.py` runs these steps:
1. **Load.** `services/docs.py: load_docs()` parses the front-matter and body of every `.md` file.
2. **Chunk.** `services/chunking.py: chunk_doc(doc)` splits on `##` headings. Long sections are split again into pieces of about 300–500 tokens with a small overlap. Each chunk keeps `slug`, `title`, `heading`, `text` and `roles`. The doc title and heading go at the front of the text, so the chunk makes sense on its own.
3. **Embed.** `services/embeddings.py: embed(texts)` sends batches of chunks to `get_client().embeddings.create(model=HELP_EMBED_MODEL, input=[...])`. Each vector is L2-normalised, so cosine similarity becomes a plain dot product.
4. **Store.** In one transaction, the `HelpChunk` table is replaced. Fields: `slug`, `title`, `heading`, `text`, `roles` (JSON), `content_hash`, `embedding` (BinaryField storing float32 bytes) and `model`.
5. **Bust the cache.** The in-memory index is cleared.

### Retrieval: `backend/help/services/retrieval.py`
- `_index()` loads every `HelpChunk` row once into a numpy matrix `(N, 1024)` plus a metadata list, and caches it in-process. It reloads when the index version (the latest `HelpChunk` timestamp) changes.
- `retrieve(role, question, k=5, min_score=~0.45) -> list[Chunk]`:
  1. Mask to the rows where `role in roles`. This happens **before** scoring, so other roles' content is never even a candidate.
  2. Embed and normalise the question.
  3. `scores = M[mask] @ q`, then `argsort`, then top-k above `min_score`.
- The `min_score` threshold is tuned by hand with a few real questions.

### Answering: `backend/help/services/chat.py: answer(user, question, history)`
1. `chunks = retrieve(user.role, question)`.
2. If `chunks` is empty, return the fixed "I couldn't find that in the help docs; contact your branch manager / admin" message **without calling the LLM**.
3. Build the messages:
   - **system** (`backend/help/prompts.py`): you are the help assistant for {role}; answer ONLY from the context; if the context doesn't cover it, say so; never invent features; cite sources as [slug].
   - **system/context:** the numbered chunks, each `[slug] Title › Heading\n text`.
   - The last ≤6 history turns, then the user's question.
4. Call the LLM with a new `chat(messages, model, max_tokens=500, temperature=0.1)` in `backend/llm/services/client.py`. It sits next to the existing `generate()` and has the same error handling. For Qwen3, turn thinking off with `extra_body={"chat_template_kwargs": {"enable_thinking": False}}` (check this on the server) so answers come back fast.
5. Return `{answer, sources: [{slug, title}]}`. The sources come from the retrieved chunks the answer actually cited, or else from all retrieved chunks.

### API: `backend/help/urls.py`, mounted at `/api/help/` in `backend/config/urls.py`
All endpoints use `IsAuthenticated`. The role always comes from `request.user.role`, never from the client.
- `GET  /api/help/articles/` returns `[{slug, title, order}]` filtered by role.
- `GET  /api/help/articles/<slug>/` returns the article Markdown, or 404 if the role isn't allowed.
- `POST /api/help/chat/` takes `{question (≤500 chars), history (≤6 turns)}` and returns `{answer, sources}`.
  - Calls are synchronous, without Celery: answers are short and the client timeout is 200s.
  - DRF `ScopedRateThrottle` (`help_chat`: about 20 per 10 min per user) uses the existing Redis cache.

### Frontend
- Routes `/super-admin/help`, `/branch-manager/help` and `/instructor/help` all load one shared `views/Help.vue`, each with its `meta.roles`. This is the same pattern as `Documents.vue`.
- A "Help" item is added to each role's list in `DashboardNav.vue` `NAV_ITEMS`.
- `Help.vue` contains:
  - an article sidebar with a title filter
  - the article body rendered with `MarkdownResponse.vue`
  - `components/help/HelpChat.vue`, which shows the messages, a "Sources" chip list that opens the cited article, a loading state, and error handling
- Possible later improvement: stream the answer as it is written (`stream=True` + `StreamingHttpResponse`).

### Config: `backend/config/settings.py` and `backend/.env_skeleton`
- `HELP_LLM_MODEL`, which defaults to `DEFAULT_LLM_MODEL`.
- `HELP_EMBED_MODEL=ONCAMPUS/BAAI/bge-m3`.
- `help` is added to `INSTALLED_APPS`.
- `numpy` goes in `backend/requirements.txt` if it isn't already pulled in.

### Safety
- The bot sees **only help docs**: no participant data and no DB queries. This avoids leaking medical or personal data.
- Role filtering happens on the server, before retrieval.
- Output is rendered through the existing HTML-escaping Markdown renderer.
- Rate limiting and input length caps apply to the chat endpoint.

---

## Files
- **New:**
  - `backend/help/`: `models.py` (`HelpChunk`), `content/*.md`, `services/{docs,chunking,embeddings,retrieval,chat}.py`, `prompts.py`, `views.py`, `urls.py`, `management/commands/build_help_index.py`, `tests.py`
  - `frontend/src/views/Help.vue`
  - `frontend/src/components/help/HelpChat.vue`
  - `Documentation/system/backend-component/backend/help-chatbot.md`
  - `chat-bot-feature-plan.md` (this plan)
- **Modified:**
  - `backend/config/settings.py`
  - `backend/config/urls.py`
  - `backend/llm/services/client.py` (adds `chat()`)
  - `backend/requirements.txt`
  - `backend/.env_skeleton`
  - `frontend/src/router/index.js`
  - `frontend/src/components/DashboardNav.vue`

## Suggested build order
1. Content format plus `load_docs()`, the articles API and `Help.vue` docs view. This gives working docs with no AI.
2. The `HelpChunk` model, chunking, embeddings and `build_help_index`.
3. `retrieve()` and `answer()`, the chat endpoint and `HelpChat.vue`.
4. Write the real help content for each role, then tune the chunk size, `k` and `min_score`.

## Verification
- **Backend tests** (`backend/help/tests.py`, with embeddings and the LLM mocked via `unittest.mock`, as in `reporting/test_model_selection.py`):
  - Chunking splits on headings and keeps the roles.
  - `retrieve()` never returns chunks for other roles and ranks the closest vector first. Use fake vectors to test this.
  - Below the threshold, the "don't know" message comes back and the LLM is not called.
  - The article list and detail endpoints are scoped by role (another role's article returns 404).
  - Unauthenticated requests are rejected, and the throttle triggers.
- **Frontend:** `node --test tests/*.test.js`, with a router-access test for the help routes.
- **Manual:**
  1. Connect to the VPN and run `python manage.py build_help_index`, then `scripts/dev.sh`.
  2. As each role, check that the sidebar link appears and the articles are scoped.
  3. Ask an in-scope question; it should return an answer with correct sources.
  4. Ask an off-topic question; the bot should decline.
  5. Ask about another role's feature; the bot should not explain it.
