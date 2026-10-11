"""Shared departure time resolution and window validation for services."""

import datetime
from collections.abc import Callable

from core.domain import timezones
from core.domain.errors import DepartureOutOfWindowError
from core.domain.types import Coordinate
from core.providers.base import WeatherProvider


def resolve_departure(
    origin_coord: Coordinate,
    departure_local: datetime.datetime,
    weather: WeatherProvider,
    clock: Callable[[], datetime.datetime],
) -> tuple[str, datetime.datetime]:
    """Resolve origin timezone, convert local departure to UTC, and validate window."""
    origin_tz = weather.get_timezone(origin_coord)
    departure_utc = timezones.local_to_utc(departure_local, origin_tz)
    try:
        timezones.validate_departure_window(departure_utc, now_utc=clock())
    except DepartureOutOfWindowError as e:
        raise DepartureOutOfWindowError(
            str(e),
            allowed_from=e.allowed_from,
            allowed_to=e.allowed_to,
            origin_tz=origin_tz,
        ) from e
    return origin_tz, departure_utc
