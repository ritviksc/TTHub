# Participant details and files

Each participant has a **Details** page and an **Attendance history** page. Buttons next to the participant's name switch between them.

| Role | Details | Attendance history |
| --- | --- | --- |
| Super admin | `/super-admin/participants/:id` | `/super-admin/participants/:id/attendance` |
| Branch manager | `/branch-manager/participants/:id` | `/branch-manager/participants/:id/attendance` |
| Instructor | `/instructor/participants/:id` | `/instructor/participants/:id/attendance` |

The shared link `/participants/:id` redirects to the signed-in user's own page.

## Details

The Details page shows and edits contact details, emergency contacts, general notes, photo consent, GP consent and active status. It also holds the participant's physical assessments (see [physical-assessments.md](physical-assessments.md)) and documents (see [document-storage.md](../backend/document-storage.md)).

- All staff roles can edit basic details, record photo consent and deactivate participants they can see.
- Super admins and branch managers record GP consent. Instructors see the GP consent status and date but can't change them or see the document.
- Deactivating a participant keeps their attendance history.

## Attendance history

The history lists past sessions with totals. Future sessions are left out of the summary. Attendance records default to absent until an instructor marks them.

## Date rules

All dates use New Zealand time (Pacific/Auckland).

- GP and photo consent dates must be today or earlier. The date pickers stop at today and the API rejects future dates.
- New sessions must be today or later. The date picker and the API both enforce this, and today is always allowed whatever the time.

## GP consent documents

Super admins can upload and download GP consent documents for any branch, and branch managers for their own branch. Instructors can't upload or download them, or see who uploaded them.

- The document is optional. Uploading one doesn't change the consent status, and a consent record doesn't need a document.
- PDF, JPG/JPEG and PNG up to 10 MB are accepted. The extension, PDF signature and image content are checked. This isn't malware scanning or a check of the medical content.
- Replacing a document keeps the old file in storage, but only the current one can be downloaded.

## Photos

A participant photo is only shown while the participant has photo consent. Withdrawing consent hides the photo, and its link returns 404.

## Storage

- The database (SQLite) stores file keys and consent and upload metadata.
- GP documents use Django's `private` storage (`backend/private_media/`). Photos use `backend/media/`. Git ignores both folders.
- Both are served only through authenticated participant endpoints that return `Cache-Control: private, no-store`. Never configure a web server to serve either folder publicly.
- Backups need the database **and** both file folders. The database alone doesn't contain the files.

## How to check it

1. As a super admin, open a participant. Edit contact details, record a consent date, attach a PDF and save. Reload and download the document.
2. Try an unsupported or over-10 MB file. An error appears and the saved document is still there.
3. As a branch manager, open a participant in your branch and check upload and download. A participant from another branch returns not found.
4. As an instructor, check the GP status is visible but the document controls are absent, and GP-document requests are refused.
5. Withdraw photo consent and save. The photo disappears.
6. Check that tomorrow can't be picked for a consent date, and yesterday can't be picked for a new session.

Automated tests: `python manage.py test participants sessions`.

## Key files

- `backend/participants/models.py`, `serializers.py`, `views.py`: participant fields, validation, file and history endpoints
- `backend/participants/storage.py`: private storage and random file names
- `backend/sessions/serializers.py`: session date rule
- `frontend/src/components/participants/ParticipantDetail.vue`: details form, documents, photo and deactivation
- `frontend/src/components/participants/ParticipantAttendance.vue`: attendance history
- `frontend/src/router/access.js`: redirect from `/participants/:id`
