"""Domain route ranking and deterministic recommendation logic."""

import math
from collections.abc import Sequence

from core.domain.types import (
    DecidingFactor,
    RankedRoute,
    RankingInput,
    Recommendation,
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


def rank_routes(inputs: Sequence[RankingInput]) -> Recommendation:
    """Rank candidate routes and produce an explainable recommendation."""
    if not inputs:
        raise ValueError("inputs sequence cannot be empty")

    seen_ids: set[str] = set()
    for inp in inputs:
        if inp.route_id in seen_ids:
            raise ValueError(f"Duplicate route_id found: {inp.route_id}")
        seen_ids.add(inp.route_id)

    min_duration = min(inp.summary.duration_seconds for inp in inputs)
    sorted_inputs = sorted(inputs, key=_route_sort_key)

    ranked_routes = tuple(
        RankedRoute(
            route_id=inp.route_id,
            rank=idx + 1,
            delta_vs_fastest_seconds=max(0.0, inp.summary.duration_seconds - min_duration),
        )
        for idx, inp in enumerate(sorted_inputs)
    )

    winner = sorted_inputs[0]
    winner_delta = ranked_routes[0].delta_vs_fastest_seconds

    has_any_data = any(inp.summary.avg_risk_score is not None for inp in inputs)
    all_have_no_travel = all(inp.summary.has_no_travel for inp in inputs)
    no_safe_route = all_have_no_travel and has_any_data

    if len(sorted_inputs) == 1:
        decided_by = DecidingFactor.ONLY_OPTION
    else:
        runner = sorted_inputs[1]
        k_win = _route_sort_key(winner)
        k_run = _route_sort_key(runner)
        diff_pos = None
        for i in range(len(k_win)):
            if k_win[i] != k_run[i]:
                diff_pos = i
                break

        if diff_pos is None:
            decided_by = DecidingFactor.TIE
        elif diff_pos == 0:
            decided_by = DecidingFactor.NO_DATA
        elif diff_pos in (1, 2):
            decided_by = DecidingFactor.NO_TRAVEL
        elif diff_pos == 3:
            decided_by = DecidingFactor.SEVERE_MILES
        elif diff_pos == 4:
            decided_by = DecidingFactor.HIGH_MILES
        elif diff_pos == 5:
            decided_by = DecidingFactor.AVG_RISK
        else:
            decided_by = DecidingFactor.TRAVEL_TIME

    if no_safe_route:
        w_nt = winner.summary.miles_by_level.no_travel
        headline = (
            f"No route avoids No Travel conditions. "
            f"{winner.label} has the least ({w_nt:.1f} mi). Consider delaying departure."
        )
    else:
        time_clause = _format_time_clause(winner_delta)
        match decided_by:
            case DecidingFactor.ONLY_OPTION:
                headline = f"Only one route is available: {winner.label}."
            case DecidingFactor.NO_DATA:
                headline = (
                    f"{winner.label} is recommended because weather data was "
                    f"unavailable for the other routes.{time_clause}"
                )
            case DecidingFactor.NO_TRAVEL:
                runner = sorted_inputs[1]
                if not winner.summary.has_no_travel:
                    headline = (
                        f"{winner.label} avoids the No Travel conditions found on "
                        f"{runner.label}.{time_clause}"
                    )
                else:
                    w_nt = winner.summary.miles_by_level.no_travel
                    r_nt = runner.summary.miles_by_level.no_travel
                    headline = (
                        f"{winner.label} has fewer No Travel miles ({w_nt:.1f} vs {r_nt:.1f} on "
                        f"{runner.label}).{time_clause}"
                    )
            case DecidingFactor.SEVERE_MILES:
                runner = sorted_inputs[1]
                w_sev = winner.summary.miles_by_level.severe
                r_sev = runner.summary.miles_by_level.severe
                headline = (
                    f"{winner.label} has {w_sev:.1f} Severe miles vs {r_sev:.1f} on "
                    f"{runner.label}.{time_clause}"
                )
            case DecidingFactor.HIGH_MILES:
                runner = sorted_inputs[1]
                w_high = winner.summary.miles_by_level.high
                r_high = runner.summary.miles_by_level.high
                headline = (
                    f"{winner.label} has {w_high:.1f} High miles vs {r_high:.1f} on "
                    f"{runner.label}, with equal Severe miles.{time_clause}"
                )
            case DecidingFactor.AVG_RISK:
                runner = sorted_inputs[1]
                w_avg = (
                    winner.summary.avg_risk_score
                    if winner.summary.avg_risk_score is not None
                    else 0.0
                )
                r_avg = (
                    runner.summary.avg_risk_score
                    if runner.summary.avg_risk_score is not None
                    else 0.0
                )
                headline = (
                    f"{winner.label} has lower average risk ({w_avg:.2f} vs {r_avg:.2f} on "
                    f"{runner.label}), with equal Severe and High miles.{time_clause}"
                )
            case DecidingFactor.TRAVEL_TIME:
                headline = f"{winner.label} is the fastest route with equal weather risk."
            case DecidingFactor.TIE:
                runner = sorted_inputs[1]
                headline = (
                    f"{winner.label} and {runner.label} are equivalent; "
                    f"{winner.label} is listed first.{time_clause}"
                )

    return Recommendation(
        route_id=winner.route_id,
        decided_by=decided_by,
        headline=headline,
        no_safe_route=no_safe_route,
        ranked=ranked_routes,
    )
