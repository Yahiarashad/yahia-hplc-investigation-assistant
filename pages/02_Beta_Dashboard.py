from pathlib import Path
import sys

import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from beta_feedback import dashboard_snapshot, rows_to_csv

st.set_page_config(page_title="Founding Beta Dashboard", page_icon="📊", layout="wide")

try:
    expected_pin = str(st.secrets.get("BETA_DASHBOARD_PIN", "")).strip()
except Exception:
    expected_pin = ""

st.title("📊 Founding Beta Dashboard")
st.caption("Anonymous usage signals + optional user feedback. No HPLC case text is stored here.")

if not expected_pin:
    st.warning("Dashboard is locked until BETA_DASHBOARD_PIN is added to Streamlit Secrets.")
    st.code('BETA_DASHBOARD_PIN = "choose-a-private-pin"', language="toml")
    st.stop()

pin = st.text_input("Dashboard PIN", type="password")
if pin != expected_pin:
    if pin:
        st.error("Incorrect PIN.")
    st.stop()

events, feedback = dashboard_snapshot()

unique_sessions = len({r["session_id"] for r in events})
assessment_starts = sum(1 for r in events if r["event"] == "assessment_started")
assessment_completions = sum(1 for r in events if r["event"] == "assessment_completed")
investigation_starts = sum(1 for r in events if r["event"] == "investigation_started")
feedback_count = len(feedback)
ratings = [int(r["rating"]) for r in feedback if r.get("rating")]
avg_rating = (sum(ratings) / len(ratings)) if ratings else 0

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Unique sessions", unique_sessions)
c2.metric("Assessment starts", assessment_starts)
c3.metric("Assessment completions", assessment_completions)
c4.metric("Investigation starts", investigation_starts)
c5.metric("Avg feedback", f"{avg_rating:.1f}/5" if ratings else "—")

if assessment_starts:
    completion_rate = assessment_completions / assessment_starts * 100
    st.metric("Assessment completion rate", f"{completion_rate:.1f}%")

st.subheader("Feedback")
if feedback:
    safe_feedback = []
    for row in feedback:
        item = dict(row)
        item["consent_research"] = "Yes" if item.get("consent_research") else "No"
        safe_feedback.append(item)
    st.dataframe(safe_feedback, use_container_width=True, hide_index=True)
    st.download_button(
        "Download feedback CSV",
        data=rows_to_csv(feedback),
        file_name="founding_beta_feedback.csv",
        mime="text/csv",
        use_container_width=True,
    )
else:
    st.info("No feedback submitted yet.")

st.subheader("Event log")
if events:
    st.dataframe(events[:500], use_container_width=True, hide_index=True)
    st.download_button(
        "Download events CSV",
        data=rows_to_csv(events),
        file_name="founding_beta_events.csv",
        mime="text/csv",
        use_container_width=True,
    )
else:
    st.info("No beta events recorded yet.")

st.warning(
    "Current beta storage is local to the running Streamlit instance. Export regularly. "
    "For durable launch analytics, connect BETA_FEEDBACK_WEBHOOK to Google Sheets, Make, Zapier, or a database endpoint."
)
