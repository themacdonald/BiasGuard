from biasguard.calibration import (
    action_report,
    binary_report,
    calibration_summary,
    score_report,
    threshold_sweep,
)


def _judgments():
    return [
        {
            "state_hash": "a",
            "judgments": {
                "bias_gender": {
                    "kind": "noul", "probability": 0.9, "confidence": 0.9
                },
                "severity": {
                    "kind": "score", "value": 3, "confidence": 0.9
                },
                "review_track": {
                    "kind": "choice", "value": "block", "confidence": 0.9
                },
            },
            "result": {"action": "block"},
        },
        {
            "state_hash": "b",
            "judgments": {
                "bias_gender": {
                    "kind": "noul", "probability": 0.1, "confidence": 0.9
                },
                "severity": {
                    "kind": "score", "value": 1, "confidence": 0.9
                },
                "review_track": {
                    "kind": "choice", "value": "pass", "confidence": 0.9
                },
            },
            "result": {"action": "pass"},
        },
    ]


def _labels():
    return [
        {
            "state_hash": "a",
            "binary": {"bias_gender": 1},
            "score": {"severity": 3},
            "choice": {"review_track": "block"},
            "expected_action": "block",
        },
        {
            "state_hash": "b",
            "binary": {"bias_gender": 0},
            "score": {"severity": 1},
            "choice": {"review_track": "pass"},
            "expected_action": "pass",
        },
    ]


def test_reports_are_question_specific():
    judgments, labels = _judgments(), _labels()
    assert binary_report(judgments, labels, "bias_gender")["n"] == 2
    assert score_report(judgments, labels, "severity")["exact_agreement"] == 1.0
    assert action_report(judgments, labels)["action_accuracy"] == 1.0


def test_threshold_sweep():
    rows = threshold_sweep(_judgments(), _labels(), "bias_gender", [0.8])
    assert rows[0]["flagged"] == 1
    assert rows[0]["missed"] == 0


def test_summary_discovers_questions():
    summary = calibration_summary(_judgments(), _labels())
    assert "bias_gender" in summary["binary"]
    assert "severity" in summary["scores"]
    assert "review_track" in summary["choices"]
    assert summary["action"]["correct"] == 2
