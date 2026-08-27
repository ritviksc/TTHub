from datetime import date

from rest_framework import serializers

from users.models import UserAccount

from .models import Participant


class ParticipantSerializer(serializers.ModelSerializer):
    """Full record: used for create, retrieve and edit on the kapa page."""

    full_name = serializers.CharField(read_only=True)
    branch_name = serializers.CharField(source="branch.name", read_only=True)

    class Meta:
        model = Participant
        fields = [
            "id",
            "first_name",
            "last_name",
            "preferred_name",
            "full_name",
            "date_of_birth",
            "email",
            "phone",
            "emergency_contact_name",
            "emergency_contact_phone",
            "branch",
            "branch_name",
            "joined_on",
            "is_active",
            "notes",
        ]
        # is_active is read-only here on purpose: it changes through the
        # deactivate endpoint, the same way staff accounts do.
        read_only_fields = ["id", "is_active"]
        extra_kwargs = {"branch": {"required": False}}

    def validate_date_of_birth(self, value):
        if value and value > date.today():
            raise serializers.ValidationError("Date of birth cannot be in the future.")
        return value

    def validate(self, attrs):
        user = self.context["request"].user

        # Only a Super Admin picks the kapa. For everyone else it is forced to
        # their own, so a branch manager cannot create a participant in, or move
        # one to, a kapa they do not run.
        if user.role != UserAccount.Role.SUPER_ADMIN:
            attrs["branch"] = user.branch
        elif self.instance is None and not attrs.get("branch"):
            raise serializers.ValidationError({"branch": "Kapa is required."})

        return attrs


class ParticipantListSerializer(serializers.ModelSerializer):
    """The lighter shape the participant table renders from."""

    full_name = serializers.CharField(read_only=True)
    branch_name = serializers.CharField(source="branch.name", read_only=True)

    class Meta:
        model = Participant
        fields = [
            "id",
            "full_name",
            "preferred_name",
            "branch",
            "branch_name",
            "phone",
            "is_active",
        ]
