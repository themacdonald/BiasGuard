from biasguard.calibration import (
    brier_score,
    calibration_summary,
    choice_report,
    expected_calibration_error,
    score_report,
    threshold_sweep,
)


def judgment(state_hash, answers, action="human_review"):
    return {
        "state_hash": state_hash,
        "judgments": answers,
        "result": {"action": action},
    }


def test_brier():
    assert abs(brier_score([0.9, 0.1], [1, 0]) - 0.01) < 1e-9


def test_ece():
    value = expected_calibration_error([0.9, 0.1], [1, 0], bins=2)
    assert value == 0.0


def test_binary_calibration_is_per_question():
    from biasguard.calibration import binary_report

    judgments = [
        judgment(
            "a",
            {
                "bias_gender": {
                    "kind": "noul",
                    "probability": 0.9,
                    "confidence": 0.9,
                },
                "bias_race": {
                    "kind": "noul",
                    "probability": 0.1,
                    "confidence": 0.9,
                },
            },
        )
    ]
    labels = [
        {
            "state_hash": "a",
            "bias": {"bias_gender": 1, "bias_race": 0},
        }
    ]

    gender = binary_report(judgments, labels, "bias_gender")
    race = binary_report(judgments, labels, "bias_race")

    assert gender["n"] == 1
    assert race["n"] == 1
    assert gender["brier"] == 0.01
    assert race["brier"] == 0.01


def test_threshold_sweep_does_not_collapse_groups():
    judgments = [
        judgment(
            "a",
            {"bias_gender": {"probability": 0.9, "kind": "noul"}},
        ),
        judgment(
            "b",
            {"bias_gender": {"probability": 0.1, "kind": "noul"}},
        ),
    ]
    labels = [
        {"state_hash": "a", "bias": {"bias_gender": 1}},
        {"state_hash": "b", "bias": {"bias_gender": 0}},
    ]

    rows = threshold_sweep(judgments, labels, "bias_gender", [0.8])
    assert rows[0]["flagged"] == 1
    assert rows[0]["missed"] == 0


def test_score_report():
    judgments = [
        judgment(
            "a",
            {"severity": {"kind": "score", "value": 3, "confidence": 0.8}},
        )
    ]
    labels = [
        {"state_hash": "a", "severity": {"severity": 2}},
    ]

    result = score_report(judgments, labels, "severity")
    assert result["exact_agreement"] == 0.0
    assert result["within_one_level"] == 1.0
    assert result["mae"] == 1.0


def test_choice_report():
    judgments = [
        judgment(
            "a",
            {"root_cause": {"kind": "choice", "value": "data"}},
        )
    ]
    labels = [
        {"state_hash": "a", "choice": {"root_cause": "data"}},
    ]

    result = choice_report(judgments, labels, "root_cause")
    assert result["accuracy"] == 1.0


def test_summary_contains_all_layers():
    judgments = [
        judgment(
            "a",
            {
                "bias_gender": {
                    "kind": "noul",
                    "probability": 0.8,
                    "confidence": 0.4,
                },
                "severity": {
                    "kind": "score",
                    "value": 2,
                    "confidence": 0.4,
                },
            },
        )
    ]
    labels = [
        {
            "state_hash": "a",
            "bias": {"bias_gender": 1},
            "severity": {"severity": 2},
            "action_ok": True,
        }
    ]

    result = calibration_summary(
        judgments,
        labels,
        binary_questions=["bias_gender"],
        score_questions=["severity"],
    )

    assert "bias_gender" in result["binary"]
    assert "severity" in result["scores"]
    assert result["action"]["n"] == 1
    assert len(result["low_confidence"]) == 2
