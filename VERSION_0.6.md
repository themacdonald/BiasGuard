# BiasGuard v0.6

v0.6 combines the v0.5 governance protocol with the deterministic fairness-audit foundation.

## What changed

### Preserved from v0.5
- GovernanceCase and evidence model
- Evidence fingerprints and state hashing
- Counterfactual sensitivity experiments
- Governance recommendations separated from institutional authority
- Human adjudication artifacts
- Remediation and re-evaluation artifacts
- Append-only governance ledger prototype
- Governance dashboard prototype
- Structured evaluation and calibration modules

### Added in v0.6
- CSV audit data loader
- Required-column and binary-label validation
- Explicit protected/reference group split
- Correct DIR calculation without integer truncation
- Explicit `null` semantics for undefined DIR/EOD
- Deterministic `biasguard audit` command
- JSON and optional Markdown audit reports
- Adversarial/edge-case tests for the measurement layer

## Boundary

The audit layer answers what happened in the observed data. It does not infer why it happened and does not delegate fairness measurement to an LLM. Later layers can use audit evidence for structured evaluation and governance.
