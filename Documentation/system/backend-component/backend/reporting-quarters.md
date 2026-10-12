# Branch reporting quarters

Super admins can configure any branch's reporting quarters. Branch managers can configure only their own branch. Instructors cannot read or edit these settings through this API.

## Using the screens

1. Open Reporting, then Attendance or Physical Testing.
2. As a super admin, select a branch. All branches uses fixed calendar quarters.
3. Choose a year and quarter. The displayed dates are inclusive.
4. Click **Use Q… dates**, then **Refresh statistics**. AI analysis uses these same report dates.
5. To configure the branch, expand **Edit this branch’s quarter dates**, adjust all four periods, and save. Then apply the desired quarter to the report.
6. **Fill calendar defaults** populates the editor; **Save quarter dates** persists those dates.

Manual date ranges and the existing initial last-three-months report remain available. Selecting a quarter explicitly fills the date range; editing the dates afterwards gives a custom range.

## Storage and validation

`users.BranchQuarter` stores branch, year, quarter number, start date and end date. Each branch/year/quarter combination is unique. Without stored settings, the API returns January–March, April–June, July–September and October–December. Reading defaults does not create records.

`GET /api/branches/<uuid>/quarters/<year>/` returns `year`, `is_default` and four `quarters`.
`PUT` on the same URL accepts `{ "quarters": [{ "quarter": 1, "start_date": "2026-01-01", "end_date": "2026-03-31" }, ...] }`.

Save all four quarters together: exactly Q1–Q4, dates within the selected year (1900–9998), start no later than end, ordered without overlapping inclusive dates. Gaps are allowed. Cross-year quarters are not supported in this version. Validation happens before an atomic replacement; locking the branch serialises concurrent saves on databases supporting row locks. The last successful save wins.

Years and branches are independent. Changing past settings affects future selections for that year; saved AI jobs retain their captured statistics and date range. Existing report APIs continue accepting explicit start/end dates, so their calculations and Celery tasks do not change. National reports use one common calendar period, not an aggregation of different branch-specific periods.

## Verification

Backend regression tests cover default fallback, branch/year isolation, permissions, invalid updates preserving saved settings, invalid years, and using saved dates in both reporting APIs (including attendance boundary dates). The frontend test checks calendar-quarter boundaries.

For manual testing, configure Q1 to February 1–21 for one branch. Apply it in both report screens and verify the displayed range. Switch to another branch and year to confirm unchanged defaults. Log in as that branch's manager to edit the same settings. Try overlapping dates and confirm a validation message without losing the saved schedule. Switch to All branches as a super admin and confirm calendar quarters are used.

## Settings from branch pages

Super admins can also open Kapa → a branch → Reporting quarters, below the branch details. Branch admins can open their Overview dashboard → Reporting quarters. Choose the year, expand Edit this branch’s quarter dates, edit and save. These entry points reuse `QuarterPeriod.vue` in settings-only mode, so they do not show the report's Use quarter button or quarter filter. Existing reporting-screen controls remain available.

The dashboard's average-attendance tile still describes the current calendar quarter and is now explicitly labelled that way. Custom branch periods are applied through the reporting filters.

Frontend files changed for these entry points: `components/reporting/QuarterPeriod.vue` (settings-only mode and load retry), `views/SuperAdmin/BranchDetail.vue`, and `views/BranchManager/Overview.vue`. Existing API permissions, validation and audit logging apply. Check a saved year in either report screen to confirm it uses the same dates.
