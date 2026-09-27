from rest_framework import serializers


class AttendanceReportRequestSerializer(serializers.Serializer):
    start_date = serializers.DateField()
    end_date = serializers.DateField()
    branch_id = serializers.UUIDField(required=False, allow_null=True)

    def validate(self, attrs):
        if attrs["start_date"] > attrs["end_date"]:
            raise serializers.ValidationError("Start date must not be after end date.")
        # Bound monthly output and synchronous report work for interactive requests.
        if (attrs["end_date"] - attrs["start_date"]).days > 3660:
            raise serializers.ValidationError("Select a reporting period of ten years or less.")
        return attrs
