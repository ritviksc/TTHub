# Physical reporting and demonstration data

## Reporting pages

The super admin **Reporting** page (`/super-admin/reporting`) and branch manager **Reports** page (`/branch-manager/reports`) now offer two explained choices:

- **Attendance:** opens `/attendance` beneath the reporting route. Existing attendance statistics and Celery analysis are retained.
- **Physical testing:** opens `/physical` beneath the reporting route. Shows a date-range completion summary, participant Yes/No and assessment counts, individual result graphs, exercise means/outcome counts, monthly graphs, paired changes and optional Celery analysis.

Both reports load current-quarter statistics automatically and allow inclusive custom dates. Super admins can select one branch or all branches. Managers are limited to their own branch. Instructors can record and view their branch participants' assessment histories and graphs, but cannot open aggregate reporting or request AI analysis.

## Calculation rules

The report starts from participants, not just assessment records, so an eligible person without tests appears as **No**. The roster includes currently active participants whose joined date is on/before the selected end date (unknown dates included), plus inactive participants with completed assessments in the selected period. It uses current branch membership and excludes assessment records from an earlier branch following a transfer. The system does not yet keep a full enrolment/exit history, so this is explicitly a current-roster report, not a reconstruction of historical membership.

**Yes** means at least one completed assessment within the date range. Count means completed assessment occasions, not individual exercises. Drafts are counted separately and excluded from measurements. Completion denotes a fully recorded assessment, including valid inability outcomes; it does not mean every exercise was successfully performed.

Numeric means include scored outcomes (`measured` and chair `arms_used`, which is zero). Unable and skipped outcomes are separately counted and have no numerical value. Monthly means weight assessment occasions, so repeated tests count more than once and contributing people can differ between months.

Paired changes compare each person's first and last scored results on different dates within the selected range, separately for each exercise. Endpoint outcomes must match. TUG also requires equal walking-aid descriptions after trimming/case normalization. Change is last minus first; no change is inferred from one measurement. The aggregate paired mean gives each comparable person one contribution and reports the sample size. These checks do not establish that all testing conditions were identical; results are descriptive, not clinical interpretation or causal evidence.

Graphs use actual date spacing. Missing/unperformed results break the line, while explicitly scored zeros remain zero. Exact values are available below each graph. Individual graphs also appear on the participant profile for instructors, managers and admins.

## Celery and privacy

`GET /api/reporting/physical/` calculates statistics in Django. `POST /api/reporting/physical/analyse/` saves a `PhysicalAnalysisJob` snapshot and queues `reporting.tasks.generate_physical_analysis` with only its UUID. The frontend polls `GET /api/reporting/physical/jobs/<uuid>/` and then displays the saved snapshot with its Markdown explanation. No completed assessments means no provider call.

Physical and attendance analysis share the abstract job model, queue helper, permission/status checks and worker execution helper. Existing attendance table and URLs are preserved. The requesting account must retain access to the job's branch. Queue errors return a safe 503; provider failures save a safe error. Duplicate delivery cannot claim the same job twice. Expiry prevents endless polling. Jobs protect their branch from deletion and currently have no automated retention policy.

Only whitelisted aggregate totals, exercise summaries, monthly summaries, paired changes and limitations enter the LLM prompt. Participant names/IDs, assessment IDs, DOB, notes and walking-aid descriptions are excluded. Names and individual measurements remain in the authorised application report/snapshot. The prompt prohibits diagnosis, clinical risk classification, invented causes and programme-effectiveness claims. The UI labels AI output as variable and requiring review.

Start or restart the worker after these changes, using `./scripts/dev.sh` or the commands in [celery-setup.md](celery-setup.md). No live provider call is made by seeding or automated tests.

## Load fictional demo data

From the repository root:

```sh
.venv/bin/python backend/manage.py migrate
.venv/bin/python backend/manage.py seed_reporting_demo
```

This creates a dedicated dataset, without modifying existing non-demo records:

- Branches **DEMO Harbour** and **DEMO Hills**.
- One application super admin, two branch managers and two instructors.
- 24 clearly named fictional participants, ages roughly 55–77 at initial seeding.
- 24 weekly sessions across the preceding 12 weeks, with deterministically random attendance. Includes finalised empty sessions and incomplete registers.
- 50 completed assessments, two drafts and four participants without assessment records. Each branch has nine people with completed testing, one draft-only person and two untested people.
- Repeated measurements with increases, decreases, chair-arm zeros, inability outcomes and skipped balance stages.

The command runs only with `DEBUG=True`. It uses stable IDs and a fixed random seed. Reruns preserve existing records, edits, passwords and the initial dataset dates. There is no destructive clear option. An optional `--as-of YYYY-MM-DD` sets the initial last-session date; future dates and changing an existing dataset's anchor are rejected. It does not invoke the old `seed_test_data` command, which has different behaviour.

New demo accounts use **`DemoReports123!`**:

| Role | Email |
| --- | --- |
| Super admin | `demo.admin@example.com` |
| Harbour manager | `demo.manager.harbour@example.com` |
| Harbour instructor | `demo.instructor.harbour@example.com` |
| Hills manager | `demo.manager.hills@example.com` |
| Hills instructor | `demo.instructor.hills@example.com` |

The super admin is the application's `super_admin` role, not a Django superuser. Participants are not login accounts.

## Manual verification

1. Start `./scripts/dev.sh` and sign in using the demo admin.
2. Open Reporting. Verify the two choices and open each report.
3. Select **DEMO Harbour** and use the date range printed by the seed command. Physical totals should initially be 12 eligible, 9 tested, 3 untested, 75% completion, 25 completed assessments and one draft. Each branch has 12 sessions, ten finalised (including one empty) and two incomplete registers.
4. Click **View results** for a participant and switch graph exercises. Open that participant's profile to view the full assessment history.
5. Click **Analyse physical testing** with Redis, the worker and LLM configured. Observe queued/running progress and then Markdown text. Statistics work without the LLM.
6. Sign in as the Harbour manager. Confirm the branch picker is absent and requests for Hills data are denied. Sign in as an instructor to view participant graphs; aggregate report routes should be denied.
7. Run the seed command again. Counts and any existing edits should remain unchanged.

For both demo branches together, the initial physical totals are 24 eligible, 18 tested, 6 untested, 75% completion, 50 completed assessments and two drafts. A national report may also include other records already in your database.

## Implementation files

- `backend/reporting/services/scope.py`, `services/attendance.py`: extract shared date/branch validation while preserving attendance calculations.
- `backend/reporting/services/physical.py`: cohort selection, completion counts, measurement means, monthly buckets and paired changes.
- `backend/reporting/prompts/physical.py`: aggregate-only provider payload and narrative instructions.
- `backend/reporting/models.py`, `migrations/0002_physicalanalysisjob.py`: shared abstract job fields plus a separate physical job table.
- `backend/reporting/tasks.py`, `views.py`, `urls.py`: shared execution/queue/status helpers and physical report endpoints.
- `backend/users/views.py`: physical analysis jobs block branch deletion.
- `backend/reporting/management/__init__.py`, `management/commands/__init__.py`, `management/commands/seed_reporting_demo.py`: repeatable fictional fixtures.
- `backend/reporting/test_physical.py`: statistics, access, query-count, privacy, task, worker and seeding tests.
- `frontend/src/apis.js`: physical report and analysis API helpers.
- `frontend/src/utils/measurementCharts.js`, `components/charts/MeasurementChart.vue`: numeric chart preparation and accessible SVG rendering without a new dependency.
- `frontend/src/components/physicalTests/AssessmentTrend.vue`, `AssessmentHistory.vue`: exercise selection and profile result graphs.
- `frontend/src/components/reporting/ReportingOptions.vue`: shared reporting choice cards.
- `frontend/src/components/reporting/PhysicalReport.vue`: date/branch filters, completion tables, means, paired changes and graphs.
- `frontend/src/components/reporting/ReportAnalysis.vue`: request/poll/render component using the existing polling helper and Markdown renderer.
- `frontend/src/views/SuperAdmin/Reporting.vue`, `frontend/src/views/BranchManager/Reports.vue`: reporting choice pages.
- `frontend/src/views/SuperAdmin/AttendanceReporting.vue`, `PhysicalReporting.vue`, `frontend/src/views/BranchManager/AttendanceReporting.vue`, `PhysicalReporting.vue`: role-specific report pages with links back to the options.
- `frontend/src/router/index.js`: protected routes for the two report types.
- `frontend/tests/measurement-charts.test.js`, `frontend/tests/apis.test.js`: graph semantics and API retry behaviour.
- `Documentation/backend/physical-reporting.md`, `physical-assessments.md`, `seed_test_data.md`, `celery-setup.md`: updated feature, fixture and worker documentation.
