"""Human-readable, deliberately limited projection of stored audit events."""
from datetime import date

ROLES = {"super_admin": "Super admin", "branch_manager": "Branch admin", "instructor": "Instructor"}
ACTIONS = {
    "staff.created": "Created a staff account",
    "staff.role_changed": "Changed a staff role",
    "staff.branch_changed": "Changed a staff member’s branch",
    "staff.deactivated": "Deactivated a staff account",
    "staff.reactivated": "Reactivated a staff account",
    "staff.updated": "Updated a staff account",
    "branch.created": "Created a branch",
    "branch.updated": "Updated branch settings",
    "branch.deleted": "Deleted a branch",
    "branch.quarters_updated": "Updated reporting quarter dates",
    "report.requested": "Requested a report",
    "report.succeeded": "Report ready",
    "report.failed": "Report could not be completed",
    "report.statistics_viewed": "Viewed reporting statistics",
    "auth.login": "Signed in",
    "auth.logout": "Signed out",
}
RESOURCES = {
    "ParticipantListCreateView": "participant record", "ParticipantDetailView": "participant record",
    "ParticipantDeactivateView": "participant account", "FeedbackListCreateView": "feedback record",
    "SessionListCreateView": "session", "SessionDetailView": "session",
    "AttendanceRecordDetailView": "attendance record", "AttendanceFinalisationView": "attendance register",
    "AssessmentListView": "physical assessment", "AssessmentDetailView": "physical assessment",
    "ExerciseGroupView": "physical test results", "CompleteAssessmentView": "physical assessment",
    "DocumentListCreateView": "document", "DocumentDetailView": "document",
    "FolderListCreateView": "folder", "FolderDetailView": "folder",
    "StaffCreateView": "staff account", "StaffDetailView": "staff account",
    "StaffDeactivateView": "staff account", "BranchQuartersView": "reporting quarter dates",
    "BranchListCreateView": "branch", "BranchDetailView": "branch",
    "BranchStaffView": "staff assignment", "BranchStaffDetailView": "staff assignment",
    "AttendanceAnalysisView": "attendance report", "PhysicalAnalysisView": "physical-testing report",
}


def summary(event, viewer, staff_label=None):
    staff_label = staff_label or event.target_label
    text = ACTIONS.get(event.action, "Recorded an administrative action")
    if event.action == "api.write":
        resource = RESOURCES.get(event.target_type, "record")
        verb = {"POST": "Submitted", "PATCH": "Updated", "PUT": "Updated", "DELETE": "Removed"}.get(event.details.get("method"), "Changed")
        return f"{verb} {resource}" if event.outcome == "success" else f"Attempted a change to {resource}"
    if event.action.startswith("staff."):
        # Only the recorded staff identity and recognised role labels are presented;
        # raw change dictionaries may contain information about another branch.
        if staff_label:
            text += f" — {staff_label}"
        if event.action == "staff.role_changed":
            roles = event.details.get("changes", {}).get("role", {})
            before, after = ROLES.get(roles.get("before")), ROLES.get(roles.get("after"))
            if before and after:
                text += f" ({before} → {after})"
        if event.action == "staff.branch_changed" and viewer.role == "branch_manager":
            previous = event.details.get("changes", {}).get("branch_id", {}).get("before")
            if previous == str(viewer.branch_id) and event.branch_id != viewer.branch_id:
                text = "Staff member left your branch" + (f" — {staff_label}" if staff_label else "")
    elif event.action.startswith("report."):
        kind = {"attendance": "Attendance", "physical": "Physical testing"}.get(event.details.get("report_type"))
        if kind:
            text += f" — {kind}"
        try:
            start = date.fromisoformat(event.details.get("start_date", ""))
            end = date.fromisoformat(event.details.get("end_date", ""))
        except (ValueError, TypeError):
            pass
        else:
            text += f" ({start:%d %b %Y} – {end:%d %b %Y})"
    elif event.action == "branch.quarters_updated":
        year = event.details.get("year")
        if isinstance(year, int) and 1900 <= year <= 9998:
            text += f" for {year}"
    elif event.action.startswith("branch.") and event.target_label:
        text += f" — {event.target_label}"
    return text
