from __future__ import annotations

import json
from collections import defaultdict
from typing import Any, Iterable, Mapping

from .calibration_coverage import PairingResult, coverage_from_pairing, pair_binary_records


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
        if not 0.0 <= float(p) <= 1.0:
            raise ValueError("probabilities must be between 0 and 1")
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


def _binary_pairing(
    judgments: list[Mapping[str, Any]],
    labels: list[Mapping[str, Any]],
    question_id: str,
) -> tuple[list[tuple[float, int]], dict[str, Any]]:
    result = pair_binary_records(judgments, labels, question_id)
    coverage = coverage_from_pairing(result, supplied=len(labels))
    return list(result.pairs), {
        "supplied": coverage.supplied,
        "valid": coverage.valid,
        "invalid": coverage.invalid,
        "unmatched": coverage.unmatched,
        "missing_answer": coverage.missing_answer,
        "evaluated": coverage.evaluated,
    }


def _matched_values(
    judgments: list[Mapping[str, Any]],
    labels: list[Mapping[str, Any]],
    question_id: str,
    section: str,
) -> tuple[list[tuple[Any, Any, Any]], dict[str, Any]]:
    by_hash: dict[str, Mapping[str, Any]] = {}
    invalid = 0
    for row in judgments:
        state_hash = row.get("state_hash")
        if not isinstance(state_hash, str) or not state_hash or state_hash in by_hash:
            invalid += 1
            continue
        by_hash[state_hash] = row

    pairs: list[tuple[Any, Any, Any]] = []
    unmatched = 0
    missing_answer = 0
    for label in labels:
        state_hash = label.get("state_hash")
        if not isinstance(state_hash, str) or not state_hash:
            invalid += 1
            continue
        row = by_hash.get(state_hash)
        if row is None:
            unmatched += 1
            continue
        answer = row.get("judgments", {}).get(question_id)
        target = label.get(section, {}).get(question_id)
        if not isinstance(answer, Mapping) or target is None:
            missing_answer += 1
            continue
        pairs.append((answer, target, state_hash))

    return pairs, {
        "supplied": len(labels),
        "valid": len(pairs),
        "invalid": invalid,
        "unmatched": unmatched,
        "missing_answer": missing_answer,
        "evaluated": len(pairs),
    }


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
    pairs, coverage = _binary_pairing(judgments, labels, question_id)
    tp = sum(p >= 0.5 and y == 1 for p, y in pairs)
    tn = sum(p < 0.5 and y == 0 for p, y in pairs)
    fp = sum(p >= 0.5 and y == 0 for p, y in pairs)
    fn = sum(p < 0.5 and y == 1 for p, y in pairs)
    return {
        "question_id": question_id,
        "n": len(pairs),
        "coverage": coverage,
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
    pairs, coverage = _binary_pairing(judgments, labels, question_id)
    return [
        {
            "threshold": float(t),
            "flagged": sum(p >= t for p, _ in pairs),
            "missed": sum(p < t and y == 1 for p, y in pairs),
            "false_positive": sum(p >= t and y == 0 for p, y in pairs),
            "n": len(pairs),
            "coverage": coverage,
        }
        for t in thresholds
    ]


def score_report(
    judgments: list[Mapping[str, Any]],
    labels: list[Mapping[str, Any]],
    question_id: str,
) -> dict[str, Any]:
    pairs, coverage = _matched_values(judgments, labels, question_id, "score")
    values = []
    invalid = coverage["invalid"]
    for answer, target, _ in pairs:
        try:
            value = answer.get("value", answer.get("score"))
            confidence = (
                float(answer["confidence"])
                if answer.get("confidence") is not None
                else None
            )
            target = float(target)
            value = float(value)
            if not 0.0 <= confidence <= 1.0 if confidence is not None else False:
                invalid += 1
                continue
            values.append((value, target, confidence))
        except (TypeError, ValueError):
            invalid += 1
    coverage["invalid"] = invalid
    coverage["valid"] = len(values)
    coverage["evaluated"] = len(values)

    if not values:
        return {
            "question_id": question_id,
            "n": 0,
            "coverage": coverage,
            "exact_agreement": 0.0,
            "within_one_level": 0.0,
            "mae": 0.0,
            "average_confidence": None,
            "low_confidence_rate": 0.0,
        }

    confidences = [c for _, _, c in values if c is not None]
    return {
        "question_id": question_id,
        "n": len(values),
        "coverage": coverage,
        "exact_agreement": sum(p == t for p, t, _ in values) / len(values),
        "within_one_level": sum(abs(p - t) <= 1 for p, t, _ in values) / len(values),
        "mae": sum(abs(p - t) for p, t, _ in values) / len(values),
        "average_confidence": (
            _safe_div(sum(confidences), len(confidences))
            if confidences else None
        ),
        "low_confidence_rate": (
            _safe_div(sum(c < 0.5 for c in confidences), len(confidences))
            if confidences else 0.0
        ),
    }


def choice_report(
    judgments: list[Mapping[str, Any]],
    labels: list[Mapping[str, Any]],
    question_id: str,
) -> dict[str, Any]:
    pairs, coverage = _matched_values(judgments, labels, question_id, "choice")
    values = [
        (str(answer["value"]), str(target))
        for answer, target, _ in pairs
        if answer.get("value") is not None
    ]
    coverage["valid"] = len(values)
    coverage["evaluated"] = len(values)
    exact = sum(p == t for p, t in values)
    classes = sorted({p for p, _ in values} | {t for _, t in values})
    per_class = {
        cls: _safe_div(
            sum(p == t for p, t in values if t == cls),
            sum(t == cls for _, t in values),
        )
        for cls in classes
    }
    return {
        "question_id": question_id,
        "n": len(values),
        "coverage": coverage,
        "accuracy": _safe_div(exact, len(values)),
        "per_class_accuracy": per_class,
    }


def action_report(
    judgments: list[Mapping[str, Any]],
    labels: list[Mapping[str, Any]],
) -> dict[str, Any]:
    by_hash: dict[str, Mapping[str, Any]] = {}
    invalid = 0
    for row in judgments:
        state_hash = row.get("state_hash")
        if not isinstance(state_hash, str) or not state_hash or state_hash in by_hash:
            invalid += 1
            continue
        by_hash[state_hash] = row

    values = []
    unmatched = 0
    missing_answer = 0
    for label in labels:
        state_hash = label.get("state_hash")
        expected = label.get("expected_action")
        if not isinstance(state_hash, str) or not state_hash:
            invalid += 1
            continue
        row = by_hash.get(state_hash)
        if row is None:
            unmatched += 1
            continue
        if expected is None:
            missing_answer += 1
            continue
        actual = row.get("result", {}).get("action")
        if actual is None:
            missing_answer += 1
            continue
        values.append(actual == expected)

    coverage = {
        "supplied": len(labels),
        "valid": len(values),
        "invalid": invalid,
        "unmatched": unmatched,
        "missing_answer": missing_answer,
        "evaluated": len(values),
    }
    return {
        "n": len(values),
        "coverage": coverage,
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
            if confidence is not None:
                try:
                    confidence = float(confidence)
                except (TypeError, ValueError):
                    continue
                if confidence < threshold:
                    findings.append({
                        "state_hash": row.get("state_hash"),
                        "question_id": question_id,
                        "kind": answer.get("kind"),
                        "confidence": confidence,
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
