from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from typing import Sequence


Binary = Sequence[int]


def _validate_binary(values: Binary, name: str) -> None:
    for value in values:
        if value not in (0, 1):
            raise ValueError(f"{name} must contain only 0/1 values; got {value!r}")


def _require_same_length(left: Sequence[object], right: Sequence[object], left_name: str, right_name: str) -> None:
    if len(left) != len(right):
        raise ValueError(f"{left_name} and {right_name} must have same length")


def selection_rate(y_pred: Binary) -> float:
    """Return P(y_pred=1). Empty samples are invalid for an audit."""
    _validate_binary(y_pred, "y_pred")
    if not y_pred:
        raise ValueError("selection_rate is undefined for an empty sample")
    return sum(y_pred) / len(y_pred)


def disparate_impact_ratio(
    y_pred_protected: Binary,
    y_pred_reference: Binary,
) -> float | None:
    """DIR = selection_rate(protected) / selection_rate(reference).

    Returns None when the reference selection rate is zero because the ratio
    is undefined, rather than silently reporting a misleading numeric value.
    """
    sr_p = selection_rate(y_pred_protected)
    sr_r = selection_rate(y_pred_reference)
    if sr_r == 0:
        return None
    value = sr_p / sr_r
    return value if isfinite(value) else None


def statistical_parity_difference(
    y_pred_protected: Binary,
    y_pred_reference: Binary,
) -> float:
    """SPD = SR_protected - SR_reference."""
    return selection_rate(y_pred_protected) - selection_rate(y_pred_reference)


def true_positive_rate(
    y_true: Binary,
    y_pred: Binary,
) -> float | None:
    """TPR = TP / P.

    Returns None when there are no positive ground-truth examples because
    the denominator is zero and the metric is undefined.
    """
    _require_same_length(y_true, y_pred, "y_true", "y_pred")
    _validate_binary(y_true, "y_true")
    _validate_binary(y_pred, "y_pred")

    positives = sum(y_true)
    if positives == 0:
        return None

    true_positives = sum(yt == 1 and yp == 1 for yt, yp in zip(y_true, y_pred))
    return true_positives / positives


def equal_opportunity_difference(
    y_true_protected: Binary,
    y_pred_protected: Binary,
    y_true_reference: Binary,
    y_pred_reference: Binary,
) -> float | None:
    """EOD = TPR_protected - TPR_reference."""
    tpr_p = true_positive_rate(y_true_protected, y_pred_protected)
    tpr_r = true_positive_rate(y_true_reference, y_pred_reference)
    if tpr_p is None or tpr_r is None:
        return None
    return tpr_p - tpr_r


@dataclass(frozen=True)
class FairnessReport:
    dir: float | None
    spd: float
    eod: float | None
