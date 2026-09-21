# BiasGuard Calibration v2

This milestone adds offline calibration for stored BiasGuard judgments.

## Design rule

Calibration is evidence about evaluator reliability. It does **not** automatically select policy thresholds.

```text
stored judgments
       +
human labels
       ↓
calibration
       ↓
threshold analysis
       ↓
policy owner chooses operating point
```

## What changed

### Binary / Noul

Calibration is performed **per question** and therefore per protected group where questions are group-specific.

It supports:

- Brier score
- Expected Calibration Error
- Reliability bins
- Precision
- Recall
- False-positive rate
- False-negative rate
- Threshold sweeps

### Score

Ordered evaluations support:

- Exact agreement
- Within-one-level agreement
- Mean Absolute Error
- Average confidence
- Low-confidence rate

### Choice

Categorical evaluations support:

- Overall accuracy
- Per-class accuracy

### Action

`action_ok` is evaluated separately from judgment correctness. This prevents a correct judgment from being confused with a correct operational decision.

### Confidence

Low-confidence findings preserve the question type instead of treating Noul, Score, and Choice confidence as interchangeable.

## Label format

Example:

```json
{
  "state_hash": "abc123",
  "bias": {
    "bias_gender": 1,
    "bias_race": 0
  },
  "severity": {
    "severity": 2
  },
  "action_ok": true
}
```

Judgments are expected to contain the matching `state_hash` and typed answers.

## Example

```python
from biasguard.calibration import calibration_summary, load_jsonl

judgments = load_jsonl("judgments.jsonl")
labels = load_jsonl("labels.jsonl")

summary = calibration_summary(
    judgments,
    labels,
    binary_questions=["bias_gender", "bias_race"],
    score_questions=["severity", "harm"],
    choice_questions=["root_cause"],
)
```
