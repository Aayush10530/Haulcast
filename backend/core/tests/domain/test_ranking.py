import pytest

from core.domain.ranking import _format_time_clause, rank_routes
from core.domain.types import (
    DecidingFactor,
    MilesByLevel,
    RankedRoute,
    RankingInput,
    Recommendation,
    RiskLevel,
    RouteSummary,
)


def _make_summary(
    distance_miles: float = 100.0,
    duration_seconds: float = 3600.0,
    low: float = 0.0,
    moderate: float = 0.0,
    high: float = 0.0,
    severe: float = 0.0,
    no_travel: float = 0.0,
    unavailable_miles: float = 0.0,
    avg_risk_score: float | None = 0.0,
    max_level: RiskLevel | None = RiskLevel.LOW,
    unavailable_checkpoints: int = 0,
) -> RouteSummary:
    miles = MilesByLevel(
        low=low,
        moderate=moderate,
        high=high,
        severe=severe,
        no_travel=no_travel,
    )
    return RouteSummary(
        distance_miles=distance_miles,
        duration_seconds=duration_seconds,
        miles_by_level=miles,
        unavailable_miles=unavailable_miles,
        avg_risk_score=avg_risk_score,
        max_level=max_level,
        unavailable_checkpoints=unavailable_checkpoints,
    )


def test_ranking_deciding_factor_only_option_exact_headline() -> None:
    inp = RankingInput("r1", "Route A", _make_summary())
    rec = rank_routes([inp])

    assert rec.route_id == "r1"
    assert rec.decided_by == DecidingFactor.ONLY_OPTION
    assert rec.headline == "Only one route is available: Route A."
    assert not rec.no_safe_route
    assert len(rec.ranked) == 1
    assert rec.ranked[0].rank == 1
    assert rec.ranked[0].delta_vs_fastest_seconds == 0.0


def test_ranking_deciding_factor_no_data_exact_headline() -> None:
    r1 = RankingInput(
        "r1", "Route A", _make_summary(avg_risk_score=1.5, max_level=RiskLevel.MODERATE)
    )
    r2 = RankingInput("r2", "Route B", _make_summary(avg_risk_score=None, max_level=None))
    rec = rank_routes([r1, r2])

    assert rec.route_id == "r1"
    assert rec.decided_by == DecidingFactor.NO_DATA
    assert rec.headline == (
        "Route A is recommended because weather data was unavailable for the other routes. "
        "It is also the fastest route."
    )
    assert not rec.no_safe_route


def test_ranking_deciding_factor_no_travel_winner_has_none_exact_headline() -> None:
    r1 = RankingInput(
        "r1",
        "Route A",
        _make_summary(severe=10.0, no_travel=0.0, max_level=RiskLevel.SEVERE),
    )
    r2 = RankingInput(
        "r2",
        "Route B",
        _make_summary(severe=0.0, no_travel=5.0, max_level=RiskLevel.NO_TRAVEL),
    )
    rec = rank_routes([r1, r2])

    assert rec.route_id == "r1"
    assert rec.decided_by == DecidingFactor.NO_TRAVEL
    assert rec.headline == (
        "Route A avoids the No Travel conditions found on Route B. It is also the fastest route."
    )
    assert not rec.no_safe_route


def test_ranking_deciding_factor_no_travel_both_have_some_exact_headline() -> None:
    # Route C has no weather data so no_safe_route is False
    r1 = RankingInput(
        "r1",
        "Route A",
        _make_summary(
            no_travel=5.0,
            avg_risk_score=3.5,
            max_level=RiskLevel.NO_TRAVEL,
        ),
    )
    r2 = RankingInput(
        "r2",
        "Route B",
        _make_summary(
            no_travel=10.0,
            avg_risk_score=3.8,
            max_level=RiskLevel.NO_TRAVEL,
        ),
    )
    r3 = RankingInput(
        "r3",
        "Route C",
        _make_summary(avg_risk_score=None, max_level=None),
    )
    rec = rank_routes([r1, r2, r3])

    assert rec.route_id == "r1"
    assert rec.decided_by == DecidingFactor.NO_TRAVEL
    assert rec.headline == (
        "Route A has fewer No Travel miles (5.0 vs 10.0 on Route B). It is also the fastest route."
    )
    assert not rec.no_safe_route


def test_ranking_deciding_factor_severe_miles_exact_headline() -> None:
    r1 = RankingInput("r1", "Route A", _make_summary(severe=10.0))
    r2 = RankingInput("r2", "Route B", _make_summary(severe=20.0))
    rec = rank_routes([r1, r2])

    assert rec.route_id == "r1"
    assert rec.decided_by == DecidingFactor.SEVERE_MILES
    assert (
        rec.headline
        == "Route A has 10.0 Severe miles vs 20.0 on Route B. It is also the fastest route."
    )
    assert not rec.no_safe_route


def test_ranking_deciding_factor_high_miles_exact_headline() -> None:
    r1 = RankingInput("r1", "Route A", _make_summary(severe=10.0, high=5.0))
    r2 = RankingInput("r2", "Route B", _make_summary(severe=10.0, high=15.0))
    rec = rank_routes([r1, r2])

    assert rec.route_id == "r1"
    assert rec.decided_by == DecidingFactor.HIGH_MILES
    assert rec.headline == (
        "Route A has 5.0 High miles vs 15.0 on Route B, with equal Severe miles. "
        "It is also the fastest route."
    )
    assert not rec.no_safe_route


def test_ranking_deciding_factor_avg_risk_exact_headline() -> None:
    r1 = RankingInput("r1", "Route A", _make_summary(severe=10.0, high=5.0, avg_risk_score=1.20))
    r2 = RankingInput("r2", "Route B", _make_summary(severe=10.0, high=5.0, avg_risk_score=1.80))
    rec = rank_routes([r1, r2])

    assert rec.route_id == "r1"
    assert rec.decided_by == DecidingFactor.AVG_RISK
    assert rec.headline == (
        "Route A has lower average risk (1.20 vs 1.80 on Route B), with equal Severe and "
        "High miles. It is also the fastest route."
    )
    assert not rec.no_safe_route


def test_ranking_deciding_factor_travel_time_exact_headline() -> None:
    r1 = RankingInput(
        "r1",
        "Route A",
        _make_summary(severe=10.0, high=5.0, avg_risk_score=1.50, duration_seconds=3600.0),
    )
    r2 = RankingInput(
        "r2",
        "Route B",
        _make_summary(severe=10.0, high=5.0, avg_risk_score=1.50, duration_seconds=4200.0),
    )
    rec = rank_routes([r1, r2])

    assert rec.route_id == "r1"
    assert rec.decided_by == DecidingFactor.TRAVEL_TIME
    assert rec.headline == "Route A is the fastest route with equal weather risk."
    assert not rec.no_safe_route


def test_ranking_deciding_factor_tie_exact_headline() -> None:
    r1 = RankingInput(
        "r1",
        "Route A",
        _make_summary(severe=10.0, high=5.0, avg_risk_score=1.50, duration_seconds=3600.0),
    )
    r2 = RankingInput(
        "r2",
        "Route B",
        _make_summary(severe=10.0, high=5.0, avg_risk_score=1.50, duration_seconds=3600.0),
    )
    rec = rank_routes([r1, r2])

    assert rec.route_id == "r1"
    assert rec.decided_by == DecidingFactor.TIE
    assert rec.headline == (
        "Route A and Route B are equivalent; Route A is listed first. It is also the fastest route."
    )
    assert not rec.no_safe_route


def test_ranking_severe_beats_high_beats_average_risk_beats_time() -> None:
    # Route A has severe=5.0 but high=40.0, avg=2.5, duration=7000.0
    # Route B has severe=10.0, high=0.0, avg=1.0, duration=3000.0
    r1 = RankingInput(
        "r1",
        "Route A",
        _make_summary(severe=5.0, high=40.0, avg_risk_score=2.5, duration_seconds=7000.0),
    )
    r2 = RankingInput(
        "r2",
        "Route B",
        _make_summary(severe=10.0, high=0.0, avg_risk_score=1.0, duration_seconds=3000.0),
    )
    rec = rank_routes([r1, r2])

    assert rec.route_id == "r1"
    assert rec.decided_by == DecidingFactor.SEVERE_MILES


def test_ranking_severe_difference_of_point_zero_four_rounds_away_and_falls_to_high() -> None:
    # Route A has 10.02 severe (rounds to 10.0), 5.0 high
    # Route B has 10.04 severe (rounds to 10.0), 10.0 high
    r1 = RankingInput("r1", "Route A", _make_summary(severe=10.02, high=5.0))
    r2 = RankingInput("r2", "Route B", _make_summary(severe=10.04, high=10.0))
    rec = rank_routes([r1, r2])

    assert rec.route_id == "r1"
    assert rec.decided_by == DecidingFactor.HIGH_MILES
    assert rec.headline == (
        "Route A has 5.0 High miles vs 10.0 on Route B, with equal Severe miles. "
        "It is also the fastest route."
    )


def test_ranking_fewer_severe_miles_with_any_no_travel_loses_to_route_without_no_travel() -> None:
    r1 = RankingInput(
        "r1",
        "Route A",
        _make_summary(
            no_travel=0.1,
            severe=0.0,
            max_level=RiskLevel.NO_TRAVEL,
        ),
    )
    r2 = RankingInput(
        "r2",
        "Route B",
        _make_summary(
            no_travel=0.0,
            severe=50.0,
            max_level=RiskLevel.SEVERE,
        ),
    )
    rec = rank_routes([r1, r2])

    assert rec.route_id == "r2"
    assert rec.decided_by == DecidingFactor.NO_TRAVEL
    assert rec.headline == (
        "Route B avoids the No Travel conditions found on Route A. It is also the fastest route."
    )


def test_ranking_all_routes_no_travel_least_no_travel_wins_and_no_safe_route_is_true() -> None:
    r1 = RankingInput(
        "r1",
        "Route A",
        _make_summary(
            no_travel=5.0,
            max_level=RiskLevel.NO_TRAVEL,
            duration_seconds=3600.0,
        ),
    )
    r2 = RankingInput(
        "r2",
        "Route B",
        _make_summary(
            no_travel=12.0,
            max_level=RiskLevel.NO_TRAVEL,
            duration_seconds=3600.0,
        ),
    )
    rec = rank_routes([r1, r2])

    assert rec.route_id == "r1"
    assert rec.no_safe_route
    assert rec.decided_by == DecidingFactor.NO_TRAVEL
    assert rec.headline == (
        "No route avoids No Travel conditions. Route A has the least (5.0 mi). "
        "Consider delaying departure."
    )


def test_ranking_single_route_no_travel_sets_no_safe_route_and_exact_headline() -> None:
    r1 = RankingInput(
        "r1",
        "Route A",
        _make_summary(
            no_travel=8.4,
            max_level=RiskLevel.NO_TRAVEL,
            duration_seconds=3600.0,
        ),
    )
    rec = rank_routes([r1])

    assert rec.route_id == "r1"
    assert rec.no_safe_route
    assert rec.decided_by == DecidingFactor.ONLY_OPTION
    assert rec.headline == (
        "No route avoids No Travel conditions. Route A has the least (8.4 mi). "
        "Consider delaying departure."
    )


def test_ranking_route_with_no_weather_data_ranks_last_despite_zero_miles() -> None:
    r1 = RankingInput(
        "r1",
        "Route A",
        _make_summary(severe=50.0, avg_risk_score=3.0, max_level=RiskLevel.SEVERE),
    )
    r2 = RankingInput("r2", "Route B", _make_summary(avg_risk_score=None, max_level=None))
    rec = rank_routes([r1, r2])

    assert rec.route_id == "r1"
    assert rec.ranked[0].route_id == "r1"
    assert rec.ranked[1].route_id == "r2"


def test_ranking_stable_tie_order_preserves_input_sequence() -> None:
    r1 = RankingInput("r1", "Route A", _make_summary())
    r2 = RankingInput("r2", "Route B", _make_summary())

    rec_ab = rank_routes([r1, r2])
    assert rec_ab.route_id == "r1"
    assert rec_ab.ranked[0].route_id == "r1"
    assert rec_ab.ranked[1].route_id == "r2"

    rec_ba = rank_routes([r2, r1])
    assert rec_ba.route_id == "r2"
    assert rec_ba.ranked[0].route_id == "r2"
    assert rec_ba.ranked[1].route_id == "r1"


def test_ranking_deltas_computed_against_fastest_of_all_inputs() -> None:
    # Route C is fastest (3000s)
    # Route A (5000s) wins on weather (0 severe vs 50 on B and C)
    r1 = RankingInput(
        "r1",
        "Route A",
        _make_summary(severe=0.0, duration_seconds=5000.0),
    )
    r2 = RankingInput(
        "r2",
        "Route B",
        _make_summary(severe=50.0, duration_seconds=4000.0),
    )
    r3 = RankingInput(
        "r3",
        "Route C",
        _make_summary(severe=50.0, duration_seconds=3000.0),
    )
    rec = rank_routes([r1, r2, r3])

    assert rec.route_id == "r1"
    by_id = {r.route_id: r for r in rec.ranked}
    assert by_id["r3"].delta_vs_fastest_seconds == 0.0
    assert by_id["r2"].delta_vs_fastest_seconds == 1000.0
    assert by_id["r1"].delta_vs_fastest_seconds == 2000.0


def test_ranking_winner_slower_than_fastest_compares_with_fastest_route() -> None:
    # A fastest with avg risk 0.13
    # B slower 48 min with avg 0.00
    # C slowest with avg 0.00
    # gives winner B, decided_by AVG_RISK
    r_a = RankingInput(
        "r1",
        "Route A",
        _make_summary(avg_risk_score=0.13, duration_seconds=3600.0),
    )
    r_b = RankingInput(
        "r2",
        "Route B",
        _make_summary(avg_risk_score=0.00, duration_seconds=3600.0 + 48 * 60),
    )
    r_c = RankingInput(
        "r3",
        "Route C",
        _make_summary(avg_risk_score=0.00, duration_seconds=3600.0 + 60 * 60),
    )
    rec = rank_routes([r_a, r_b, r_c])

    assert rec.route_id == "r2"
    assert rec.decided_by == DecidingFactor.AVG_RISK
    assert rec.headline == (
        "Route B has lower average risk (0.00 vs 0.13 on Route A), with equal Severe and "
        "High miles. It is 48 min slower than the fastest route."
    )


@pytest.mark.parametrize(
    ("delta_sec", "expected_clause"),
    [
        (0.0, " It is also the fastest route."),
        (59.0, ""),
        (2520.0, " It is 42 min slower than the fastest route."),
        (3900.0, " It is 1 h 05 min slower than the fastest route."),
        (3570.0, " It is 1 h 00 min slower than the fastest route."),
    ],
)
def test_ranking_time_clause_duration_formats(delta_sec: float, expected_clause: str) -> None:
    clause = _format_time_clause(delta_sec)
    assert clause == expected_clause


def test_ranking_empty_input_raises_value_error() -> None:
    with pytest.raises(ValueError, match="sequence cannot be empty"):
        rank_routes([])


def test_ranking_duplicate_route_ids_raise_value_error() -> None:
    r1 = RankingInput("r1", "Route A", _make_summary())
    r2 = RankingInput("r1", "Route B", _make_summary())
    with pytest.raises(ValueError, match="Duplicate route_id found"):
        rank_routes([r1, r2])


def test_ranking_types_validation_errors() -> None:
    summary = _make_summary()

    with pytest.raises(ValueError, match="route_id cannot be empty"):
        RankingInput("", "Route A", summary)

    with pytest.raises(ValueError, match="label cannot be empty"):
        RankingInput("r1", "   ", summary)

    with pytest.raises(ValueError, match="rank must be a positive 1-based integer"):
        RankedRoute("r1", 0, 10.0)

    with pytest.raises(ValueError, match="delta_vs_fastest_seconds must be a non-negative"):
        RankedRoute("r1", 1, -5.0)

    with pytest.raises(ValueError, match="delta_vs_fastest_seconds must be a non-negative"):
        RankedRoute("r1", 1, float("nan"))

    with pytest.raises(ValueError, match="headline cannot be empty"):
        Recommendation(
            route_id="r1",
            decided_by=DecidingFactor.ONLY_OPTION,
            headline="",
            no_safe_route=False,
            ranked=(RankedRoute("r1", 1, 0.0),),
        )

    with pytest.raises(ValueError, match="route_id cannot be empty"):
        RankedRoute("", 1, 0.0)

    with pytest.raises(ValueError, match="route_id cannot be empty"):
        Recommendation(
            route_id="",
            decided_by=DecidingFactor.ONLY_OPTION,
            headline="Headline",
            no_safe_route=False,
            ranked=(RankedRoute("r1", 1, 0.0),),
        )

    with pytest.raises(ValueError, match="ranked cannot be empty"):
        Recommendation(
            route_id="r1",
            decided_by=DecidingFactor.ONLY_OPTION,
            headline="Headline",
            no_safe_route=False,
            ranked=(),
        )

    rec = Recommendation(
        route_id="r1",
        decided_by=DecidingFactor.ONLY_OPTION,
        headline="Headline",
        no_safe_route=False,
        ranked=[RankedRoute("r1", 1, 0.0)],
    )
    assert isinstance(rec.ranked, tuple)
