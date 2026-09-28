from rest_framework import serializers

from participants.models import Participant
from users.models import Branch

from .models import Document
from .permissions import can_delete
from .validators import validate_upload


class DocumentSerializer(serializers.ModelSerializer):
    uploaded_by_name = serializers.CharField(source="uploaded_by.get_full_name", read_only=True, default=None)
    can_delete = serializers.SerializerMethodField()

    class Meta:
        model = Document
        fields = [
            "id", "name", "size", "scope", "branch", "participant",
            "uploaded_by_name", "uploaded_at", "can_delete",
        ]
        read_only_fields = ["id", "size", "scope", "uploaded_by_name", "uploaded_at", "can_delete"]

    def get_can_delete(self, obj):
        request = self.context.get("request")
        return bool(request and can_delete(request.user, obj))


class DocumentUploadSerializer(serializers.ModelSerializer):
    file = serializers.FileField(write_only=True)
    branch = serializers.PrimaryKeyRelatedField(queryset=Branch.objects.all(), required=False, allow_null=True)
    participant = serializers.PrimaryKeyRelatedField(queryset=Participant.objects.all(), required=False, allow_null=True)

    class Meta:
        model = Document
        fields = ["file", "branch", "participant"]

    def validate_file(self, value):
        return validate_upload(value)

    def validate(self, attrs):
        if attrs.get("branch") and attrs.get("participant"):
            raise serializers.ValidationError("A document belongs to a branch or a participant, not both.")
        return attrs
