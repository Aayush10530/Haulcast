"""Domain route ranking and deterministic recommendation logic."""

import math
from collections.abc import Sequence

from core.domain.types import (
    DecidingFactor,
    RankedRoute,
    RankingInput,
    Recommendation,
)

_POSITION_TO_FACTOR: tuple[DecidingFactor, ...] = (
    DecidingFactor.NO_DATA,
    DecidingFactor.NO_TRAVEL,
    DecidingFactor.NO_TRAVEL,
    DecidingFactor.SEVERE_MILES,
    DecidingFactor.HIGH_MILES,
    DecidingFactor.AVG_RISK,
    DecidingFactor.TRAVEL_TIME,
)


def _route_sort_key(inp: RankingInput) -> tuple[bool, bool, float, float, float, float, float]:
    summary = inp.summary
    no_data = summary.avg_risk_score is None
    has_no_travel = summary.has_no_travel
    no_travel_miles = round(summary.miles_by_level.no_travel, 1)
    severe_miles = round(summary.miles_by_level.severe, 1)
    high_miles = round(summary.miles_by_level.high, 1)
    avg_risk = round(summary.avg_risk_score, 2) if summary.avg_risk_score is not None else 0.0
    duration = summary.duration_seconds
    return (no_data, has_no_travel, no_travel_miles, severe_miles, high_miles, avg_risk, duration)


def _format_time_clause(delta_seconds: float) -> str:
    if math.isclose(delta_seconds, 0.0, abs_tol=1e-9):
        return " It is also the fastest route."
    if delta_seconds < 60.0:
        return ""
    total_minutes = round(delta_seconds / 60.0)
    if total_minutes < 60:
        duration = f"{total_minutes} min"
    else:
        hours = total_minutes // 60
        mins = total_minutes % 60
        duration = f"{hours} h {mins:02d} min"
    return f" It is {duration} slower than the fastest route."


def _deciding_factor(winner: RankingInput, runner: RankingInput | None) -> DecidingFactor:
    if runner is None:
        return DecidingFactor.ONLY_OPTION
    k_win = _route_sort_key(winner)
    k_run = _route_sort_key(runner)
    for idx, (w_val, r_val) in enumerate(zip(k_win, k_run, strict=True)):
        if w_val != r_val:
            return _POSITION_TO_FACTOR[idx]
    return DecidingFactor.TIE


def _comparison_message(
    decided_by: DecidingFactor, winner: RankingInput, runner: RankingInput
) -> str:
    w_sum, r_sum, r_lbl = winner.summary, runner.summary, runner.label
    match decided_by:
        case DecidingFactor.NO_DATA:
            return (
                f"{winner.label} is recommended because weather data was "
                f"unavailable for the other routes."
            )
        case DecidingFactor.NO_TRAVEL:
            if not w_sum.has_no_travel:
                return f"{winner.label} avoids the No Travel conditions found on {r_lbl}."
            w_nt, r_nt = w_sum.miles_by_level.no_travel, r_sum.miles_by_level.no_travel
            return (
                f"{winner.label} has fewer No Travel miles ({w_nt:.1f} vs {r_nt:.1f} on {r_lbl})."
            )
        case DecidingFactor.SEVERE_MILES:
            w_s, r_s = w_sum.miles_by_level.severe, r_sum.miles_by_level.severe
            return f"{winner.label} has {w_s:.1f} Severe miles vs {r_s:.1f} on {r_lbl}."
        case DecidingFactor.HIGH_MILES:
            w_h, r_h = w_sum.miles_by_level.high, r_sum.miles_by_level.high
            return (
                f"{winner.label} has {w_h:.1f} High miles vs {r_h:.1f} on {r_lbl}, "
                f"with equal Severe miles."
            )
        case DecidingFactor.AVG_RISK:
            w_a, r_a = w_sum.avg_risk_score or 0.0, r_sum.avg_risk_score or 0.0
            return (
                f"{winner.label} has lower average risk ({w_a:.2f} vs {r_a:.2f} on {r_lbl}), "
                f"with equal Severe and High miles."
            )
        case DecidingFactor.TIE:
            return f"{winner.label} and {r_lbl} are equivalent; {winner.label} is listed first."


def _build_headline(
    decided_by: DecidingFactor,
    winner: RankingInput,
    runner: RankingInput | None,
    delta: float,
    no_safe_route: bool,
) -> str:
    if no_safe_route:
        w_nt = winner.summary.miles_by_level.no_travel
        return (
            f"No route avoids No Travel conditions. "
            f"{winner.label} has the least ({w_nt:.1f} mi). Consider delaying departure."
        )
    if decided_by == DecidingFactor.ONLY_OPTION:
        return f"Only one route is available: {winner.label}."
    if decided_by == DecidingFactor.TRAVEL_TIME:
        return f"{winner.label} is the fastest route with equal weather risk."

    assert runner is not None
    msg = _comparison_message(decided_by, winner, runner)
    return f"{msg}{_format_time_clause(delta)}"


def _validate_inputs(inputs: Sequence[RankingInput]) -> None:
    if not inputs:
        raise ValueError("inputs sequence cannot be empty")
    seen_ids: set[str] = set()
    for inp in inputs:
        if inp.route_id in seen_ids:
            raise ValueError(f"Duplicate route_id found: {inp.route_id}")
        seen_ids.add(inp.route_id)


def rank_routes(inputs: Sequence[RankingInput]) -> Recommendation:
    """Rank candidate routes and produce an explainable recommendation."""
    _validate_inputs(inputs)

    min_dur = min(inp.summary.duration_seconds for inp in inputs)
    sorted_inputs = sorted(inputs, key=_route_sort_key)

    ranked = tuple(
        RankedRoute(
            route_id=inp.route_id,
            rank=idx + 1,
            delta_vs_fastest_seconds=max(0.0, inp.summary.duration_seconds - min_dur),
        )
        for idx, inp in enumerate(sorted_inputs)
    )

    winner = sorted_inputs[0]
    runner = sorted_inputs[1] if len(sorted_inputs) > 1 else None
    has_data = any(inp.summary.avg_risk_score is not None for inp in inputs)
    all_no_travel = all(inp.summary.has_no_travel for inp in inputs)
    no_safe_route = all_no_travel and has_data

    decided_by = _deciding_factor(winner, runner)
    headline = _build_headline(
        decided_by, winner, runner, ranked[0].delta_vs_fastest_seconds, no_safe_route
    )

    return Recommendation(
        route_id=winner.route_id,
        decided_by=decided_by,
        headline=headline,
        no_safe_route=no_safe_route,
        ranked=ranked,
    )
