from rest_framework import serializers

MAX_HISTORY = 6


class TurnSerializer(serializers.Serializer):
    role = serializers.ChoiceField(choices=["user", "assistant"])
    content = serializers.CharField(max_length=2000, trim_whitespace=False)


class ChatSerializer(serializers.Serializer):
    question = serializers.CharField(max_length=500)
    history = TurnSerializer(many=True, required=False, default=list)

    def validate_history(self, value):
        # Older turns are dropped rather than rejected, keeping prompts small.
        return value[-MAX_HISTORY:]
