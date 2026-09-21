# BiasGuard CLI v0.2

This milestone connects BiasGuard's structured evaluation layer and calibration layer to a usable command-line workflow.

## Offline evaluation

```bash
biasguard evaluate \
  --input case.json \
  --answers answers.json \
  --model jev-latest \
  --output reports/judgment.json \
  --append judgments.jsonl
```

The offline mode is deterministic and useful for tests and fixtures.

## Live TypeSafe System One evaluation

Set the API key:

```bash
export TYPESAFE_API_KEY="..."
```

Then:

```bash
biasguard evaluate \
  --input case.json \
  --model jev-latest \
  --output reports/judgment.json \
  --append judgments.jsonl
```

When `--answers` is omitted, BiasGuard sends the state and typed questions to:

```text
POST https://api.typesafe.ai/v1/systemone
```

The adapter maps BiasGuard's internal question representation to the documented System One wire format and normalizes the native response fields:

- Noul → `noul`
- Score → `score`
- Choice → `choice`
- Choice/Score → `confidence`
- Choice/Score → `probabilities`

Noul does not provide a separate confidence field; its probability is the answer signal.

## Calibration

```bash
biasguard calibrate \
  --judgments judgments.jsonl \
  --labels labels.jsonl \
  --output reports/calibration.json
```

## Architecture boundary

```text
TypeSafe / Jev
      │
      │ typed judgments
      ▼
BiasGuard adapter
      │
      ▼
BiasGuard deterministic policy
      │
      ├── pass
      ├── log_only
      ├── human_review
      └── block
      │
      ▼
Audit record + calibration
```

The evaluator supplies structured evidence. BiasGuard owns governance and policy composition.
