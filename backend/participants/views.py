from django.core.exceptions import ValidationError as DjangoValidationError
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.http import FileResponse, Http404
from rest_framework import generics
from rest_framework.response import Response

from users.models import UserAccount
from users.permissions import IsBranchManager, IsInstructor, IsSuperAdmin

from .models import Feedback, Participant
from .serializers import FeedbackSerializer, ParticipantListSerializer, ParticipantSerializer

# All three roles get the same participant screens, so they share one permission
# set and are separated by what the queryset below will hand them.
ANY_STAFF = [IsSuperAdmin | IsBranchManager | IsInstructor]


def participants_for(user):
    """Every participant this user is allowed to touch.

    A Super Admin sees the motu. Everyone else is scoped to their own branch,
    which is what keeps one branch's records out of another's screens.
    """
    qs = Participant.objects.select_related("branch")
    if user.role != UserAccount.Role.SUPER_ADMIN:
        qs = qs.filter(branch=user.branch)
    return qs


class ParticipantListCreateView(generics.ListCreateAPIView):
    permission_classes = ANY_STAFF

    def get_serializer_class(self):
        if self.request.method == "GET":
            return ParticipantListSerializer
        return ParticipantSerializer

    def get_queryset(self):
        qs = participants_for(self.request.user)
        params = self.request.query_params

        branch = params.get("branch")
        if branch:
            try:
                qs = qs.filter(branch_id=branch)
            except (DjangoValidationError, ValueError):
                # A malformed uuid is a filter that matches nothing, not a 500.
                return qs.none()

        is_active = params.get("is_active")
        if is_active in ("true", "false"):
            qs = qs.filter(is_active=(is_active == "true"))

        search = params.get("search", "").strip()
        if search:
            qs = qs.filter(
                Q(first_name__icontains=search)
                | Q(last_name__icontains=search)
                | Q(preferred_name__icontains=search)
            )

        return qs


class ParticipantDetailView(generics.RetrieveUpdateAPIView):
    """GET for the participant record, PATCH for edits from the branch page."""

    serializer_class = ParticipantSerializer
    permission_classes = ANY_STAFF

    def get_queryset(self):
        return participants_for(self.request.user)


class ParticipantDeactivateView(generics.GenericAPIView):
    permission_classes = ANY_STAFF
    active = False

    def post(self, request, pk):
        participant = get_object_or_404(participants_for(request.user), pk=pk)
        participant.is_active = self.active
        participant.save()
        return Response({"id": str(participant.id), "is_active": participant.is_active})


class ParticipantReactivateView(ParticipantDeactivateView):
    active = True


class ParticipantFileView(generics.GenericAPIView):
    permission_classes = ANY_STAFF
    document = False

    def get_permissions(self):
        if self.document:
            return [(IsSuperAdmin | IsBranchManager)()]
        return super().get_permissions()

    def get(self, request, pk):
        participant = get_object_or_404(participants_for(request.user), pk=pk)
        file = participant.gp_consent_document if self.document else participant.photo
        if not file or (not self.document and not participant.photo_consent_given):
            raise Http404
        try:
            opened = file.open("rb")
        except FileNotFoundError:
            raise Http404
        extension = file.name.rsplit(".", 1)[-1].lower()
        response = FileResponse(
            opened, as_attachment=self.document,
            filename=f"gp-consent.{extension}" if self.document else f"photo.{extension}",
        )
        response["Cache-Control"] = "private, no-store"
        response["X-Content-Type-Options"] = "nosniff"
        return response


class ParticipantAttendanceView(generics.GenericAPIView):
    permission_classes = ANY_STAFF

    def get(self, request, pk):
        participant = get_object_or_404(participants_for(request.user), pk=pk)
        records = participant.attendance_records.select_related("session")
        # Transferring a participant must not expose another branch's sessions.
        if request.user.role != UserAccount.Role.SUPER_ADMIN:
            records = records.filter(session__branch=request.user.branch)
        return Response([
            {
                "id": str(record.pk), "session_id": str(record.session_id),
                "date": record.session.date, "time": record.session.time,
                "activity": record.session.activity, "status": record.status,
                "attendance_finalised": record.session.attendance_finalised,
                "absence_reason": record.get_absence_reason_display(),
                "absence_reason_other": record.absence_reason_other,
            }
            for record in records.order_by("-session__date", "-session__time")
        ])


class FeedbackListCreateView(generics.ListCreateAPIView):
    permission_classes = ANY_STAFF
    serializer_class = FeedbackSerializer

    def get_queryset(self):
        qs = Feedback.objects.select_related('recorded_by')
        user = self.request.user
        if user.role != UserAccount.Role.SUPER_ADMIN:
            qs = qs.filter(branch_id=user.branch_id)
        return qs

    def perform_create(self, serializer):
        serializer.save(recorded_by=self.request.user)
