# Participant detail and file storage

The existing `/participants/:id` page now displays and edits participant contact
details, emergency contacts, general notes, photo consent, GP consent and active
status. Attendance history is retained for inactive participants. Its summary
excludes future sessions; existing attendance records default to absent until an
instructor updates them. All current staff roles retain the existing ability to
edit basic details, record photo consent, and deactivate accessible participants.

Super Admins following the consent/photo link are redirected to
`/super-admin/participants/:id`. The Details and Attendance history buttons next
to the participant identity navigate between that page and
`/super-admin/participants/:id/attendance`. Instructors have the same split at
`/instructor/participants/:id` and `/instructor/participants/:id/attendance`, with
GP consent still read-only. Branch Managers retain the combined page.

GP and photo consent dates must be today or earlier in Pacific/Auckland time.
Both date pickers have an upper bound and the API rejects future dates.

New sessions must use today's date or a future date in Pacific/Auckland time.
The date picker and API both enforce this. This is a calendar-date restriction;
today remains available regardless of the selected time.

Super Admins may upload/download GP documents across branches. Branch Managers
may do so for their own branch. Instructors see GP consent status/date but cannot
upload/download the document or see its upload metadata. Files are optional;
uploading one does not change consent status, and existing consent records do not
require a document. Supported uploads are PDF, JPG/JPEG and PNG up to 10 MB.
Validation checks extensions, PDF signatures and decodable image content. It is
not malware scanning or verification of the document's medical contents.

## Storage and deployment

- PostgreSQL (or SQLite locally) stores file keys and consent/upload metadata.
- GP documents use Django's `private` storage alias, currently backed by
  `backend/private_media/`. This directory is ignored by Git.
- Photos keep their existing storage and keys in `backend/media/`; no existing
  photo files need moving for this change.
- Both file types are served through authenticated participant API endpoints.
  Photos require current photo consent. File responses use `private, no-store`.
  The former public development `/media/` route is removed.
- Do not configure a web server to publicly serve either upload directory.
  Production object storage must also use private buckets for both aliases.
- Switching to object storage means configuring Django's `default` and `private`
  storage aliases, installing the chosen provider's adapter, and copying existing
  files while preserving their keys. The file endpoints use storage `open()`,
  not local filesystem paths, so their permission checks remain in place.
- Back up the database and both file stores. A database migration alone does not
  transfer uploaded files. Replaced files are retained in storage by Django;
  only the current document is downloadable through this API. Retention/version
  management is not implemented by this change.

## Local setup and review

From the repository root, run `.venv/bin/python backend/manage.py migrate`, then
start/restart the backend and frontend normally. No new packages are needed.

1. Log in as Super Admin, open Participants, then the existing consent/photo link.
   Check the name, branch, contact fields and active status on Details. Click
   Attendance history beside the name: only history and totals should appear.
   Click Details to return; refresh either page to verify its direct URL works.
2. Edit contact details, record a consent date, select a PDF/JPG/PNG document and
   save. Reload the page and download the document; confirm its contents match.
3. Replace the document, and try an unsupported or over-10-MB file. Confirm an
   error appears and the previously saved document remains available.
4. Log in as Branch Manager and open `/participants/<id>` for a participant in
   their branch. Verify upload/download. A participant ID from another branch
   must return a not-found error. The Branch Manager list is still a separate
   pending feature, so use a known participant detail URL for this review.
5. Log in as Instructor and open a participant from their Participants list.
   Check that GP status/date are visible but document controls are absent.
   GP-document requests must be forbidden, even with a known endpoint URL.
   Use Details and Attendance history beside the name to switch pages. Refresh
   each URL and check that it stays within the instructor section.
6. Upload/replace a participant photo with consent, then withdraw photo consent
   and save. The photo disappears; the old protected photo link returns 404.
7. Check a participant with no past sessions, and one with present/absent records.
   On a disposable participant, confirm deactivation preserves existing history.
8. Stop the backend and reload the page to check the load-error state.
9. As Instructor, open Sessions and New session. Yesterday must be unavailable
   in the date picker; today and tomorrow must be accepted. A direct API POST
   with a past date must return a date error without creating a session.
10. As Super Admin or Branch Manager, record GP/photo consent and open each date
    picker. Tomorrow must be unavailable, while today and earlier dates work.
    Repeat photo consent as Instructor; GP consent remains read-only. Manually
    entering a future date must prevent saving.

## Files changed

- `backend/participants/models.py`: document reference and uploader/time metadata.
- `backend/participants/storage.py`: private storage alias and random file keys.
- `backend/participants/migrations/0003_participant_gp_consent_document_and_more.py`:
  database fields; no existing participant data is removed.
- `backend/participants/serializers.py`: document validation, upload metadata,
  role restrictions and protected photo URLs.
- `backend/participants/views.py`: permission-checked files and attendance history.
- `backend/participants/urls.py`: photo, document and attendance endpoints.
- `backend/participants/tests.py`: upload, file-access, validation and history tests.
- `backend/config/settings.py`: local private file storage configuration.
- `backend/config/urls.py`: remove public media serving.
- `backend/sessions/serializers.py`: attendance photos use the protected endpoint.
- `.gitignore`: exclude private uploads.
- `frontend/src/apis.js`: authenticated document and attendance requests.
- `frontend/src/views/ParticipantConsent.vue`: retain the URL with a shared detail
  component and explicit GP-edit permission prop.
- `frontend/src/components/participants/ParticipantDetail.vue`: participant form,
  document actions, photos and deactivation confirmation.
- `frontend/src/components/participants/ParticipantAttendance.vue`: history and totals.
- `docs/backend/participant-detail-and-files.md`: storage and review instructions.

Follow-up files for the date restriction and separate Super Admin pages:

- `backend/sessions/serializers.py`: reject past dates at session creation.
- `backend/sessions/tests.py`: API rejection and today/future acceptance,
  including when New Zealand's date differs from UTC.
- `frontend/src/utils/sessions.js`: shared New Zealand date helper.
- `frontend/src/components/sessions/CreateSessionModal.vue`: minimum selectable
  date, submit-time check and server date-error display.
- `frontend/src/components/participants/ParticipantDetail.vue`: navigation and
  separate details/history rendering, reusing the existing form and history.
- `frontend/src/views/SuperAdmin/ParticipantDetail.vue`: Details page wrapper.
- `frontend/src/views/SuperAdmin/ParticipantAttendance.vue`: history page wrapper.
- `frontend/src/router/index.js`: protected Super Admin routes and compatibility
  redirect for existing consent/photo links.

Instructor-page and consent-date follow-up:

- `frontend/src/views/Instructor/ParticipantDetail.vue` and
  `frontend/src/views/Instructor/ParticipantAttendance.vue`: role-specific wrappers
  using the shared participant UI with instructor navigation and permissions.
- `frontend/src/router/index.js`: instructor routes and existing-link redirect.
- `frontend/src/components/participants/ParticipantDetail.vue`: configurable
  navigation route prefix, consent date limits and submit-time validation.
- `backend/participants/serializers.py`: use New Zealand's current date for both
  existing consent-date validations.
- `backend/participants/tests.py`: test past/today/future consent dates for every
  authorized role at a New Zealand/UTC date boundary.
- `docs/backend/participant-detail-and-files.md`: updated review instructions.
