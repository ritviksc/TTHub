# Frontend conventions

These rules apply to all frontend code in this repo, whether you wrote it yourself or an AI assistant did. If you use an AI assistant, make it read this file before it writes anything (see [ai-assisted-coding.md](../ai-assisted-coding/ai-assisted-coding.md)). Pull requests that break these rules get sent back.

## Where things go

```
frontend/src/
  apis.js                  every call to the backend lives here
  router/index.js          every page's URL and which roles can open it
  stores/auth.js           who is logged in (auth.user)
  utils/                   plain JavaScript helpers with no Vue in them
  components/<feature>/    pieces used by more than one page, grouped by feature
  views/SuperAdmin/        one file per super admin page
  views/BranchManager/     one file per branch manager page
  views/Instructor/        one file per instructor page
  assets/theme.css         colours, font sizes, radii, shadows (design tokens)
  assets/dashboard.css     shared classes for every logged-in page
```

Before writing anything new, check whether it already exists in `apis.js`, `utils/`, `components/` or `dashboard.css`.

## One page per file, one role per page

A file in `views/` is one page at one URL for one role. Never put several roles' dashboards in a single file and switch between them with `v-if`. The router already decides who can see what.

If a page goes past about 300 lines, look for parts you can pull out into components, such as a modal, a table or a side panel. `views/Instructor/Sessions.vue` is a good example. Its create form lives in `components/sessions/CreateSessionModal.vue`, which keeps the page itself short and easy to read.

## Sharing code between roles

When two or more roles need the same UI, don't copy the file into each role's folder. Copies drift apart, and every bug then has to be fixed in three places.

Do this instead:

1. Move the shared part into `components/<feature>/`.
2. Use props for the parts that change between roles (which branch to show, whether the user can edit, whether to show a filter).
3. Keep each role's view file small. It should mostly set up props and render the component.

If you're about to copy more than about 20 lines from another view, stop and make a component.

Here's a sketch of what a role's page looks like when the list is shared. `ParticipantList` doesn't exist yet. It's only here to show the shape.

```vue
<!-- views/BranchManager/Participants.vue -->
<script setup>
import { auth } from '@/stores/auth.js'
import ParticipantList from '@/components/participants/ParticipantList.vue'
</script>

<template>
  <div class="dash-page">
    <main class="content">
      <div class="page-header">
        <h1>Participants</h1>
      </div>
      <ParticipantList :branch-id="auth.user.branch.id" :show-branch-filter="false" />
    </main>
  </div>
</template>
```

## Talking to the backend

All backend requests go through functions in `frontend/src/apis.js`.

- Don't import axios in a view or component, and don't write URLs in pages.
- If an endpoint has no function yet, add one to `apis.js` under the right section (`/* ---- participants ---- */` and so on). If its parameters aren't obvious, add a one-line comment above it, like the one on `listBranches`.
- Wrap read-only (GET) calls in `withRetry`, for example `await withRetry(null, listParticipants, { branch: id })`. Passing `null` uses the default of 3 attempts. Don't wrap POST calls, because retrying them can create duplicates.
- When a request fails, show the server's message if there is one and a friendly fallback if not:

```js
error.value = e.response?.data?.detail ?? 'Could not create this session.'
```

## Routes

- Add every page to `router/index.js` with `meta: { requiresAuth: true, roles: SA }` (or `BM` or `IN`).
- Load pages lazily: `component: () => import('@/views/SuperAdmin/Users.vue')`.
- Route names start with the role: `sa-`, `bm-` or `in-`.
- When you build a page that's currently a `comingSoon(...)` placeholder, replace that line with a real route and keep the same path and name, so nav links keep working.
- Link by route name, not by typing the path: `{ name: 'in-session-detail', params: { id } }`.

## Styling

- Wrap every logged-in page in `<div class="dash-page"><main class="content">`.
- Use the classes in `dashboard.css` first: `page-header`, `page-subtitle`, `btn-primary`, `btn-cancel`, `pills`/`pill`, `data-table`, `status-badge`, `card`/`card-grid`, `modal-backdrop`/`modal`, `form-group`, `form-row`, `form-error`, `stat-grid`/`stat-tile`, `initials-avatar`, `loading-note`, `back-link`.
- Styles that only one page needs go in that file's `<style scoped>`.
- Every colour, font size, radius and shadow comes from a variable in `theme.css`, for example `var(--maroon)` or `var(--text-sm)`. Never write a hex code.
- If a style is needed on more than one page, add it to `dashboard.css`. Don't create new global CSS files, and don't use inline `style="..."`.

## Loading, error and empty states

Every page that loads data needs to handle four cases: still loading, failed to load, loaded but empty, and loaded with data. Follow the pattern in `views/Instructor/Sessions.vue`, which uses a `loading` ref, a `loadError` ref and a `v-if` / `v-else-if` chain in the template.

## Helpers

Formatting and calculations that don't need Vue belong in `utils/`, for example `formatSessionDate` and `countByStatus` in `utils/sessions.js`. Don't write a new `initials()` function inside every page.

## Comments

Write comments so someone new to the file can understand why the code does what it does without asking you. Don't explain what the code obviously does.

Add a comment when:

- the reason for the code isn't obvious from reading it
- there's a trap someone could fall into (timezones, ordering, a backend quirk)
- you export a function from `apis.js` or `utils/` and its inputs or return value aren't obvious
- something is temporary, in which case start the comment with `TEMPORARY:` and say what should replace it

Good comments already in the codebase:

```js
// "YYYY-MM-DD" on its own parses as UTC midnight, which can land on the wrong day.

// A new session has nobody marked yet, so take the instructor straight to it.
```

Comments that don't help (don't write these):

```js
// set loading to false
loading.value = false

// loop through participants
for (const p of participants) { ... }
```

Longer `<script setup>` blocks can be split into sections with dividers like `/* ---- load ---- */` and `/* ---- navigation ---- */`.

As a rough guide, a 150-line page usually has somewhere between two and five comments. A page with none is almost always missing something.

## Naming and file layout

- Views use PascalCase and are named after the page: `Participants.vue`, `SessionDetail.vue`.
- Components use PascalCase and describe what they are: `CreateSessionModal.vue`.
- Functions use camelCase and start with a verb: `listParticipants`, `formatSessionDate`.
- Always use `<script setup>` (Composition API). Don't use the Options API.
- Order the sections of a `.vue` file as `<script setup>`, `<template>`, then `<style scoped>`.

## Checklist before opening a pull request

- [ ] No view file renders more than one role's dashboard.
- [ ] Nothing was copied from another view. Shared parts are components.
- [ ] Every backend request goes through a function in `apis.js`.
- [ ] No hex codes, inline styles or new global CSS files.
- [ ] New pages are in `router/index.js` with the right roles.
- [ ] Loading, error and empty states are handled.
- [ ] Comments explain the non-obvious parts, and no page has zero comments.
- [ ] No leftover `console.log`, dummy data or commented-out code.
- [ ] `npm run build` in `frontend/` finishes without errors.
