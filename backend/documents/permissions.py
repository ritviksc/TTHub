from django.db.models import Q

from participants.views import participants_for
from users.models import UserAccount

from .models import Document


def documents_for(user):
    """Every document this user is allowed to see.

    A Super Admin sees everything. Everyone else sees organisation-wide
    documents, their own branch's documents, and documents on participants at
    their branch -- the same scoping rule as `participants_for`.
    """
    qs = Document.objects.select_related("branch", "participant", "uploaded_by")
    if user.role == UserAccount.Role.SUPER_ADMIN:
        return qs
    return qs.filter(
        Q(branch_id=user.branch_id)
        | Q(participant__branch_id=user.branch_id)
        | Q(branch__isnull=True, participant__isnull=True)
    )


def can_upload(user, branch, participant):
    """Whether `user` may add a document to this branch/participant/organisation scope."""
    if user.role == UserAccount.Role.SUPER_ADMIN:
        return True
    if participant is not None:
        return participants_for(user).filter(pk=participant.pk).exists()
    if branch is not None:
        return user.branch_id == branch.pk
    # Organisation scope: Super Admin only.
    return False


def can_delete(user, document):
    """Whether `user` may remove an existing document."""
    if user.role == UserAccount.Role.SUPER_ADMIN:
        return True
    if user.role != UserAccount.Role.BRANCH_MANAGER:
        return False
    if document.scope == "organisation":
        return False
    return document.owning_branch_id == user.branch_id
