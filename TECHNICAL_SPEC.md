# Technical Specification: BiasGuard

This document outlines the architecture, components, dependencies and data flow for the BiasGuard project.

## System Architecture

- **Data Ingestion & Preprocessing:** Functions to load structured recruiting datasets (CSV/JSON), handle missing values, encode categorical variables and separate sensitive attributes from features.
- **Synthetic Test Generation:** Module to create counterfactual examples by swapping sensitive attributes (e.g. gender, race) while keeping other features constant【590103229441939†L156-L165】.
- **Fairness Metrics Computation:** Library of functions implementing disparate impact ratio, statistical parity difference, equal opportunity difference and calibration metrics【590103229441939†L114-L142】. Each function accepts ground truth labels and model predictions and returns a scalar metric.
- **Mitigation Algorithms:** Implementations of pre-processing re-weighting, resampling, in-processing adversarial debiasing and post-processing threshold adjustment【590103229441939†L156-L165】.
- **Reporting & Visualization:** Scripts and UI components (e.g. using Streamlit) to visualize metric results, compare model versions and highlight high-impact features.
- **Configuration & Data Storage:** Use YAML/JSON config files to specify sensitive attributes, protected groups and thresholds. Store processed datasets and metric outputs in local files.

## Dependencies

- Python ≥ 3.8.
- **Libraries:** 
  - `pandas` and `numpy` for data manipulation.
  - `scikit-learn` for preprocessing utilities.
  - `fairlearn` and/or `aif360` for fairness metrics and mitigation algorithms.
  - `matplotlib` or `plotly` for plotting.
  - `streamlit` or `dash` for interactive dashboard development.
- Optional: `imbalanced-learn` for resampling techniques; `torch` or `tensorflow` if implementing adversarial models.

## Data Flow

1. The user provides a dataset (e.g. CSV) containing features, labels and sensitive attributes.
2. The Data Ingestion module loads and preprocesses the data (imputation, encoding). Sensitive attributes are identified.
3. The Synthetic Test Generation module creates a counterfactual dataset by swapping sensitive attribute values【590103229441939†L156-L165】.
4. A trained hiring model is evaluated on both the original and counterfactual data; predictions are stored.
5. The Fairness Metrics module computes disparate impact ratio, statistical parity difference, equal opportunity difference and other metrics【590103229441939†L114-L142】.
6. If metrics fall outside acceptable thresholds, the Mitigation Algorithms are applied to retrain or adjust the model, producing new predictions.
7. The Reporting module generates tables and plots summarizing metrics before and after mitigation, and optionally exports a report.

## Implementation Notes

- **Modularity:** Each metric and mitigation method should be a separate function/class to enable reuse.
- **Configurability:** Sensitive attributes and target thresholds should be configurable via a YAML file; default values provided.
- **Efficiency:** Use vectorized operations in pandas/NumPy to handle large datasets efficiently. For adversarial debiasing, leverage GPU acceleration if available.
- **Extensibility:** Additional metrics (e.g. equalized odds, predictive parity) can be added by following the same interface.

## Scalability and Deployment

BiasGuard is designed for prototyping on free-tier cloud platforms such as Google Colab or Kaggle. For larger datasets or multiple users, containerize the application using Docker and deploy to a lightweight cloud VM. Use caching for metric computations to reduce recomputation.

        
