"""Uniform error handling and HTTP status mapping for API layer."""

import logging
from typing import Any

from rest_framework import exceptions, status
from rest_framework.response import Response
from rest_framework.views import exception_handler

from core.domain import timezones
from core.domain.errors import (
    BeyondForecastHorizonError,
    DepartureOutOfWindowError,
    NonexistentLocalTimeError,
)
from core.providers.base import (
    NoRouteFound,
    ProviderBadResponse,
    ProviderRateLimited,
    ProviderTimeout,
    ProviderUnavailable,
)

logger = logging.getLogger(__name__)


def _format_error_envelope(
    code: str,
    message: str,
    fields: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "error": {
            "code": code,
            "message": message,
        }
    }
    if fields:
        payload["error"]["fields"] = fields
    return payload


def custom_exception_handler(exc: Exception, context: dict[str, Any]) -> Response:
    """DRF custom exception handler producing standard JSON error envelopes."""
    # 1. Departure out of window error (400 validation_error with field error)
    if isinstance(exc, DepartureOutOfWindowError):
        if exc.origin_tz:
            from_local = timezones.utc_to_local(exc.allowed_from, exc.origin_tz)
            to_local = timezones.utc_to_local(exc.allowed_to, exc.origin_tz)
            msg = (
                f"Departure time must be between {from_local.strftime('%Y-%m-%d %H:%M')} "
                f"and {to_local.strftime('%Y-%m-%d %H:%M')} in {exc.origin_tz}."
            )
        else:
            msg = (
                f"Departure time must be between {exc.allowed_from.isoformat()} "
                f"and {exc.allowed_to.isoformat()}."
            )
        return Response(
            _format_error_envelope(
                code="validation_error",
                message="Departure time is outside the allowed window.",
                fields={"departure_local": [msg]},
            ),
            status=status.HTTP_400_BAD_REQUEST,
        )

    # 2. Nonexistent local time (400 validation_error with field error)
    if isinstance(exc, NonexistentLocalTimeError):
        return Response(
            _format_error_envelope(
                code="validation_error",
                message="Invalid departure time.",
                fields={"departure_local": [str(exc)]},
            ),
            status=status.HTTP_400_BAD_REQUEST,
        )

    # 3. DRF Validation Error (400 validation_error with fields)
    if isinstance(exc, exceptions.ValidationError):
        fields_data: dict[str, Any] = {}
        if isinstance(exc.detail, dict):
            for k, v in exc.detail.items():
                if isinstance(v, list):
                    fields_data[k] = [str(item) for item in v]
                else:
                    fields_data[k] = [str(v)]
        elif isinstance(exc.detail, list):
            fields_data["non_field_errors"] = [str(item) for item in exc.detail]
        else:
            fields_data["detail"] = [str(exc.detail)]

        return Response(
            _format_error_envelope(
                code="validation_error",
                message="Validation failed.",
                fields=fields_data,
            ),
            status=status.HTTP_400_BAD_REQUEST,
        )

    # 4. NoRouteFound (422 no_route_found)
    if isinstance(exc, NoRouteFound):
        return Response(
            _format_error_envelope(
                code="no_route_found",
                message=str(exc) or "No route found between origin and destination.",
            ),
            status=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )

    # 5. BeyondForecastHorizonError (422 beyond_forecast_horizon)
    if isinstance(exc, BeyondForecastHorizonError):
        return Response(
            _format_error_envelope(
                code="beyond_forecast_horizon",
                message=str(exc) or "Trip times extend beyond the available forecast horizon.",
            ),
            status=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )

    # 6. ProviderRateLimited (503 weather_unavailable or routing_unavailable)
    if isinstance(exc, ProviderRateLimited):
        is_weather = "weather" in str(exc).lower()
        code = "weather_unavailable" if is_weather else "routing_unavailable"
        msg = (
            "Weather service rate limit exceeded. Please try again later."
            if is_weather
            else "Routing service rate limit exceeded. Please try again later."
        )
        return Response(
            _format_error_envelope(code=code, message=msg),
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )

    # 7. ProviderUnavailable (503 weather_unavailable or routing_unavailable)
    if isinstance(exc, ProviderUnavailable):
        is_weather = "weather" in str(exc).lower()
        code = "weather_unavailable" if is_weather else "routing_unavailable"
        msg = (
            "Weather service is currently unavailable. Please try again later."
            if is_weather
            else "Routing service is currently unavailable. Please try again later."
        )
        return Response(
            _format_error_envelope(code=code, message=msg),
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )

    # 8. ProviderTimeout (504 upstream_timeout)
    if isinstance(exc, ProviderTimeout):
        return Response(
            _format_error_envelope(
                code="upstream_timeout",
                message="An upstream provider timed out.",
            ),
            status=status.HTTP_504_GATEWAY_TIMEOUT,
        )

    # 9. ProviderBadResponse (502 upstream_error)
    if isinstance(exc, ProviderBadResponse):
        return Response(
            _format_error_envelope(
                code="upstream_error",
                message="An upstream provider returned an unexpected or malformed response.",
            ),
            status=status.HTTP_502_BAD_GATEWAY,
        )

    # 10. DRF Throttled (429 rate_limited)
    if isinstance(exc, exceptions.Throttled):
        msg = (
            f"Request was throttled. Expected available in {exc.wait} seconds."
            if exc.wait is not None
            else "Request was throttled."
        )
        return Response(
            _format_error_envelope(code="rate_limited", message=msg),
            status=status.HTTP_429_TOO_MANY_REQUESTS,
        )

    # 11. Other DRF API exceptions (e.g. MethodNotAllowed, NotAcceptable, ParseError)
    if isinstance(exc, exceptions.APIException):
        response = exception_handler(exc, context)
        if response is not None:
            return Response(
                _format_error_envelope(
                    code=getattr(exc, "default_code", "api_error"),
                    message=str(exc.detail) if hasattr(exc, "detail") else str(exc),
                ),
                status=response.status_code,
            )

    # 12. Anything else -> 500 internal_error
    logger.error("Unhandled exception: %s", exc.__class__.__name__)
    return Response(
        _format_error_envelope(
            code="internal_error",
            message="An internal server error occurred.",
        ),
        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )
