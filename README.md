# BiasGuard

**Purpose:** BiasGuard is an open-source toolkit that provides end-to-end bias detection and mitigation for AI-driven hiring systems. It helps developers audit models, identify fairness issues and apply corrections.

**Key Features:**
- **Data Analysis & Synthetic Test Generation:** Load real or synthetic recruiting datasets and generate counterfactual resumes (identical candidate profiles with different demographic attributes) to stress test models【590103229441939†L156-L165】.
- **Fairness Metrics Module:** Compute metrics like Disparate Impact Ratio (80% rule), Statistical Parity Difference and Equal Opportunity Difference【590103229441939†L114-L142】.
- **Mitigation Algorithms:** Apply re-weighting, re-sampling or adversarial debiasing to reduce unfairness【590103229441939†L156-L165】.
- **Interactive Dashboards:** Visualize distribution differences, fairness scores and trade-off curves. Adjust thresholds and see the impact instantly.
- **Regulatory Compliance Templates:** Get documentation templates addressing Equal Employment Opportunity Commission guidelines and emerging AI regulations【590103229441939†L175-L177】.

**Quick Start:**
1. Install the package in editable mode:
   ```sh
   pip install -e .
   ```
2. Run the demo CLI:
   ```sh
   biasguard --demo
   ```
   The CLI will generate a small fairness report and save it under `reports/report.json`.

**License:** This project is released under the MIT License.
