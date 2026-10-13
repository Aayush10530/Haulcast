"""Shared validation helpers for domain types."""

import math
from collections.abc import Sequence
from typing import Any


def validate_non_empty_str(val: str, name: str) -> None:
    if not val or not val.strip():
        raise ValueError(f"{name} cannot be empty")


def validate_positive_finite(val: float, name: str) -> None:
    if not math.isfinite(val) or val <= 0.0:
        raise ValueError(f"{name} must be a positive finite number, got {val}")


def validate_non_negative_finite(val: float, name: str) -> None:
    if not math.isfinite(val) or val < 0.0:
        if "delta_vs_fastest_seconds" in name or "miles" in name:
            raise ValueError(f"{name} must be a non-negative finite number, got {val}")
        raise ValueError(f"{name} must be non-negative finite, got {val}")


def validate_load_weight_lb(val: Any) -> None:
    if not isinstance(val, int) or isinstance(val, bool):
        raise TypeError(f"load_weight_lb must be an int, got {type(val)}")
    if val < 0:
        raise ValueError(f"load_weight_lb must be non-negative, got {val}")


def coerce_tuple[T](val: Sequence[T]) -> tuple[T, ...]:
    return tuple(val) if not isinstance(val, tuple) else val
