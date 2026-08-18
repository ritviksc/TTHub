from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('djoser.urls')), # placeholders
    path('api/v1', include('djoser.urls.authtoken')) # placeholders
]
