# Using AI coding assistants on this project

You can use whichever AI coding assistant you like (Claude Code, Copilot, Cursor, Codex and so on). This guide explains how to use one without creating extra work for everyone else. The short version is that the AI writes code for you, but you're still the one responsible for it.

Related files:

- [frontend-conventions.md](../frontend/frontend-conventions.md) covers how frontend code in this repo should look.
- [ai-agent-rules.md](ai-agent-rules.md) is the rules file you give your AI at the start of every session.
- [frontend-issues.md](../frontend/frontend-issues.md) is the list of work to pick from.

## The ground rules

1. Run your AI inside this repo, never in a separate copy of the project.
2. Don't open a pull request for code you can't explain line by line.
3. Follow [frontend-conventions.md](../frontend/frontend-conventions.md).
4. One issue gets one branch and one pull request. Nothing goes into `master` without someone else reviewing it.
5. Keep changes small. A pull request that touches 3 files gets a proper review. One that touches 30 doesn't.

## Why you can't work in a copy of the repo

If you run the AI in a separate project and paste folders across afterwards, the AI never sees `apis.js`, `dashboard.css`, `router/index.js`, `utils/` or the existing components. So it invents its own versions of all of them. What you end up pasting in:

- makes its own axios calls and URLs instead of using `apis.js`
- ships its own CSS instead of using the shared classes and theme variables
- skips the router, so every role's dashboard ends up in one huge file switching between views
- duplicates helpers that already exist

Someone then has to take it apart and rebuild it the proper way, which takes longer than writing it from scratch. Working in the real repo avoids all of this, because the AI can read the existing code and reuse it.

## One-time setup

```bash
git clone https://isgb.otago.ac.nz/cosc345/git/dunja131/Group_4.git
cd Group_4

# frontend
cd frontend
npm install
npm run dev
```

For the backend, follow the root [README.md](../../README.md) and [venv-setup.md](../backend/venv-setup.md), then load test data with [seed_test_data.md](../backend/seed_test_data.md). The seed command creates branch manager and instructor logins. It doesn't create a super admin, so make one using the steps in the README.

Always open your AI tool from the repo root (the `Group_4` folder), not from inside `frontend/` and not from a different project.

## The workflow, step by step

### 1. Pick an issue and understand it yourself

Choose an issue from GitBucket or [frontend-issues.md](../frontend/frontend-issues.md) and assign it to yourself. Read it, open the prototype image if it has one, and open the existing pages it mentions.

Before you prompt anything, you should be able to say in two sentences what's going to change and which files are involved. If you can't, keep reading the code or ask in the group chat.

### 2. Make a branch

```bash
git checkout master
git pull
git checkout -b feature/sa-participants-branch-filter
```

Branch off `master` unless the team is working from a sprint branch (like `sprint-2-frontend`). If you're not sure which, ask.

### 3. Ask for a plan before any code

Start a new AI session and send something like:

```
Read docs/ai-assisted-coding/ai-agent-rules.md and docs/frontend/frontend-conventions.md.
Then read frontend/src/views/SuperAdmin/Participants.vue and frontend/src/apis.js.

Don't edit anything yet. I want to add a branch filter to the super admin
Participants page. Tell me which files you would change, what you would change
in each one, and which existing functions and CSS classes you would reuse.
```

Many tools also have a plan mode that does this. Read the plan properly. Push back if it:

- creates files you weren't expecting
- copies code from another page instead of reusing it
- changes files that have nothing to do with the issue
- invents a new API call when `apis.js` already has one

### 4. Give it a precise task prompt

Once the plan looks right, give the actual task. A good prompt says what to build, which files it may touch, what to reuse, and how you'll know it's done. Use this template:

```
Read docs/ai-assisted-coding/ai-agent-rules.md and docs/frontend/frontend-conventions.md before doing anything.

Task: <one or two sentences on what the feature does, from the user's point of view>

Context:
- Issue: <paste the issue title and description>
- Prototype: <path to the prototype image, if there is one>
- Similar working code to follow: <a page that already does something like this>

You may only edit these files:
- <file>
- <file>
You may create these new files: <list them, or say "none">
If you think any other file needs changing, stop and ask me first.

Reuse:
- backend calls from frontend/src/apis.js (add a function there if one is missing)
- classes from frontend/src/assets/dashboard.css and variables from theme.css
- helpers from frontend/src/utils/

Done means:
- <something you can see or click in the browser>
- <another one>
- npm run build in frontend/ finishes with no errors
- nothing else on the page has changed

When you're finished, list every file you changed with a short explanation of
each change, and tell me exactly how to test it by hand.
```

#### A bad prompt

```
make the participants page for branch manager like the prototype
```

This gives the AI nothing to go on. It doesn't know which files it's allowed to touch, what already exists, what "done" means or how to test it. It will probably produce one big new file with its own styles and API calls, which is exactly what we're trying to avoid.

#### A good prompt

```
Read docs/ai-assisted-coding/ai-agent-rules.md and docs/frontend/frontend-conventions.md before doing anything.

Task: On the super admin Participants page, add a dropdown that filters the
list to a single branch.

Context:
- Issue: "Super admin Participants page: branch filter, photos and links to
  the detail page". Only do the branch filter part for now.
- Similar working code: the Active/Inactive pills and the search box on the same
  page already filter the list in the visibleParticipants computed property.

You may only edit these files:
- frontend/src/views/SuperAdmin/Participants.vue
You may create these new files: none.
If you think any other file needs changing, stop and ask me first.

Reuse:
- listBranches() from apis.js to fill the dropdown. The page already calls it
  when the Add participant modal opens.
- the form-group class from dashboard.css for the dropdown
- the existing visibleParticipants computed for the filtering

Done means:
- the dropdown shows "All branches" first, then every branch by name
- choosing a branch shows only that branch's participants
- the search box and Active/Inactive pills still work together with the dropdown
- the "X of Y participants" count updates correctly
- npm run build in frontend/ finishes with no errors

When you're finished, list every file you changed with a short explanation of
each change, and tell me exactly how to test it by hand.
```

### 5. Read every line of the diff

```bash
git status
git diff
```

Go through this list:

- Only the files you allowed have changed.
- There are no new axios imports or hardcoded URLs.
- There are no hex colours, inline styles or new CSS files.
- Nothing has been copied from another view.
- The comments explain why, not what, and there's at least one where the code isn't obvious.
- There's no leftover `console.log`, dummy data or commented-out code.
- `package.json` and `package-lock.json` haven't changed unless you meant them to.
- You can explain every line.

If there's a part you don't understand, ask the AI to explain it line by line. If you still don't get it, ask the AI to rewrite it more simply, or write that part yourself. "The AI wrote it" isn't an answer in code review.

If the AI went off in the wrong direction, throw the changes away and start again with a tighter prompt instead of patching on top of them:

```bash
git restore .          # discards changes to tracked files
git clean -n           # shows new untracked files; use -f to delete them
```

### 6. Test it yourself

There are no automated frontend tests yet, so testing is manual. Do all of this every time:

1. Run `npm run build` in `frontend/` and make sure it passes.
2. Start the backend and the frontend (`npm run dev`).
3. Log in as every role the change affects. The seeded logins are in [seed_test_data.md](../backend/seed_test_data.md).
4. Check each item from "Done means" in your prompt.
5. Check the other states too: what the page looks like while loading, with no data, and when the backend is stopped (this is how you see the error state).
6. Open the browser dev tools console and make sure there are no red errors.
7. Click around the rest of the page and anything nearby to check nothing else broke.

### 7. Commit, push and open a pull request

Commit messages follow the same style as the existing history, `type(scope): short summary`:

```bash
git add frontend/src/views/SuperAdmin/Participants.vue
git commit -m "feat(frontend): add branch filter to super admin participants page"
git push -u origin feature/sa-participants-branch-filter
```

The types we use are `feat` for new features, `fix` for bug fixes and `docs` for documentation. Add files by name instead of running `git add .` so nothing unexpected gets committed.

Then open the repo on GitBucket, go to Pull requests, and create a new pull request. Set the base to `master` (or the sprint branch) and compare it with your branch. Use this description:

```
What this does:
<one or two sentences>

Issue:
<issue number and title>

Files changed:
<list, with one line on each>

How I tested:
<which logins, which pages, what you clicked>

Screenshots:
<before and after, for anything visual>

Where AI helped:
<which parts the AI wrote, and anything you rewrote yourself>

Anything I'm unsure about:
<questions for the reviewer>
```

Don't merge your own pull request. Wait for Jack or another dev to review it. If they ask for changes, make them on the same branch and push again, and the pull request updates on its own.

## When things go wrong

- If the AI wants to rewrite a whole file or change lots of files, say no and remind it which files it's allowed to edit.
- If it still doesn't work after two or three tries, stop prompting. Discard the changes, reread the code yourself, and write a smaller prompt, or split the task in two.
- If you're stuck, push your branch and ask in the group chat. Link the branch and say what you tried. It's much faster for someone to help early than to untangle it at review time.
