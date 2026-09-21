# Fairness Audit Foundation

BiasGuard's deterministic audit layer is deliberately independent of structured
AI evaluation.

## CLI

```bash
biasguard audit dataset.csv \
  --y-true outcome \
  --y-pred prediction \
  --group gender \
  --protected female \
  --reference male \
  --output reports/audit.json \
  --markdown reports/audit.md
```

Missing values are rejected by default. Use `--allow-missing` only when excluding
incomplete rows is an intentional part of the audit.

## Guarantees

The foundation layer:

- validates required CSV columns
- validates binary outcome/prediction values
- requires both comparison groups
- rejects empty audit samples
- does not silently turn undefined metrics into zero
- reports excluded rows
- calculates DIR directly from exact selection rates
- keeps deterministic metrics independent from evaluator/model judgments

Undefined metrics are represented as `null` in JSON.

## Deliberate boundary

This command answers:

> What happened in the observed dataset?

It does not answer:

> Why did it happen?

That question belongs to the later evaluation/investigation layers.
