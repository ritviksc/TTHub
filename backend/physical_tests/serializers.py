from django.utils import timezone
from rest_framework import serializers

from .models import Assessment, ExerciseResult

BALANCE = ["feet_together", "semi_tandem", "heel_to_toe", "one_foot"]
GROUPS = {"tug": ["tug"], "chair": ["chair"], "balance": BALANCE}


class ResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExerciseResult
        fields = ["exercise", "outcome", "value", "notes", "walking_aid", "recorded_by", "updated_at"]
        read_only_fields = ["recorded_by", "updated_at"]
        validators = []

    def validate(self, data):
        exercise, outcome, value = data["exercise"], data["outcome"], data.get("value")
        if outcome == "measured":
            if value is None or value < 0:
                raise serializers.ValidationError("Enter a non-negative measurement.")
            if exercise == "tug" and value <= 0:
                raise serializers.ValidationError("TUG time must be greater than zero.")
            if exercise == "chair" and value != int(value):
                raise serializers.ValidationError("Chair stands must be a whole number.")
            if exercise in BALANCE and value > 10:
                raise serializers.ValidationError("Balance times cannot exceed 10 seconds.")
        elif outcome == "arms_used":
            if exercise != "chair" or value != 0:
                raise serializers.ValidationError("Arms used applies only to chair stands and must score zero.")
        elif value is not None:
            raise serializers.ValidationError("Unmeasured results must have no numeric value.")
        if outcome in ("unable", "not_attempted") and not data.get("notes", "").strip():
            raise serializers.ValidationError("Record why the exercise was stopped or not attempted.")
        if exercise not in BALANCE and outcome == "skipped":
            raise serializers.ValidationError("Skipped is reserved for later balance stages.")
        if exercise != "tug" and data.get("walking_aid"):
            raise serializers.ValidationError("Walking aids are recorded only for TUG.")
        return data


def validate_balance(results):
    # Later stages are unavailable after a failed or unattempted stage, never zero.
    by_exercise = {row["exercise"]: row for row in results}
    stopped = False
    for exercise in BALANCE:
        row = by_exercise[exercise]
        if stopped != (row["outcome"] == "skipped"):
            raise serializers.ValidationError("Proceed through balance stages only after a 10-second hold; mark later stages skipped after stopping.")
        stopped = stopped or row["outcome"] != "measured" or row["value"] < 10


class DateSerializer(serializers.Serializer):
    assessed_on = serializers.DateField()

    def validate_assessed_on(self, value):
        if value > timezone.localdate():
            raise serializers.ValidationError("Assessment date cannot be in the future.")
        participant = self.context["participant"]
        if participant.date_of_birth and value < participant.date_of_birth:
            raise serializers.ValidationError("Assessment date cannot precede date of birth.")
        return value


class VersionSerializer(serializers.Serializer):
    version = serializers.IntegerField(min_value=0)


class GroupSerializer(VersionSerializer):
    results = ResultSerializer(many=True, allow_empty=False)

    def validate_results(self, value):
        expected = GROUPS[self.context["group"]]
        if len(value) != len(expected) or {r["exercise"] for r in value} != set(expected):
            raise serializers.ValidationError("Supply exactly one result for each exercise in this group.")
        if self.context["group"] == "balance":
            validate_balance(value)
        return value


class AssessmentSerializer(serializers.ModelSerializer):
    results = ResultSerializer(many=True, read_only=True)
    participant_name = serializers.CharField(source="participant.full_name", read_only=True)
    recorded_by_name = serializers.CharField(source="recorded_by.get_full_name", read_only=True)
    status = serializers.SerializerMethodField()

    def get_status(self, obj):
        return "completed" if obj.completed_at else "draft"

    class Meta:
        model = Assessment
        fields = ["id", "participant", "participant_name", "branch", "recorded_by", "recorded_by_name", "assessed_on", "status", "completed_at", "version", "results"]
