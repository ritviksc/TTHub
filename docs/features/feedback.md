# Qualitative feedback

All staff roles use the shared `frontend/src/views/Feedback.vue` screen. Branch Managers and Instructors see and record feedback for their own branch. Super Admins work nationally with a branch filter and a branch selector in the recording form.

## Recording and finding entries

Each entry contains a quote or short story, date, reporting consent and the original speaker’s type: Kaumātua, Kaimahi, Whānau or Unknown. The speaker type is separate from the related participant/session and the recording staff member. Existing entries without a speaker classification remain Unknown.

At least one related kaumātua or session is required. When both are selected, they must belong to the same branch. The backend derives the branch from the subject and sets `recorded_by` from the authenticated request; the client cannot supply either identity. Dates cannot be in the future.

For Super Admins, choose a branch before subjects; changing it clears old participant/session selections. A current national branch filter prefills the form’s branch. Failed saves retain the draft, and pending saves block repeated submission and dismissal.

Combine All / With quote consent / Without consent with text search. Super Admins can also filter by branch. Entries show their saved source label, speaker type, date, author and, nationally, branch name. The source label is captured when recorded rather than derived later from changing participant details.

## Consent and ACC evidence

Only consented entries in the selected reporting period and branch scope are offered for ACC preparation. The reviewer works on copies, redacts identifying details and approves the selection for ACC reporting and AI processing. The saved speaker type carries through automatically. See [ACC reporting](acc-reporting.md).

Saved feedback cannot currently be edited or deleted through the app. Check its subject, quote, date, speaker and consent before saving. Linked participants and sessions are protected from deletion; a session with saved feedback returns a conflict when deletion is attempted.

## API and checks

`GET` and `POST /api/participants/feedback/` list and create authorised entries. Scope and subject validation run in `backend/participants/views.py` and `serializers.py`. The Feedback model enforces at least one subject at database level.

From backend: `python manage.py test participants reporting`. From frontend: `node --test tests/feedback.test.js tests/acc-reporting.test.js`.
