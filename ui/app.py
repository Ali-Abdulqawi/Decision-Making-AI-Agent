import json
import os
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

# ✅ Make imports work on Streamlit Cloud (project root in PYTHONPATH)
ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT_DIR))

from app.agent import mock_decision
from app.models import OpportunityInput
from app.memory import append_memory, build_record

MEMORY_PATH = os.getenv("MEMORY_PATH", "memory/decisions.jsonl")


def load_memory_as_dataframe(path: str) -> pd.DataFrame:
    rows = []
    if not os.path.exists(path):
        return pd.DataFrame()

    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
                opp = rec.get("opportunity", {}) or {}

                # IMPORTANT:
                # Your memory currently stores decision under "result" (from your screenshot)
                # but we also support "decision" just in case.
                dec = rec.get("result") or rec.get("decision") or {}

                rows.append({
                    "timestamp": rec.get("timestamp", ""),
                    "opportunity_title": opp.get("opportunity_title", ""),
                    "client_type": opp.get("client_type", ""),
                    "client_level": opp.get("client_level", ""),
                    "expected_time_days": opp.get("expected_time_days", ""),
                    "cost_to_fulfill": opp.get("cost_to_fulfill", ""),
                    "expected_earnings": opp.get("expected_earnings", ""),
                    "decision": dec.get("decision", ""),
                    "confidence": dec.get("confidence", ""),
                    "total_score": (dec.get("score", {}) or {}).get("total_score", ""),
                    "summary": dec.get("summary", ""),
                })
            except Exception:
                continue

    return pd.DataFrame(rows)


st.set_page_config(
    page_title="Decision-Making AI Agent",
    page_icon="🧠",
    layout="wide",
)

st.title("🧠 Decision-Making AI Agent")
st.caption("Streamlit-only (no FastAPI). Evaluates opportunities + stores memory + CSV export.")


def decision_badge(decision: str) -> str:
    d = (decision or "").upper()
    if d == "ACCEPT":
        return "✅ **ACCEPT**"
    if d == "REJECT":
        return "❌ **REJECT**"
    return "🟡 **NEEDS_INFO**"


def decision_color(decision: str) -> str:
    d = (decision or "").upper()
    if d == "ACCEPT":
        return "#16a34a"
    if d == "REJECT":
        return "#dc2626"
    return "#f59e0b"


left, right = st.columns([1.05, 0.95], gap="large")

with left:
    st.subheader("Opportunity input")

    with st.form("decision_form", clear_on_submit=False):
        opportunity_title = st.text_input("Opportunity Title", placeholder="e.g., Website + SEO for a clinic")
        client_type = st.text_input("Client Type", placeholder="e.g., New client / Returning client / Enterprise")
        description = st.text_area("Description", height=120, placeholder="Write the details of the opportunity...")

        c1, c2, c3 = st.columns(3)
        with c1:
            expected_time_days = st.number_input("Expected time (days)", min_value=1, value=14, step=1)
        with c2:
            cost_to_fulfill = st.number_input("Cost to fulfill", min_value=0.0, value=600.0, step=50.0)
        with c3:
            expected_earnings = st.number_input("Expected earnings", min_value=0.0, value=900.0, step=50.0)

        expected_benefits = st.text_area("Expected benefits", height=80, placeholder="e.g., Retainer, referrals, portfolio value")
        can_close = st.checkbox("Can I close the deal within the timeframe?", value=True)
        risks = st.text_area("Risks & concerns", height=90, placeholder="e.g., unclear requirements, scope creep...")

        c4, c5 = st.columns(2)
        with c4:
            excitement = st.slider("Excitement level", 0, 10, 5)
        with c5:
            client_level = st.selectbox("Client level", ["low", "normal", "high", "sensitive"], index=2)

        submitted = st.form_submit_button("Evaluate ✅", use_container_width=True)

with right:
    st.subheader("Decision output")

    if "last_result" not in st.session_state:
        st.session_state.last_result = None

    if submitted:
        try:
            # ✅ Build Pydantic input (same schema as FastAPI)
            opp = OpportunityInput(
                opportunity_title=opportunity_title,
                client_type=client_type,
                description=description,
                expected_time_days=expected_time_days,
                cost_to_fulfill=cost_to_fulfill,
                expected_earnings=expected_earnings,
                expected_benefits=expected_benefits,
                can_close_within_timeframe=can_close,
                risks_and_concerns=risks,
                excitement_level=excitement,
                client_level=client_level,
            )

            # ✅ Decision locally (no API call)
            decision_output = mock_decision(opp)

            # ✅ Save to memory JSONL
            append_memory(build_record(opp, decision_output))

            # ✅ Show result
            st.session_state.last_result = decision_output.model_dump()

        except Exception as e:
            st.error(f"Evaluation failed:\n\n{e}")

    data = st.session_state.last_result

    if not data:
        st.info("Submit an opportunity on the left to see the decision here.")
    else:
        decision = data.get("decision", "NEEDS_INFO")
        confidence = int(data.get("confidence", 0))
        score = data.get("score", {}) or {}
        total_score = int(score.get("total_score", 0))

        st.markdown(
            f"""
            <div style="
                border: 1px solid rgba(255,255,255,0.12);
                border-radius: 16px;
                padding: 16px 18px;
                background: rgba(255,255,255,0.04);
            ">
                <div style="font-size: 18px; margin-bottom: 6px;">
                    {decision_badge(decision)}
                </div>
                <div style="color: rgba(255,255,255,0.75);">
                    Confidence: <b>{confidence}%</b> · Total Score: <b>{total_score}/100</b>
                </div>
                <div style="margin-top: 10px;">
                    <div style="height: 10px; background: rgba(255,255,255,0.12); border-radius: 999px;">
                        <div style="height: 10px; width: {min(max(total_score,0),100)}%;
                            background: {decision_color(decision)}; border-radius: 999px;">
                        </div>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.write("")
        st.write("**Summary**")
        st.write(data.get("summary", ""))

        with st.expander("✅ Key reasons", expanded=True):
            for r in data.get("key_reasons", []) or []:
                st.write(f"- {r}")

        with st.expander("⚠️ Risks", expanded=False):
            risks_list = data.get("risks", []) or []
            if not risks_list:
                st.write("No major risks detected.")
            else:
                for r in risks_list:
                    st.write(f"- {r}")

        with st.expander("🧭 Next actions", expanded=(decision == "NEEDS_INFO")):
            actions = data.get("next_actions", []) or []
            if not actions:
                st.write("No actions suggested.")
            else:
                for a in actions:
                    st.write(f"- {a}")

        with st.expander("📊 Score breakdown", expanded=False):
            c1, c2 = st.columns(2)
            with c1:
                st.metric("ROI", f"{score.get('roi', 0)}")
                st.metric("ROI score", score.get("roi_score", 0))
                st.metric("Feasibility score", score.get("feasibility_score", 0))
            with c2:
                st.metric("Risk score", score.get("risk_score", 0))
                st.metric("Motivation score", score.get("motivation_score", 0))
                st.metric("Total score", score.get("total_score", 0))

            st.caption("Raw score object")
            st.json(score)

st.divider()
st.subheader("📤 Export")

df = load_memory_as_dataframe(MEMORY_PATH)

if df.empty:
    st.info("No saved decisions yet. Run a few evaluations first, then export.")
else:
    csv_bytes = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="Download decisions as CSV",
        data=csv_bytes,
        file_name="decisions_export.csv",
        mime="text/csv",
        use_container_width=True,
    )
    st.caption(f"Exported rows: {len(df)}")

st.caption("Note: Streamlit Cloud storage is not permanent. Use DB/Google Sheets later if you want persistence.")
