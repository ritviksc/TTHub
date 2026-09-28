# Document storage

Staff can store files in three places. Each place has its own access rules:

| Scope | Who sees it | Who uploads | Who creates folders, renames, moves, deletes |
| --- | --- | --- | --- |
| Organisation | All staff | Super Admin | Super Admin |
| Branch | Staff at that branch, and Super Admin | Staff at that branch, and Super Admin | That branch's Branch Manager, and Super Admin |
| Participant | Anyone who can see the participant | Same | That branch's Branch Manager, and Super Admin |

Organisation and branch files can be organised into nested folders. Participant files are a flat list, shown on the participant's profile.

## Using the feature

1. Run migrations (`python manage.py migrate`). The `documents` app adds the `Document` and `Folder` tables.
2. Sign in and open **Documents** in the nav. The sidebar shows **Organisation** and one branch. A Super Admin switches branch with **Change ▾**, which offers search, recently opened branches, and branches grouped by region.
3. **Upload** accepts several files at once, or you can drag files onto the list. Click a folder to open it, or click a file to download it. Each row has a **⋯** menu with Rename, Move and Delete, which only appears for people allowed to use it.
4. On a participant's profile, the **Documents** card lists that participant's files.

Accepted types are PDF, JPG, PNG, DOCX and XLSX, up to 10 MB each. The file's contents are checked against its extension.

## How files are stored

Files are saved to the `private` storage alias (`backend/private_media/documents/`) under a random filename. This location is never served publicly. The original filename is kept in `Document.name`. Downloads go through an authenticated endpoint that returns `Cache-Control: private, no-store`, which is the same approach as GP consent documents.

A document's scope comes from its foreign keys. If `participant` is set it is a participant file, if `branch` is set it is a branch file, and if neither is set it is an organisation file. `Folder.branch` works the same way, with `None` meaning organisation. Database constraints stop a document from having both a branch and a participant, and stop a participant document from being in a folder. `PROTECT` on folder relations means a folder can only be deleted once it is empty.

## Backend (`backend/documents/`)

| File | Purpose |
| --- | --- |
| `models.py` | `Document` and `Folder` |
| `permissions.py` | `documents_for` and `folders_for` (the querysets a user may see), `can_upload`, and `can_manage_scope`, the single rule for create, rename, move and delete |
| `validators.py` | `validate_upload`: size limit and file-type checks. Also used by the GP consent upload |
| `folder_rules.py` | Unique names among sibling folders, no moving a folder into itself, moves stay within one scope |
| `serializers.py` | Read, upload and folder shapes. Rename keeps the file extension. Each item includes `can_manage` for the UI |
| `views.py`, `urls.py`, `folder_urls.py` | The endpoints below |
| `tests.py` | Access, upload, download, delete, validation and folder tests |

Every view starts from `documents_for` or `folders_for`, so an out-of-scope item returns 404 rather than 403.

| Endpoint | Purpose |
| --- | --- |
| `GET /api/documents/?branch=\|participant=\|scope=organisation&folder=<id>\|root` | List files |
| `POST /api/documents/` | Upload (multipart: `file`, plus one of `branch`, `participant`, `folder`) |
| `PATCH /api/documents/<id>/` | Rename (`name`) or move (`folder`) |
| `DELETE /api/documents/<id>/` | Delete |
| `GET /api/documents/<id>/download/` | Download the file |
| `GET /api/folders/?branch=<id>` or `?scope=organisation` | Every folder in that scope, as a flat list |
| `POST /api/folders/` | Create (`name`, `parent`, `branch`). A subfolder inherits its parent's branch |
| `PATCH /api/folders/<id>/` | Rename (`name`) or move (`parent`) |
| `DELETE /api/folders/<id>/` | Delete. Returns 409 while the folder has contents |

## Frontend

| File | Purpose |
| --- | --- |
| `src/apis.js` | Document and folder API calls. GETs retry on timeout, writes never do, and uploads use a 60 s timeout |
| `src/utils/documents.js` | Pure helpers for building the folder tree, breadcrumb, move exclusions, region grouping and recent branches |
| `src/components/documents/FileExplorer.vue` | The explorer: sidebar, breadcrumb toolbar, combined folder and file list, upload and drag-and-drop, row menus, name and move dialogs |
| `src/components/documents/FolderTree.vue` | Expandable folder tree, used in the sidebar and the move dialog |
| `src/components/documents/BranchSwitcher.vue` | Branch picker with search, recents (in `localStorage`) and region groups |
| `src/components/documents/DocumentList.vue` | Flat list used on the participant profile |
| `src/views/Documents.vue` | `/documents` page. Builds the explorer's `scopes` from the signed-in user's role and keeps the selected branch in `?branch=` |

`FileExplorer` takes a `scopes` prop, which is a list of `{ key, label, region, branchId, canUpload, canManage }`. It loads all folders for the open scope in one request and builds the tree on the client, since each branch only has a few folders. It loads files one folder at a time, and discards stale responses if the user clicks faster than the network. The Super Admin branch page (`views/SuperAdmin/BranchDetail.vue`) reuses it with a single scope.

## Tests

- Backend: `python manage.py test documents`
- Frontend: `node --test tests/*.test.js` (see `tests/documents.test.js` and `tests/apis.test.js`)
