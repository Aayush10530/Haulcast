import datetime
import math
from collections.abc import Sequence

from core.domain import risk, weather_align
from core.domain.types import (
    AssessedCheckpoint,
    Checkpoint,
    MilesByLevel,
    RiskLevel,
    RouteSummary,
    WeatherSeries,
)


def assess_checkpoint(
    checkpoint: Checkpoint,
    eta_utc: datetime.datetime,
    series: WeatherSeries | None,
    load_weight_lb: float,
) -> AssessedCheckpoint:
    """Assess a route checkpoint against weather series data at its estimated arrival time."""
    if eta_utc.tzinfo is None or eta_utc.tzinfo.utcoffset(eta_utc) is None:
        raise ValueError(f"eta_utc must be a timezone-aware datetime, got {eta_utc}")

    eta_in_utc = eta_utc.astimezone(datetime.UTC)
    tz_name = series.tz_name if series is not None else ""

    sample = weather_align.sample_at(series, eta_in_utc) if series is not None else None
    if sample is None:
        return AssessedCheckpoint(
            checkpoint=checkpoint,
            eta_utc=eta_in_utc,
            tz_name=tz_name,
            sample=None,
            assessment=None,
            reason=None,
        )

    assessment = risk.assess(sample, load_weight_lb)
    reason = risk.describe(sample, load_weight_lb, assessment)

    return AssessedCheckpoint(
        checkpoint=checkpoint,
        eta_utc=eta_in_utc,
        tz_name=tz_name,
        sample=sample,
        assessment=assessment,
        reason=reason,
    )


def summarize_route(
    assessed: Sequence[AssessedCheckpoint],
    distance_miles: float,
    duration_seconds: float,
) -> RouteSummary:
    """Aggregate risk profile, covered miles by risk level, and summary metrics for a route."""
    if not assessed:
        raise ValueError("assessed checkpoints sequence cannot be empty")
    if not math.isfinite(distance_miles) or distance_miles <= 0.0:
        raise ValueError(f"distance_miles must be a positive finite number, got {distance_miles}")
    if not math.isfinite(duration_seconds) or duration_seconds < 0.0:
        raise ValueError(
            f"duration_seconds must be a non-negative finite number, got {duration_seconds}"
        )

    coverages: list[float] = [
        cp.checkpoint.covers_to_mile - cp.checkpoint.covers_from_mile for cp in assessed
    ]
    total_coverage = math.fsum(coverages)

    rel_diff = abs(total_coverage - distance_miles) / distance_miles
    if rel_diff > 1e-6:
        raise ValueError(
            f"Total checkpoint coverage ({total_coverage:.6f} mi) differs from route "
            f"distance ({distance_miles:.6f} mi) by more than 1e-6 relative"
        )

    level_miles_lists: dict[RiskLevel, list[float]] = {lvl: [] for lvl in RiskLevel}
    unavailable_coverages: list[float] = []
    assessed_coverages: list[float] = []
    assessed_levels: list[RiskLevel] = []
    assessed_products: list[float] = []

    for cp, cov in zip(assessed, coverages, strict=True):
        if cp.assessment is None:
            unavailable_coverages.append(cov)
        else:
            level = cp.assessment.level
            level_miles_lists[level].append(cov)
            assessed_coverages.append(cov)
            assessed_levels.append(level)
            assessed_products.append(int(level) * cov)

    miles_by_level = MilesByLevel(
        low=math.fsum(level_miles_lists[RiskLevel.LOW]),
        moderate=math.fsum(level_miles_lists[RiskLevel.MODERATE]),
        high=math.fsum(level_miles_lists[RiskLevel.HIGH]),
        severe=math.fsum(level_miles_lists[RiskLevel.SEVERE]),
        no_travel=math.fsum(level_miles_lists[RiskLevel.NO_TRAVEL]),
    )
    unavailable_miles = math.fsum(unavailable_coverages)
    unavailable_checkpoints = len(unavailable_coverages)

    assessed_miles = math.fsum(assessed_coverages)
    if not assessed_levels:
        avg_risk_score = None
        max_level = None
    else:
        max_level = max(assessed_levels)
        if assessed_miles <= 0.0:
            avg_risk_score = None
        else:
            raw_avg = math.fsum(assessed_products) / assessed_miles
            avg_risk_score = min(4.0, max(0.0, raw_avg))

    return RouteSummary(
        distance_miles=distance_miles,
        duration_seconds=duration_seconds,
        miles_by_level=miles_by_level,
        unavailable_miles=unavailable_miles,
        avg_risk_score=avg_risk_score,
        max_level=max_level,
        unavailable_checkpoints=unavailable_checkpoints,
    )
