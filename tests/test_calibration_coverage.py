from biasguard.calibration_coverage import (
    coverage_from_pairing,
    pair_binary_records,
)


def test_pairing_counts_unmatched_and_missing_records():
    judgments = [
        {
            "state_hash": "a",
            "judgments": {"bias_gender": {"probability": 0.8}},
        },
        {
            "state_hash": "b",
            "judgments": {},
        },
        {
            "state_hash": "b",
            "judgments": {},
        },
        {"state_hash": None, "judgments": {}},
    ]
    labels = [
        {"state_hash": "a", "binary": {"bias_gender": 1}},
        {"state_hash": "missing", "binary": {"bias_gender": 0}},
        {"state_hash": "b", "binary": {"other": 1}},
        {"state_hash": None, "binary": {"bias_gender": 1}},
    ]

    result = pair_binary_records(judgments, labels, "bias_gender")
    report = coverage_from_pairing(result, supplied=len(labels))

    assert result.pairs == ((0.8, 1),)
    assert report.supplied == 4
    assert report.valid == 1
    assert report.invalid == 3
    assert report.unmatched == 1
    assert report.missing_answer == 1


def test_invalid_probability_is_counted():
    result = pair_binary_records(
        [
            {
                "state_hash": "a",
                "judgments": {"bias_gender": {"probability": 1.5}},
            }
        ],
        [{"state_hash": "a", "binary": {"bias_gender": 1}}],
        "bias_gender",
    )
    assert result.pairs == ()
    assert result.invalid == 1
