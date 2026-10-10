"""Root URL configuration for Haulcast."""

from django.urls import include, path

urlpatterns = [
    path("api/", include("api.urls")),
]
