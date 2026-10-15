# Audit log

Super admins and branch managers can open a read-only audit log from their Administration page. Instructors have no Administration item and can't reach the audit routes or API. The log records activity from deployment onwards; it doesn't reconstruct earlier events.

## What is recorded

| Event | Details |
| --- | --- |
| `staff.created` | Actor, target staff email/ID, initial role, branch and active state |
| `staff.role_changed` | Before/after role, plus any other changed staff fields |
| `staff.branch_changed` | Before/after branch IDs, including unassignment |
| `staff.deactivated`, `staff.updated` | Active-state or profile changes; never passwords or hashes |
| `branch.created`, `branch.updated`, `branch.deleted` | Branch identity and changed name/region |
| `branch.quarters_updated` | Year and all before/after quarter dates |
| `report.requested` | Requester, job ID, report type, branch, date range and model |
| `report.running`, `report.succeeded`, `report.failed` | Worker status or queue failure/expiry, with a safe reason code |
| `report.statistics_viewed` | Statistics request outcome; branch and date range on success |
| `auth.login`, `auth.logout` | Authenticated identity and outcome; failed login input is not kept |
| `api.write` | Matched API write endpoint, HTTP method/status, resource identifiers and actor |

`api.write` entries cover participant, session/attendance, physical-assessment, document/folder and administrative endpoints. They summarise the request outcome, not a field-by-field history, and a successful request can still be a no-op. Detailed staff events record the actual changes. When several fields change, one event holds all of them.

A detailed event and its API summary can both exist, linked by a server-generated request ID. Report request and worker events are linked by job ID. For worker events the actor is the account that requested the report.

Audit payloads are explicit allowlists. Request and response bodies, passwords, hashes, tokens, prompts, narratives, participant measurements and clinical notes are never copied. Events store UUIDs and identity snapshots instead of foreign keys, so deleting an account, report or branch can't delete its history.

## Viewing the log

The viewer groups events into **Staff changes**, **Branch settings**, **Reports**, **Record updates** and **Sign-ins**. Each row shows the time, staff name (or recorded email), a plain-language description, branch and result. It doesn't show stored payloads, IDs, role codes, endpoint paths or error text. Staff role changes use readable role names, and report entries include the reporting dates. Duplicate request summaries and intermediate "running" events are hidden from the list but kept in the database.

Results are newest first, 50 per page, and can be filtered by search text, activity group, branch (super admins only), result and date range (inclusive New Zealand dates).

## Access

`GET /api/audit/` gives super admins every event. Branch managers see only events for their current branch, including staff who left it and records transferred out of it. A manager with no branch sees nothing. Other branches' and national events are removed before any search, filter or paging, so query parameters can't widen the scope. Branch-manager views describe departures as "left your branch" without naming the other branch.

There are no endpoints to create, edit or delete audit records, and the model rejects normal ORM edits and deletes. These are application protections, not a tamper-proof database: someone with direct database access can still change records.

An event's branch is the affected branch (or national). For record updates it is taken from the URL or the record's branch, including a snapshot taken before a delete. Transfers record both branches. If no branch applies, the actor's branch is used.

## Consistency

Staff and branch changes, quarter updates and report creation are saved in the same database transaction as their audit entry, so if the audit entry fails the change is rolled back. Report status changes go through `transition_job`, which updates the job and writes the audit entry together. Only the process that actually changes the status records the event, so duplicate Celery deliveries and repeated polling don't create duplicates.

Request summaries (`api.write`) are written by middleware after the response, outside the endpoint's transaction. Polling job status, ordinary reads and reading the audit log don't create entries. Help chatbot questions aren't logged, because they change nothing.

## Limits

- Records are kept indefinitely. Nothing is backfilled or deleted automatically.
- Direct SQL, management commands and Django admin changes aren't in this log. Django admin keeps its own.
- It is an activity log, not billing telemetry: token counts, costs and provider request IDs aren't recorded.
- A hard-killed report job is recorded as timed out when job-expiry handling next sees it.

## How to check it

1. As a super admin, open Administration → Audit log.
2. Create an instructor, change their role and branch, then deactivate them. Search their email and check each change appears with the right description and actor.
3. Edit a branch's quarter dates and check the change is listed under Branch settings.
4. Request an AI report and check the request and its result appear under Reports.
5. As that branch's manager, check only branch-related events appear. As an instructor, check there is no Administration item and the audit API is denied.

Automated tests: `python manage.py test audit`.

## Key files

- `backend/audit/models.py`: audit event model and write guards
- `backend/audit/services.py`: payloads, staff change comparison and `transition_job`
- `backend/audit/middleware.py`: request summaries and request IDs
- `backend/audit/presentation.py`: plain-language descriptions
- `backend/audit/views.py`: filtered, scoped read endpoint
- `frontend/src/components/audit/AuditLog.vue`: the viewer
