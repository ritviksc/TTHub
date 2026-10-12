# Absence reasons in attendance analysis

Attendance statistics now include `absence_reasons` for the entire selected period and for each month. The saved analysis snapshot and LLM prompt contain the same calculated breakdown.

Each breakdown contains `total_absences` and entries with `reason`, `label`, `count` and `percent_of_absences`. Categories follow the current attendance model: No show, Medical appointment, Transport issue and Other. Blank or unrecognised values are combined as Not recorded or unrecognised; unknown raw values are never sent to the provider.

Only absent records in finalised sessions within the authorised branch/date scope count. This includes finalised sessions where everyone was absent. Incomplete sessions and present records are excluded. Counts represent missed session places, not distinct people. Percentages use all counted absences, including missing reasons; when there are no absences, percentages are null. Rounded shares may not add to exactly 100%.

The prompt asks for the overall breakdown and supported monthly comparisons without guessing missing reasons or interpreting the Other category. Participant/session identifiers and free-text Other notes remain excluded. Existing saved snapshots without the breakdown send null rather than incorrectly reporting zero absences.

The existing grouped session query calculates reason counts, so query count does not grow with session count. No database migration is needed.

Changed files:

- `backend/reporting/services/attendance.py`: grouped reason counts, monthly/overall breakdowns and interpretation limitations.
- `backend/reporting/prompts/attendance.py`: aggregate payload and instructions to explain the split.
- `backend/reporting/tests.py`: scope, completion, zero-denominator, legacy-snapshot and privacy regression checks.
- This document records the counting rules.

To verify manually, finalise a session with several absent participants and different reasons. Request a new attendance explanation for that date range. Check its reason counts against the register. An incomplete register in the same period must not contribute, and free-text Other notes must not be included in the prompt. Existing generated narratives are not regenerated automatically.
