"""Validation shared by folder create/rename/move and document move.

Kept separate from validators.py, which is about file contents rather than
the folder tree's shape.
"""

from rest_framework import serializers


def assert_unique_sibling_name(parent, branch, name, exclude_pk=None):
    """A folder's name must be unique among its siblings, ignoring case.

    Siblings share a parent (None means the scope's root) and a branch (None
    means the organisation scope).
    """
    from .models import Folder

    siblings = Folder.objects.filter(parent=parent, branch=branch, name__iexact=name)
    if exclude_pk is not None:
        siblings = siblings.exclude(pk=exclude_pk)
    if siblings.exists():
        raise serializers.ValidationError({"name": "A folder with that name already exists here."})


def assert_no_cycle(folder, new_parent):
    """Reject moving `folder` into itself or one of its own descendants."""
    node = new_parent
    while node is not None:
        if node.pk == folder.pk:
            raise serializers.ValidationError({"parent": "A folder cannot be moved into itself or its own subfolder."})
        node = node.parent


def assert_same_branch(folder, branch_id):
    """A folder can only move within its own branch/organisation scope."""
    if folder.branch_id != branch_id:
        raise serializers.ValidationError({"parent": "A folder cannot move to a different branch or scope."})
