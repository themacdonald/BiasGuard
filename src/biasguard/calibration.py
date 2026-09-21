from __future__ import annotations

import json
from collections import defaultdict
from typing import Any, Iterable, Mapping


def load_jsonl(path: str) -> list[dict[str, Any]]:
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def _safe_div(num: float, den: float) -> float:
    return num / den if den else 0.0


def brier_score(predictions: Iterable[float], labels: Iterable[int]) -> float:
    pairs = list(zip(predictions, labels))
    return _safe_div(sum((p - y) ** 2 for p, y in pairs), len(pairs))


def expected_calibration_error(
    predictions: Iterable[float], labels: Iterable[int], bins: int = 10
) -> float:
    pairs = list(zip(predictions, labels))
    if not pairs or bins <= 0:
        return 0.0
    buckets: dict[int, list[tuple[float, int]]] = defaultdict(list)
    for p, y in pairs:
        index = min(int(float(p) * bins), bins - 1)
        buckets[index].append((float(p), int(y)))
    total = len(pairs)
    return sum(
        (len(items) / total)
        * abs(
            sum(p for p, _ in items) / len(items)
            - sum(y for _, y in items) / len(items)
        )
        for items in buckets.values()
    )


def _binary_pairs(
    judgments: list[Mapping[str, Any]],
    labels: list[Mapping[str, Any]],
    question_id: str,
) -> list[tuple[float, int]]:
    by_hash = {row.get("state_hash"): row for row in judgments}
    pairs = []
    for label in labels:
        row = by_hash.get(label.get("state_hash"))
        answer = row.get("judgments", {}).get(question_id) if row else None
        target = label.get("binary", {}).get(question_id)
        if not isinstance(answer, Mapping) or target is None:
            continue
        probability = answer.get("probability")
        if probability is not None:
            pairs.append((float(probability), int(target)))
    return pairs


def reliability_bins(
    pairs: list[tuple[float, int]], bins: int = 10
) -> list[dict[str, float | int]]:
    grouped: dict[int, list[tuple[float, int]]] = defaultdict(list)
    for probability, label in pairs:
        index = min(int(probability * bins), bins - 1)
        grouped[index].append((probability, label))
    return [
        {
            "lower": index / bins,
            "upper": (index + 1) / bins,
            "n": len(values),
            "mean_prediction": sum(p for p, _ in values) / len(values),
            "empirical_positive_rate": sum(y for _, y in values) / len(values),
        }
        for index, values in sorted(grouped.items())
    ]


def binary_report(
    judgments: list[Mapping[str, Any]],
    labels: list[Mapping[str, Any]],
    question_id: str,
) -> dict[str, Any]:
    pairs = _binary_pairs(judgments, labels, question_id)
    tp = sum(p >= 0.5 and y == 1 for p, y in pairs)
    tn = sum(p < 0.5 and y == 0 for p, y in pairs)
    fp = sum(p >= 0.5 and y == 0 for p, y in pairs)
    fn = sum(p < 0.5 and y == 1 for p, y in pairs)
    return {
        "question_id": question_id,
        "n": len(pairs),
        "brier": brier_score((p for p, _ in pairs), (y for _, y in pairs)),
        "ece": expected_calibration_error((p for p, _ in pairs), (y for _, y in pairs)),
        "precision": _safe_div(tp, tp + fp),
        "recall": _safe_div(tp, tp + fn),
        "false_positive_rate": _safe_div(fp, fp + tn),
        "false_negative_rate": _safe_div(fn, fn + tp),
        "reliability": reliability_bins(pairs),
    }


def threshold_sweep(
    judgments: list[Mapping[str, Any]],
    labels: list[Mapping[str, Any]],
    question_id: str,
    thresholds: Iterable[float] = tuple(x / 100 for x in range(50, 96, 5)),
) -> list[dict[str, Any]]:
    pairs = _binary_pairs(judgments, labels, question_id)
    return [
        {
            "threshold": float(t),
            "flagged": sum(p >= t for p, _ in pairs),
            "missed": sum(p < t and y == 1 for p, y in pairs),
            "false_positive": sum(p >= t and y == 0 for p, y in pairs),
            "n": len(pairs),
        }
        for t in thresholds
    ]


def score_report(
    judgments: list[Mapping[str, Any]],
    labels: list[Mapping[str, Any]],
    question_id: str,
) -> dict[str, Any]:
    by_hash = {row.get("state_hash"): row for row in judgments}
    pairs = []
    for label in labels:
        row = by_hash.get(label.get("state_hash"))
        answer = row.get("judgments", {}).get(question_id) if row else None
        target = label.get("score", {}).get(question_id)
        if not isinstance(answer, Mapping) or target is None:
            continue
        value = answer.get("value", answer.get("score"))
        if value is not None:
            pairs.append((
                float(value), float(target),
                float(answer["confidence"]) if answer.get("confidence") is not None else None
            ))
    if not pairs:
        return {
            "question_id": question_id, "n": 0, "exact_agreement": 0.0,
            "within_one_level": 0.0, "mae": 0.0,
            "average_confidence": None, "low_confidence_rate": 0.0,
        }
    confidences = [c for _, _, c in pairs if c is not None]
    return {
        "question_id": question_id,
        "n": len(pairs),
        "exact_agreement": sum(p == t for p, t, _ in pairs) / len(pairs),
        "within_one_level": sum(abs(p - t) <= 1 for p, t, _ in pairs) / len(pairs),
        "mae": sum(abs(p - t) for p, t, _ in pairs) / len(pairs),
        "average_confidence": _safe_div(sum(confidences), len(confidences)),
        "low_confidence_rate": _safe_div(sum(c < 0.5 for c in confidences), len(confidences)),
    }


def choice_report(
    judgments: list[Mapping[str, Any]],
    labels: list[Mapping[str, Any]],
    question_id: str,
) -> dict[str, Any]:
    by_hash = {row.get("state_hash"): row for row in judgments}
    pairs = []
    for label in labels:
        row = by_hash.get(label.get("state_hash"))
        answer = row.get("judgments", {}).get(question_id) if row else None
        target = label.get("choice", {}).get(question_id)
        if isinstance(answer, Mapping) and target is not None and answer.get("value") is not None:
            pairs.append((str(answer["value"]), str(target)))
    exact = sum(p == t for p, t in pairs)
    classes = sorted({p for p, _ in pairs} | {t for _, t in pairs})
    per_class = {
        cls: _safe_div(sum(p == t for p, t in pairs if t == cls),
                       sum(t == cls for _, t in pairs))
        for cls in classes
    }
    return {
        "question_id": question_id,
        "n": len(pairs),
        "accuracy": _safe_div(exact, len(pairs)),
        "per_class_accuracy": per_class,
    }


def action_report(
    judgments: list[Mapping[str, Any]],
    labels: list[Mapping[str, Any]],
) -> dict[str, Any]:
    """Measure policy-action accuracy against adjudicated expected_action labels."""
    by_hash = {row.get("state_hash"): row for row in judgments}
    values = []
    for label in labels:
        row = by_hash.get(label.get("state_hash"))
        expected = label.get("expected_action")
        if not row or expected is None:
            continue
        actual = row.get("result", {}).get("action")
        values.append(actual == expected)
    return {
        "n": len(values),
        "action_accuracy": _safe_div(sum(values), len(values)),
        "correct": sum(values),
        "incorrect": len(values) - sum(values),
    }


def low_confidence_findings(
    judgments: list[Mapping[str, Any]], threshold: float = 0.5
) -> list[dict[str, Any]]:
    findings = []
    for row in judgments:
        for question_id, answer in row.get("judgments", {}).items():
            if not isinstance(answer, Mapping):
                continue
            confidence = answer.get("confidence")
            if confidence is not None and float(confidence) < threshold:
                findings.append({
                    "state_hash": row.get("state_hash"),
                    "question_id": question_id,
                    "kind": answer.get("kind"),
                    "confidence": float(confidence),
                })
    return findings


def _question_ids(judgments: list[Mapping[str, Any]], prefix: str) -> list[str]:
    ids = set()
    for row in judgments:
        for question_id in row.get("judgments", {}):
            if prefix == "binary" and (
                question_id.startswith("bias_")
                or question_id.startswith("verify_")
                or question_id in {"protected_reference", "proxy_influence"}
            ):
                ids.add(question_id)
            elif prefix == "score" and question_id in {"severity", "harm"}:
                ids.add(question_id)
            elif prefix == "choice" and question_id in {"review_track", "root_cause"}:
                ids.add(question_id)
    return sorted(ids)


def calibration_summary(
    judgments: list[Mapping[str, Any]],
    labels: list[Mapping[str, Any]],
    *,
    binary_questions: Iterable[str] | None = None,
    score_questions: Iterable[str] | None = None,
    choice_questions: Iterable[str] | None = None,
) -> dict[str, Any]:
    binary_questions = list(binary_questions or _question_ids(judgments, "binary"))
    score_questions = list(score_questions or _question_ids(judgments, "score"))
    choice_questions = list(choice_questions or _question_ids(judgments, "choice"))
    return {
        "binary": {q: binary_report(judgments, labels, q) for q in binary_questions},
        "thresholds": {q: threshold_sweep(judgments, labels, q) for q in binary_questions},
        "scores": {q: score_report(judgments, labels, q) for q in score_questions},
        "choices": {q: choice_report(judgments, labels, q) for q in choice_questions},
        "action": action_report(judgments, labels),
        "low_confidence": low_confidence_findings(judgments),
    }
