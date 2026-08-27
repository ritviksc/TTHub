from django.core.exceptions import ValidationError as DjangoValidationError
from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import generics
from rest_framework.response import Response

from users.models import UserAccount
from users.permissions import IsBranchManager, IsInstructor, IsSuperAdmin

from .models import Participant
from .serializers import ParticipantListSerializer, ParticipantSerializer

# All three roles get the same participant screens, so they share one permission
# set and are separated by what the queryset below will hand them.
ANY_STAFF = [IsSuperAdmin | IsBranchManager | IsInstructor]


def participants_for(user):
    """Every participant this user is allowed to touch.

    A Super Admin sees the motu. Everyone else is scoped to their own kapa,
    which is what keeps one kapa's records out of another's screens.
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
    """GET for the participant record, PATCH for edits from the kapa page."""

    serializer_class = ParticipantSerializer
    permission_classes = ANY_STAFF

    def get_queryset(self):
        return participants_for(self.request.user)


class ParticipantDeactivateView(generics.GenericAPIView):
    permission_classes = ANY_STAFF

    def post(self, request, pk):
        participant = get_object_or_404(participants_for(request.user), pk=pk)
        participant.is_active = False
        participant.save()
        return Response({"id": str(participant.id), "is_active": participant.is_active})
