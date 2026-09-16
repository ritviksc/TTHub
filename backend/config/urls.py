from django.urls import path, include
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static

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

    # LLM API endpoint for generating responses from the language model
    path("api/llm/", include("llm.urls")),
]

# Configures Django to serve user-uploaded media files (like profile pictures or documents) from your local machine while you are developing your project
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
