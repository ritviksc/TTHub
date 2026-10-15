# Sessions and attendance

## Roles and navigation

Every role has Sessions in the main navigation. All three role routes use the shared Sessions and SessionDetail views under `frontend/src/views/Instructor/`.

| Action | Super Admin | Branch Manager | Instructor |
| --- | --- | --- | --- |
| View list, calendar and register | Any branch, with branch filter | Own branch | Own branch |
| Create session | Select a branch | Own branch automatically | Own branch automatically |
| Mark attendance, edit reasons, finalise or reopen | Any branch | Own branch | Own branch |
| Delete session | No | No | Only sessions they created, without saved feedback |

Calendar and List share the selected branch filter. The national list also shows a Branch column. List date filters are This month, This quarter and All; these use calendar periods, independently of branch reporting-quarter configuration. Calendar dates show a selected-day agenda. The blue Add session button and day quick-add controls are available for today and future dates; the empty agenda has no duplicate gray create button.

## Creation and rosters

Create new session requires date, time and activity. The UI offers Standard strength and mobility training or Fitness test. Dates use Pacific/Auckland: today is allowed regardless of the time; earlier dates are rejected.

Super Admins must select an existing branch. The Sessions branch filter prefills that selection when one branch is selected. Branch Managers and Instructors cannot override their branch through the request, and unassigned branch staff cannot create sessions. The server records the authenticated creator.

The session and its roster are created in one transaction. The roster contains participants active at the chosen branch at creation time. Every record initially has Absent status. Later enrolments, deactivations, reactivations or transfers do not rewrite that fixed roster. A failed save keeps the form and its draft; pending creation blocks repeated submission and dismissal.

## Marking and reviewing attendance

Attendance mode shows a list of participant cards, with consented photos or initials. Tap a card to toggle Present/Absent. Marking mode has no absence-reason row. Done finalises the register and returns to the session details; an all-absent register requires confirmation.

Review attendance on a finalised register locks status changes and displays reason controls only for absent participants. Save reason persists one participant’s reason and stays in review. Done saves all pending reason edits and returns to the session details while preserving finalisation. Reasons are No show, Medical appointment, Transport issue and Other; Other requires a description. Marking someone present clears an earlier absence reason.

Reopen attendance saves pending review reasons before reopening. Reopened attendance returns to the simple participant list without reason rows. Make status changes and use Done to finalise again. Failed saves remain visible and must succeed before completing the transition.

All three roles can edit an unfinished register from the session-details table. Finalised table controls are read-only and have no dropdown arrows; use Review attendance to edit reasons and Reopen attendance to change status. Super Admins can do this for any branch, including sessions created by other staff. Branch Managers and Instructors remain restricted to their assigned branch.

Only finalised registers contribute to attendance totals and reporting. Incomplete registers are excluded rather than treated as zero attendance. See [absence reasons](attendance-absence-reasons.md) for reporting rules.

## API

| Endpoint | Behaviour |
| --- | --- |
| `GET /api/sessions/` | National list for Super Admins; branch-scoped otherwise |
| `POST /api/sessions/` | Create; Super Admin payload includes `branch`; branch staff use their assigned branch |
| `GET /api/sessions/<id>/` | Register, counts, branch and finalisation state |
| `DELETE /api/sessions/<id>/` | Creator-instructor only; saved feedback returns 409 |
| `PATCH /api/sessions/<id>/attendance/<record-id>/` | All staff; national scope for Super Admins, own branch otherwise. Finalised registers permit absent-reason edits; status changes require reopening |
| `PATCH /api/sessions/<id>/attendance-state/` | All staff; national scope for Super Admins, own branch otherwise. Finalise or reopen |

The branch dropdown filters already-authorised list results in the frontend; the API does not use it as an access-control boundary. Non-national staff never receive another branch’s sessions.

## Audit attribution

Attendance updates, finalisation and reopening are recorded by the existing API-write audit trail. Events identify the acting user, role, session and actual session branch, including when a Super Admin has no branch assignment. Record updates also identify the attendance record. Request bodies and free-text absence explanations are not stored in the audit log. Super Admins still cannot delete sessions.

## Verification

From backend: `python manage.py test sessions`. From frontend: `node --test tests/session-creation.test.js tests/super-admin-sessions.test.js tests/session-attendance-access.test.js tests/attendance-mode.test.js`.
