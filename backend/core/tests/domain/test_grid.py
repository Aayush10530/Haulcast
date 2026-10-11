"""Unit tests for spatial grid cell snapping and centering."""

import pytest

from core.domain.grid import cell_center, snap_to_cell
from core.domain.types import Coordinate, GridCell


def test_snap_to_cell_positive_and_negative_coords() -> None:
    # Positive coordinates (Dallas, TX ~ 32.7767, -96.7970)
    c_dallas = Coordinate(lat=32.7767, lon=-96.7970)
    cell_dallas = snap_to_cell(c_dallas, grid_deg=0.1)
    assert cell_dallas == GridCell(lat_index=328, lon_index=-968)

    # Negative latitude and longitude (e.g. Southern/Western hemisphere ~ -33.8688, -70.6483)
    c_santiago = Coordinate(lat=-33.8688, lon=-70.6483)
    cell_santiago = snap_to_cell(c_santiago, grid_deg=0.1)
    assert cell_santiago == GridCell(lat_index=-339, lon_index=-706)

    # Exact boundary ties (round-half-up deterministic)
    c_half_pos = Coordinate(lat=0.05, lon=0.15)
    assert snap_to_cell(c_half_pos, grid_deg=0.1) == GridCell(lat_index=1, lon_index=2)

    c_half_neg = Coordinate(lat=-0.05, lon=-0.15)
    # With symmetric round-half-up: -0.5 -> -1, -1.5 -> -2
    assert snap_to_cell(c_half_neg, grid_deg=0.1) == GridCell(lat_index=-1, lon_index=-2)


def test_neighbours_map_to_different_cells() -> None:
    c1 = Coordinate(lat=32.80, lon=-96.80)
    c2 = Coordinate(lat=32.90, lon=-96.80)
    c3 = Coordinate(lat=32.80, lon=-96.70)

    cell1 = snap_to_cell(c1, grid_deg=0.1)
    cell2 = snap_to_cell(c2, grid_deg=0.1)
    cell3 = snap_to_cell(c3, grid_deg=0.1)

    assert cell1 != cell2
    assert cell1 != cell3
    assert cell2 != cell3
    assert cell1 == GridCell(328, -968)
    assert cell2 == GridCell(329, -968)
    assert cell3 == GridCell(328, -967)


def test_same_cell_for_points_within_0_04_degrees() -> None:
    center = Coordinate(lat=32.80, lon=-96.80)
    p_offset1 = Coordinate(lat=32.80 + 0.04, lon=-96.80 + 0.04)
    p_offset2 = Coordinate(lat=32.80 - 0.04, lon=-96.80 - 0.04)

    cell_center_val = snap_to_cell(center, grid_deg=0.1)
    cell1 = snap_to_cell(p_offset1, grid_deg=0.1)
    cell2 = snap_to_cell(p_offset2, grid_deg=0.1)

    assert cell_center_val == cell1
    assert cell_center_val == cell2
    assert cell1 == GridCell(328, -968)


def test_cell_center_inside_0_05_degrees_of_original() -> None:
    test_points = [
        Coordinate(lat=32.7767, lon=-96.7970),
        Coordinate(lat=39.7392, lon=-104.9903),
        Coordinate(lat=-45.1234, lon=-75.6789),
        Coordinate(lat=0.0123, lon=0.0456),
    ]

    for pt in test_points:
        cell = snap_to_cell(pt, grid_deg=0.1)
        center = cell_center(cell, grid_deg=0.1)
        assert abs(center.lat - pt.lat) <= 0.05 + 1e-9
        assert abs(center.lon - pt.lon) <= 0.05 + 1e-9


def test_grid_invalid_grid_deg_raises() -> None:
    c = Coordinate(lat=0.0, lon=0.0)
    with pytest.raises(ValueError, match="grid_deg must be positive finite"):
        snap_to_cell(c, grid_deg=0.0)
    with pytest.raises(ValueError, match="grid_deg must be positive finite"):
        snap_to_cell(c, grid_deg=-0.1)
    with pytest.raises(ValueError, match="grid_deg must be positive finite"):
        snap_to_cell(c, grid_deg=float("nan"))

    cell = GridCell(0, 0)
    with pytest.raises(ValueError, match="grid_deg must be positive finite"):
        cell_center(cell, grid_deg=0.0)
