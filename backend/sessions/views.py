from django.db import transaction
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404
from rest_framework import generics
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response

from participants.models import Participant
from users.models import UserAccount
from users.permissions import IsBranchManager, IsInstructor, IsSuperAdmin

from .models import AttendanceRecord, ProgrammeSession
from .serializers import (
    AttendanceRecordSerializer,
    SessionCreateSerializer,
    SessionDetailSerializer,
    SessionListSerializer,
)


ANY_STAFF = [IsSuperAdmin | IsBranchManager | IsInstructor]


def sessions_for(user):
    """Sessions visible to this user; non-national roles never cross branches."""
    queryset = ProgrammeSession.objects.select_related("branch", "created_by").prefetch_related(
        "attendance__participant"
    )
    if user.role != UserAccount.Role.SUPER_ADMIN:
        queryset = queryset.filter(branch=user.branch)
    return queryset


class SessionListCreateView(generics.ListCreateAPIView):
    permission_classes = ANY_STAFF

    def get_serializer_class(self):
        if self.request.method == "POST":
            return SessionCreateSerializer
        return SessionListSerializer

    def get_queryset(self):
        return sessions_for(self.request.user).annotate(
            present_count=Count("attendance", filter=Q(attendance__status=AttendanceRecord.Status.PRESENT)),
            roster_count=Count("attendance"),
        )

    @transaction.atomic
    def perform_create(self, serializer):
        user = self.request.user
        session = serializer.save(branch=user.branch, created_by=user)
        roster = Participant.objects.filter(branch=user.branch, is_active=True)
        AttendanceRecord.objects.bulk_create(
            [AttendanceRecord(session=session, participant=participant) for participant in roster]
        )


class SessionDetailView(generics.RetrieveDestroyAPIView):
    permission_classes = ANY_STAFF
    serializer_class = SessionDetailSerializer

    def get_queryset(self):
        return sessions_for(self.request.user).annotate(
            present_count=Count("attendance", filter=Q(attendance__status=AttendanceRecord.Status.PRESENT)),
            roster_count=Count("attendance"),
        )

    def perform_destroy(self, instance):
        if self.request.user.role != UserAccount.Role.INSTRUCTOR or instance.created_by_id != self.request.user.id:
            raise PermissionDenied("Only the Instructor who created this session can delete it.")
        instance.delete()


class AttendanceRecordDetailView(generics.GenericAPIView):
    permission_classes = ANY_STAFF
    serializer_class = AttendanceRecordSerializer

    def get_object(self):
        return get_object_or_404(
            AttendanceRecord.objects.select_related("participant", "session"),
            pk=self.kwargs["attendance_id"],
            session__in=sessions_for(self.request.user),
            session_id=self.kwargs["pk"],
        )

    def patch(self, request, *args, **kwargs):
        if request.user.role != UserAccount.Role.INSTRUCTOR:
            raise PermissionDenied("Only an Instructor can record attendance.")

        attendance = self.get_object()
        serializer = self.get_serializer(attendance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
