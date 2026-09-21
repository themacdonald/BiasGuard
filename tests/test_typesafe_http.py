from biasguard.typesafe_adapter import normalize_observation
from biasguard.typesafe_http import TypeSafeHTTPClient


def test_noul_native_response_is_normalized():
    obs = normalize_observation(
        "bias_gender",
        "noul",
        {"type": "noul", "noul": 0.91},
    )
    assert obs.probability == 0.91
    assert obs.value == 0.91
    assert obs.confidence is None


def test_score_native_response_is_normalized():
    obs = normalize_observation(
        "severity",
        "score",
        {
            "type": "score",
            "score": 2.68,
            "confidence": 0.81,
            "probabilities": {"0": 0.02, "1": 0.30, "2": 0.68},
        },
    )
    assert obs.value == 2.68
    assert obs.confidence == 0.81


def test_choice_native_response_is_normalized():
    obs = normalize_observation(
        "root_cause",
        "choice",
        {
            "type": "choice",
            "choice": "policy",
            "probabilities": {"policy": 0.8, "model": 0.2},
            "confidence": 0.8,
        },
    )
    assert obs.value == "policy"
    assert obs.confidence == 0.8


def test_question_wire_conversion():
    q = TypeSafeHTTPClient._wire_question({
        "id": "severity",
        "type": "score",
        "prompt": "How severe is this?",
        "levels": ["low", "medium", "high"],
    })
    assert q == {
        "type": "score",
        "instructions": "How severe is this?",
        "criteria": ["low", "medium", "high"],
    }


def test_choice_wire_conversion():
    q = TypeSafeHTTPClient._wire_question({
        "id": "root_cause",
        "type": "choice",
        "prompt": "What caused it?",
        "options": ["data", "model", "policy"],
    })
    assert q["criteria"] == {"data": None, "model": None, "policy": None}
