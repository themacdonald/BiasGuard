import json
from pathlib import Path

from biasguard.cli import build_parser, cmd_evaluate
from biasguard.evaluation import BiasGuardEvaluator, build_questions, build_state, state_hash
from biasguard.typesafe_adapter import OfflineAnswersClient


def test_parser_has_milestones():
    parser = build_parser()
    assert parser.parse_args(["demo"])
    assert parser.parse_args([
        "evaluate", "--input", "case.json", "--answers", "answers.json"
    ])
    assert parser.parse_args([
        "calibrate", "--judgments", "judgments.jsonl", "--labels", "labels.jsonl"
    ])


def test_high_concern_requires_evidence():
    state = build_state({"candidate": "A"})
    questions = build_questions(["gender"])
    client = OfflineAnswersClient({
        "bias_gender": {"probability": 0.95, "confidence": 0.95},
        "severity": {"value": 3, "confidence": 0.95},
        "harm": {"value": 3, "confidence": 0.95},
    })
    result = BiasGuardEvaluator(client, model="jev-latest").evaluate(state, questions)
    assert result.result["action"] == "block"


def test_no_bias_does_not_block_from_severity_alone():
    observations = []
    result = BiasGuardEvaluator().compose(observations)
    assert result.action == "pass"


def test_state_hash_is_stable():
    state = {"b": 2, "a": 1}
    assert state_hash(state) == state_hash({"a": 1, "b": 2})


def test_offline_evaluation_produces_audit_record():
    state = build_state({"candidate": "A"}, biasguard_flags={"dir": True})
    questions = build_questions(["gender"], ["dir"])
    client = OfflineAnswersClient({
        "bias_gender": {"probability": 0.85, "confidence": 0.9},
        "severity": {"value": 2, "confidence": 0.9},
        "harm": {"value": 2, "confidence": 0.9},
    })
    record = BiasGuardEvaluator(client, model="jev-latest").evaluate(state, questions)
    assert record.state_hash
    assert record.result["action"] == "human_review"
    assert record.judgments["bias_gender"]["kind"] == "noul"
