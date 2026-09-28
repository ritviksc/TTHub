from django.db.models import Q

from participants.views import participants_for
from users.models import UserAccount

from .models import Document, Folder


def documents_for(user):
    """Every document this user is allowed to see.

    A Super Admin sees everything. Everyone else sees organisation-wide
    documents, their own branch's documents, and documents on participants at
    their branch -- the same scoping rule as `participants_for`.
    """
    qs = Document.objects.select_related("branch", "participant", "uploaded_by", "folder")
    if user.role == UserAccount.Role.SUPER_ADMIN:
        return qs
    return qs.filter(
        Q(branch_id=user.branch_id)
        | Q(participant__branch_id=user.branch_id)
        | Q(branch__isnull=True, participant__isnull=True)
    )


def folders_for(user):
    """Every folder this user is allowed to see: organisation-wide, plus their own branch."""
    qs = Folder.objects.select_related("branch", "parent", "created_by")
    if user.role == UserAccount.Role.SUPER_ADMIN:
        return qs
    return qs.filter(Q(branch_id=user.branch_id) | Q(branch__isnull=True))


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


def can_manage_scope(user, branch_id):
    """Whether `user` may create, rename, move or delete within this scope.

    `branch_id` is None for the organisation scope. This is the same rule for
    folders as for documents: a Branch Manager may manage their own branch,
    only a Super Admin may manage the organisation area, and an instructor may
    never rename, move or delete.
    """
    if user.role == UserAccount.Role.SUPER_ADMIN:
        return True
    if user.role != UserAccount.Role.BRANCH_MANAGER:
        return False
    if branch_id is None:
        return False
    return user.branch_id == branch_id


def can_manage(user, document):
    """Whether `user` may rename, move or delete an existing document."""
    return can_manage_scope(user, document.owning_branch_id)


def can_manage_folder(user, folder):
    """Whether `user` may rename, move or delete an existing folder."""
    return can_manage_scope(user, folder.branch_id)
