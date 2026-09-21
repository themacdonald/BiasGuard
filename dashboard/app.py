from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import streamlit as st


st.set_page_config(
    page_title="BiasGuard Governance",
    page_icon="🛡️",
    layout="wide",
)

st.title("BiasGuard Governance Console")
st.caption("Evaluation → Calibration → Human Adjudication → Governance")

DEFAULT_JUDGMENT = {
    "state_hash": "demo-7f3b",
    "model": "jev-latest",
    "policy_version": "policy-v1",
    "judgments": {
        "bias_gender": {"kind": "noul", "probability": 0.91, "confidence": 0.93},
        "bias_race": {"kind": "noul", "probability": 0.12, "confidence": 0.88},
        "severity": {"kind": "score", "value": 3, "confidence": 0.91},
        "harm": {"kind": "score", "value": 3, "confidence": 0.88},
        "review_track": {"kind": "choice", "value": "human_review", "confidence": 0.80},
        "root_cause": {"kind": "choice", "value": "policy", "confidence": 0.74},
        "proxy_influence": {"kind": "noul", "probability": 0.72, "confidence": 0.70},
    },
    "result": {
        "action": "human_review",
        "reason": "evaluation reached the configured human-review threshold",
        "priority": 0.71,
        "top_bias_probability": 0.91,
        "severity": 3,
        "severity_confidence": 0.91,
        "human_review": True,
    },
}


def load_record(uploaded) -> dict[str, Any]:
    if uploaded is None:
        return DEFAULT_JUDGMENT
    return json.loads(uploaded.getvalue().decode("utf-8"))


uploaded = st.sidebar.file_uploader(
    "Load judgment JSON",
    type=["json"],
)
record = load_record(uploaded)

result = record.get("result", {})
judgments = record.get("judgments", {})

action = result.get("action", "unknown")
action_label = {
    "pass": "PASS",
    "log_only": "LOG ONLY",
    "human_review": "HUMAN REVIEW",
    "block": "BLOCK",
}.get(action, action.upper())

c1, c2, c3, c4 = st.columns(4)
c1.metric("Policy Action", action_label)
c2.metric("Priority", f'{float(result.get("priority", 0)):.2f}')
c3.metric("Top Bias Probability", f'{float(result.get("top_bias_probability", 0)):.0%}')
c4.metric("Severity", result.get("severity", "—"))

st.divider()

left, right = st.columns([1.25, 1])

with left:
    st.subheader("Evaluation Evidence")

    rows = []
    for question_id, answer in judgments.items():
        probability = answer.get("probability")
        value = answer.get("value")
        confidence = answer.get("confidence")
        rows.append({
            "Question": question_id,
            "Type": answer.get("kind", "unknown"),
            "Value": (
                f"{float(probability):.0%}" if probability is not None
                else value
            ),
            "Confidence": (
                f"{float(confidence):.0%}" if confidence is not None else "—"
            ),
        })

    st.dataframe(rows, use_container_width=True, hide_index=True)

with right:
    st.subheader("Policy Decision")
    st.info(result.get("reason", "No reason recorded."))

    st.write("**Model**", record.get("model", "unknown"))
    st.write("**Policy version**", record.get("policy_version", "unknown"))
    st.write("**State hash**")
    st.code(record.get("state_hash", "unknown"))

st.divider()

st.subheader("Human Adjudication")

if action in {"human_review", "block"}:
    st.warning("This case requires human adjudication before final governance action.")

    decision = st.radio(
        "Adjudicator outcome",
        [
            "Confirm evaluator finding",
            "Reject evaluator finding",
            "Modify severity",
            "Request second review",
        ],
        horizontal=True,
    )

    notes = st.text_area(
        "Adjudication rationale",
        placeholder="Record the evidence and reasoning supporting the adjudication.",
    )

    col_a, col_b = st.columns(2)
    with col_a:
        reviewer = st.text_input("Reviewer ID")
    with col_b:
        reference = st.text_input("Evidence/reference")

    if st.button("Record adjudication", type="primary"):
        if not reviewer or not notes:
            st.error("Reviewer ID and rationale are required.")
        else:
            st.success(
                "Adjudication captured in the session. "
                "Persistence should be connected to the audit store before production use."
            )
            st.json({
                "state_hash": record.get("state_hash"),
                "reviewer": reviewer,
                "outcome": decision,
                "rationale": notes,
                "evidence_reference": reference,
            })
else:
    st.success("No human adjudication is currently required for this case.")

st.divider()

st.subheader("Governance Trail")
st.markdown(
    """
    **Evidence** → typed evaluator judgments → **policy composition** → action → **human adjudication when required** → re-evaluation → audit record
    """
)

st.caption(
    "This prototype intentionally does not persist reviewer decisions. "
    "Production persistence should use an append-only audit store with reviewer identity, "
    "timestamps, evidence references, and immutable case/version identifiers."
)
