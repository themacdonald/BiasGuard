import pytest

from biasguard.validation import (
    InvalidEvaluatorResponse,
    validate_evaluator_response,
)


QUESTIONS = [
    {"id": "bias_gender", "type": "noul"},
    {"id": "severity", "type": "score"},
    {"id": "review_track", "type": "choice"},
]


def test_valid_response_and_coverage():
    result = validate_evaluator_response(
        {
            "answers": {
                "bias_gender": {"noul": 0.9, "confidence": 0.8},
                "severity": {"score": 3, "confidence": 0.9},
                "review_track": {"choice": "human_review"},
            }
        },
        QUESTIONS,
    )
    assert result.expected == 3
    assert result.received == 3
    assert result.valid == 3
    assert result.missing == 0
    assert result.unknown == 0


def test_missing_answer_is_explicit():
    result = validate_evaluator_response(
        {"answers": {"bias_gender": {"noul": 0.9}}},
        QUESTIONS,
    )
    assert result.missing == 2
    assert result.valid == 1


def test_unknown_answers_are_counted():
    result = validate_evaluator_response(
        {
            "answers": {
                "bias_gender": {"noul": 0.9},
                "unexpected": {"value": "ignored"},
            }
        },
        QUESTIONS,
    )
    assert result.unknown == 1


@pytest.mark.parametrize(
    "response",
    [None, [], "invalid", 42],
)
def test_non_mapping_response_rejected(response):
    with pytest.raises(InvalidEvaluatorResponse):
        validate_evaluator_response(response, QUESTIONS)


def test_answers_must_be_mapping():
    with pytest.raises(InvalidEvaluatorResponse, match="answers"):
        validate_evaluator_response({"answers": []}, QUESTIONS)


@pytest.mark.parametrize("field", ["confidence", "probability"])
def test_probability_fields_must_be_bounded(field):
    with pytest.raises(InvalidEvaluatorResponse, match="between 0 and 1"):
        validate_evaluator_response(
            {
                "answers": {
                    "bias_gender": {"noul": 1.2} if field == "probability"
                    else {"noul": 0.8, "confidence": -0.1}
                }
            },
            QUESTIONS,
        )


def test_score_must_be_numeric():
    with pytest.raises(InvalidEvaluatorResponse, match="numeric"):
        validate_evaluator_response(
            {"answers": {"severity": {"score": "high"}}},
            QUESTIONS,
        )


def test_duplicate_question_ids_rejected():
    with pytest.raises(InvalidEvaluatorResponse, match="duplicate"):
        validate_evaluator_response(
            {"answers": {}},
            [{"id": "x", "type": "noul"}, {"id": "x", "type": "noul"}],
        )
