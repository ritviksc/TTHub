# ACC reporting drafts

Super admins open **Reporting → Prepare ACC report**, choose inclusive dates (or a branch quarter), and select consented feedback. The source list is paginated and selections persist across pages. Each reporting copy can be redacted and attributed to a participant, whānau, kaimahi, or unknown speaker. The super admin must confirm approval for ACC reporting and AI processing; changing any selected copy or attribution clears that confirmation.

The backend checks dates, branch, consent, approval, model selection, and input size before queueing. A draft accepts 1–100 sources, at most 4,000 characters per copy and 40,000 characters total. Narrow the selection if these limits are reached; sources are never silently truncated.

The saved snapshot includes the reviewed copies, original text for internal review, approval actor/time, and calculated participation, enrolment, and physical-testing aggregates. The provider receives only reviewed copies with source IDs, date, speaker label, branch name, reporting scope, and the aggregate allowlist. Original feedback, participant names/records, contact details, individual assessments, and engagement percentages are not included in the provider payload. Free-text redaction is a human review step, not automatic anonymisation.

`reporting/prompts/acc.py` contains the fixed instruction prompt and request builder. One low-temperature generation call aims for 300–500 words (less when evidence is limited), supported sections, up to four original excerpts, and review notes. Categories without evidence should be omitted. The backend validates the JSON shape, recognised section titles, source IDs, and exact quote matches before rendering Markdown. Sections returned with empty source lists are omitted and flagged in review notes; their uncited prose is never included. A draft must retain at least one cited section. Unknown source IDs, invented quotations, and other invalid responses still fail the job. This validation cannot prove that a narrative claim is factually supported: the reviewer must check it against the linked sources.

Jobs use the existing Celery queue, deadlines, polling, safe failure messages, and audit events. Before contacting the provider, the worker rechecks the requesting user's role and selected feedback consent/scope. Successful drafts appear in **View past ACC reports**, where any super admin can inspect and edit the saved narrative. Editing does not change source statistics or constitute approval/submission to ACC. No automatic submission or export is added.

Endpoints (all super-admin only):

- `GET /api/reporting/acc/sources/` — dates, optional branch, and page.
- `POST /api/reporting/acc/analyse/` — scope, model, reviewed sources (`id`, `text`, `speaker`), and `approved_for_acc_and_ai`.
- `GET/PATCH /api/reporting/acc/jobs/<id>/` — requester polling / super-admin narrative editing.
- `GET /api/reporting/acc/history/` and `history/<id>/` — completed drafts and saved evidence.

Apply the database migration with `python manage.py migrate`, and restart existing Celery workers to register `reporting.tasks.generate_acc_analysis` when deploying. No new dependencies are required.

Validation: `python manage.py test reporting audit`; from `frontend`, `node --test tests/acc-reporting.test.js tests/report-narrative.test.js tests/report-history.test.js` and `npm run build`. Tests mock the provider and do not send feedback externally.
