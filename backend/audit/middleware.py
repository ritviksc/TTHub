import uuid
from django.apps import apps
from .services import record


class AuditRequestMiddleware:
    """Request outcomes complement detailed domain events, without logging bodies."""
    def __init__(self, get_response):
        self.get_response = get_response

    def resource_scope(self, request, created_id=None):
        match = request.resolver_match
        if not match:
            return None
        route = match.route
        models = {
            "api/participants/": ("participants", "Participant"),
            "api/sessions/": ("programme_sessions", "ProgrammeSession"),
            "api/physical-tests/": ("physical_tests", "Assessment"),
            "api/documents/": ("documents", "Document"),
            "api/folders/": ("documents", "Folder"),
        }
        model_label = next((label for prefix, label in models.items() if route.startswith(prefix)), None)
        pk = match.kwargs.get("pk") or created_id
        if route == "api/participants/feedback/":
            model_label = ("participants", "Feedback")
        if "participant_id" in match.kwargs and not created_id:
            model_label = ("participants", "Participant")
            pk = match.kwargs["participant_id"]
        if not model_label or not pk:
            return None
        try:
            pk = uuid.UUID(str(pk))
        except (ValueError, TypeError):
            return None
        obj = apps.get_model(*model_label).objects.filter(pk=pk).first()
        if obj is None:
            return None
        branch_id = obj.owning_branch_id if model_label == ("documents", "Document") else obj.branch_id
        # A tuple distinguishes a national resource from a resource we could not resolve.
        return (branch_id,)

    def process_view(self, request, view_func, view_args, view_kwargs):
        if request.method in {"POST", "PUT", "PATCH", "DELETE"}:
            # Capture before deletion/transfer; after the response the row may be gone.
            request.audit_resource_scope = self.resource_scope(request)

    def __call__(self, request):
        request.audit_request_id = uuid.uuid4()
        original_actor = request.user if request.user.is_authenticated else None
        response = self.get_response(request)
        match = request.resolver_match
        if not match or not request.path.startswith("/api/"):
            return response
        route = match.route
        # Asking the help chatbot is a POST but changes no records; logging every
        # question would bury real writes in the audit log.
        if route == "api/help/chat/":
            return response
        if request.method not in {"POST", "PUT", "PATCH", "DELETE"}:
            # Statistics reads are meaningful usage; job polling is deliberately excluded.
            if request.method != "GET" or route not in {"api/reporting/attendance/", "api/reporting/physical/"}:
                return response
        actor = request.user if request.user.is_authenticated else original_actor
        outcome = "success" if response.status_code < 400 else "denied" if response.status_code in (401, 403) else "failed"
        if route == "api/auth/login/":
            action = "auth.login"
        elif route == "api/auth/logout/":
            action = "auth.logout"
        elif request.method == "GET":
            action = "report.statistics_viewed"
        else:
            action = "api.write"
        # Route templates and UUID/integer arguments identify the operation without
        # retaining submitted values, filenames, query strings, or free-form notes.
        identifiers = {key: str(value) for key, value in match.kwargs.items()
                       if isinstance(value, (uuid.UUID, int))}
        view = getattr(match.func, "view_class", None) or getattr(match.func, "cls", None)
        data = getattr(response, "data", None)
        data = data if isinstance(data, dict) else {}
        target_id = identifiers.get("pk", identifiers.get("participant_id", ""))
        # Capture the ID of newly created resources, but never their response body.
        try:
            target_id = str(uuid.UUID(str(data.get("id") or data.get("job_id") or target_id)))
        except (ValueError, TypeError):
            pass
        branch_id = getattr(actor, "branch_id", None)
        details = {"method": request.method, "route": route,
                   "identifiers": identifiers, "status_code": response.status_code}
        if action == "report.statistics_viewed" and response.status_code == 200:
            scope = data.get("scope", {})
            branch_id = scope.get("branch_id")
            details.update({key: scope.get(key) for key in ("start_date", "end_date")})
        elif route.startswith("api/branches/") and "pk" in identifiers:
            branch_id = identifiers["pk"]
        elif response.status_code < 400:
            previous = getattr(request, "audit_resource_scope", None)
            current = self.resource_scope(request, target_id) or previous
            if current is not None:
                branch_id = current[0]
            if previous is not None and previous != current:
                details["previous_branch_id"] = str(previous[0]) if previous[0] else None
        record(action, request=request, actor=actor, branch_id=branch_id,
               target_type=view.__name__ if view else match.url_name or "endpoint",
               target_id=target_id, outcome=outcome, details=details)
        return response
