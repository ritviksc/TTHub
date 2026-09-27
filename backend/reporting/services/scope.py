"""Date and branch validation shared by reporting services."""
from datetime import date, datetime
from uuid import UUID
from django.core.exceptions import PermissionDenied, ValidationError
from users.models import Branch, UserAccount


def resolve_report_scope(user, start_date, end_date, branch_id):
    if not user.is_authenticated or not user.is_active or user.role not in UserAccount.Role.values:
        raise PermissionDenied("An active staff account is required.")
    if any(not isinstance(value, date) or isinstance(value, datetime)
           for value in (start_date, end_date)):
        raise ValidationError("Report dates must be date objects.")
    if start_date > end_date:
        raise ValidationError("Start date must not be after end date.")
    if branch_id is not None:
        try:
            branch_id = UUID(str(branch_id))
        except (ValueError, TypeError, AttributeError) as exc:
            raise ValidationError("Invalid branch ID.") from exc
    if user.role != UserAccount.Role.SUPER_ADMIN:
        if not user.branch_id or branch_id not in (None, user.branch_id):
            raise PermissionDenied("You may only report on your own branch.")
        branch_id = user.branch_id
    if branch_id is not None and not Branch.objects.filter(pk=branch_id).exists():
        raise ValidationError("Branch does not exist.")
    return branch_id
