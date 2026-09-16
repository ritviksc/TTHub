from datetime import date

from rest_framework import serializers

from users.models import UserAccount

from .models import Participant


class ParticipantSerializer(serializers.ModelSerializer):
    """Full record: used for create, retrieve and edit on the branch page."""

    full_name = serializers.CharField(read_only=True)
    branch_name = serializers.CharField(source="branch.name", read_only=True)

    def to_representation(self, instance):
        data = super().to_representation(instance)
        # A file may remain in storage after consent is withdrawn. It must not
        # be exposed to attendance screens unless current consent permits it.
        if not instance.photo_consent_given:
            data["photo"] = None
        return data

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
            "gp_consent_given",
            "gp_consent_date",
            "photo",
            "photo_consent_given",
            "photo_consent_date",
        ]
        # is_active is read-only here on purpose: it changes through the
        # deactivate endpoint, the same way staff accounts do.
        read_only_fields = ["id", "is_active"]
        extra_kwargs = {"branch": {"required": False}}

    def validate_date_of_birth(self, value):
        if value and value > date.today():
            raise serializers.ValidationError("Date of birth cannot be in the future.")
        return value

    def _consent_value(self, attrs, field):
        if field in attrs:
            return attrs[field]
        return getattr(self.instance, field, None)

    def validate(self, attrs):
        user = self.context["request"].user

        gp_consent_fields = {"gp_consent_given", "gp_consent_date"}
        if user.role == UserAccount.Role.INSTRUCTOR and gp_consent_fields.intersection(attrs):
            raise serializers.ValidationError(
                {"gp_consent_given": "Only a Branch Manager or Super Admin can record GP consent."}
            )

        # Only a Super Admin picks the branch. For everyone else it is forced to
        # their own, so a branch manager cannot create a participant in, or move
        # one to, a branch they do not run.
        if user.role != UserAccount.Role.SUPER_ADMIN:
            attrs["branch"] = user.branch
        elif self.instance is None and not attrs.get("branch"):
            raise serializers.ValidationError({"branch": "Branch is required."})
        
        gp_consent_given = self._consent_value(attrs, "gp_consent_given")
        gp_consent_date = self._consent_value(attrs, "gp_consent_date")
        photo_consent_given = self._consent_value(attrs, "photo_consent_given")
        photo_consent_date = self._consent_value(attrs, "photo_consent_date")

        errors = {}
        if gp_consent_given and not gp_consent_date:
            errors["gp_consent_date"] = "Record the date GP consent was given."
        if gp_consent_date and gp_consent_date > date.today():
            errors["gp_consent_date"] = "GP consent date cannot be in the future."
        if photo_consent_given and not photo_consent_date:
            errors["photo_consent_date"] = "Record the date photo consent was given."
        if photo_consent_date and photo_consent_date > date.today():
            errors["photo_consent_date"] = "Photo consent date cannot be in the future."
        if attrs.get("photo") and not photo_consent_given:
            errors["photo_consent_given"] = "Consent must be recorded before attaching a photo."

        if errors:
            raise serializers.ValidationError(
                errors
            )

        return attrs


class ParticipantListSerializer(serializers.ModelSerializer):
    """The lighter shape the participant table renders from."""

    full_name = serializers.CharField(read_only=True)
    branch_name = serializers.CharField(source="branch.name", read_only=True)
    photo = serializers.SerializerMethodField()

    def get_photo(self, obj):
        if not obj.photo or not obj.photo_consent_given:
            return None

        url = obj.photo.url
        request = self.context.get("request")
        return request.build_absolute_uri(url) if request else url

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
            "photo",
        ]
