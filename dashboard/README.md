# BiasGuard Governance Dashboard

Prototype Streamlit console for the BiasGuard evaluation/governance loop.

## Run

From the repository root:

```bash
pip install -r dashboard/requirements.txt
streamlit run dashboard/app.py
```

## Current capabilities

- judgment overview
- policy action
- priority and severity
- typed evaluator evidence
- confidence display
- model and policy version
- state hash
- human adjudication form
- governance trail

## Deliberate boundary

This is a prototype UI. Reviewer decisions are not persisted yet.

The next persistence milestone should store:

- state hash
- case/version ID
- evaluator/model
- policy version
- original judgments
- policy action
- reviewer identity
- adjudication outcome
- rationale
- evidence references
- timestamp
- subsequent re-evaluation result

The dashboard should never silently overwrite the original evaluator judgment.
