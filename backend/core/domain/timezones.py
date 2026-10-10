"""Domain timezone conversions and departure window validation."""

import datetime
import zoneinfo

from core.domain import rules_config
from core.domain.errors import DepartureOutOfWindowError, NonexistentLocalTimeError


def _get_zone(tz_name: str) -> zoneinfo.ZoneInfo:
    if not tz_name or not isinstance(tz_name, str) or not tz_name.strip():
        raise ValueError(f"Invalid timezone name: {tz_name!r}")
    try:
        return zoneinfo.ZoneInfo(tz_name)
    except (zoneinfo.ZoneInfoNotFoundError, ValueError) as err:
        raise ValueError(f"Unknown or invalid timezone: {tz_name!r}") from err


def local_to_utc(local: datetime.datetime, tz_name: str) -> datetime.datetime:
    """Convert naive local datetime to timezone-aware UTC datetime."""
    if local.tzinfo is not None:
        raise ValueError(f"local datetime must be naive, got aware: {local}")

    tz = _get_zone(tz_name)
    local_folded = local.replace(tzinfo=tz, fold=0)
    utc_dt = local_folded.astimezone(datetime.UTC)

    back = utc_dt.astimezone(tz)
    if back.replace(tzinfo=None) != local:
        raise NonexistentLocalTimeError(
            f"Local time {local} does not exist in timezone {tz_name} (spring-forward gap)"
        )

    return utc_dt


def utc_to_local(utc_dt: datetime.datetime, tz_name: str) -> datetime.datetime:
    """Convert timezone-aware UTC datetime to timezone-aware local datetime."""
    if utc_dt.tzinfo is None or utc_dt.tzinfo.utcoffset(utc_dt) is None:
        raise ValueError(f"utc_dt must be timezone-aware, got naive: {utc_dt}")

    tz = _get_zone(tz_name)
    return utc_dt.astimezone(tz)


def validate_departure_window(
    departure_utc: datetime.datetime,
    now_utc: datetime.datetime,
) -> None:
    """Validate that departure is within allowed scheduling window [now-1h, now+7d]."""
    if departure_utc.tzinfo is None or departure_utc.tzinfo.utcoffset(departure_utc) is None:
        raise ValueError(f"departure_utc must be timezone-aware, got {departure_utc}")
    if now_utc.tzinfo is None or now_utc.tzinfo.utcoffset(now_utc) is None:
        raise ValueError(f"now_utc must be timezone-aware, got {now_utc}")

    dep = departure_utc.astimezone(datetime.UTC)
    now = now_utc.astimezone(datetime.UTC)

    allowed_from = now - datetime.timedelta(hours=rules_config.DEPARTURE_PAST_GRACE_HOURS)
    allowed_to = now + datetime.timedelta(days=rules_config.DEPARTURE_MAX_DAYS_AHEAD)

    if dep < allowed_from or dep > allowed_to:
        raise DepartureOutOfWindowError(
            f"Departure {dep.isoformat()} outside window "
            f"[{allowed_from.isoformat()}, {allowed_to.isoformat()}]",
            allowed_from=allowed_from,
            allowed_to=allowed_to,
        )
