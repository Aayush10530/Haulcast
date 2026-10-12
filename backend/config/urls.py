"""Root URL configuration for StormRoute."""

from django.urls import include, path

urlpatterns = [
    path("api/", include("api.urls")),
]
