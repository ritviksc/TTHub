from django.db import transaction
from django.db.models import F
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.exceptions import APIException, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from participants.views import ANY_STAFF, participants_for
from .models import Assessment, ExerciseResult
from .serializers import AssessmentSerializer, DateSerializer, GroupSerializer, VersionSerializer, GROUPS


class Conflict(APIException):
    status_code = 409
    default_detail = "This assessment changed. Reload it before saving."


def accessible_assessments(user):
    qs = Assessment.objects.filter(participant__in=participants_for(user))
    if user.role != "super_admin":
        qs = qs.filter(branch_id=user.branch_id)
    return qs.select_related("participant", "recorded_by").prefetch_related("results")


def claim_draft(assessment, version):
    if assessment.completed_at:
        raise ValidationError("Completed assessments are read-only.")
    if not Assessment.objects.filter(pk=assessment.pk, version=version, completed_at__isnull=True).update(version=F("version") + 1):
        raise Conflict()
    assessment.version += 1


class AssessmentListView(APIView):
    permission_classes = ANY_STAFF

    def get(self, request, participant_id):
        get_object_or_404(participants_for(request.user), pk=participant_id)
        return Response(AssessmentSerializer(accessible_assessments(request.user).filter(participant_id=participant_id), many=True).data)

    def post(self, request, participant_id):
        participant = get_object_or_404(participants_for(request.user), pk=participant_id)
        if not participant.is_active:
            raise ValidationError("Cannot start an assessment for an inactive participant.")
        # The unique database constraint also prevents duplicate drafts from two tabs.
        assessment, created = Assessment.objects.get_or_create(
            participant=participant, completed_at=None,
            defaults={"branch": participant.branch, "recorded_by": request.user},
        )
        if assessment.branch_id != participant.branch_id:
            raise Conflict("An earlier branch has an unfinished assessment. Ask a super admin to resolve it.")
        return Response(AssessmentSerializer(assessment).data, status=201 if created else 200)


class AssessmentDetailView(APIView):
    permission_classes = ANY_STAFF

    def get(self, request, pk):
        return Response(AssessmentSerializer(get_object_or_404(accessible_assessments(request.user), pk=pk)).data)

    @transaction.atomic
    def patch(self, request, pk):
        assessment = get_object_or_404(accessible_assessments(request.user), pk=pk)
        version = VersionSerializer(data=request.data)
        version.is_valid(raise_exception=True)
        dates = DateSerializer(data=request.data, context={"participant": assessment.participant})
        dates.is_valid(raise_exception=True)
        claim_draft(assessment, version.validated_data["version"])
        assessment.assessed_on = dates.validated_data["assessed_on"]
        assessment.save(update_fields=["assessed_on"])
        return Response(AssessmentSerializer(assessment).data)


class ExerciseGroupView(APIView):
    permission_classes = ANY_STAFF

    @transaction.atomic
    def put(self, request, pk, group):
        if group not in GROUPS:
            raise ValidationError("Unknown exercise group.")
        assessment = get_object_or_404(accessible_assessments(request.user), pk=pk)
        serializer = GroupSerializer(data=request.data, context={"group": group})
        serializer.is_valid(raise_exception=True)
        claim_draft(assessment, serializer.validated_data["version"])
        for row in serializer.validated_data["results"]:
            ExerciseResult.objects.update_or_create(
                assessment=assessment, exercise=row["exercise"],
                defaults={"value": None, "notes": "", "walking_aid": "", **row, "recorded_by": request.user},
            )
        # Reload because the prefetched result list predates this write.
        return Response(AssessmentSerializer(accessible_assessments(request.user).get(pk=pk)).data)


class CompleteAssessmentView(APIView):
    permission_classes = ANY_STAFF

    @transaction.atomic
    def post(self, request, pk):
        assessment = get_object_or_404(accessible_assessments(request.user), pk=pk)
        version = VersionSerializer(data=request.data)
        version.is_valid(raise_exception=True)
        claim_draft(assessment, version.validated_data["version"])
        rows = list(assessment.results.all())
        if len(rows) != 6 or any(row.outcome == "not_attempted" for row in rows):
            raise ValidationError("Record all exercise groups before completing. Not-attempted exercises remain incomplete.")
        assessment.completed_at = timezone.now()
        assessment.save(update_fields=["completed_at"])
        return Response(AssessmentSerializer(assessment).data)
