from pathlib import Path

from rest_framework import serializers

from participants.models import Participant
from users.models import Branch

from .folder_rules import assert_no_cycle, assert_same_branch, assert_unique_sibling_name
from .models import Document, Folder
from .permissions import can_manage, can_manage_folder
from .validators import validate_upload


class DocumentSerializer(serializers.ModelSerializer):
    uploaded_by_name = serializers.CharField(source="uploaded_by.get_full_name", read_only=True, default=None)
    can_manage = serializers.SerializerMethodField()

    class Meta:
        model = Document
        fields = [
            "id", "name", "size", "scope", "branch", "participant", "folder",
            "uploaded_by_name", "uploaded_at", "can_manage",
        ]
        # branch/participant are set once, at upload time, and never reassigned
        # through this serializer -- only `name` (rename) and `folder` (move).
        read_only_fields = ["id", "size", "scope", "branch", "participant", "uploaded_by_name", "uploaded_at", "can_manage"]

    def get_can_manage(self, obj):
        request = self.context.get("request")
        return bool(request and can_manage(request.user, obj))

    def validate_name(self, value):
        # Renaming never changes what the file opens as -- keep the original
        # extension even if the new name is missing or has a different one.
        if self.instance is not None:
            extension = Path(self.instance.name).suffix.lower()
            if extension and not value.lower().endswith(extension):
                value = f"{value}{extension}"
        return value


class DocumentUploadSerializer(serializers.ModelSerializer):
    file = serializers.FileField(write_only=True)
    branch = serializers.PrimaryKeyRelatedField(queryset=Branch.objects.all(), required=False, allow_null=True)
    participant = serializers.PrimaryKeyRelatedField(queryset=Participant.objects.all(), required=False, allow_null=True)
    folder = serializers.PrimaryKeyRelatedField(queryset=Folder.objects.all(), required=False, allow_null=True)

    class Meta:
        model = Document
        fields = ["file", "branch", "participant", "folder"]

    def validate_file(self, value):
        return validate_upload(value)

    def validate(self, attrs):
        folder = attrs.get("folder")
        if folder is not None:
            if attrs.get("participant"):
                raise serializers.ValidationError("A document in a folder cannot also belong to a participant.")
            if attrs.get("branch") and attrs["branch"] != folder.branch:
                raise serializers.ValidationError("That folder does not belong to the selected branch.")
            # The folder is the source of truth for scope; a document takes its branch from it.
            attrs["branch"] = folder.branch
        if attrs.get("branch") and attrs.get("participant"):
            raise serializers.ValidationError("A document belongs to a branch or a participant, not both.")
        return attrs


class FolderSerializer(serializers.ModelSerializer):
    can_manage = serializers.SerializerMethodField()

    class Meta:
        model = Folder
        fields = ["id", "name", "parent", "branch", "can_manage"]
        read_only_fields = ["id", "can_manage"]

    def get_can_manage(self, obj):
        request = self.context.get("request")
        return bool(request and can_manage_folder(request.user, obj))

    def validate(self, attrs):
        if self.instance is not None:
            # Rename and/or move. The scope (branch) a folder belongs to never
            # changes here -- only which parent within that scope it sits under.
            parent = attrs.get("parent", self.instance.parent)
            if "parent" in attrs and attrs["parent"] is not None:
                assert_no_cycle(self.instance, attrs["parent"])
                assert_same_branch(self.instance, attrs["parent"].branch_id)
            branch = self.instance.branch
        else:
            # A subfolder always takes its branch from its parent; only a root
            # folder's branch is chosen directly.
            parent = attrs.get("parent")
            branch = parent.branch if parent is not None else attrs.get("branch")
        attrs["branch"] = branch
        name = attrs.get("name", self.instance.name if self.instance else None)
        assert_unique_sibling_name(
            parent, branch, name, exclude_pk=self.instance.pk if self.instance else None,
        )
        return attrs
