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


def _build_departure_window_error(
    exc: DepartureOutOfWindowError,
) -> tuple[int, str, str, dict[str, Any] | None]:
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
    return (
        status.HTTP_400_BAD_REQUEST,
        "validation_error",
        "Departure time is outside the allowed window.",
        {"departure_local": [msg]},
    )


def _build_nonexistent_local_time(
    exc: NonexistentLocalTimeError,
) -> tuple[int, str, str, dict[str, Any] | None]:
    return (
        status.HTTP_400_BAD_REQUEST,
        "validation_error",
        "Invalid departure time.",
        {"departure_local": [str(exc)]},
    )


def _build_drf_validation_error(
    exc: exceptions.ValidationError,
) -> tuple[int, str, str, dict[str, Any] | None]:
    fields_data: dict[str, Any] = {}
    if isinstance(exc.detail, dict):
        for k, v in exc.detail.items():
            fields_data[k] = [str(item) for item in v] if isinstance(v, list) else [str(v)]
    elif isinstance(exc.detail, list):
        fields_data["non_field_errors"] = [str(item) for item in exc.detail]
    else:
        fields_data["detail"] = [str(exc.detail)]
    return (
        status.HTTP_400_BAD_REQUEST,
        "validation_error",
        "Validation failed.",
        fields_data,
    )


def _build_no_route(exc: NoRouteFound) -> tuple[int, str, str, dict[str, Any] | None]:
    return (
        status.HTTP_422_UNPROCESSABLE_ENTITY,
        "no_route_found",
        str(exc) or "No route found between origin and destination.",
        None,
    )


def _build_beyond_horizon(
    exc: BeyondForecastHorizonError,
) -> tuple[int, str, str, dict[str, Any] | None]:
    return (
        status.HTTP_422_UNPROCESSABLE_ENTITY,
        "beyond_forecast_horizon",
        str(exc) or "Trip times extend beyond the available forecast horizon.",
        None,
    )


def _build_rate_limited(exc: ProviderRateLimited) -> tuple[int, str, str, dict[str, Any] | None]:
    is_weather = "weather" in str(exc).lower()
    return (
        status.HTTP_503_SERVICE_UNAVAILABLE,
        "weather_unavailable" if is_weather else "routing_unavailable",
        (
            "Weather service rate limit exceeded. Please try again later."
            if is_weather
            else "Routing service rate limit exceeded. Please try again later."
        ),
        None,
    )


def _build_unavailable(exc: ProviderUnavailable) -> tuple[int, str, str, dict[str, Any] | None]:
    is_weather = "weather" in str(exc).lower()
    return (
        status.HTTP_503_SERVICE_UNAVAILABLE,
        "weather_unavailable" if is_weather else "routing_unavailable",
        (
            "Weather service is currently unavailable. Please try again later."
            if is_weather
            else "Routing service is currently unavailable. Please try again later."
        ),
        None,
    )


def _build_timeout(_exc: ProviderTimeout) -> tuple[int, str, str, dict[str, Any] | None]:
    return (
        status.HTTP_504_GATEWAY_TIMEOUT,
        "upstream_timeout",
        "An upstream provider timed out.",
        None,
    )


def _build_bad_response(_exc: ProviderBadResponse) -> tuple[int, str, str, dict[str, Any] | None]:
    return (
        status.HTTP_502_BAD_GATEWAY,
        "upstream_error",
        "An upstream provider returned an unexpected or malformed response.",
        None,
    )


def _build_throttled(exc: exceptions.Throttled) -> tuple[int, str, str, dict[str, Any] | None]:
    msg = (
        f"Request was throttled. Expected available in {exc.wait} seconds."
        if exc.wait is not None
        else "Request was throttled."
    )
    return (
        status.HTTP_429_TOO_MANY_REQUESTS,
        "rate_limited",
        msg,
        None,
    )


_EXCEPTION_HANDLERS: tuple[tuple[type[Exception], Any], ...] = (
    (DepartureOutOfWindowError, _build_departure_window_error),
    (NonexistentLocalTimeError, _build_nonexistent_local_time),
    (exceptions.ValidationError, _build_drf_validation_error),
    (NoRouteFound, _build_no_route),
    (BeyondForecastHorizonError, _build_beyond_horizon),
    (ProviderRateLimited, _build_rate_limited),
    (ProviderUnavailable, _build_unavailable),
    (ProviderTimeout, _build_timeout),
    (ProviderBadResponse, _build_bad_response),
    (exceptions.Throttled, _build_throttled),
)


def custom_exception_handler(exc: Exception, context: dict[str, Any]) -> Response:
    """DRF custom exception handler producing standard JSON error envelopes."""
    for exc_cls, handler in _EXCEPTION_HANDLERS:
        if isinstance(exc, exc_cls):
            http_status, code, message, fields = handler(exc)
            return Response(
                _format_error_envelope(code=code, message=message, fields=fields),
                status=http_status,
            )

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

    logger.error("Unhandled exception: %s", exc.__class__.__name__)
    return Response(
        _format_error_envelope(
            code="internal_error",
            message="An internal server error occurred.",
        ),
        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )
