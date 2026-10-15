# Absence reasons in attendance analysis

Attendance statistics include `absence_reasons` for the whole selected period and for each month. The saved analysis snapshot and the AI prompt use the same breakdown.

Each breakdown has `total_absences` and a list of entries with `reason`, `label`, `count` and `percent_of_absences`. The categories are No show, Medical appointment, Transport issue and Other. Blank or unrecognised values are grouped as **Not recorded or unrecognised**, and unrecognised raw values are never sent to the provider.

## Counting rules

- Only absent records in finalised sessions inside the authorised branch and date range count, including finalised sessions where everyone was absent.
- Incomplete sessions and present records are excluded.
- Counts are missed session places, not distinct people.
- Percentages are out of all counted absences, including those with no reason. With no absences, the percentages are null.
- Rounded shares may not add up to exactly 100%.

Reason counts come from the same grouped query as the rest of the attendance statistics, so the number of queries doesn't grow with the number of sessions.

## What the AI receives

The prompt asks for the overall breakdown and for monthly comparisons the data supports, without guessing missing reasons or interpreting the Other category. Participant and session identifiers and the free-text notes for Other are never sent. Snapshots saved before the breakdown existed send null, not zero.

## How to check it

Finalise a session with several absent participants and different reasons, then request an attendance explanation for that date range. The reason counts should match the register. An incomplete register in the same period must not count, and Other notes must not appear in the prompt.

## Key files

- `backend/reporting/services/attendance.py`: reason counts and breakdowns
- `backend/reporting/prompts/attendance.py`: AI payload and instructions
- `backend/reporting/tests.py`: tests
