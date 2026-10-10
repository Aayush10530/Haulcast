import datetime

import pytest

from core.domain.errors import DepartureOutOfWindowError, NonexistentLocalTimeError
from core.domain.timezones import local_to_utc, utc_to_local, validate_departure_window


def test_local_to_utc_chicago_daylight_saving_converts_to_thirteen_utc() -> None:
    dt = datetime.datetime(2026, 10, 12, 8, 0, 0)
    utc = local_to_utc(dt, "America/Chicago")
    assert utc == datetime.datetime(2026, 10, 12, 13, 0, 0, tzinfo=datetime.UTC)


def test_local_to_utc_chicago_standard_time_converts_to_fourteen_utc() -> None:
    dt = datetime.datetime(2026, 12, 1, 8, 0, 0)
    utc = local_to_utc(dt, "America/Chicago")
    assert utc == datetime.datetime(2026, 12, 1, 14, 0, 0, tzinfo=datetime.UTC)


def test_local_to_utc_kolkata_converts_to_two_thirty_utc() -> None:
    dt = datetime.datetime(2026, 10, 12, 8, 0, 0)
    utc = local_to_utc(dt, "Asia/Kolkata")
    assert utc == datetime.datetime(2026, 10, 12, 2, 30, 0, tzinfo=datetime.UTC)


def test_local_to_utc_spring_forward_gap_raises_nonexistent_local_time_error() -> None:
    dt = datetime.datetime(2026, 3, 8, 2, 30, 0)
    with pytest.raises(NonexistentLocalTimeError, match="spring-forward gap"):
        local_to_utc(dt, "America/Chicago")


def test_local_to_utc_spring_forward_after_jump_converts_successfully() -> None:
    dt = datetime.datetime(2026, 3, 8, 3, 30, 0)
    utc = local_to_utc(dt, "America/Chicago")
    assert utc == datetime.datetime(2026, 3, 8, 8, 30, 0, tzinfo=datetime.UTC)


def test_local_to_utc_fall_back_ambiguous_time_resolves_to_first_occurrence() -> None:
    dt = datetime.datetime(2026, 11, 1, 1, 30, 0)
    utc = local_to_utc(dt, "America/Chicago")
    assert utc == datetime.datetime(2026, 11, 1, 6, 30, 0, tzinfo=datetime.UTC)


def test_local_to_utc_fall_back_boundaries_before_and_after_overlap() -> None:
    dt_before = datetime.datetime(2026, 11, 1, 0, 30, 0)
    utc_before = local_to_utc(dt_before, "America/Chicago")
    assert utc_before == datetime.datetime(2026, 11, 1, 5, 30, 0, tzinfo=datetime.UTC)

    dt_after = datetime.datetime(2026, 11, 1, 2, 30, 0)
    utc_after = local_to_utc(dt_after, "America/Chicago")
    assert utc_after == datetime.datetime(2026, 11, 1, 8, 30, 0, tzinfo=datetime.UTC)


def test_local_to_utc_aware_input_raises_value_error() -> None:
    aware = datetime.datetime(2026, 10, 12, 8, 0, 0, tzinfo=datetime.UTC)
    with pytest.raises(ValueError, match="local datetime must be naive"):
        local_to_utc(aware, "America/Chicago")


@pytest.mark.parametrize("invalid_tz", ["", "   ", "Invalid/Timezone", "Mars/Olympus"])
def test_local_to_utc_invalid_or_empty_timezone_raises_value_error(invalid_tz: str) -> None:
    dt = datetime.datetime(2026, 10, 12, 8, 0, 0)
    with pytest.raises(ValueError, match="timezone"):
        local_to_utc(dt, invalid_tz)


def test_utc_to_local_round_trips_across_both_dst_changes() -> None:
    tz_name = "America/Chicago"

    # Spring-forward transition
    spring_utc = datetime.datetime(2026, 3, 8, 8, 30, 0, tzinfo=datetime.UTC)
    spring_local = utc_to_local(spring_utc, tz_name)
    assert spring_local.hour == 3
    assert spring_local.minute == 30
    assert spring_local.astimezone(datetime.UTC) == spring_utc

    # Fall-back first occurrence (06:30Z -> 01:30 CDT fold=0)
    fall1_utc = datetime.datetime(2026, 11, 1, 6, 30, 0, tzinfo=datetime.UTC)
    fall1_local = utc_to_local(fall1_utc, tz_name)
    assert fall1_local.hour == 1
    assert fall1_local.minute == 30
    assert fall1_local.fold == 0
    assert fall1_local.astimezone(datetime.UTC) == fall1_utc

    # Fall-back second occurrence (07:30Z -> 01:30 CST fold=1)
    fall2_utc = datetime.datetime(2026, 11, 1, 7, 30, 0, tzinfo=datetime.UTC)
    fall2_local = utc_to_local(fall2_utc, tz_name)
    assert fall2_local.hour == 1
    assert fall2_local.minute == 30
    assert fall2_local.fold == 1
    assert fall2_local.astimezone(datetime.UTC) == fall2_utc


def test_utc_to_local_naive_input_raises_value_error() -> None:
    naive = datetime.datetime(2026, 10, 12, 8, 0, 0)
    with pytest.raises(ValueError, match="utc_dt must be timezone-aware"):
        utc_to_local(naive, "America/Chicago")


@pytest.mark.parametrize("invalid_tz", ["", "   ", "Invalid/Timezone"])
def test_utc_to_local_invalid_timezone_raises_value_error(invalid_tz: str) -> None:
    utc = datetime.datetime(2026, 10, 12, 8, 0, 0, tzinfo=datetime.UTC)
    with pytest.raises(ValueError, match="timezone"):
        utc_to_local(utc, invalid_tz)


def test_validate_departure_window_exact_minus_one_hour_passes() -> None:
    now = datetime.datetime(2026, 10, 15, 12, 0, 0, tzinfo=datetime.UTC)
    dep = now - datetime.timedelta(hours=1)
    validate_departure_window(dep, now)


def test_validate_departure_window_one_second_before_minus_one_hour_fails() -> None:
    now = datetime.datetime(2026, 10, 15, 12, 0, 0, tzinfo=datetime.UTC)
    dep = now - datetime.timedelta(hours=1, seconds=1)
    with pytest.raises(DepartureOutOfWindowError) as exc_info:
        validate_departure_window(dep, now)

    err = exc_info.value
    expected_from = now - datetime.timedelta(hours=1)
    expected_to = now + datetime.timedelta(days=7)
    assert err.allowed_from == expected_from
    assert err.allowed_to == expected_to


def test_validate_departure_window_exact_plus_seven_days_passes() -> None:
    now = datetime.datetime(2026, 10, 15, 12, 0, 0, tzinfo=datetime.UTC)
    dep = now + datetime.timedelta(days=7)
    validate_departure_window(dep, now)


def test_validate_departure_window_one_second_after_plus_seven_days_fails() -> None:
    now = datetime.datetime(2026, 10, 15, 12, 0, 0, tzinfo=datetime.UTC)
    dep = now + datetime.timedelta(days=7, seconds=1)
    with pytest.raises(DepartureOutOfWindowError) as exc_info:
        validate_departure_window(dep, now)

    err = exc_info.value
    expected_from = now - datetime.timedelta(hours=1)
    expected_to = now + datetime.timedelta(days=7)
    assert err.allowed_from == expected_from
    assert err.allowed_to == expected_to


def test_validate_departure_window_naive_arguments_raise_value_error() -> None:
    now = datetime.datetime(2026, 10, 15, 12, 0, 0, tzinfo=datetime.UTC)
    dep = now + datetime.timedelta(days=1)
    naive = datetime.datetime(2026, 10, 15, 12, 0, 0)

    with pytest.raises(ValueError, match="departure_utc must be timezone-aware"):
        validate_departure_window(naive, now)

    with pytest.raises(ValueError, match="now_utc must be timezone-aware"):
        validate_departure_window(dep, naive)
