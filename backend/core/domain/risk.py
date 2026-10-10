import math

from core.domain import rules_config
from core.domain.types import (
    ConditionLevels,
    RiskAssessment,
    RiskDriver,
    RiskLevel,
    WeatherSample,
)


def _validate_non_negative_finite(val: float, name: str) -> None:
    if not math.isfinite(val) or val < 0.0:
        raise ValueError(f"{name} must be a finite non-negative number, got {val}")


def classify_wind(mph: float) -> RiskLevel:
    """Classify wind speed in mph into an ordinal RiskLevel."""
    _validate_non_negative_finite(mph, "wind_mph")
    if mph >= rules_config.WIND_NO_TRAVEL_MPH:
        return RiskLevel.NO_TRAVEL
    if mph >= rules_config.WIND_SEVERE_MPH:
        return RiskLevel.SEVERE
    if mph >= rules_config.WIND_HIGH_MPH:
        return RiskLevel.HIGH
    if mph >= rules_config.WIND_MODERATE_MPH:
        return RiskLevel.MODERATE
    return RiskLevel.LOW


def classify_rain(in_hr: float) -> RiskLevel:
    """Classify rain precipitation rate in in/hr into an ordinal RiskLevel."""
    _validate_non_negative_finite(in_hr, "rain_in_hr")
    if in_hr > rules_config.RAIN_NO_TRAVEL_IN_HR:
        return RiskLevel.NO_TRAVEL
    if in_hr >= rules_config.RAIN_SEVERE_IN_HR:
        return RiskLevel.SEVERE
    if in_hr >= rules_config.RAIN_HIGH_IN_HR:
        return RiskLevel.HIGH
    if in_hr >= rules_config.RAIN_MODERATE_IN_HR:
        return RiskLevel.MODERATE
    return RiskLevel.LOW


def classify_snow(in_hr: float) -> RiskLevel:
    """Classify snow precipitation rate in in/hr into an ordinal RiskLevel."""
    _validate_non_negative_finite(in_hr, "snow_in_hr")
    if in_hr > rules_config.SNOW_NO_TRAVEL_IN_HR:
        return RiskLevel.NO_TRAVEL
    if in_hr >= rules_config.SNOW_SEVERE_IN_HR:
        return RiskLevel.SEVERE
    if in_hr >= rules_config.SNOW_HIGH_IN_HR:
        return RiskLevel.HIGH
    if in_hr >= rules_config.SNOW_MODERATE_IN_HR:
        return RiskLevel.MODERATE
    return RiskLevel.LOW


def assess(sample: WeatherSample, load_weight_lb: float) -> RiskAssessment:
    """Assess overall risk level and primary driver for a weather sample and load weight."""
    _validate_non_negative_finite(load_weight_lb, "load_weight_lb")
    wind_lvl = classify_wind(sample.wind_mph)
    rain_lvl = classify_rain(sample.rain_in_hr)
    snow_lvl = classify_snow(sample.snow_in_hr)
    per_conditions = ConditionLevels(wind=wind_lvl, rain=rain_lvl, snow=snow_lvl)

    table_level = max(wind_lvl, rain_lvl, snow_lvl)

    load_level = RiskLevel.LOW
    if wind_lvl == RiskLevel.SEVERE and load_weight_lb > rules_config.LOAD_RULE_NO_TRAVEL_OVER_LB:
        load_level = RiskLevel.NO_TRAVEL
    elif wind_lvl == RiskLevel.HIGH and load_weight_lb > rules_config.LOAD_RULE_SEVERE_OVER_LB:
        load_level = RiskLevel.SEVERE

    final_level = max(table_level, load_level)
    load_rule_applied = final_level > table_level

    if load_rule_applied:
        driver = RiskDriver.LOAD_RULE
    else:
        # Tie order: wind, rain, snow
        if wind_lvl >= rain_lvl and wind_lvl >= snow_lvl:
            driver = RiskDriver.WIND
        elif rain_lvl >= snow_lvl:
            driver = RiskDriver.RAIN
        else:
            driver = RiskDriver.SNOW

    return RiskAssessment(
        level=final_level,
        table_level=table_level,
        driver=driver,
        load_rule_applied=load_rule_applied,
        per_condition_levels=per_conditions,
    )


def describe(sample: WeatherSample, load_weight_lb: float, assessment: RiskAssessment) -> str:
    """Return a short plain-English reason string for the risk assessment."""
    _validate_non_negative_finite(load_weight_lb, "load_weight_lb")
    _validate_non_negative_finite(sample.wind_mph, "wind_mph")
    _validate_non_negative_finite(sample.rain_in_hr, "rain_in_hr")
    _validate_non_negative_finite(sample.snow_in_hr, "snow_in_hr")

    if assessment.load_rule_applied:
        if assessment.level == RiskLevel.NO_TRAVEL:
            return (
                f"Wind {sample.wind_mph:.1f} mph is Severe; "
                f"load {load_weight_lb:,.0f} lb over "
                f"{rules_config.LOAD_RULE_NO_TRAVEL_OVER_LB:,.0f} lb makes it No Travel."
            )
        return (
            f"Wind {sample.wind_mph:.1f} mph is High; "
            f"load {load_weight_lb:,.0f} lb over "
            f"{rules_config.LOAD_RULE_SEVERE_OVER_LB:,.0f} lb makes it Severe."
        )

    if assessment.driver == RiskDriver.WIND:
        return f"Wind {sample.wind_mph:.1f} mph is {assessment.level.label}."
    if assessment.driver == RiskDriver.RAIN:
        return f"Rain {sample.rain_in_hr:.2f} in/hr is {assessment.level.label}."
    return f"Snow {sample.snow_in_hr:.2f} in/hr is {assessment.level.label}."
