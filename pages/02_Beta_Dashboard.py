import json
from pathlib import Path
import sys

import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from beta_feedback import (
    dashboard_snapshot,
    external_storage_configured,
    rows_to_csv,
    test_external_storage,
)

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

st.subheader("Durable storage")
if external_storage_configured():
    st.success("External beta mirror is configured. Local storage remains as a temporary fallback.")
    if st.button("Test Google Sheets / webhook connection", use_container_width=True):
        with st.spinner("Testing durable storage..."):
            if test_external_storage():
                st.success("Connection verified. A harmless storage_test event was accepted by the external store.")
            else:
                st.error(
                    "The external URL is configured, but the test was not accepted. "
                    "Check the Apps Script deployment URL and BETA_FEEDBACK_WEBHOOK_TOKEN."
                )
else:
    st.warning("Durable Google Sheets mirroring is not configured yet. Local Streamlit storage can reset after redeploy/restart.")
    st.code(
        'BETA_FEEDBACK_WEBHOOK = "https://script.google.com/macros/s/.../exec"\n'
        'BETA_FEEDBACK_WEBHOOK_TOKEN = "same-private-token-as-apps-script"',
        language="toml",
    )
    st.caption("Repository guide: GOOGLE_SHEETS_SETUP.md")

st.divider()

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


def _metadata(row):
    try:
        value = json.loads(row.get("metadata_json") or "{}")
        return value if isinstance(value, dict) else {}
    except Exception:
        return {}


def _campaign_breakdown(rows):
    buckets = {}
    tracked_sessions = set()
    linkedin_sessions = set()

    for row in rows:
        meta = _metadata(row)
        source = str(meta.get("utm_source") or "").strip()
        if not source:
            continue

        medium = str(meta.get("utm_medium") or "").strip() or "—"
        campaign = str(meta.get("utm_campaign") or "").strip() or "—"
        key = (source, medium, campaign)
        session_id = str(row.get("session_id") or "")
        event = str(row.get("event") or "")

        tracked_sessions.add(session_id)
        if source.lower() == "linkedin":
            linkedin_sessions.add(session_id)

        if key not in buckets:
            buckets[key] = {
                "Source": source,
                "Medium": medium,
                "Campaign": campaign,
                "Sessions": set(),
                "Assessment starts": set(),
                "Assessment completions": set(),
                "Investigation starts": set(),
                "Feedback submissions": set(),
            }

        bucket = buckets[key]
        bucket["Sessions"].add(session_id)
        if event == "assessment_started":
            bucket["Assessment starts"].add(session_id)
        elif event == "assessment_completed":
            bucket["Assessment completions"].add(session_id)
        elif event == "investigation_started":
            bucket["Investigation starts"].add(session_id)
        elif event == "feedback_submitted":
            bucket["Feedback submissions"].add(session_id)

    table = []
    for bucket in buckets.values():
        table.append(
            {
                "Source": bucket["Source"],
                "Medium": bucket["Medium"],
                "Campaign": bucket["Campaign"],
                "Sessions": len(bucket["Sessions"]),
                "Assessment starts": len(bucket["Assessment starts"]),
                "Assessment completions": len(bucket["Assessment completions"]),
                "Investigation starts": len(bucket["Investigation starts"]),
                "Feedback submissions": len(bucket["Feedback submissions"]),
            }
        )

    table.sort(key=lambda x: (-x["Sessions"], x["Source"], x["Campaign"]))
    return table, len(tracked_sessions), len(linkedin_sessions)


campaign_rows, tracked_campaign_sessions, linkedin_sessions = _campaign_breakdown(events)

st.subheader("Campaign attribution")
a1, a2 = st.columns(2)
a1.metric("Tracked campaign sessions", tracked_campaign_sessions)
a2.metric("LinkedIn sessions", linkedin_sessions)

if campaign_rows:
    st.dataframe(campaign_rows, use_container_width=True, hide_index=True)
    st.caption(
        "First-touch attribution is preserved for the Streamlit session and mirrored inside metadata_json in the durable Google Sheets event log. "
        "No LinkedIn identity, IP address, browser fingerprint, or HPLC case text is collected."
    )
else:
    st.info("No UTM-tagged visits have been recorded on this running instance yet.")

st.caption("LinkedIn launch tracking link")
st.code(
    "https://yahiaqc.streamlit.app/?utm_source=linkedin&utm_medium=organic_social&utm_campaign=founding_beta_launch&utm_content=launch_post",
    language=None,
)

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

if external_storage_configured():
    st.info(
        "Durable mirroring is enabled. Keep the webhook token private. "
        "The analytics mirror does not include HPLC case text."
    )
else:
    st.warning(
        "Current beta storage is local to the running Streamlit instance. Export regularly until the Google Sheets mirror is connected."
    )
