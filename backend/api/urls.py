"""URL routing for API layer."""

from django.urls import path

from api.views import GeocodeView, HealthCheckView, TripAnalyzeView, TripHeatmapView

urlpatterns = [
    path("health/", HealthCheckView.as_view(), name="health"),
    path("geocode/", GeocodeView.as_view(), name="geocode"),
    path("trips/analyze/", TripAnalyzeView.as_view(), name="trip-analyze"),
    path("trips/heatmap/", TripHeatmapView.as_view(), name="trip-heatmap"),
]
