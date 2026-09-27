from rest_framework import serializers
from django.utils import timezone

from users.models import UserAccount
from participants.serializers import participant_photo_url

from .models import AttendanceRecord, ProgrammeSession


class AttendanceRecordSerializer(serializers.ModelSerializer):
    participant_id = serializers.UUIDField(source="participant.id", read_only=True)
    first_name = serializers.CharField(source="participant.first_name", read_only=True)
    last_name = serializers.CharField(source="participant.last_name", read_only=True)
    name = serializers.SerializerMethodField()
    photo = serializers.SerializerMethodField()

    class Meta:
        model = AttendanceRecord
        fields = [
            "id", "participant_id", "first_name", "last_name", "name", "photo", "status",
            "absence_reason", "absence_reason_other", "updated_at",
        ]
        read_only_fields = [
            "id", "participant_id", "first_name", "last_name", "name", "photo", "updated_at",
        ]

    def get_name(self, obj):
        return obj.participant.preferred_name or obj.participant.full_name

    def get_photo(self, obj):
        return participant_photo_url(obj.participant, self.context.get("request"))

    def validate(self, attrs):
        status = attrs.get(
            "status", getattr(self.instance, "status", AttendanceRecord.Status.ABSENT)
        )
        reason = attrs.get("absence_reason", getattr(self.instance, "absence_reason", ""))
        other = attrs.get(
            "absence_reason_other", getattr(self.instance, "absence_reason_other", "")
        )
        errors = {}

        if status == AttendanceRecord.Status.PRESENT:
            # Marking present supersedes an earlier absence and its explanation.
            attrs["absence_reason"] = ""
            attrs["absence_reason_other"] = ""
            return attrs
        if reason == AttendanceRecord.AbsenceReason.OTHER and not other:
            errors["absence_reason_other"] = "Describe the other absence reason."
        if reason != AttendanceRecord.AbsenceReason.OTHER and other:
            errors["absence_reason_other"] = "Only use this field when the reason is Other."
        if errors:
            raise serializers.ValidationError(errors)
        return attrs


class SessionListSerializer(serializers.ModelSerializer):
    branch_name = serializers.CharField(source="branch.name", read_only=True)
    present_count = serializers.IntegerField(read_only=True)
    roster_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = ProgrammeSession
        fields = [
            "id", "branch", "branch_name", "date", "time", "activity",
            "present_count", "roster_count", "created_at", "attendance_finalised",
        ]


class SessionDetailSerializer(SessionListSerializer):
    attendance = AttendanceRecordSerializer(many=True, read_only=True)

    class Meta(SessionListSerializer.Meta):
        fields = SessionListSerializer.Meta.fields + ["attendance"]


class SessionCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProgrammeSession
        fields = ["id", "date", "time", "activity"]
        read_only_fields = ["id"]

    def validate_date(self, value):
        # The programme's local day can be one day ahead of UTC.
        if value < timezone.localdate():
            raise serializers.ValidationError("Session date cannot be in the past.")
        return value

    def validate(self, attrs):
        user = self.context["request"].user
        if user.role != UserAccount.Role.INSTRUCTOR:
            raise serializers.ValidationError(
                {"detail": "Only an Instructor can create a session."}
            )
        if not user.branch_id:
            raise serializers.ValidationError({"detail": "An Instructor must belong to a branch."})
        return attrs


class AttendanceFinalisationSerializer(serializers.Serializer):
    attendance_finalised = serializers.BooleanField(required=True)
