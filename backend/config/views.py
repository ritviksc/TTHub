from django.http import JsonResponse
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_safe


@never_cache
@require_safe
def health_check(request):
    """Liveness only: dependency readiness is not checked here."""
    return JsonResponse({"status": "ok"})
