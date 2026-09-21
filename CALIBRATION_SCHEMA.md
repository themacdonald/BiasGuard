# BiasGuard Calibration Data Contract

Calibration separates evaluator evidence from policy choice.

## Judgment JSONL

Each line is an audit record emitted by `biasguard evaluate --append`.

The important fields are:

- `state_hash`: stable identifier for the evaluated case state.
- `model`: evaluator/model identifier.
- `policy_version`: policy version used for routing.
- `judgments`: typed observations keyed by question ID.
- `result.action`: the policy action selected.

## Label JSONL

Each line is an adjudicated reference label:

```json
{
  "state_hash": "…",
  "binary": {
    "bias_gender": 1
  },
  "score": {
    "severity": 3
  },
  "choice": {
    "review_track": "block"
  },
  "expected_action": "block"
}
```

`expected_action` is intentionally a string. It is compared to the recorded action; it is not treated as a boolean.

## Interpretation

Calibration reports:

- binary probability quality: Brier score, ECE, reliability bins
- operating-point analysis: threshold sweep
- Score agreement: exact agreement, within-one-level agreement, MAE
- Choice accuracy: overall and per-class
- policy action accuracy: expected action vs actual action
- low-confidence findings, retaining question type

The calibration report is evidence for policy owners. It does not automatically select production thresholds.
