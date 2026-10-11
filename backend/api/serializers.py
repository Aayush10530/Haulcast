"""Serializers and response formatters for trip analysis API."""

import datetime
from typing import Any

from rest_framework import serializers

from core.domain import geometry, timezones
from core.domain.types import (
    Coordinate,
    IntervalMode,
    Place,
    TripAnalysis,
    TripRequest,
    Warning,
)


class PlaceSerializer(serializers.Serializer):
    """Serializer for geographic place with coordinates."""

    label = serializers.CharField(required=True, min_length=1, max_length=200)
    lat = serializers.FloatField(required=True, min_value=-90.0, max_value=90.0)
    lon = serializers.FloatField(required=True, min_value=-180.0, max_value=180.0)


class TripRequestSerializer(serializers.Serializer):
    """Serializer validating incoming trip analysis requests."""

    origin = PlaceSerializer(required=True)
    destination = PlaceSerializer(required=True)
    departure_local = serializers.CharField(required=True)
    load_weight_lb = serializers.IntegerField(required=True, min_value=0, max_value=120000)
    interval = serializers.CharField(required=False, default="auto")

    def validate_departure_local(self, value: str) -> datetime.datetime:
        """Validate naive ISO datetime without offset."""
        try:
            dt = datetime.datetime.fromisoformat(value)
        except (ValueError, TypeError):
            raise serializers.ValidationError(
                "departure_local must be a valid ISO datetime (e.g. '2026-10-12T08:00')."
            ) from None

        if dt.tzinfo is not None and dt.tzinfo.utcoffset(dt) is not None:
            raise serializers.ValidationError(
                "departure_local must be a naive local datetime without timezone offset."
            )
        return dt

    def validate_interval(self, value: Any) -> tuple[IntervalMode, int | None]:
        """Validate interval option ('auto' or 10, 25, 50)."""
        val_str = str(value).strip().lower()
        if val_str == "auto":
            return IntervalMode.AUTO, None
        if val_str in ("10", "25", "50"):
            return IntervalMode.MANUAL, int(val_str)
        raise serializers.ValidationError("interval must be 'auto' or one of 10, 25, 50.")

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        """Verify origin and destination are distinct points at least 0.5 miles apart."""
        origin_data = attrs["origin"]
        dest_data = attrs["destination"]

        p1 = Coordinate(lat=float(origin_data["lat"]), lon=float(origin_data["lon"]))
        p2 = Coordinate(lat=float(dest_data["lat"]), lon=float(dest_data["lon"]))

        dist = geometry.haversine_miles(p1, p2)
        if dist < 0.5:
            raise serializers.ValidationError(
                {"destination": ["Origin and destination must be at least 0.5 miles apart."]}
            )
        return attrs

    def to_domain(self) -> TripRequest:
        """Convert validated serializer data to TripRequest domain object."""
        data = self.validated_data
        origin_data = data["origin"]
        dest_data = data["destination"]

        origin = Place(
            label=origin_data["label"].strip(),
            coordinate=Coordinate(lat=float(origin_data["lat"]), lon=float(origin_data["lon"])),
        )
        destination = Place(
            label=dest_data["label"].strip(),
            coordinate=Coordinate(lat=float(dest_data["lat"]), lon=float(dest_data["lon"])),
        )

        interval_mode, manual_interval = data["interval"]

        return TripRequest(
            origin=origin,
            destination=destination,
            departure_local=data["departure_local"],
            load_weight_lb=int(data["load_weight_lb"]),
            interval_mode=interval_mode,
            manual_interval=manual_interval,
        )


def format_trip_analysis(
    analysis: TripAnalysis,
    warnings: list[Warning] | None = None,
) -> dict[str, Any]:
    """Produce the exact JSON response shape specified in ARCHITECTURE §8."""
    all_warnings = warnings if warnings is not None else list(analysis.warnings)
    origin_tz = analysis.request.origin_tz

    routes_data: list[dict[str, Any]] = []
    for r in analysis.routes:
        tags: list[str] = []
        if r.is_recommended:
            tags.append("recommended")
        if r.delta_vs_fastest_seconds == 0:
            tags.append("fastest")

        arrival_utc = analysis.request.departure_utc + datetime.timedelta(
            seconds=r.raw.duration_seconds
        )
        dest_tz = (
            r.checkpoints[-1].tz_name
            if (r.checkpoints and r.checkpoints[-1].tz_name)
            else origin_tz
        )
        arrival_local = timezones.utc_to_local(arrival_utc, dest_tz)

        checkpoints_data: list[dict[str, Any]] = []
        for cp in r.checkpoints:
            cp_tz = cp.tz_name or origin_tz
            eta_local = timezones.utc_to_local(cp.eta_utc, cp_tz)

            weather_data: dict[str, Any] | None = None
            if cp.sample is not None:
                weather_data = {
                    "wind_mph": round(cp.sample.wind_mph, 1),
                    "rain_in_hr": round(cp.sample.rain_in_hr, 2),
                    "snow_in_hr": round(cp.sample.snow_in_hr, 2),
                }

            risk_data: dict[str, Any] | None = None
            if cp.assessment is not None:
                risk_data = {
                    "level": cp.assessment.level.key,
                    "level_label": cp.assessment.level.label,
                    "driver": cp.assessment.driver.value,
                    "load_rule_applied": cp.assessment.load_rule_applied,
                    "reason": cp.reason,
                }

            checkpoints_data.append(
                {
                    "index": cp.checkpoint.index,
                    "mile": round(cp.checkpoint.mile, 1),
                    "lat": round(cp.checkpoint.coordinate.lat, 5),
                    "lon": round(cp.checkpoint.coordinate.lon, 5),
                    "eta_utc": cp.eta_utc.isoformat(),
                    "eta_local": eta_local.isoformat(),
                    "local_tz": cp_tz,
                    "covers_miles": [
                        round(cp.checkpoint.covers_from_mile, 1),
                        round(cp.checkpoint.covers_to_mile, 1),
                    ],
                    "weather": weather_data,
                    "risk": risk_data,
                }
            )

        routes_data.append(
            {
                "id": r.route_id,
                "label": r.label,
                "tags": tags,
                "rank": r.rank,
                "via": r.via_summary,
                "distance_miles": round(r.raw.distance_miles, 1),
                "duration_seconds": round(r.raw.duration_seconds),
                "departure_utc": analysis.request.departure_utc.isoformat(),
                "arrival_utc": arrival_utc.isoformat(),
                "arrival_local": arrival_local.isoformat(),
                "geometry": [[round(c.lat, 5), round(c.lon, 5)] for c in r.display_polyline],
                "summary": {
                    "miles_by_level": {
                        "low": round(r.summary.miles_by_level.low, 1),
                        "moderate": round(r.summary.miles_by_level.moderate, 1),
                        "high": round(r.summary.miles_by_level.high, 1),
                        "severe": round(r.summary.miles_by_level.severe, 1),
                        "no_travel": round(r.summary.miles_by_level.no_travel, 1),
                    },
                    "avg_risk_score": (
                        round(r.summary.avg_risk_score, 2)
                        if r.summary.avg_risk_score is not None
                        else None
                    ),
                    "max_level": (
                        r.summary.max_level.key if r.summary.max_level is not None else None
                    ),
                    "has_no_travel": r.summary.has_no_travel,
                    "unavailable_miles": round(r.summary.unavailable_miles, 1),
                    "delta_vs_fastest_seconds": r.delta_vs_fastest_seconds,
                },
                "checkpoints": checkpoints_data,
            }
        )

    return {
        "request": {
            "origin": {
                "label": analysis.request.origin.label,
                "lat": round(analysis.request.origin.coordinate.lat, 5),
                "lon": round(analysis.request.origin.coordinate.lon, 5),
            },
            "destination": {
                "label": analysis.request.destination.label,
                "lat": round(analysis.request.destination.coordinate.lat, 5),
                "lon": round(analysis.request.destination.coordinate.lon, 5),
            },
            "departure_utc": analysis.request.departure_utc.isoformat(),
            "departure_local": analysis.request.departure_local.isoformat(),
            "origin_timezone": origin_tz,
            "load_weight_lb": analysis.request.load_weight_lb,
            "interval_miles": analysis.request.interval_miles,
            "interval_mode": analysis.request.interval_mode.value,
        },
        "recommended_route_id": analysis.recommendation.route_id,
        "recommendation": {
            "route_id": analysis.recommendation.route_id,
            "decided_by": analysis.recommendation.decided_by.value,
            "headline": analysis.recommendation.headline,
            "comparisons": [
                {
                    "route_id": r.route_id,
                    "severe_miles": round(r.summary.miles_by_level.severe, 1),
                    "high_miles": round(r.summary.miles_by_level.high, 1),
                    "avg_risk_score": (
                        round(r.summary.avg_risk_score, 2)
                        if r.summary.avg_risk_score is not None
                        else None
                    ),
                    "duration_seconds": round(r.raw.duration_seconds),
                }
                for r in analysis.routes
                if r.route_id != analysis.recommendation.route_id
            ],
        },
        "routes": routes_data,
        "warnings": [{"code": w.code, "message": w.message} for w in all_warnings],
        "meta": {
            "routing_provider": "tomtom",
            "weather_provider": "open-meteo",
            "weather_cells": analysis.meta.weather_cells,
            "route_count": analysis.meta.route_count,
            "elapsed_ms": round(analysis.meta.elapsed_ms, 1),
            "routing_ms": round(analysis.meta.routing_ms, 1),
            "weather_ms": round(analysis.meta.weather_ms, 1),
            "in_process_ms": round(analysis.meta.in_process_ms, 1),
        },
    }
