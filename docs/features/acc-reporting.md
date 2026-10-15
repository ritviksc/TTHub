# ACC reporting drafts

Super admins can prepare a draft report for ACC from consented participant feedback, attendance and physical-testing figures. The AI writes the narrative. A person reviews, edits and exports it. Nothing is sent to ACC automatically.

## Recording feedback

When entering feedback, staff record **Who gave this feedback?**: Kaumātua, Kaimahi, Whānau or Unknown. This is stored in `Feedback.speaker`, separately from the related participant, session and the staff member who recorded it. The same label appears in the feedback list, ACC source selection, review rows and saved reports.

## Preparing a report

1. Open **Reporting → Prepare ACC report**.
2. Choose inclusive dates (or a branch quarter) and optionally a branch.
3. Select consented feedback. The list is paginated and selections are kept across pages.
4. Review each copy and redact it if needed. The speaker type is taken from the saved feedback, not chosen here.
5. Confirm approval for ACC reporting and AI processing. Changing a selection or a reviewed copy clears that confirmation.
6. Choose a model and generate the draft.

Before queueing, the backend checks dates, branch, consent, approval, model and size. A draft takes 1–100 sources, at most 4,000 characters per copy and 40,000 in total. Narrow the selection if a limit is reached; sources are never cut off silently.

## Engagement table

The first section, **Engagement**, has one row for every branch in scope (all branches when no branch is selected, including branches without feedback or attendance):

| Column | Meaning |
| --- | --- |
| Entity, Location | Branch name and `Branch.region` (shows Not recorded when missing) |
| # Participants | Active registrations joined by the report end date, including unknown joined dates |
| # New Participants | Joined dates inside the period, including people now inactive; unknown dates are excluded |
| % Engagement | Total attendances ÷ total roster places across finalised sessions × 100, rounded to the nearest 5 (halves round up) |

Engagement is weighted by session places, not an average of session rates. For example, 85.06% shows as 85% and 87.5% as 90%. Incomplete registers are excluded. With no finalised sessions it shows Not available. A finalised register where everyone was absent gives 0%, and rates below 2.5% also round to 0%. Because membership is current, the table can't reconstruct an exact historical roster.

## What the AI receives

The provider receives only the reviewed copies (with source ID, date, speaker label, branch name), the reporting scope, and an allowlist of aggregate figures, including the engagement table with its definitions and limitations. Original feedback, participant names and records, contact details and individual assessments are never sent. Redaction is a human review step, not automatic anonymisation. The AI may quote the engagement figures but doesn't create the table or infer health outcomes from attendance.

The saved snapshot keeps the reviewed copies, the original text for internal review, who approved it and when, and the calculated aggregates.

## Narrative and validation

`backend/reporting/prompts/acc.py` holds the instructions. One low-temperature call (up to 6,000 output tokens) aims for 300–500 words of summary in total, not counting quotations, and less when the evidence is thin. Each section has its own supporting quotations (1–3 preferred, no hard cap), a summary and its source IDs. It renders as the heading, **Supporting quotations**, then **Summary**. Categories without quotable evidence are left out.

The backend checks section titles, source IDs, that every quotation exactly matches its source, and that each quotation's source is cited by its section. Every section needs at least one quotation, and a draft needs at least one cited section. Sections with no sources are dropped and flagged in the review notes. Unknown source IDs or invented quotations fail the job. These checks can't prove a quotation is relevant to its section, so the reviewer must check the evidence.

Source IDs are used only for validation. They aren't shown in the report, the editor, the statistics or the saved feedback.

## Reviewing and exporting

Drafts run through the Celery worker, with the same deadlines, polling, safe failure messages and audit events as other reports. Before contacting the provider, the worker checks the requester's role and each source's consent and scope again.

Finished drafts appear in **View past ACC reports**, where any super admin can read and edit the narrative. Editing doesn't change the saved statistics and isn't approval or submission.

**Download PDF** opens a print view and the browser's print dialog, where you choose **Save as PDF**. The export includes saved edits, reviewed feedback, figures and limitations. It leaves out navigation, controls and the original unredacted feedback. The button is disabled while editing. Allow pop-ups if the print view is blocked. Exporting makes no AI call or backend request.

## API

All endpoints are super-admin only:

| Endpoint | Purpose |
| --- | --- |
| `GET /api/reporting/acc/sources/` | Consented feedback for the dates, optional branch and page |
| `POST /api/reporting/acc/analyse/` | Queue a draft: scope, model, reviewed sources (`id`, `text`) and `approved_for_acc_and_ai` |
| `GET`/`PATCH /api/reporting/acc/jobs/<id>/` | Poll a draft, or edit its narrative |
| `GET /api/reporting/acc/history/` and `history/<id>/` | Finished drafts and their saved evidence |

## Tests

From `backend/`: `python manage.py test reporting audit`. From `frontend/`: `node --test tests/acc-reporting.test.js tests/report-narrative.test.js tests/report-history.test.js`. The provider is mocked, so no feedback is sent anywhere.

## Key files

- `backend/reporting/services/acc.py`: sources, engagement table, snapshot and validation
- `backend/reporting/prompts/acc.py`: prompt and request builder
- `backend/reporting/tasks.py`: `generate_acc_analysis`
- `frontend/src/views/SuperAdmin/ACCReporting.vue`, `ReportHistory.vue`: preparing and reviewing drafts
