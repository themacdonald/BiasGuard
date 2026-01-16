# BiasGuard

**Goal:** Build a comprehensive toolkit to audit AI‑driven hiring systems, identify sources of bias, and apply mitigation techniques. This framework implements standard fairness metrics such as disparate impact ratio, statistical parity difference, and equal opportunity difference【590103229441939†L114-L142】 and provides practical mitigation algorithms.

## Features

- **Data Analysis & Synthetic Test Generation:** Tools to load real or synthetic recruiting datasets and generate counterfactual resumes—identical candidate profiles with different demographic attributes—to stress test models【590103229441939†L156-L165】.
- **Fairness Metrics Module:** Functions to compute:
  - Disparate Impact (80% rule)【590103229441939†L114-L127】.
  - Statistical Parity Difference【590103229441939†L128-L139】.
  - Equal Opportunity Difference【590103229441939†L140-L142】.
  - Predictive Parity and Calibration Error.
  - Additional 2026 metrics like intersectional fairness.
- **Mitigation Algorithms:** Implement pre‑processing techniques (re‑weighting, resampling), in‑processing (adversarial debiasing) and post‑processing (threshold adjustment), plus interpretability tools (SHAP/LIME) to highlight features influencing predictions【590103229441939†L156-L160】.
- **Interactive Dashboards:** Streamlit dashboards to visualize distribution differences, fairness scores, and trade‑off curves; adjust decision thresholds interactively and see the impact.
- **Regulatory Compliance Templates:** Example templates covering emerging AI governance requirements, such as EEOC assessments and EU AI Act guidelines【590103229441939†L175-L177】.

## Quick Start

BiasGuard is designed for research and experimentation on free cloud GPUs (Google Colab, Kaggle). To get started:

1. Clone the repository in a notebook and install dependencies:
   ```bash
   git clone https://github.com/themacdonald/BiasGuard.git
   cd BiasGuard
   pip install -r requirements.txt
   ```
2. Load your recruiting dataset (or the provided synthetic demo) and run the `analysis_notebook.ipynb` to compute fairness metrics.
3. Use the `mitigation` module to apply algorithms like re‑weighting or adversarial debiasing.
4. Launch the Streamlit dashboard (`streamlit run dashboard.py`) to explore fairness scores and threshold adjustments.
5. Review the regulatory templates and adapt them for your organization’s compliance reporting.

## Implementation Plan

This project is scoped as a two‑week sprint (~30 hours):

- **Week 1:** Develop dataset loaders and implement fairness metrics; produce baseline fairness reports.
- **Week 2:** Add mitigation algorithms and interactive dashboards; prepare example notebooks and documentation.

## Contributing

We welcome contributions! Please open issues for bugs or improvements and submit pull requests for new features or metrics. See `CONTRIBUTING.md` for guidelines.

## License

This project is licensed under the MIT License (see `LICENSE` for details).
