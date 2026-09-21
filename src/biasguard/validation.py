from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence


class InvalidEvaluatorResponse(ValueError):
    """Raised when an evaluator response violates the BiasGuard contract."""


@dataclass(frozen=True)
class ValidationSummary:
    expected: int
    received: int
    valid: int
    invalid: int
    missing: int
    unknown: int


def _validate_probability(value: Any, field: str, question_id: str) -> None:
    if value is None:
        return
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise InvalidEvaluatorResponse(
            f"{question_id}.{field} must be numeric"
        ) from exc
    if not 0.0 <= number <= 1.0:
        raise InvalidEvaluatorResponse(
            f"{question_id}.{field} must be between 0 and 1"
        )


def validate_evaluator_response(
    response: Any,
    questions: Sequence[Mapping[str, Any]],
) -> ValidationSummary:
    """Validate an untrusted evaluator payload before normalization.

    Expected questions define the contract. Missing expected answers are
    explicitly counted. Unknown extra answer IDs are ignored for evaluation
    but counted so they cannot disappear silently.
    """
    if not isinstance(response, Mapping):
        raise InvalidEvaluatorResponse("evaluator response must be a mapping")

    raw_answers = response.get("answers", response)
    if not isinstance(raw_answers, Mapping):
        raise InvalidEvaluatorResponse(
            "evaluator response 'answers' must be a mapping"
        )

    expected: dict[str, str] = {}
    for question in questions:
        if not isinstance(question, Mapping):
            raise InvalidEvaluatorResponse(
                "every question definition must be a mapping"
            )
        question_id = question.get("id")
        kind = question.get("type")
        if not isinstance(question_id, str) or not question_id:
            raise InvalidEvaluatorResponse(
                "every question must have a non-empty string id"
            )
        if not isinstance(kind, str) or not kind:
            raise InvalidEvaluatorResponse(
                f"{question_id} must declare a question type"
            )
        if question_id in expected:
            raise InvalidEvaluatorResponse(
                f"duplicate question id: {question_id}"
            )
        expected[question_id] = kind

    valid = 0
    missing = 0

    for question_id, kind in expected.items():
        if question_id not in raw_answers:
            missing += 1
            continue

        answer = raw_answers[question_id]
        if not isinstance(answer, Mapping):
            raise InvalidEvaluatorResponse(
                f"{question_id} answer must be a mapping"
            )

        _validate_probability(
            answer.get("confidence"), "confidence", question_id
        )

        probability = answer.get("probability")
        if kind == "noul" and "noul" in answer:
            probability = answer.get("noul")
        _validate_probability(probability, "probability", question_id)

        if kind == "score":
            value = answer.get("score", answer.get("value"))
            if value is not None:
                try:
                    float(value)
                except (TypeError, ValueError) as exc:
                    raise InvalidEvaluatorResponse(
                        f"{question_id}.score/value must be numeric"
                    ) from exc

        elif kind == "choice":
            value = answer.get("choice", answer.get("value"))
            if value is not None and not isinstance(
                value, (str, int, float, bool)
            ):
                raise InvalidEvaluatorResponse(
                    f"{question_id}.choice/value must be scalar"
                )

        valid += 1

    unknown = sum(
        1 for question_id in raw_answers if question_id not in expected
    )

    return ValidationSummary(
        expected=len(expected),
        received=len(raw_answers),
        valid=valid,
        invalid=0,
        missing=missing,
        unknown=unknown,
    )
