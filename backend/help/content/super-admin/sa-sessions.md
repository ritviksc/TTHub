---
title: Sessions across branches
section: Sessions
order: 25
---
## Finding sessions

Open **Sessions**. Choose **All branches** or a specific **Branch**. The filter applies to both **Calendar** and **List**. Calendar entries identify their branch, and the selected day’s agenda shows each session’s branch and activity. In List, the Branch column identifies each session; use **This month**, **This quarter** or **All** to narrow dates.

Select a session to open its register. **‹ All sessions** returns to the national Sessions page.

## Creating a session as a super admin

1. Select **+ New session**, or select a calendar day today or later and use the blue **+ Add session** button.
2. In **Create new session**, choose the **Branch**. If the Sessions page was filtered to one branch, it is preselected; with All branches, you must choose one.
3. Enter the date, time and activity, then select **Create session**. Dates cannot be in the past; today is allowed regardless of the time.
4. The new session’s details open. Its roster contains only participants active at the selected branch when it was created. The signed-in super admin is recorded as its creator.

A failed request keeps the form open with the draft and an error. Wait for a pending creation to finish before closing or submitting again. Later enrolments, reactivations or deactivations do not change an existing roster.

## Viewing attendance

The register shows the branch, date, time, finalisation state, present and absent counts, attendance rate and each participant’s absence reason. Filter the participants by All, Present or Absent.

Super admins can mark, review, finalise and reopen attendance for sessions in any kapa, including sessions created by other staff. Incomplete registers are excluded from attendance reporting totals until finalised. Super admins cannot delete sessions.

## Taking attendance as a super admin

Open an unfinished session and select **Attendance mode**. Check the session’s branch, activity and date in the header. Tap a participant card to mark Present, or tap again to mark Absent. The photo appears only when photo consent is recorded; otherwise an initial is shown. Marking mode has no absence-reason rows.

Select **Done** to finalise and return to the Super Admin session details. If everyone is absent, confirm the empty register. A failed save stays on the page with an error for retry.

## Reviewing and reopening attendance

Open a finalised session and select **Review attendance**. Present/absent cards are locked, while absent participants have reason controls: No show, Medical appointment, Transport issue or Other. Other needs a description. **Save reason** saves one participant’s reason and keeps review open. **Done** saves all pending reason edits and returns to session details while keeping the register finalised.

To change who was present, select **Reopen attendance**. Pending reasons must save first. The simple marking list returns without reason rows; make corrections and select **Done** to finalise again. Marking someone present clears their old absence reason.

## Who changed the register?

The audit log records the acting Super Admin, the session and its actual kapa for attendance edits, finalisation and reopening. It does not store the submitted absence explanation. Open **Administration → Audit log** to review those operations.
