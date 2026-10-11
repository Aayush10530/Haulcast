"""API views for Haulcast."""

from rest_framework import exceptions
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from api.container import get_container
from api.serializers import TripRequestSerializer, format_heatmap_response, format_trip_analysis
from api.throttles import AnalyzeThrottle, GeocodeThrottle, HeatmapThrottle
from core.domain.types import Warning


class HealthCheckView(APIView):
    """Health check endpoint returning service status."""

    def get(self, request: Request) -> Response:
        return Response({"status": "ok"})


class GeocodeView(APIView):
    """Geocode search endpoint returning matching places."""

    throttle_classes = [GeocodeThrottle]
    throttle_scope = "geocode"

    def get(self, request: Request) -> Response:
        q = request.query_params.get("q", "").strip()
        if len(q) < 3 or len(q) > 100:
            raise exceptions.ValidationError(
                {"q": ["Query string 'q' must be between 3 and 100 characters."]}
            )
        places = get_container().geocoding.search(q, limit=5)
        results = [
            {
                "id": p.id or f"{p.coordinate.lat:.5f},{p.coordinate.lon:.5f}",
                "label": p.label,
                "lat": p.coordinate.lat,
                "lon": p.coordinate.lon,
            }
            for p in places
        ]
        return Response(results)


class TripAnalyzeView(APIView):
    """Trip analysis endpoint assessing routes, weather risks, and recommendations."""

    throttle_classes = [AnalyzeThrottle]
    throttle_scope = "analyze"

    def post(self, request: Request) -> Response:
        serializer = TripRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        trip_request = serializer.to_domain()

        analysis = get_container().trip_analysis.analyze(trip_request)
        warnings = list(analysis.warnings)
        if trip_request.load_weight_lb > 80000:
            warnings.append(
                Warning(
                    code="LOAD_ABOVE_LEGAL_LIMIT",
                    message=(
                        "Load weight exceeds standard legal limit of 80,000 lb. "
                        "Overweight permits may be required."
                    ),
                )
            )

        return Response(format_trip_analysis(analysis, warnings=warnings))


class TripHeatmapView(APIView):
    """Trip corridor heatmap endpoint returning grid cells and 49 hourly risk frames."""

    throttle_classes = [HeatmapThrottle]
    throttle_scope = "heatmap"

    def post(self, request: Request) -> Response:
        serializer = TripRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        trip_request = serializer.to_domain()

        result = get_container().heatmap_service.build(trip_request)
        return Response(format_heatmap_response(result))
