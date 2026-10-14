from django.urls import reverse
from django.utils import timezone

from rest_framework import serializers

from documents.validators import validate_upload
from users.models import UserAccount
from sessions.models import ProgrammeSession

from .models import Feedback, Participant


def participant_photo_url(participant, request=None):
    if not participant.photo or not participant.photo_consent_given:
        return None
    url = reverse("participant-photo", args=[participant.pk])
    return request.build_absolute_uri(url) if request else url


class ParticipantSerializer(serializers.ModelSerializer):
    """Full record: used for create, retrieve and edit on the branch page."""

    full_name = serializers.CharField(read_only=True)
    branch_name = serializers.CharField(source="branch.name", read_only=True)
    gp_consent_document = serializers.FileField(write_only=True, required=False)
    gp_document_available = serializers.SerializerMethodField()
    gp_document_uploader = serializers.CharField(
        source="gp_document_uploaded_by.get_full_name", read_only=True, default=None,
    )

    def get_gp_document_available(self, instance):
        return bool(instance.gp_consent_document)

    def to_representation(self, instance):
        data = super().to_representation(instance)
        # A file may remain in storage after consent is withdrawn. It must not
        # be exposed to attendance screens unless current consent permits it.
        data["photo"] = participant_photo_url(instance, self.context.get("request"))
        if self.context["request"].user.role == UserAccount.Role.INSTRUCTOR:
            for field in ("gp_document_available", "gp_document_uploaded_at", "gp_document_uploader"):
                data.pop(field, None)
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
            "gp_consent_document",
            "gp_document_available",
            "gp_document_uploaded_at",
            "gp_document_uploader",
            "photo",
            "photo_consent_given",
            "photo_consent_date",
        ]
        # is_active is read-only here on purpose: it changes through the
        # deactivate/reactivate endpoints, the same way staff accounts do.
        read_only_fields = ["id", "is_active", "gp_document_uploaded_at"]
        extra_kwargs = {"branch": {"required": False}}

    def validate_date_of_birth(self, value):
        if value and value > timezone.localdate():
            raise serializers.ValidationError("Date of birth cannot be in the future.")
        return value

    def validate_gp_consent_document(self, value):
        return validate_upload(
            value, allowed=(".pdf", ".jpg", ".jpeg", ".png"),
            type_message="Use a PDF, JPG or PNG document.",
        )

    def _consent_value(self, attrs, field):
        if field in attrs:
            return attrs[field]
        return getattr(self.instance, field, None)

    def validate(self, attrs):
        user = self.context["request"].user

        gp_consent_fields = {"gp_consent_given", "gp_consent_date", "gp_consent_document"}
        if user.role == UserAccount.Role.INSTRUCTOR and gp_consent_fields.intersection(attrs):
            raise serializers.ValidationError(
                {"gp_consent_given": "Only a Branch Manager or Super Admin can record GP consent."}
            )

        # Only a Super Admin picks the branch. For everyone else it is forced to
        # their own, so a branch manager cannot create a participant in, or move
        # one to, a branch they do not run.
        if user.role != UserAccount.Role.SUPER_ADMIN:
            if not user.branch_id:
                raise serializers.ValidationError({"branch": "You must belong to a branch to manage participants."})
            attrs["branch"] = user.branch
        elif self.instance is None and not attrs.get("branch"):
            raise serializers.ValidationError({"branch": "Branch is required."})
        
        gp_consent_given = self._consent_value(attrs, "gp_consent_given")
        gp_consent_date = self._consent_value(attrs, "gp_consent_date")
        photo_consent_given = self._consent_value(attrs, "photo_consent_given")
        photo_consent_date = self._consent_value(attrs, "photo_consent_date")

        # Match the New Zealand date used by the consent date pickers.
        today = timezone.localdate()
        errors = {}
        if gp_consent_given and not gp_consent_date:
            errors["gp_consent_date"] = "Record the date GP consent was given."
        if gp_consent_date and gp_consent_date > today:
            errors["gp_consent_date"] = "GP consent date cannot be in the future."
        if photo_consent_given and not photo_consent_date:
            errors["photo_consent_date"] = "Record the date photo consent was given."
        if photo_consent_date and photo_consent_date > today:
            errors["photo_consent_date"] = "Photo consent date cannot be in the future."
        if attrs.get("photo") and not photo_consent_given:
            errors["photo_consent_given"] = "Consent must be recorded before attaching a photo."

        if errors:
            raise serializers.ValidationError(
                errors
            )

        if attrs.get("gp_consent_document"):
            attrs["gp_document_uploaded_at"] = timezone.now()
            attrs["gp_document_uploaded_by"] = user

        return attrs


class ParticipantListSerializer(serializers.ModelSerializer):
    """The lighter shape the participant table renders from."""

    full_name = serializers.CharField(read_only=True)
    branch_name = serializers.CharField(source="branch.name", read_only=True)
    photo = serializers.SerializerMethodField()

    def get_photo(self, obj):
        return participant_photo_url(obj, self.context.get("request"))

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
            "gp_consent_given",
            "photo",
        ]


class FeedbackSerializer(serializers.ModelSerializer):
    recordedBy = serializers.SerializerMethodField()

    def get_recordedBy(self, obj):
        return obj.recorded_by.get_full_name() or obj.recorded_by.email

    class Meta:
        model = Feedback
        fields = ['id', 'branch', 'participant', 'session', 'quote', 'source', 'speaker', 'date',
                  'consent', 'recorded_by', 'recordedBy', 'created_at']
        read_only_fields = ['id', 'branch', 'source', 'recorded_by', 'created_at']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        user = self.context['request'].user
        participants = Participant.objects.select_related("branch")
        sessions = ProgrammeSession.objects.all()
        if user.role != UserAccount.Role.SUPER_ADMIN:
            participants = participants.filter(branch_id=user.branch_id)
            sessions = sessions.filter(branch_id=user.branch_id)
        self.fields['participant'].queryset = participants
        self.fields['session'].queryset = sessions

    def validate(self, attrs):
        participant, session = attrs.get('participant'), attrs.get('session')
        if not participant and not session:
            raise serializers.ValidationError('Choose a kaumātua or session.')
        if participant and session and participant.branch_id != session.branch_id:
            raise serializers.ValidationError('Participant and session must belong to the same branch.')
        if attrs['date'] > timezone.localdate():
            raise serializers.ValidationError({'date': 'Date cannot be in the future.'})
        subject = participant or session
        attrs['branch'] = subject.branch
        # Preserve the name at recording time, rather than exposing later branch changes.
        attrs['source'] = participant.full_name if participant else session.activity
        return attrs
