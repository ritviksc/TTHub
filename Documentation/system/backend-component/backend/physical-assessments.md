# Physical assessment recording

## Using the feature

1. Start the development system with `./scripts/dev.sh` (it applies migrations).
2. Sign in as an instructor or branch manager and open Participants, or use the super admin participant list.
3. Click a participant name. The existing consent page is now also their profile, with a physical assessment section.
4. Select **Start physical assessment**. An existing draft instead offers **Continue assessment**. Starting twice resumes the same draft.
5. On the assessment page, check the date. Save changes to the date before recording exercises.
6. Select **Record / edit results** for timed up and go, chair stand, or balance. Read the instructions, record results and save. Closing the popup without saving discards only that popup's edits.
7. Complete the assessment after reviewing every exercise group. Completed assessments are read-only. Return to the profile to compare results in the history table or start another assessment.

Saved results survive a reload or leaving the page. No new dependencies are required. The three supplied source PDFs are available through links in the exercise popups, under `frontend/public/testing-guides/`. They are blank public testing guides, not participant records.

## Measurements and completion rules

One assessment contains six result rows: TUG seconds, chair-stand count, and seconds for each of four balance positions. This is three exercise groups, not six separate assessment occasions. The participant's existing name and date of birth are reused.

- TUG requires a positive time. A walking aid and observations can be recorded.
- Chair stands require a non-negative whole count. **Arms needed to stand** records exactly zero with that explicit outcome, following the supplied sheet.
- Balance positions must follow the supplied order. Each time is between zero and ten seconds. Only a measured ten-second hold permits the next stage; all later positions after stopping are saved as `skipped` with no numeric value.
- **Unable / stopped for safety** requires a reason and has no numeric value. It is a valid recorded outcome, including when a test is avoided for safety.
- **Not attempted** requires a reason and leaves the assessment incomplete. It is different from a later balance position skipped under the protocol.
- Completing requires all six outcomes to have been recorded, with no `not_attempted` outcome. A completed assessment means the assessment record is complete, not that the participant succeeded in every exercise. An assessment can be completed with inability outcomes; future reports must present these separately from measured outcomes.

Drafts do not represent completed testing. Completion stores a timestamp. Assessment date is separately recorded for future date-range reporting. Future dates and dates before the participant's birth are rejected. Clinical risk ratings and diagnostic claims are not generated. Participant graphs, date-range statistics and optional aggregate AI explanations are now implemented; see [physical-reporting.md](physical-reporting.md). Corrections/reopening of completed records are not implemented.

## Backend structure and access

`physical_tests` is separate from the LLM and reporting apps. `Assessment` stores participant, branch at assessment creation, creator, date, completion timestamp and version. `ExerciseResult` stores a typed exercise/outcome, optional measurement, notes, walking aid, the last recording staff member and update time. The database permits only one draft per participant and one result per exercise per assessment.

All three staff roles can record assessments. Instructors and branch managers can access only assessments belonging to both their current branch and participants currently in that branch. Super admins have national access. If a participant moves, old branch records stay in their original scope and are accessible by super admins; automatic transfer of historic records is not implemented. An old branch's unfinished draft must be resolved by a super admin before a new draft can be started in the new branch. Inactive participants cannot start new assessments, but saved assessments remain accessible. Branch deletion checks historical assessments even after participants move.

Mutations send the last-read `version`. The server atomically advances it with the result write, returning HTTP 409 for a stale edit so a second tab cannot silently overwrite a newer save. Reload the saved assessment after a conflict. Failed validation rolls back the version update. GET helpers use the existing retry helper; writes are not automatically retried.

| Endpoint (under `/api/physical-tests/`) | Purpose |
| --- | --- |
| `GET participants/<participant-id>/` | List accessible assessment history |
| `POST participants/<participant-id>/` | Start or resume a draft |
| `GET <assessment-id>/` | Read a draft or completed assessment |
| `PATCH <assessment-id>/` | Save `assessed_on` with `version` |
| `PUT <assessment-id>/results/<group>/` | Save the complete group (`tug`, `chair`, `balance`) with `results` and `version` |
| `POST <assessment-id>/complete/` | Complete a validated draft with `version` |

## Files introduced or changed

- `backend/physical_tests/__init__.py`, `apps.py`: register the new app.
- `backend/physical_tests/models.py`: assessment and exercise result storage.
- `backend/physical_tests/serializers.py`: measurement, date and balance-sequence validation; API representation.
- `backend/physical_tests/views.py`, `urls.py`: authorised draft, result and completion endpoints.
- `backend/physical_tests/migrations/__init__.py`, `0001_initial.py`: database schema and uniqueness constraints.
- `backend/physical_tests/tests.py`: workflow, permission, measurement, date and conflict tests.
- `backend/config/settings.py`, `backend/config/urls.py`: register and mount the app.
- `backend/users/views.py`: prevent branch deletion when historical assessments exist.
- `frontend/src/apis.js`: physical assessment API helpers.
- `frontend/src/utils/physicalTests.js`: display labels, condensed procedures, result payloads and error formatting.
- `frontend/src/components/physicalTests/AssessmentHistory.vue`: profile start/resume controls and comparison table.
- `frontend/src/components/physicalTests/AssessmentPage.vue`: date, exercise groups, saved observations and completion.
- `frontend/src/components/physicalTests/ExerciseModal.vue`: accessible native dialog for instructions and result entry.
- `frontend/src/components/participants/ParticipantList.vue`: existing instructor participant list extracted for reuse by managers.
- `frontend/src/views/Instructor/Participants.vue`, `frontend/src/views/BranchManager/Participants.vue`: thin wrappers around the shared participant list.
- `frontend/src/views/ParticipantConsent.vue`: adds assessment history to the participant profile while retaining consent editing.
- `frontend/src/views/SuperAdmin/Participants.vue`: participant-name links to profiles.
- `frontend/src/views/SuperAdmin/PhysicalAssessment.vue`, `frontend/src/views/BranchManager/PhysicalAssessment.vue`, `frontend/src/views/Instructor/PhysicalAssessment.vue`: role-specific wrappers around the shared assessment page.
- `frontend/src/router/index.js`: protected assessment routes and the manager participant list route.
- `frontend/public/testing-guides/tug.pdf`, `chair-stand.pdf`, `balance.pdf`: supplied reference instructions, copied without modification.
- `frontend/tests/physical-tests.test.js`, `frontend/tests/apis.test.js`: protocol payload/display tests and API retry behaviour.
- `Documentation/backend/physical-assessments.md`: implementation and manual testing guide.

## Verification

```sh
.venv/bin/python backend/manage.py test physical_tests participants reporting sessions users llm
node --test frontend/tests/*.test.js
npm --prefix frontend run build
```

For a manual stopping-rule check, record TUG, select chair **Arms needed to stand**, and record five seconds for the first balance position. Later positions should become unavailable and save as skipped, not zero. Complete the assessment and confirm the profile history shows those distinctions. Open a draft in two tabs and save one; the stale tab should receive a conflict rather than overwrite it. Verify another branch's participant and assessment URLs cannot be read.
