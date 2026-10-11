"""DRF rate throttling classes for API endpoints."""

from rest_framework.throttling import ScopedRateThrottle


class AnalyzeThrottle(ScopedRateThrottle):
    """Scoped throttle for /api/trips/analyze/ endpoint."""

    scope = "analyze"


class HeatmapThrottle(ScopedRateThrottle):
    """Scoped throttle for /api/trips/heatmap/ endpoint."""

    scope = "heatmap"


class GeocodeThrottle(ScopedRateThrottle):
    """Scoped throttle for /api/geocode/ endpoint."""

    scope = "geocode"
