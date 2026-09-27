# Rules for AI coding agents

This file is for the AI coding assistant, not for people. Developers should tell their agent to read it at the start of every session.

You are working in the Taurite Tū repo. The frontend is Vue 3 with Vite in `frontend/`, and the backend is Django in `backend/`. Follow these rules on every task. Before writing any frontend code, also read `docs/frontend/frontend-conventions.md` and follow it.

## Scope

- Only edit the files the developer listed. If you think another file needs to change, stop and ask first.
- Don't reformat, rename or tidy up code that isn't part of the task.
- Don't add npm or pip packages without asking.
- Never create a new project, a copy of the repo, or duplicate folders. All work happens in this repo.
- Don't commit, push or merge unless the developer asks. Never push to `master`.

## Before writing code

- Read every file you're going to change, and at least one working page that does something similar.
- Check `frontend/src/apis.js`, `frontend/src/utils/`, `frontend/src/components/` and `frontend/src/assets/dashboard.css` for code you can reuse.
- If the task is unclear, or it conflicts with `docs/frontend/frontend-conventions.md`, ask instead of guessing.
- For anything bigger than a small change, reply with a plan first: which files you'll change and what you'll change in each one. Wait for the developer to approve it.

## While writing code

- One view file is one page for one role. Never render several roles' dashboards in the same file.
- If more than one role needs the same UI, build a component with props. Don't copy the view.
- Send all backend requests through functions in `apis.js`. Use `withRetry` for GET requests.
- Use `dashboard.css` classes and `theme.css` variables. Use scoped styles only for page-specific styling. No hex codes and no inline styles.
- Register new pages in `frontend/src/router/index.js` with the correct `roles`.
- Handle loading, error and empty states.
- Comment the non-obvious parts, explaining why rather than what, as described in the conventions file.
- Don't add placeholder or dummy data unless the developer asks for it. If they do, mark it with a `// TEMPORARY:` comment that says what should replace it.

## When you finish

1. Run `npm run build` in `frontend/` and report whether it passed.
2. List every file you changed, with one or two sentences on what changed and why.
3. Give the developer step-by-step instructions for testing it by hand: which account to log in with, which page to open and what to click.
4. Point out anything you weren't sure about or couldn't check.

The developer has to be able to explain this code in code review. Keep your explanations simple, and if you used a pattern they might not know, explain it briefly.
