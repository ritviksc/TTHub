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


class AnalysisModelSerializer(serializers.Serializer):
    model = serializers.CharField(required=False, max_length=200)

    def validate(self, attrs):
        from llm.services.catalog import report_models
        catalog = report_models()
        chosen = attrs.get("model", catalog["default"])
        if not chosen or chosen not in catalog["models"]:
            raise serializers.ValidationError({"model": "Choose an available AI model."})
        return {"model": chosen}
