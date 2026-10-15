# Physical reporting

The super admin **Reports** page (`/super-admin/reporting`) and branch manager **Reports** page (`/branch-manager/reports`) offer two reports:

- **Attendance** (`…/attendance`): attendance statistics and an optional AI explanation.
- **Physical testing** (`…/physical`): a completion summary for the date range, a Yes/No and assessment count per participant, individual result graphs, exercise means and outcome counts, monthly graphs, paired changes and an optional AI explanation.

Both open on the last three months and accept custom inclusive dates or a branch quarter (see [reporting-quarters.md](reporting-quarters.md)). Super admins can pick one branch or all branches, and branch managers see only their own. Instructors can view their participants' assessment histories and graphs, but not the aggregate reports or AI analysis.

## Calculation rules

**Who is included.** The report starts from participants, so an eligible person with no tests shows as **No**. The roster is active participants who joined on or before the end date (unknown join dates included), plus inactive participants with a completed assessment in the period. It uses current branch membership and leaves out assessments from a previous branch. The system doesn't keep enrolment history, so this is a current-roster report, not a reconstruction of past membership.

**Yes and counts.** **Yes** means at least one completed assessment in the range. Counts are completed assessment occasions, not exercises. Drafts are counted separately and excluded from measurements. A completed assessment can include valid inability outcomes, so completion doesn't mean every exercise was performed.

**Means.** Numeric means include `measured` results and chair `arms_used`, which is zero. Unable and skipped outcomes are counted separately and have no value. Monthly means are weighted by assessment occasion, so someone tested twice counts twice and the people contributing can differ between months.

**Paired changes.** For each exercise, a person's first and last scored results on different dates in the range are compared, if their outcomes match. For TUG, the walking aid must also match (ignoring case and spacing). Change is last minus first, and one measurement gives no change. The aggregate mean counts each person once and reports the sample size. Results are descriptive. They aren't clinical interpretation or evidence that the programme caused the change.

**Graphs.** Graphs use real date spacing. Missing or unperformed results break the line, and scored zeros stay at zero. Exact values are listed under each graph. Individual graphs also appear on the participant's Details page.

## AI explanation and privacy

`GET /api/reporting/physical/` calculates the statistics in Django. `POST /api/reporting/physical/analyse/` saves a `PhysicalAnalysisJob` snapshot and queues `reporting.tasks.generate_physical_analysis` with just its ID. The page polls `GET /api/reporting/physical/jobs/<id>/` and shows the Markdown explanation alongside the saved figures. With no completed assessments, no provider call is made.

Physical and attendance analysis share the same job model, queueing, permission checks and worker code (see [celery-setup.md](../setup/celery-setup.md)). The requester must still have access to the branch when the job runs. Queue errors return a safe 503, and provider failures save a safe error. Jobs are kept indefinitely, and a branch with saved jobs can't be deleted.

Only allowlisted aggregates are sent to the AI: totals, exercise and monthly summaries, paired changes and limitations. Participant names and IDs, assessment IDs, dates of birth, notes and walking-aid descriptions are never sent. The prompt forbids diagnosis, clinical risk ratings, invented causes and claims about programme effectiveness. The page labels AI output as variable and needing review.

## Demo data

`seed_reporting_demo` creates two demo branches with known figures for checking this report. See [seed-test-data.md](../setup/seed-test-data.md#reporting-demo-data).

## How to check it

1. Load the reporting demo data and sign in as `demo.admin@example.com`.
2. Open Reporting → Physical testing, select **DEMO Harbour** and use the dates the seed command printed. Expect 12 eligible, 9 tested, 3 untested, 75% completion, 25 completed assessments and one draft. Both demo branches together give 24, 18, 6, 75%, 50 and two drafts.
3. Click **View results** for a participant and switch between exercises.
4. With Redis, the worker and the LLM available, click **Analyse physical testing**. Progress shows, then the explanation. Statistics work without the LLM.
5. As the Harbour manager, check there's no branch picker and Hills data is refused. As an instructor, check the aggregate report is refused.

Automated tests: `python manage.py test reporting` (see `reporting/test_physical.py`) and, from `frontend/`, `node --test tests/measurement-charts.test.js`.

## Key files

- `backend/reporting/services/physical.py`: roster, completion, means, monthly figures and paired changes
- `backend/reporting/prompts/physical.py`: AI payload and instructions
- `backend/reporting/models.py`, `tasks.py`, `views.py`: jobs, worker and endpoints
- `frontend/src/components/reporting/PhysicalReport.vue`: report page
- `frontend/src/components/reporting/ReportAnalysis.vue`: AI request, polling and display
- `frontend/src/components/charts/MeasurementChart.vue`, `frontend/src/utils/measurementCharts.js`: graphs
