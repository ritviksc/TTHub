# Audit log

Super-admin and branch-manager Administration pages link to a shared read-only audit log. Instructors have neither an Administration navigation item nor access to those routes or the audit API. This records activity from deployment onwards; it does not reconstruct earlier events from current database values.

## What is recorded

| Event | Details |
| --- | --- |
| `staff.created` | Actor, target staff email/ID, initial role, branch and active state |
| `staff.role_changed` | Before/after role, plus any other changed staff fields |
| `staff.branch_changed` | Before/after branch IDs, including unassignment |
| `staff.deactivated`, `staff.updated` | Active-state or profile changes; no password/hash |
| `branch.created`, `branch.updated`, `branch.deleted` | Branch identity and changed name/region |
| `branch.quarters_updated` | Year and all before/after quarter dates |
| `report.requested` | Requester, job ID, report type, branch and date range |
| `report.running`, `report.succeeded`, `report.failed` | Worker status or queue failure/expiry, with a safe reason code |
| `report.statistics_viewed` | Statistics request outcome; branch and date range on success |
| `auth.login`, `auth.logout` | Authenticated identity and outcome; failed login input is not retained |
| `api.write` | Matched API write endpoint, HTTP method/status, typed resource identifiers and actor |

API write entries cover participant, session/attendance, physical-assessment, document/folder and administrative endpoints. They are request outcome summaries, not field-by-field histories. A successful request can be a no-op. Detailed staff events record actual changes; when several fields change, one event includes all deltas (deactivation takes precedence over role, then branch, then profile changes in the action label).

A detailed event and its API summary can both appear. Their server-generated request ID connects them. Job ID connects report request and worker events. Worker actor means the account that requested the report, not an interactive user currently executing the worker. Source distinguishes `api`, `worker` and `system`.

Audit payloads are explicit allowlists. Request/response bodies, passwords, hashes, tokens, prompts, narratives, participant measurements and free-text clinical notes are not copied. Account names/emails are retained where needed to identify staff actions. Events retain UUIDs and identity snapshots rather than foreign keys, so deleting accounts, reports or branches cannot cascade-delete history.

## Access and filtering

`GET /api/audit/` allows super admins to see all events. Branch managers see only events associated with their current branch, including staff departures and resource transfers whose previous branch was theirs. Managers with no assigned branch receive an empty list. National and unrelated branch events are excluded before search, filtering and pagination; query parameters cannot widen this scope. There are no create, edit or delete endpoints for audit records. The application model also rejects normal ORM edits/deletes. These are application protections, not a tamper-proof database: a database administrator or raw SQL can bypass them.

Results are newest first, paginated at 50 events. Filters:

- `q`: actor email, target label/ID or action substring.
- `action`, `actor_id`, `branch_id`, `outcome`: exact values.
- `start_date`, `end_date`: inclusive New Zealand calendar dates.
- `page`: results page.

For detailed events, branch identifies the affected branch (or national scope). For successful generic writes it uses the branch URL or the affected participant/session/assessment/document/folder's recorded branch, including a snapshot taken before deletion. When a resource transfers, its previous branch is also recorded. Otherwise it falls back to the actor's branch. Older events keep their original attribution; this update does not infer or backfill missing historical scope. Transfers retain both branch IDs in details. Unassignment has no current branch but is visible to the former branch through its recorded before value. Deleted branch IDs remain in events but no longer appear in the active branch dropdown.

## Consistency and report integration

Staff/branch changes, quarter updates and report creation commit with their detailed audit entries in a database transaction. Failure to save that audit entry rolls back the database change. Staff update paths lock the target before capturing before/after values on databases supporting row locks.

Report state changes use `transition_job`: the conditional job update and audit insert are one transaction. Only the process that changes status records an event, so duplicate Celery deliveries and repeated expiry polling do not create repeated transitions. Queue failure, generation failure and timeout use reason codes rather than raw exceptions. Empty reports record request and success with `no_data`, without calling the provider.

Generic request summaries are written by middleware after the response is produced; they are not in the same transaction as arbitrary endpoint changes. They complement rather than replace domain events. Polling job status, ordinary page/data reads and reading the audit log do not generate request-summary rows.

## Boundaries and operation

- No backfill, automatic deletion, or retention schedule is enabled.
- Direct SQL, management scripts and Django admin changes are outside this application audit trail. Django admin has its own existing log.
- This is an activity audit, not provider billing telemetry: token counts, model costs and provider request IDs are not collected.
- Hard-killed jobs are recorded as timed out when existing job-expiry handling detects them; this feature adds no periodic sweeper.
- Apply `python manage.py migrate` before starting the updated web server and Celery worker. Restart both to load the hooks.

## Manual checks

1. Log in as a super admin. Open Administration → Audit log.
2. Create an instructor, promote them to branch manager, transfer or unassign them, then deactivate them. Filter by their email. Expand details and check before/after values and actor identity.
3. Edit a branch's quarter dates. Confirm year and before/after dates are logged.
4. Generate attendance or physical analysis while Celery is running. Refresh the audit page and search its job ID; expect requested, running and succeeded (or failed) events.
5. Select a date, action, branch or outcome filter; navigate pages. Try a range without events.
6. As a branch manager, open Administration → Audit log. Confirm only branch-related events appear, including a super-admin action on your branch and a staff departure. Try another branch ID in the API filter; unrelated events must remain hidden. As an instructor, confirm no Administration item appears and both admin routes and the API deny access.

Automated tests cover actor attribution, permissions, staff changes, rollback on audit failure, identity retention, filtering/pagination, write guards, login/logout privacy, both report types, duplicate delivery, no-data reports, queue failures, expiry, worker failure, branch changes and quarter changes.

## Implementation files

- `backend/audit/{apps.py,__init__.py}`: register the dedicated audit app.
- `backend/audit/models.py` and `migrations/{__init__.py,0001_initial.py}`: persistent audit events, indexes and application write guards.
- `backend/audit/services.py`: explicit payloads, staff change comparison and atomic job transitions.
- `backend/audit/middleware.py`: safe API request outcome summaries and request correlation IDs.
- `backend/audit/{views.py,urls.py}`: admin-only filtered, paginated read endpoint with enforced branch scope.
- `backend/audit/tests.py`: regression coverage.
- `backend/config/{settings.py,urls.py}`: app, middleware and route registration.
- `backend/users/views.py`: staff and branch domain hooks.
- `backend/users/quarters.py`: quarter change snapshots (extends the preceding quarter feature).
- `backend/reporting/{models.py,tasks.py,views.py}`: request and job lifecycle hooks.
- `frontend/src/apis.js`: audit GET wrapper using existing retry handling.
- `frontend/src/router/index.js`: super-admin route guard.
- `frontend/src/components/audit/AuditLog.vue`: shared filters, paging and detail viewer.
- `frontend/src/views/{SuperAdmin,BranchManager}/{AuditLog.vue,Administration.vue}`: role-specific wrappers and administration links.
- `frontend/src/components/DashboardNav.vue`: Administration for branch managers; instructors remain excluded.
- This document: scope, implementation, operational boundaries and manual verification.

## Administrator-friendly presentation

The list API returns only an event key, time, staff display name (recorded email as a fallback), a plain-language description, branch label and readable result. It does not return the stored payload, account/resource IDs, role codes, endpoint paths, request IDs, exception text or cross-branch change dictionaries. Branch-manager views label departures as leaving their branch without naming the other branch. User-supplied names are rendered as text, never HTML.

The viewer uses activity groups (Staff changes, Branch settings, Reports, Record updates and Sign-ins) instead of event codes. It has no expandable technical detail panel. Duplicate successful request summaries and intermediate report-running events are omitted before pagination; the underlying audit records remain intact. Staff role changes use readable role names and report descriptions include validated reporting dates when available.

`category` is an optional API filter (`staff`, `branches`, `reports`, `records`, `signins`). The former raw serializer is no longer exposed through this endpoint. `backend/audit/presentation.py` contains the explicit summary rules; unknown events fall back to a generic administrative description rather than exposing their metadata.
