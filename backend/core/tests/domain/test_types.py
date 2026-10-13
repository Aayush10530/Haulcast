"""Domain unit tests for core dataclasses in types.py."""

import datetime

import pytest

from core.domain.types import Coordinate, IntervalMode, Place, TripRequest, TripRequestEcho


@pytest.fixture
def places() -> tuple[Place, Place]:
    return (
        Place("Dallas, TX", Coordinate(32.7767, -96.7970)),
        Place("Denver, CO", Coordinate(39.7392, -104.9903)),
    )


def test_trip_request_accepts_zero_load_weight(places: tuple[Place, Place]) -> None:
    p_orig, p_dest = places
    req = TripRequest(
        origin=p_orig,
        destination=p_dest,
        departure_local=datetime.datetime(2026, 10, 12, 8, 0, 0),
        load_weight_lb=0,
        interval_mode=IntervalMode.AUTO,
    )
    assert req.load_weight_lb == 0


def test_trip_request_rejects_negative_load_weight(places: tuple[Place, Place]) -> None:
    p_orig, p_dest = places
    with pytest.raises(ValueError, match="load_weight_lb must be non-negative"):
        TripRequest(
            origin=p_orig,
            destination=p_dest,
            departure_local=datetime.datetime(2026, 10, 12, 8, 0, 0),
            load_weight_lb=-1,
            interval_mode=IntervalMode.AUTO,
        )


def test_trip_request_rejects_bool_and_non_int_load_weight(places: tuple[Place, Place]) -> None:
    p_orig, p_dest = places
    with pytest.raises(TypeError, match="load_weight_lb must be an int"):
        TripRequest(
            origin=p_orig,
            destination=p_dest,
            departure_local=datetime.datetime(2026, 10, 12, 8, 0, 0),
            load_weight_lb=True,  # type: ignore[arg-type]
            interval_mode=IntervalMode.AUTO,
        )

    with pytest.raises(TypeError, match="load_weight_lb must be an int"):
        TripRequest(
            origin=p_orig,
            destination=p_dest,
            departure_local=datetime.datetime(2026, 10, 12, 8, 0, 0),
            load_weight_lb=42000.5,  # type: ignore[arg-type]
            interval_mode=IntervalMode.AUTO,
        )

    with pytest.raises(TypeError, match="load_weight_lb must be an int"):
        TripRequest(
            origin=p_orig,
            destination=p_dest,
            departure_local=datetime.datetime(2026, 10, 12, 8, 0, 0),
            load_weight_lb=float("nan"),  # type: ignore[arg-type]
            interval_mode=IntervalMode.AUTO,
        )


def test_trip_request_echo_accepts_zero_and_rejects_invalid_weights(
    places: tuple[Place, Place],
) -> None:
    p_orig, p_dest = places
    utc_dt = datetime.datetime(2026, 10, 12, 13, 0, 0, tzinfo=datetime.UTC)
    local_dt = datetime.datetime(2026, 10, 12, 8, 0, 0)

    echo = TripRequestEcho(
        origin=p_orig,
        destination=p_dest,
        departure_utc=utc_dt,
        departure_local=local_dt,
        origin_tz="America/Chicago",
        load_weight_lb=0,
        interval_miles=10,
        interval_mode=IntervalMode.AUTO,
    )
    assert echo.load_weight_lb == 0

    with pytest.raises(ValueError, match="load_weight_lb must be non-negative"):
        TripRequestEcho(
            origin=p_orig,
            destination=p_dest,
            departure_utc=utc_dt,
            departure_local=local_dt,
            origin_tz="America/Chicago",
            load_weight_lb=-50,
            interval_miles=10,
            interval_mode=IntervalMode.AUTO,
        )

    with pytest.raises(TypeError, match="load_weight_lb must be an int"):
        TripRequestEcho(
            origin=p_orig,
            destination=p_dest,
            departure_utc=utc_dt,
            departure_local=local_dt,
            origin_tz="America/Chicago",
            load_weight_lb=False,  # type: ignore[arg-type]
            interval_miles=10,
            interval_mode=IntervalMode.AUTO,
        )
