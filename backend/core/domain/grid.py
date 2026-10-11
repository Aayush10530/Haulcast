"""Spatial grid utilities for weather cell snapping and centering."""

import math
from decimal import ROUND_HALF_UP, Decimal

from core.domain import rules_config
from core.domain.types import Coordinate, GridCell


def _round_half_up(value: float, step: float) -> int:
    """Scale value by step and round using round-half-up with deterministic negatives."""
    d_val = Decimal(str(value))
    d_step = Decimal(str(step))
    scaled = d_val / d_step
    return int(scaled.quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def snap_to_cell(
    coord: Coordinate,
    grid_deg: float = rules_config.WEATHER_GRID_DEG,
) -> GridCell:
    """Snap a coordinate to a GridCell using round-half-up."""
    if not math.isfinite(grid_deg) or grid_deg <= 0.0:
        raise ValueError(f"grid_deg must be positive finite, got {grid_deg}")

    lat_idx = _round_half_up(coord.lat, grid_deg)
    lon_idx = _round_half_up(coord.lon, grid_deg)
    return GridCell(lat_index=lat_idx, lon_index=lon_idx)


def cell_center(
    cell: GridCell,
    grid_deg: float = rules_config.WEATHER_GRID_DEG,
) -> Coordinate:
    """Calculate the geographic center Coordinate of a GridCell."""
    if not math.isfinite(grid_deg) or grid_deg <= 0.0:
        raise ValueError(f"grid_deg must be positive finite, got {grid_deg}")

    d_lat = Decimal(cell.lat_index) * Decimal(str(grid_deg))
    d_lon = Decimal(cell.lon_index) * Decimal(str(grid_deg))
    return Coordinate(lat=float(d_lat), lon=float(d_lon))
