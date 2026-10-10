"""URL routing for API layer."""

from django.urls import path

from api.views import HealthCheckView

urlpatterns = [
    path("health/", HealthCheckView.as_view(), name="health"),
]
