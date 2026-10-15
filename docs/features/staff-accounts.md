# Staff accounts and reactivation

## Administration

Super Admins open Administration → Users to create and manage staff nationally. They can change identity, role and branch; only Super Admins can grant Super Admin. Promoting a user to Super Admin clears the branch. Other roles require a branch. The acting user’s own account is excluded from staff-management lists and detail/status endpoints.

Branch Managers open Administration → Kaimahi to create and manage instructors assigned to their own branch. They cannot manage branch managers or Super Admins, change roles or branches, or reach foreign or unassigned staff. An unassigned manager cannot manage unassigned instructors.

Staff sign in with a normalised unique email and password. The app does not send account invitation emails or provide password-reset/change screens.

## Deactivate and reactivate

Deactivate disables sign-in while preserving recorded sessions, feedback and other history. Reactivate restores sign-in with the existing credentials, role and branch. Both actions are available in the staff list and account details, subject to the permissions above. In lists, the matching small outline buttons use semantic theme colours: red for deactivation, green for reactivation.

Status changes update the displayed state only after a successful API response. Pending changes block repeated submission; failures preserve the prior status and show an error for retry. Staff accounts are retained, not deleted, and inactive accounts still prevent deletion of their attached branch.

Participant reactivation is a separate workflow under Participant status on Details. All staff can reactivate participants they are permitted to access. See [participant details](participant-detail-and-files.md).

## API and auditing

- `POST /api/auth/staff/`: create an authorised account.
- `GET /api/auth/staff/list/`: permitted staff, excluding self.
- `GET` / `PATCH /api/auth/staff/<id>/`: read or edit an authorised account.
- `POST /api/auth/staff/<id>/deactivate/` and `reactivate/`: explicit status actions; `is_active` remains read-only in normal edits.
- `POST /api/participants/<id>/deactivate/` and `reactivate/`: participant status actions, scoped to authorised participants.

Staff status changes lock the account row and write an audit event in the same transaction. `staff.deactivated` and `staff.reactivated` record the actor and old/new status. Repeating an already-applied action does not create a second status-change event. See [audit logging](../backend/audit-log.md).

From backend: `python manage.py test users participants audit`. From frontend: `node --test tests/reactivation.test.js tests/apis.test.js`.
