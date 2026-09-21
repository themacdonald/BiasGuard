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
    if not pairs:
        return 0.0
    return sum((p - y) ** 2 for p, y in pairs) / len(pairs)


def expected_calibration_error(
    predictions: Iterable[float],
    labels: Iterable[int],
    bins: int = 10,
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
    label_key: str = "bias",
) -> list[tuple[float, int]]:
    by_hash = {row.get("state_hash"): row for row in judgments}
    pairs: list[tuple[float, int]] = []

    for label in labels:
        row = by_hash.get(label.get("state_hash"))
        if not row:
            continue

        answer = row.get("judgments", {}).get(question_id)
        target = label.get(label_key, {})

        if not isinstance(answer, Mapping) or question_id not in target:
            continue

        probability = answer.get("probability", answer.get("noul"))
        if probability is None:
            continue

        pairs.append((float(probability), int(target[question_id])))

    return pairs


def reliability_bins(
    pairs: list[tuple[float, int]],
    bins: int = 10,
) -> list[dict[str, float | int]]:
    grouped: dict[int, list[tuple[float, int]]] = defaultdict(list)

    for probability, label in pairs:
        index = min(int(probability * bins), bins - 1)
        grouped[index].append((probability, label))

    result = []
    for index in sorted(grouped):
        values = grouped[index]
        result.append(
            {
                "lower": index / bins,
                "upper": (index + 1) / bins,
                "n": len(values),
                "mean_prediction": sum(p for p, _ in values) / len(values),
                "empirical_positive_rate": sum(y for _, y in values) / len(values),
            }
        )
    return result


def binary_report(
    judgments: list[Mapping[str, Any]],
    labels: list[Mapping[str, Any]],
    question_id: str,
) -> dict[str, Any]:
    pairs = _binary_pairs(judgments, labels, question_id)

    predictions = [p for p, _ in pairs]
    targets = [y for _, y in pairs]

    tp = sum(p >= 0.5 and y == 1 for p, y in pairs)
    tn = sum(p < 0.5 and y == 0 for p, y in pairs)
    fp = sum(p >= 0.5 and y == 0 for p, y in pairs)
    fn = sum(p < 0.5 and y == 1 for p, y in pairs)

    return {
        "question_id": question_id,
        "n": len(pairs),
        "brier": brier_score(predictions, targets),
        "ece": expected_calibration_error(predictions, targets),
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
    output = []

    for threshold in thresholds:
        flagged = sum(p >= threshold for p, _ in pairs)
        missed = sum(p < threshold and y == 1 for p, y in pairs)
        false_positive = sum(p >= threshold and y == 0 for p, y in pairs)
        human_band = sum(0.20 <= p < threshold for p, _ in pairs)

        output.append(
            {
                "threshold": float(threshold),
                "flagged": flagged,
                "missed": missed,
                "false_positive": false_positive,
                "human_band": human_band,
                "n": len(pairs),
            }
        )

    return output


def score_report(
    judgments: list[Mapping[str, Any]],
    labels: list[Mapping[str, Any]],
    question_id: str,
) -> dict[str, Any]:
    by_hash = {row.get("state_hash"): row for row in judgments}
    pairs: list[tuple[float, float, float | None]] = []

    for label in labels:
        row = by_hash.get(label.get("state_hash"))
        if not row:
            continue

        answer = row.get("judgments", {}).get(question_id)
        target = label.get("severity", {}).get(question_id)

        if not isinstance(answer, Mapping) or target is None:
            continue

        value = answer.get("value", answer.get("score"))
        if value is None:
            continue

        pairs.append(
            (
                float(value),
                float(target),
                float(answer["confidence"]) if answer.get("confidence") is not None else None,
            )
        )

    if not pairs:
        return {
            "question_id": question_id,
            "n": 0,
            "exact_agreement": 0.0,
            "within_one_level": 0.0,
            "mae": 0.0,
            "average_confidence": None,
            "low_confidence_rate": 0.0,
        }

    exact = sum(pred == target for pred, target, _ in pairs)
    within_one = sum(abs(pred - target) <= 1 for pred, target, _ in pairs)
    confidences = [c for _, _, c in pairs if c is not None]

    return {
        "question_id": question_id,
        "n": len(pairs),
        "exact_agreement": exact / len(pairs),
        "within_one_level": within_one / len(pairs),
        "mae": sum(abs(pred - target) for pred, target, _ in pairs) / len(pairs),
        "average_confidence": (
            sum(confidences) / len(confidences) if confidences else None
        ),
        "low_confidence_rate": (
            sum(c < 0.5 for c in confidences) / len(confidences)
            if confidences
            else 0.0
        ),
    }


def choice_report(
    judgments: list[Mapping[str, Any]],
    labels: list[Mapping[str, Any]],
    question_id: str,
) -> dict[str, Any]:
    by_hash = {row.get("state_hash"): row for row in judgments}
    pairs: list[tuple[str, str]] = []

    for label in labels:
        row = by_hash.get(label.get("state_hash"))
        if not row:
            continue

        answer = row.get("judgments", {}).get(question_id)
        target = label.get("choice", {}).get(question_id)

        if not isinstance(answer, Mapping) or target is None:
            continue

        value = answer.get("value")
        if value is not None:
            pairs.append((str(value), str(target)))

    exact = sum(pred == target for pred, target in pairs)
    classes = sorted({pred for pred, _ in pairs} | {target for _, target in pairs})
    per_class = {}

    for cls in classes:
        class_pairs = [(p, t) for p, t in pairs if t == cls]
        per_class[cls] = _safe_div(
            sum(p == t for p, t in class_pairs),
            len(class_pairs),
        )

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
    by_hash = {row.get("state_hash"): row for row in judgments}
    values: list[bool] = []

    for label in labels:
        row = by_hash.get(label.get("state_hash"))
        if not row or "action_ok" not in label:
            continue

        result = row.get("result", {})
        action = result.get("action")
        expected = label["action_ok"]

        if isinstance(expected, bool):
            values.append(bool(action) == expected)

    return {
        "n": len(values),
        "action_accuracy": _safe_div(sum(values), len(values)),
    }


def low_confidence_findings(
    judgments: list[Mapping[str, Any]],
    threshold: float = 0.5,
) -> list[dict[str, Any]]:
    findings = []

    for row in judgments:
        for question_id, answer in row.get("judgments", {}).items():
            if not isinstance(answer, Mapping):
                continue

            confidence = answer.get("confidence")
            kind = answer.get("kind")

            if confidence is not None and float(confidence) < threshold:
                findings.append(
                    {
                        "state_hash": row.get("state_hash"),
                        "question_id": question_id,
                        "kind": kind,
                        "confidence": float(confidence),
                    }
                )

    return findings


def calibration_summary(
    judgments: list[Mapping[str, Any]],
    labels: list[Mapping[str, Any]],
    *,
    binary_questions: Iterable[str] = (),
    score_questions: Iterable[str] = (),
    choice_questions: Iterable[str] = (),
) -> dict[str, Any]:
    return {
        "binary": {
            q: binary_report(judgments, labels, q)
            for q in binary_questions
        },
        "thresholds": {
            q: threshold_sweep(judgments, labels, q)
            for q in binary_questions
        },
        "scores": {
            q: score_report(judgments, labels, q)
            for q in score_questions
        },
        "choices": {
            q: choice_report(judgments, labels, q)
            for q in choice_questions
        },
        "action": action_report(judgments, labels),
        "low_confidence": low_confidence_findings(judgments),
    }
