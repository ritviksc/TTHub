"""Branch-specific reporting periods; absent settings use calendar quarters."""
from audit.services import record
from calendar import monthrange
from datetime import date

from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Branch, BranchQuarter, UserAccount
from .permissions import IsSuperAdmin, IsBranchManager


def calendar_quarters(year):
    return [dict(quarter=q, start_date=date(year, q * 3 - 2, 1),
                 end_date=date(year, q * 3, monthrange(year, q * 3)[1]))
            for q in range(1, 5)]


class QuarterSerializer(serializers.Serializer):
    quarter = serializers.IntegerField(min_value=1, max_value=4)
    start_date = serializers.DateField()
    end_date = serializers.DateField()


class QuarterYearSerializer(serializers.Serializer):
    quarters = QuarterSerializer(many=True, min_length=4, max_length=4)

    def validate_quarters(self, quarters):
        quarters = sorted(quarters, key=lambda item: item["quarter"])
        if [item["quarter"] for item in quarters] != [1, 2, 3, 4]:
            raise serializers.ValidationError("Provide Q1, Q2, Q3 and Q4 exactly once.")
        previous_end = None
        for item in quarters:
            start, end = item["start_date"], item["end_date"]
            if start.year != self.context["year"] or end.year != self.context["year"]:
                raise serializers.ValidationError("All dates must be within the selected year.")
            if start > end:
                raise serializers.ValidationError("Start date must not be after end date.")
            if previous_end and start <= previous_end:
                raise serializers.ValidationError("Quarters must be ordered and must not overlap.")
            previous_end = end
        return quarters


class BranchQuartersView(APIView):
    permission_classes = [IsSuperAdmin | IsBranchManager]

    def get_branch(self, request, pk, year):
        if not 1900 <= year <= 9998:
            raise serializers.ValidationError({"detail": "Choose a year from 1900 to 9998."})
        branches = Branch.objects.all()
        if request.user.role != UserAccount.Role.SUPER_ADMIN:
            branches = branches.filter(pk=request.user.branch_id)
        return get_object_or_404(branches, pk=pk)

    def response(self, branch, year):
        rows = list(branch.quarters.filter(year=year))
        return Response({"year": year, "is_default": not rows,
                         "quarters": QuarterSerializer(rows or calendar_quarters(year), many=True).data})

    def get(self, request, pk, year):
        return self.response(self.get_branch(request, pk, year), year)

    @transaction.atomic
    def put(self, request, pk, year):
        branch = self.get_branch(request, pk, year)
        serializer = QuarterYearSerializer(data=request.data, context={"year": year})
        serializer.is_valid(raise_exception=True)
        # Lock the parent even when this year has no rows yet, serialising initial saves.
        Branch.objects.select_for_update().get(pk=branch.pk)
        before = self.response(branch, year).data["quarters"]
        branch.quarters.filter(year=year).delete()
        BranchQuarter.objects.bulk_create([
            BranchQuarter(branch=branch, year=year, **item)
            for item in serializer.validated_data["quarters"]
        ])
        response = self.response(branch, year)
        record("branch.quarters_updated", request=request, branch_id=branch.pk,
               target_type="branch", target_id=branch.pk, target_label=branch.name,
               details={"year": year, "before": before, "after": response.data["quarters"]})
        return response
