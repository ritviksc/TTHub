import json
import logging

from django.core.exceptions import ImproperlyConfigured
from django.http import Http404, StreamingHttpResponse
from openai import OpenAIError
from rest_framework import status
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from users.permissions import IsBranchManager, IsInstructor, IsSuperAdmin

from .serializers import ChatSerializer
from .services.chat import start_answer
from .services.docs import docs_for, get_doc

logger = logging.getLogger(__name__)

# Every role has a Help page; the role decides which articles it contains.
ANY_STAFF = [IsSuperAdmin | IsBranchManager | IsInstructor]


class ArticleListView(APIView):
    permission_classes = ANY_STAFF

    def get(self, request):
        return Response([{"slug": doc.slug, "title": doc.title, "section": doc.section, "order": doc.order,
                          "audience": doc.audience, "audience_label": doc.audience_label}
                         for doc in docs_for(request.user.role)])


class ArticleDetailView(APIView):
    permission_classes = ANY_STAFF

    def get(self, request, slug):
        doc = get_doc(request.user.role, slug)
        if doc is None:
            # Same response for "missing" and "another role's article".
            raise Http404
        return Response({"slug": doc.slug, "title": doc.title, "section": doc.section, "audience": doc.audience,
                         "audience_label": doc.audience_label, "body": doc.body})


class HelpChatThrottle(ScopedRateThrottle):
    """Rate limit stored in the Redis cache. If the cache is down or not
    configured, allow the question rather than break the Help page (the same
    choice llm/services/catalog.py makes for the model list)."""

    def allow_request(self, request, view):
        try:
            return super().allow_request(request, view)
        except Exception:
            logger.warning("Help chat rate limit skipped: cache unavailable", exc_info=True)
            return True


class ChatView(APIView):
    permission_classes = ANY_STAFF
    throttle_classes = [HelpChatThrottle]
    throttle_scope = "help_chat"

    def post(self, request):
        serializer = ChatSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            # The role comes from the session, never from the request body.
            events = start_answer(request.user, serializer.validated_data["question"],
                                  serializer.validated_data["history"])
        except (OpenAIError, ValueError, ImproperlyConfigured):
            logger.exception("Help chatbot request failed")
            return Response({"detail": "The help assistant is unavailable right now. The articles on this page still work."},
                            status=status.HTTP_503_SERVICE_UNAVAILABLE)
        # One JSON event per line (NDJSON), sent as the model writes; see services/chat.py.
        response = StreamingHttpResponse((json.dumps(event) + "\n" for event in events),
                                         content_type="application/x-ndjson")
        response["Cache-Control"] = "no-cache"
        response["X-Accel-Buffering"] = "no"  # stop proxies buffering the stream
        return response
