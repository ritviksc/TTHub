# Frontend conventions

These are the conventions the frontend code follows. Keep to them when fixing or changing anything, so the code stays consistent.

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

## Role-specific routes and shared screens

Keep dashboards role-specific. When the same workflow serves several roles, route them to one shared screen and derive its available actions and filters from the signed-in role. The backend remains the authority for access. For example, all Sessions routes share `views/Instructor/Sessions.vue` and `SessionDetail.vue`, and all Feedback routes use `views/Feedback.vue`. The folder name of a shared screen does not define its permissions.

If a page goes past about 300 lines, look for parts you can pull out into components, such as a modal, a table or a side panel. `views/Instructor/Sessions.vue` is a good example. Its create form lives in `components/sessions/CreateSessionModal.vue`, which keeps the page itself short and easy to read.

## Sharing code between roles

When two or more roles need the same UI, don't copy the file into each role's folder. Copies drift apart, and every bug then has to be fixed in three places.

Do this instead:

1. Reuse an existing shared view when the whole workflow is the same.
2. Use `components/<feature>/` for reusable parts or for a shared screen wrapped by small role-specific views.
3. Use props or existing role-derived capabilities for differences such as branch filters and editing access. Keep role restrictions on routes and enforce them again in the API.

If you're about to copy more than about 20 lines from another view, stop and make a component.

For example, the branch manager and super admin audit log pages share `components/audit/AuditLog.vue`, and each role's view only sets the props:

```vue
<!-- views/BranchManager/AuditLog.vue -->
<script setup>
import AuditLog from '@/components/audit/AuditLog.vue'
import { auth } from '@/stores/auth.js'
</script>

<template><AuditLog back-route="bm-administration" :branch-id="auth.user?.branch?.id" :branch-name="auth.user?.branch?.name ?? 'Your branch'" /></template>
```

```vue
<!-- views/SuperAdmin/AuditLog.vue -->
<script setup>
import AuditLog from '@/components/audit/AuditLog.vue'
</script>

<template><AuditLog show-branch-filter back-route="sa-administration" /></template>
```

## Talking to the backend

All backend requests go through functions in `frontend/src/apis.js`.

- Don't import axios in a view or component, and don't write URLs in pages.
- If an endpoint has no function yet, add one to `apis.js` under the right section (`/* ---- participants ---- */` and so on). If its parameters aren't obvious, add a one-line comment above it, like the one on `listBranches`.
- GET functions in `apis.js` already retry timeouts (up to 3 attempts) through `getWithRetry`. Don't wrap them in `withRetry` again, which multiplies the attempts. Writes (POST, PUT, PATCH, DELETE) are never retried, because a retry could create duplicates.
- When a request fails, show the server's message if there is one and a friendly fallback if not:

```js
error.value = e.response?.data?.detail ?? 'Could not create this session.'
```

## Routes

- Add every page to `router/index.js` with `meta: { requiresAuth: true, roles: SA }` (or `BM` or `IN`).
- Load pages lazily: `component: () => import('@/views/SuperAdmin/Users.vue')`.
- Role-specific route names start with `sa-`, `bm-` or `in-`. Shared routes such as `staff-detail`, `documents` and `help` retain their existing names.
- Signed-in navigation labels, links and Administration groups live in `utils/nav.js`. Update that source when adding a destination.
- Link by route name, not by typing the path: `{ name: 'in-session-detail', params: { id } }`.

## Styling

- Wrap every logged-in page in `<div class="dash-page"><main class="content">`.
- Use the classes in `dashboard.css` first: `page-header`, `page-subtitle`, `btn-primary`, `btn-cancel`, `btn-cancel btn-small btn-reactivate` / `btn-deactivate`, `pills`/`pill`, `data-table`, `status-badge`, `card`/`card-grid`, `modal-backdrop`/`modal`, `form-group`, `form-row`, `form-error`, `stat-grid`/`stat-tile`, `initials-avatar`, `loading-note`, `back-link`.
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

## Before finishing a change

- [ ] No view file renders more than one role's dashboard.
- [ ] Nothing was copied from another view. Shared parts are components.
- [ ] Every backend request goes through a function in `apis.js`.
- [ ] No hex codes, inline styles or new global CSS files.
- [ ] New pages are in `router/index.js` with the right roles.
- [ ] Loading, error and empty states are handled.
- [ ] Comments explain the non-obvious parts, and no page has zero comments.
- [ ] No leftover `console.log`, dummy data or commented-out code.
- [ ] `npm run build` in `frontend/` finishes without errors.
