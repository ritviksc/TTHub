# Taurite Tū frontend

Vue 3 app using Vue Router, Vite and Axios. Follow the [project quickstart](../docs/quickstart/guide.md) for Python, database, Redis and optional AI setup.

## Development

From this directory:

```bash
npm ci
npm run dev
```

Open `http://localhost:5173` with Django running on port 8000. The API base can be configured with `VITE_API_BASE_URL`; requests and GET timeout retries are centralised in `src/apis.js`.

```bash
npm run build
node --test tests/*.test.js
```

## Routes and shared screens

`src/router/index.js` defines authorised role routes; `src/router/access.js` rechecks the server session and sends signed-in users to their own starting page. Super Admins and Branch Managers start at Overview; Instructors start at Home.

Signed-in navigation is defined in `src/utils/nav.js`. Users, Kaimahi, audit logs and documents are grouped under Administration for the administrative roles. Theme choices and Log out are in the account menu.

- Sessions and SessionDetail under `src/views/Instructor/` serve all three roles. Super Admins can filter, create sessions and manage attendance across branches. Branch Managers and Instructors create and manage attendance only within their own branch. All roles use the same Attendance mode and Review attendance screens.
- `src/views/Feedback.vue` serves all three roles with subject, speaker, date and reporting-consent entry.
- `src/components/participants/` shares enrolment, Details and Attendance history workflows. Status actions include deactivation and reactivation.
- `src/components/physicalTests/` provides result entry, completed baseline/latest comparison, history and charts.
- Help articles come from `backend/help/content/`; the Help assistant’s embedding index must be rebuilt after article edits.

Use [frontend conventions](../docs/frontend/conventions.md), the [system permissions](../docs/overview/system-overview.md#roles-and-access) and the [feature guides](../docs/features) when making changes.
