# Physical assessment recording

Staff record three strength and balance tests for each participant: timed up and go (TUG), chair stand and balance. The results build up a history that is compared over time and used in [physical reporting](physical-reporting.md).

## Recording an assessment

1. Open a participant's **Details** page. The physical assessment section is on it.
2. Select **Start physical assessment**. If a draft already exists, the button reads **Continue assessment**, and starting twice resumes the same draft.
3. Check the assessment date and save any change before recording exercises.
4. Select **Record / edit results** for TUG, chair stand or balance. Read the instructions, record the results and save. Closing the popup without saving discards only that popup's edits.
5. When every exercise group is reviewed, complete the assessment. Completed assessments are read-only.

Results are saved as you go and survive a reload. Each exercise popup links to the original testing guide PDF in `frontend/public/testing-guides/`. These are blank public guides, not participant records.

## Measurements and completion rules

One assessment has six results: TUG seconds, a chair-stand count, and seconds for each of four balance positions.

- **TUG** needs a positive time. A walking aid and observations can be recorded.
- **Chair stand** needs a whole count of zero or more. **Arms needed to stand** records zero with that outcome, following the testing sheet.
- **Balance** positions follow the set order. Each time is 0–10 seconds, and only a full 10-second hold unlocks the next position. Every position after a stop is saved as `skipped`, with no number.
- **Unable / stopped for safety** needs a reason and has no number. It is a valid recorded outcome, including when a test is avoided for safety.
- **Not attempted** needs a reason and keeps the assessment incomplete. It is different from a balance position skipped under the protocol.

An assessment can be completed once all six outcomes are recorded and none is `not_attempted`. Completed means the record is complete, not that the participant managed every exercise; reports show inability outcomes separately from measurements.

The assessment date is used for date-range reporting. It can't be in the future or before the participant's birth. The system doesn't generate clinical risk ratings or diagnoses.

Completed assessments can't be reopened or corrected.

## Access

All three staff roles can record assessments. Instructors and branch managers see only assessments from their current branch for participants currently in that branch. Super admins see everything.

- When a participant moves branch, their old assessments stay with the old branch and only super admins can see them. Records aren't transferred.
- An unfinished draft at the old branch must be resolved by a super admin before a new draft can be started at the new branch.
- Inactive participants can't start new assessments, but their saved assessments stay visible.
- A branch with historical assessments can't be deleted.

## Edit conflicts

Every save sends the version it last read. If someone else saved in between (for example in a second tab), the server returns HTTP 409 and nothing is overwritten. Reload the assessment and try again.

## API

Under `/api/physical-tests/`:

| Endpoint | Purpose |
| --- | --- |
| `GET participants/<participant-id>/` | Assessment history the user may see |
| `POST participants/<participant-id>/` | Start or resume a draft |
| `GET <assessment-id>/` | Read a draft or completed assessment |
| `PATCH <assessment-id>/` | Save `assessed_on` with `version` |
| `PUT <assessment-id>/results/<group>/` | Save a whole group (`tug`, `chair`, `balance`) with `results` and `version` |
| `POST <assessment-id>/complete/` | Complete a valid draft with `version` |

## Tests

From `backend/`: `python manage.py test physical_tests`. From `frontend/`: `node --test tests/physical-tests.test.js`.

To check the stopping rule by hand: record TUG, choose chair **Arms needed to stand**, and record five seconds for the first balance position. The later positions should become unavailable and save as skipped, not zero.

## Key files

- `backend/physical_tests/models.py`: `Assessment` and `ExerciseResult`
- `backend/physical_tests/serializers.py`: measurement, date and balance-order rules
- `backend/physical_tests/views.py`: draft, result and completion endpoints
- `frontend/src/components/physicalTests/AssessmentHistory.vue`, `AssessmentPage.vue`, `ExerciseModal.vue`: profile section, assessment page and result entry
- `frontend/src/utils/physicalTests.js`: labels, instructions and payloads
