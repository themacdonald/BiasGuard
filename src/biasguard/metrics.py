from __future__ import annotations

from dataclasses import dataclass


def _rate(num: int, den: int) -> float:
    return float(num) / float(den) if den else 0.0


def selection_rate(y_pred: list[int]) -> float:
    """P(ŷ=1)."""
    return _rate(sum(1 for v in y_pred if v == 1), len(y_pred))


def disparate_impact_ratio(y_pred_protected: list[int], y_pred_reference: list[int]) -> float:
    """DIR = SR_protected / SR_reference. 80% rule flag if < 0.8 (interpretation in reports)."""
    sr_p = selection_rate(y_pred_protected)
    sr_r = selection_rate(y_pred_reference)
    return _rate(int(sr_p * 1_000_000), int(sr_r * 1_000_000)) if sr_r else 0.0


def statistical_parity_difference(y_pred_protected: list[int], y_pred_reference: list[int]) -> float:
    """SPD = SR_protected - SR_reference."""
    return selection_rate(y_pred_protected) - selection_rate(y_pred_reference)


def true_positive_rate(y_true: list[int], y_pred: list[int]) -> float:
    """TPR = TP / P."""
    if len(y_true) != len(y_pred):
        raise ValueError("y_true and y_pred must have same length")
    tp = 0
    p = 0
    for yt, yp in zip(y_true, y_pred):
        if yt == 1:
            p += 1
            if yp == 1:
                tp += 1
    return _rate(tp, p)


def equal_opportunity_difference(
    y_true_protected: list[int],
    y_pred_protected: list[int],
    y_true_reference: list[int],
    y_pred_reference: list[int],
) -> float:
    """EOD = TPR_protected - TPR_reference."""
    tpr_p = true_positive_rate(y_true_protected, y_pred_protected)
    tpr_r = true_positive_rate(y_true_reference, y_pred_reference)
    return tpr_p - tpr_r


@dataclass(frozen=True)
class FairnessReport:
    dir: float
    spd: float
    eod: float
