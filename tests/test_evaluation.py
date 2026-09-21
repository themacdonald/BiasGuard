import pytest

from biasguard.evaluation import (
    BiasGuardEvaluator,
    EvaluationPolicy,
    PolicyThresholds,
    build_questions,
    build_state,
    state_hash,
)
from biasguard.typesafe_adapter import TypeSafeObservation


def obs(qid, kind, value=None, confidence=None, probability=None):
    return TypeSafeObservation(
        question_id=qid,
        kind=kind,
        value=value,
        confidence=confidence,
        probability=probability,
    )


def test_questions_use_typed_primitives():
    questions = build_questions(["gender", "race"], ["selection_rate"])
    types = {q["id"]: q["type"] for q in questions}

    assert types["bias_gender"] == "noul"
    assert types["bias_race"] == "noul"
    assert types["severity"] == "score"
    assert types["review_track"] == "choice"
    assert types["verify_selection_rate"] == "noul"


def test_state_hash_is_stable():
    state = build_state({"candidate": "A"}, context={"source": "test"})
    assert state_hash(state) == state_hash(state)


def test_high_severity_blocks_when_confident():
    evaluator = BiasGuardEvaluator()
    result = evaluator.compose(
        [
            obs("bias_gender", "noul", probability=0.95, confidence=0.95),
            obs("severity", "score", value=3, confidence=0.90),
            obs("harm", "score", value=3, confidence=0.90),
        ]
    )
    assert result.action == "block"
    assert not result.human_review


def test_uncertain_bias_routes_to_human_review():
    evaluator = BiasGuardEvaluator()
    result = evaluator.compose(
        [
            obs("bias_gender", "noul", probability=0.50, confidence=0.51),
            obs("severity", "score", value=3, confidence=0.90),
        ]
    )
    assert result.action == "human_review"


def test_low_severity_confidence_routes_to_human_review():
    evaluator = BiasGuardEvaluator()
    result = evaluator.compose(
        [
            obs("bias_gender", "noul", probability=0.85, confidence=0.80),
            obs("severity", "score", value=2, confidence=0.40),
        ]
    )
    assert result.action == "human_review"


def test_concern_below_review_threshold_is_logged():
    evaluator = BiasGuardEvaluator()
    result = evaluator.compose(
        [
            obs("bias_gender", "noul", probability=0.40, confidence=0.90),
            obs("severity", "score", value=1, confidence=0.90),
        ]
    )
    assert result.action == "log_only"


def test_no_concern_passes():
    evaluator = BiasGuardEvaluator()
    result = evaluator.compose(
        [
            obs("bias_gender", "noul", probability=0.05, confidence=0.95),
            obs("severity", "score", value=0, confidence=0.95),
        ]
    )
    assert result.action == "pass"


def test_custom_policy_is_respected():
    policy = EvaluationPolicy(
        thresholds=PolicyThresholds(
            bias_yes=0.90,
            bias_no=0.10,
            block_at_severity=4,
            review_at_severity=3,
        )
    )
    evaluator = BiasGuardEvaluator(policy=policy)
    result = evaluator.compose(
        [
            obs("bias_gender", "noul", probability=0.85, confidence=0.95),
            obs("severity", "score", value=2, confidence=0.95),
        ]
    )
    assert result.action == "log_only"


def test_evaluate_requires_client():
    evaluator = BiasGuardEvaluator()
    with pytest.raises(RuntimeError, match="No structured evaluator"):
        evaluator.evaluate({"decision": "test"}, build_questions(["gender"]))


class FakeClient:
    def evaluate(self, state, questions):
        return {
            "answers": {
                "bias_gender": {
                    "value": True,
                    "probability": 0.92,
                    "confidence": 0.90,
                },
                "severity": {
                    "value": 3,
                    "confidence": 0.90,
                },
                "harm": {
                    "value": 2,
                    "confidence": 0.80,
                },
            }
        }


def test_evaluate_creates_auditable_record():
    evaluator = BiasGuardEvaluator(client=FakeClient(), model="test-model")
    state = build_state({"decision": "reject"}, context={"case_id": "1"})
    record = evaluator.evaluate(state, build_questions(["gender"]))

    assert record.model == "test-model"
    assert record.policy_version == "policy-v1"
    assert len(record.state_hash) == 64
    assert record.result["action"] == "block"
    assert "bias_gender" in record.judgments
