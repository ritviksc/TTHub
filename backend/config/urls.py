from django.urls import path, include
from django.contrib import admin

# Specfic URLS will be used for the backend
# For each URL, a corresponding view is provided
# Return the data (or template) to the frontend as a response

"""
/api/v1/auth/login/
/api/v1/auth/me/
/api/v1/dashboard/
"""

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/", include("users.urls")),
    path("api/participants/", include("participants.urls")),
    path("api/sessions/", include("sessions.urls")),
    path("api/branches/", include("users.branch_urls")),
    path("api/physical-tests/", include("physical_tests.urls")),
    path("api/reporting/", include("reporting.urls")),
    path("api/documents/", include("documents.urls")),

    # LLM API endpoint for generating responses from the language model
    path("api/llm/", include("llm.urls")),
]

# Participant files are served by authenticated views, never a public media route.
