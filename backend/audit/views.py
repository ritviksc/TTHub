from datetime import datetime, time
from django.db.models import Q, Exists, OuterRef
from django.utils import timezone
from rest_framework import generics, serializers
from rest_framework.pagination import PageNumberPagination
from users.permissions import IsSuperAdmin, IsBranchManager
from .models import AuditEvent
from .presentation import summary
from users.models import Branch, UserAccount


class AuditSerializer(serializers.ModelSerializer):
    person = serializers.SerializerMethodField()
    description = serializers.SerializerMethodField()
    branch = serializers.SerializerMethodField()
    result = serializers.SerializerMethodField()

    class Meta:
        model = AuditEvent
        # This is the only public representation: never expose raw audit metadata.
        fields = ["id", "created_at", "person", "description", "branch", "result"]
        read_only_fields = fields

    def get_person(self, obj):
        return self.context["people"].get(obj.actor_id) or obj.actor_email or "Unknown user"

    def get_description(self, obj):
        return summary(obj, self.context["request"].user, self.context["staff_names"].get(obj.target_label))

    def get_branch(self, obj):
        viewer = self.context["request"].user
        if viewer.role != "super_admin":
            return self.context["branches"].get(viewer.branch_id, "Your branch")
        return self.context["branches"].get(obj.branch_id, "Former branch" if obj.branch_id else "Organisation")

    def get_result(self, obj):
        if obj.action == "report.requested" and obj.outcome == "success":
            return "Requested"
        return {"success": "Completed", "failed": "Could not complete", "denied": "Not permitted"}.get(obj.outcome, "Recorded")


class AuditFilters(serializers.Serializer):
    category = serializers.ChoiceField(choices=["staff", "branches", "reports", "records", "signins"], required=False)
    q = serializers.CharField(required=False, max_length=254)
    action = serializers.CharField(required=False, max_length=100)
    actor_id = serializers.UUIDField(required=False)
    branch_id = serializers.UUIDField(required=False)
    outcome = serializers.ChoiceField(choices=["success", "failed", "denied"], required=False)
    start_date = serializers.DateField(required=False)
    end_date = serializers.DateField(required=False)

    def validate(self, attrs):
        if attrs.get("start_date") and attrs.get("end_date") and attrs["start_date"] > attrs["end_date"]:
            raise serializers.ValidationError("Start date must not be after end date.")
        return attrs


class AuditPagination(PageNumberPagination):
    page_size = 50


class AuditListView(generics.ListAPIView):
    permission_classes = [IsSuperAdmin | IsBranchManager]
    serializer_class = AuditSerializer
    pagination_class = AuditPagination

    def get_serializer_context(self):
        context = super().get_serializer_context()
        # Resolve names once for this page, not once per row; never query all staff.
        rows = getattr(self, "audit_page", [])
        people = list(UserAccount.objects.filter(
            Q(pk__in={row.actor_id for row in rows if row.actor_id}) |
            Q(email__in={row.target_label for row in rows if row.action.startswith("staff.")})))
        context["people"] = {person.pk: person.get_full_name().strip() for person in people}
        context["staff_names"] = {person.email: person.get_full_name().strip() for person in people}
        branch_ids = {row.branch_id for row in rows if row.branch_id}
        if self.request.user.role != "super_admin":
            branch_ids = {self.request.user.branch_id} if self.request.user.branch_id else set()
        context["branches"] = dict(Branch.objects.filter(pk__in=branch_ids).values_list("pk", "name"))
        return context

    def paginate_queryset(self, queryset):
        page = super().paginate_queryset(queryset)
        self.audit_page = page or []
        return page

    def get_queryset(self):
        filters = AuditFilters(data=self.request.query_params)
        filters.is_valid(raise_exception=True)
        values = filters.validated_data
        qs = AuditEvent.objects.all()
        user = self.request.user
        if user.role != "super_admin":
            if not user.branch_id:
                return qs.none()
            # Transfers/unassignments also belong to the branch the staff member left.
            qs = qs.filter(Q(branch_id=user.branch_id) | Q(
                action__in=["staff.branch_changed", "staff.role_changed", "staff.deactivated", "staff.updated"],
                details__changes__branch_id__before=str(user.branch_id),
            ) | Q(action="api.write", details__previous_branch_id=str(user.branch_id)))
        # Keep the detailed records in storage, but omit worker progress and duplicate
        # successful request summaries from the administrator-facing list.
        siblings = AuditEvent.objects.filter(request_id=OuterRef("request_id"), outcome="success").exclude(action="api.write")
        qs = qs.exclude(action="report.running").annotate(has_detail=Exists(siblings)).exclude(
            action="api.write", outcome="success", request_id__isnull=False, has_detail=True)
        if "category" in values:
            prefixes = {"staff": "staff.", "branches": "branch.", "reports": "report.", "signins": "auth.", "records": "api.write"}
            qs = qs.filter(action__startswith=prefixes[values["category"]])
        for key in ("action", "actor_id", "branch_id", "outcome"):
            if key in values:
                qs = qs.filter(**{key: values[key]})
        if "q" in values:
            q = values["q"]
            qs = qs.filter(Q(actor_email__icontains=q) | Q(target_label__icontains=q)
                           | Q(target_id__icontains=q) | Q(action__icontains=q))
        if "start_date" in values:
            qs = qs.filter(created_at__gte=timezone.make_aware(datetime.combine(values["start_date"], time.min)))
        if "end_date" in values:
            qs = qs.filter(created_at__lte=timezone.make_aware(datetime.combine(values["end_date"], time.max)))
        return qs
