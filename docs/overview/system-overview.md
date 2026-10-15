# System overview

Taurite Tū is a web app for running a strength and balance programme for kaumātua: its branches (kapa), staff, participants, classes, attendance, physical assessments, documents and reporting.

```
Group_4/
|---> backend/         Django API, database models, permissions
|---> frontend/        Vue website that staff use
|---> docs/            Setup guides, feature references and conventions
|---> scripts/         Development launcher (dev.sh)
|---> .venv/           Local Python environment (not committed)
|---> .env             Local configuration and credentials (not committed)
```

The main flow of the system:

```
Vue page -> API request   -> Django permissions and validation -> Database
         <- JSON response <-
```

- **Frontend**: Vue 3, Vue Router, Vite and Axios.
- **Backend**: Django and Django REST Framework, with an SQLite database. Settings for Postgres are left commented out in `backend/config/settings.py`.
- **Background work**: Celery runs the AI report jobs, with Redis as the broker. Redis also serves as Django's cache.
- **AI**: an OpenAI-compatible model server explains report statistics and powers the help chatbot (see [llm.md](../backend/llm.md)).

Three roles use the app: kaimahi (instructors), branch managers and super admins. The frontend router hides pages a role can't use, and the backend enforces every permission again.

## Roles and access

| Feature | Super Admin | Branch Manager | Instructor / Kaimahi |
| --- | --- | --- | --- |
| Participants | Enrol and manage nationally | Enrol and manage own branch | Enrol and manage own branch |
| Participant status | Deactivate/reactivate nationally | Own branch | Own branch |
| GP consent and supporting documents | Nationally | Own branch | Read consent status only; no GP documents |
| Session creation | Choose any branch | Own branch automatically | Own branch automatically |
| Session list/calendar and registers | National branch filter; edit attendance | Own branch; edit attendance | Own branch; edit attendance |
| Session deletion | No | No | Creator only, with no linked feedback |
| Qualitative feedback | Read/create nationally | Read/create own branch | Read/create own branch |
| Physical assessments | Nationally | Own branch | Own branch |
| Staff accounts | Create, edit roles/branches, deactivate/reactivate others | Create/edit/deactivate/reactivate own instructors | No staff management |
| Attendance/physical reports | National or selected branch | Own branch | No reporting page |
| ACC drafts, saved report history, narrative editing | Available | Not available | Not available |
| Help | All role articles | General, Kaimahi and Branch Manager articles | General and Kaimahi articles |

Details and Attendance history are separate participant pages. Attendance marking uses a participant list; absence reasons are edited in Review attendance. Only finalised registers count in attendance totals. Baseline/latest physical comparisons use completed assessments. Feedback records speaker type and consent, and only consented sources are offered for ACC preparation.

Navigation is defined in `frontend/src/utils/nav.js`. Administrative roles find staff management, the audit log and Documents under Administration. Instructors find Documents in their main menu. Theme and Log out are in the account menu. Super Admins and Branch Managers land on Overview; Instructors land on Home.

## Current limits

The national Overview shows branch, active participant and staffing counts; a combined live attendance/physical/enrolment dashboard remains unfinished. Branch Attendance/Questionnaire placeholders and quarterly questionnaire entry are not complete. Attendance statuses and absence reasons are fixed in code. There is no staff password-reset flow, no editing/deleting saved feedback, and no reopening completed physical assessments. ACC drafts are reviewed and exported by staff; the app does not submit reports to ACC.

## Feature references

- [Sessions and attendance](../features/sessions-and-attendance.md)
- [Participants and files](../features/participant-detail-and-files.md)
- [Staff accounts and reactivation](../features/staff-accounts.md)
- [Physical assessments](../features/physical-assessments.md)
- [Feedback](../features/feedback.md)
- [ACC reporting](../features/acc-reporting.md)
- [Help articles and chatbot index](../setup/help-chatbot.md)
