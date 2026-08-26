from rest_framework import serializers
from .models import UserAccount

class StaffCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta: 
        model = UserAccount
        fields = ["id", "email", "first_name", "last_name", "role", "password"]
        read_only_fields = ["id"]

    def validate(self, attrs):
        if UserAccount.objects.filter(email=attrs["email"]).exists():
            raise serializers.ValidationError({"email": "An account with this email already exists."})
        
        requesting_user = self.context["request"].user
        if attrs.get("role") == UserAccount.Role.SUPER_ADMIN and requesting_user.role != UserAccount.Role.SUPER_ADMIN:
            raise serializers.ValidationError({"role": "Only a Super Admin can grant the Super Admin role."})
        return attrs
    
    def create(self, validated_data):
        password = validated_data.pop("password")
        user = UserAccount(username=validated_data["email"], **validated_data)
        user.set_password(password)
        user.save()
        return user
    