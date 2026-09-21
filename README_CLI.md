# BiasGuard CLI v0.2

This milestone connects the structured evaluation layer and calibration layer to a usable command-line workflow.

## Commands

```bash
biasguard demo
biasguard evaluate --input case.json --answers answers.json --append judgments.jsonl
biasguard calibrate --judgments judgments.jsonl --labels labels.jsonl
```

## Important implementation boundary

`evaluate` currently uses `OfflineAnswersClient` so the pipeline can be tested end-to-end without inventing or hard-coding a TypeSafe SDK.

The production adapter should replace `OfflineAnswersClient` with the actual structured evaluator client while preserving the `TypeSafeClient.evaluate(state, questions)` contract.

The evaluator remains an evidence layer. BiasGuard owns deterministic policy composition, thresholds, routing, state hashing, and audit records.

## Example case

```json
{
  "decision": {"candidate_id": "A17", "selected": false},
  "protected_groups": ["gender", "race"],
  "biasguard_flags": {"disparate_impact": true},
  "context": {"role": "analyst"}
}
```

## Example answers

```json
{
  "answers": {
    "bias_gender": {"probability": 0.91, "confidence": 0.93},
    "bias_race": {"probability": 0.08, "confidence": 0.94},
    "severity": {"value": 3, "confidence": 0.91},
    "harm": {"value": 3, "confidence": 0.88},
    "proxy_influence": {"probability": 0.72, "confidence": 0.70},
    "review_track": {"value": "block", "confidence": 0.80},
    "root_cause": {"value": "policy", "confidence": 0.74},
    "protected_reference": {"probability": 0.81, "confidence": 0.83},
    "verify_disparate_impact": {"probability": 0.90, "confidence": 0.90}
  }
}
```

## Why this is deliberately offline

The current repository does not declare a mandatory structured-evaluator SDK dependency. This milestone therefore proves the contract and audit pipeline without pretending an external SDK is already integrated.

Once the actual evaluator client is selected and configured, only the adapter boundary should need to change.
