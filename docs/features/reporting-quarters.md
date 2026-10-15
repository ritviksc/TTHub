# Branch reporting quarters

Each branch can have its own reporting quarters. Super admins can set any branch's quarters, and branch managers only their own. Instructors can't read or change them.

## Using quarters in a report

1. Open Reporting, then Attendance or Physical testing.
2. As a super admin, select a branch. **All branches** always uses calendar quarters.
3. Choose a year and quarter. The dates shown are inclusive.
4. Click **Use Q… dates**, then **Refresh statistics**. The AI explanation uses the same dates.

Choosing a quarter fills in the date range. Editing the dates afterwards gives a custom range. Reports open on the last three months through today.

## Setting a branch's quarters

The quarter editor is in three places:

- Inside either report: expand **Edit this branch's quarter dates**.
- Super admins: Kapa → a branch → **Reporting quarters**.
- Branch managers: Overview → **Reporting quarters**.

Choose the year, adjust all four periods and click **Save quarter dates**. **Fill calendar defaults** fills the editor with calendar quarters without saving.

The dashboard's average-attendance tile always uses the current calendar quarter and is labelled that way. Branch quarters apply only through the report filters.

## Rules

- All four quarters are saved together: exactly Q1–Q4, with dates inside the selected year (1900–9998).
- Each quarter's start must be on or before its end. Quarters must be in order and can't overlap. Gaps are allowed.
- Quarters can't cross into another year.
- Saving replaces the year's quarters in one transaction. If two people save at once, the last save wins.
- Without saved settings, the API returns calendar quarters (January–March, April–June, July–September, October–December). Reading the defaults doesn't create records.
- Years and branches are independent. Changing a past year affects future selections only. Saved AI jobs keep the dates and statistics they were created with.
- National reports use one common calendar period, not a mix of each branch's quarters.

## API

- `GET /api/branches/<uuid>/quarters/<year>/` returns `year`, `is_default` and four `quarters`.
- `PUT` on the same URL takes `{ "quarters": [{ "quarter": 1, "start_date": "2026-01-01", "end_date": "2026-03-31" }, ...] }`.

Quarter changes are recorded in the [audit log](../backend/audit-log.md) as `branch.quarters_updated`.

## How to check it

Set Q1 to 1–21 February for one branch and apply it in both reports. Switch to another branch or year and check it still has the defaults. Sign in as that branch's manager and edit the same settings. Enter overlapping dates and check you get a validation message and the saved quarters are unchanged.

Automated tests: `python manage.py test users reporting`.

## Key files

- `backend/users/models.py`: `BranchQuarter`
- `backend/users/quarters.py`: defaults, validation and saving
- `frontend/src/components/reporting/QuarterPeriod.vue`: quarter picker and editor
