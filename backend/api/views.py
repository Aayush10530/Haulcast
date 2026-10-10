"""API views for Haulcast."""

from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView


class HealthCheckView(APIView):
    """Health check endpoint returning service status."""

    def get(self, request: Request) -> Response:
        return Response({"status": "ok"})
