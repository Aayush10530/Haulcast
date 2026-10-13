"""Comprehensive automated tests for controlled weather scenarios, boundary handling,
load-weight overrides, route ranking priority, and risk-mile conservation.
"""

import datetime
import math

import pytest

from core.domain import geometry, risk, scoring
from core.domain.ranking import rank_routes
from core.domain.types import (
    Coordinate,
    HourlySeries,
    MilesByLevel,
    Place,
    RankingInput,
    RawRoute,
    RiskDriver,
    RiskLevel,
    RouteSummary,
    Timeline,
    WeatherSample,
    WeatherSeries,
)

# ==============================================================================
# Helper Factories
# ==============================================================================


def _make_route(
    route_id: str,
    polyline: tuple[Coordinate, ...],
    distance_miles: float,
    duration_seconds: float,
) -> RawRoute:
    timeline = Timeline.from_points([(0.0, 0.0), (distance_miles, duration_seconds)])
    return RawRoute(
        provider_id=route_id,
        polyline=polyline,
        distance_miles=distance_miles,
        duration_seconds=duration_seconds,
        timeline=timeline,
    )


def _make_series(
    start_epoch: int,
    count: int = 48,
    wind: float | None = 10.0,
    rain: float | None = 0.0,
    snow: float | None = 0.0,
    tz_name: str = "America/New_York",
) -> WeatherSeries:
    w = HourlySeries(start_epoch=start_epoch, values=tuple(wind for _ in range(count)))
    r = HourlySeries(start_epoch=start_epoch, values=tuple(rain for _ in range(count)))
    s = HourlySeries(start_epoch=start_epoch, values=tuple(snow for _ in range(count)))
    return WeatherSeries(tz_name=tz_name, wind_mph=w, rain_in_hr=r, snow_in_hr=s)


# ==============================================================================
# 1. Weather Threshold Boundaries & Mutual Exclusivity
# ==============================================================================


class TestWeatherThresholdBoundaries:
    """Tests every threshold boundary with lower-bound inclusive [min, max) definition."""

    @pytest.mark.parametrize(
        ("val", "expected"),
        [
            (0.0, RiskLevel.LOW),
            (24.9, RiskLevel.LOW),
            (25.0, RiskLevel.MODERATE),  # 25.0 inclusive lower bound of Moderate
            (34.9, RiskLevel.MODERATE),
            (35.0, RiskLevel.HIGH),  # 35.0 inclusive lower bound of High
            (44.9, RiskLevel.HIGH),
            (45.0, RiskLevel.SEVERE),  # 45.0 inclusive lower bound of Severe
            (54.9, RiskLevel.SEVERE),
            (55.0, RiskLevel.NO_TRAVEL),  # 55.0 inclusive lower bound of No Travel
            (70.0, RiskLevel.NO_TRAVEL),
        ],
    )
    def test_wind_boundaries_mutually_exclusive(self, val: float, expected: RiskLevel) -> None:
        assert risk.classify_wind(val) == expected

    @pytest.mark.parametrize(
        ("val", "expected"),
        [
            (0.0, RiskLevel.LOW),
            (0.09, RiskLevel.LOW),
            (0.10, RiskLevel.MODERATE),  # 0.10 inclusive lower bound of Moderate
            (0.24, RiskLevel.MODERATE),
            (0.25, RiskLevel.HIGH),  # 0.25 inclusive lower bound of High
            (0.49, RiskLevel.HIGH),
            (0.50, RiskLevel.SEVERE),  # 0.50 inclusive lower bound of Severe
            (1.00, RiskLevel.SEVERE),  # 1.00 inclusive upper bound of Severe
            (1.01, RiskLevel.NO_TRAVEL),  # > 1.00 is No Travel
            (2.50, RiskLevel.NO_TRAVEL),
        ],
    )
    def test_rain_boundaries_mutually_exclusive(self, val: float, expected: RiskLevel) -> None:
        assert risk.classify_rain(val) == expected

    @pytest.mark.parametrize(
        ("val", "expected"),
        [
            (0.0, RiskLevel.LOW),
            (0.49, RiskLevel.LOW),
            (0.50, RiskLevel.MODERATE),  # 0.50 inclusive lower bound of Moderate
            (0.99, RiskLevel.MODERATE),
            (1.00, RiskLevel.HIGH),  # 1.00 inclusive lower bound of High
            (1.99, RiskLevel.HIGH),
            (2.00, RiskLevel.SEVERE),  # 2.00 inclusive lower bound of Severe
            (3.00, RiskLevel.SEVERE),  # 3.00 inclusive upper bound of Severe
            (3.01, RiskLevel.NO_TRAVEL),  # > 3.00 is No Travel
            (5.00, RiskLevel.NO_TRAVEL),
        ],
    )
    def test_snow_boundaries_mutually_exclusive(self, val: float, expected: RiskLevel) -> None:
        assert risk.classify_snow(val) == expected


# ==============================================================================
# 2. Load-Weight Overrides (Below, At, and Above Limits)
# ==============================================================================


class TestLoadWeightOverrides:
    """Tests all three load overrides with exact values below, at, and above limits."""

    def test_wind_55_plus_is_no_travel_regardless_of_load(self) -> None:
        sample = WeatherSample(wind_mph=55.0, rain_in_hr=0.0, snow_in_hr=0.0)
        # Any load weight, including 0, empty truck (15k), and heavy (80k)
        for load in [0.0, 15_000.0, 30_000.0, 40_000.0, 80_000.0]:
            res = risk.assess(sample, load)
            assert res.level == RiskLevel.NO_TRAVEL
            assert res.driver == RiskDriver.WIND
            assert res.load_rule_applied is False  # Wind alone dictated No Travel

    def test_wind_45_to_54_mph_load_30000_lb_boundary(self) -> None:
        sample = WeatherSample(wind_mph=50.0, rain_in_hr=0.0, snow_in_hr=0.0)  # Severe wind
        # 1 lb below limit: remains Severe
        res_below = risk.assess(sample, 29_999.0)
        assert res_below.level == RiskLevel.SEVERE
        assert res_below.load_rule_applied is False

        # Exactly at limit (30,000 lb): remains Severe (rule requires strictly above 30,000 lb)
        res_at = risk.assess(sample, 30_000.0)
        assert res_at.level == RiskLevel.SEVERE
        assert res_at.load_rule_applied is False

        # 1 lb above limit (30,001 lb): escalates to No Travel
        res_above = risk.assess(sample, 30_001.0)
        assert res_above.level == RiskLevel.NO_TRAVEL
        assert res_above.driver == RiskDriver.LOAD_RULE
        assert res_above.load_rule_applied is True

    def test_wind_35_to_44_mph_load_40000_lb_boundary(self) -> None:
        sample = WeatherSample(wind_mph=40.0, rain_in_hr=0.0, snow_in_hr=0.0)  # High wind
        # 1 lb below limit: remains High
        res_below = risk.assess(sample, 39_999.0)
        assert res_below.level == RiskLevel.HIGH
        assert res_below.load_rule_applied is False

        # Exactly at limit (40,000 lb): remains High (rule requires strictly above 40,000 lb)
        res_at = risk.assess(sample, 40_000.0)
        assert res_at.level == RiskLevel.HIGH
        assert res_at.load_rule_applied is False

        # 1 lb above limit (40,001 lb): escalates to Severe
        res_above = risk.assess(sample, 40_001.0)
        assert res_above.level == RiskLevel.SEVERE
        assert res_above.driver == RiskDriver.LOAD_RULE
        assert res_above.load_rule_applied is True


# ==============================================================================
# 3. Conservation of Distance (Miles by Level Sum Invariant)
# ==============================================================================


class TestDistanceConservation:
    """Verifies that miles assigned to all risk categories sum to the exact route distance."""

    def test_sum_of_miles_by_level_equals_route_distance(self) -> None:
        p1 = Place("Boston, MA", Coordinate(42.3601, -71.0589))
        p2 = Place("New York, NY", Coordinate(40.7128, -74.0060))
        r1 = _make_route(
            "r1", (p1.coordinate, Coordinate(41.5, -72.5), p2.coordinate), 218.9, 14400.0
        )

        cum = geometry.cumulative_miles(r1.polyline, r1.distance_miles)
        from core.domain.sampling import build_checkpoints

        checkpoints = build_checkpoints(r1.polyline, cum, 25)

        start_epoch = 1791694800
        # Inject mix of weather: Low, Moderate, High, Severe, No Travel
        series_low = _make_series(start_epoch, count=24, wind=10.0)
        series_mod = _make_series(start_epoch, count=24, rain=0.15)
        series_high = _make_series(start_epoch, count=24, wind=38.0)
        series_severe = _make_series(start_epoch, count=24, rain=0.75)
        series_no_travel = _make_series(start_epoch, count=24, wind=58.0)

        series_cycle = [series_low, series_mod, series_high, series_severe, series_no_travel]

        assessed_cps = []
        for idx, cp in enumerate(checkpoints):
            s = series_cycle[idx % len(series_cycle)]
            eta = datetime.datetime.fromtimestamp(start_epoch + idx * 1800, tz=datetime.UTC)
            ac = scoring.assess_checkpoint(cp, eta, s, load_weight_lb=35000.0)
            assessed_cps.append(ac)

        summary = scoring.summarize_route(
            assessed=tuple(assessed_cps),
            distance_miles=r1.distance_miles,
            duration_seconds=r1.duration_seconds,
        )

        m = summary.miles_by_level
        total_sum = math.fsum(
            [m.low, m.moderate, m.high, m.severe, m.no_travel, summary.unavailable_miles]
        )
        assert abs(total_sum - r1.distance_miles) < 1e-4


# ==============================================================================
# 4. Route Ranking Priority (Lexicographic Comparison)
# ==============================================================================


class TestRouteRankingPriority:
    """Verifies strict 4-tier lexicographic ranking with controlled fixtures."""

    def _make_summary(
        self,
        severe: float = 0.0,
        high: float = 0.0,
        no_travel: float = 0.0,
        avg_risk: float = 0.0,
        duration: float = 3600.0,
    ) -> RouteSummary:
        return RouteSummary(
            distance_miles=100.0,
            duration_seconds=duration,
            miles_by_level=MilesByLevel(
                low=100.0 - severe - high - no_travel,
                moderate=0.0,
                high=high,
                severe=severe,
                no_travel=no_travel,
            ),
            unavailable_miles=0.0,
            avg_risk_score=avg_risk,
            max_level=RiskLevel.LOW,
            unavailable_checkpoints=0,
        )

    def test_priority_1_fewest_severe_miles_outranks_faster_route(self) -> None:
        # Route A has 5.0 Severe miles, but is 2 hours faster (duration 3600s vs 10800s)
        # Route B has 0.0 Severe miles
        # Deterministic rule: Route B MUST WIN on safety regardless of speed
        rA = RankingInput("rA", "Route A", self._make_summary(severe=5.0, duration=3600.0))
        rB = RankingInput("rB", "Route B", self._make_summary(severe=0.0, duration=10800.0))

        rec = rank_routes([rA, rB])
        assert rec.route_id == "rB"
        assert rec.ranked[0].route_id == "rB"
        assert rec.ranked[1].route_id == "rA"

    def test_priority_2_tied_severe_fewest_high_miles_wins(self) -> None:
        # Both routes have 0 Severe miles
        # Route A has 10.0 High miles (faster: 3600s)
        # Route B has 0.0 High miles (slower: 5000s)
        rA = RankingInput(
            "rA", "Route A", self._make_summary(severe=0.0, high=10.0, duration=3600.0)
        )
        rB = RankingInput(
            "rB", "Route B", self._make_summary(severe=0.0, high=0.0, duration=5000.0)
        )

        rec = rank_routes([rA, rB])
        assert rec.route_id == "rB"

    def test_priority_3_tied_severe_and_high_lowest_avg_risk_wins(self) -> None:
        # Both routes have 0 Severe, 0 High miles
        # Route A has avg risk 0.40 (faster: 3600s)
        # Route B has avg risk 0.10 (slower: 4200s)
        rA = RankingInput("rA", "Route A", self._make_summary(avg_risk=0.40, duration=3600.0))
        rB = RankingInput("rB", "Route B", self._make_summary(avg_risk=0.10, duration=4200.0))

        rec = rank_routes([rA, rB])
        assert rec.route_id == "rB"

    def test_priority_4_tied_risk_shortest_travel_time_wins(self) -> None:
        # Both routes have identical risk (0 Severe, 0 High, avg 0.0)
        # Route A duration 3600s, Route B duration 4000s
        # Shortest travel time breaks tie
        rA = RankingInput("rA", "Route A", self._make_summary(duration=3600.0))
        rB = RankingInput("rB", "Route B", self._make_summary(duration=4000.0))

        rec = rank_routes([rA, rB])
        assert rec.route_id == "rA"

    def test_no_travel_route_ranks_last(self) -> None:
        # Route A has 2.0 No Travel miles
        # Route B has 10.0 Severe miles but 0 No Travel
        # Route B MUST outrank Route A because No Travel is strictly unacceptable
        rA = RankingInput("rA", "Route A", self._make_summary(no_travel=2.0, duration=3000.0))
        rB = RankingInput(
            "rB", "Route B", self._make_summary(no_travel=0.0, severe=10.0, duration=4000.0)
        )

        rec = rank_routes([rA, rB])
        assert rec.route_id == "rB"


# ==============================================================================
# 5. Missing Weather Handling & Unavailable Checkpoints
# ==============================================================================


class TestMissingWeatherHandling:
    """Verifies that missing weather data produces explicit None / Unavailable states."""

    def test_missing_weather_sample_yields_none_assessment(self) -> None:
        p1 = Place("Origin", Coordinate(40.0, -75.0))
        p2 = Place("Dest", Coordinate(41.0, -74.0))
        r = _make_route("r1", (p1.coordinate, p2.coordinate), 100.0, 7200.0)

        cum = geometry.cumulative_miles(r.polyline, r.distance_miles)
        from core.domain.sampling import build_checkpoints

        checkpoints = build_checkpoints(r.polyline, cum, 50)

        # CP 0 has valid weather series; CP 1 has series=None (weather provider error/miss)
        start_epoch = 1791694800
        series_valid = _make_series(start_epoch, count=24, wind=12.0)

        t0 = datetime.datetime.fromtimestamp(start_epoch, tz=datetime.UTC)
        t1 = datetime.datetime.fromtimestamp(start_epoch + 1800, tz=datetime.UTC)
        t2 = datetime.datetime.fromtimestamp(start_epoch + 3600, tz=datetime.UTC)

        ac0 = scoring.assess_checkpoint(checkpoints[0], t0, series_valid, 40000.0)
        ac1 = scoring.assess_checkpoint(checkpoints[1], t1, None, 40000.0)
        ac2 = scoring.assess_checkpoint(checkpoints[2], t2, series_valid, 40000.0)

        assert ac0.sample is not None
        assert ac0.assessment is not None
        assert ac0.assessment.level == RiskLevel.LOW

        # Missing weather checkpoint MUST NOT report Low; must be None
        assert ac1.sample is None
        assert ac1.assessment is None
        assert ac1.reason is None

        summary = scoring.summarize_route((ac0, ac1, ac2), r.distance_miles, r.duration_seconds)
        assert summary.unavailable_checkpoints == 1
        assert summary.unavailable_miles == 50.0
