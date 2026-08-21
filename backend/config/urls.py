from django.urls import path, include

# Specfic URLS will be used for the backend
# For each URL, a corresponding view is provided
# Return the data (or template) to the frontend as a response

"""
/api/v1/auth/login/
/api/v1/auth/me/
/api/v1/dashboard/
"""

urlpatterns = [
    path("api/auth/", include("user.urls"))
]
