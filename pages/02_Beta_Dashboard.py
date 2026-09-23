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
st.caption(
    "Anonymous product analytics + optional feedback. Test traffic is excluded from live funnel metrics. "
    "IP addresses and browser fingerprints are not stored. Investigation text is stored only after the in-app privacy notice for founding-beta review."
)

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

events, feedback, investigation_messages = dashboard_snapshot(include_messages=True)


def _metadata(row):
    try:
        value = json.loads(row.get("metadata_json") or "{}")
        return value if isinstance(value, dict) else {}
    except Exception:
        return {}


def _visitor_key(row):
    meta = _metadata(row)
    return str(meta.get("visitor_id") or row.get("session_id") or "")


def _row_is_test(row):
    meta = _metadata(row)
    traffic_type = str(meta.get("traffic_type") or "").strip().lower()
    utm_content = str(meta.get("utm_content") or "").strip().lower()
    source = str(row.get("source") or "").strip().lower()
    if traffic_type == "test" or source == "beta_dashboard":
        return True
    return (
        "feedback_retest" in utm_content
        or utm_content.startswith("test_")
        or utm_content.startswith("internal_")
    )


def _session_status(rows):
    status = {}
    for row in rows:
        session_id = str(row.get("session_id") or "")
        meta = _metadata(row)
        current = status.get(session_id, "legacy")
        if _row_is_test(row):
            status[session_id] = "test"
        elif str(meta.get("traffic_type") or "").lower() == "live" and current != "test":
            status[session_id] = "live"
        elif session_id not in status:
            status[session_id] = "legacy"
    return status


session_status = _session_status(events)
test_session_ids = {sid for sid, status in session_status.items() if status == "test"}
live_events = [
    row for row in events
    if str(row.get("session_id") or "") not in test_session_ids
    and str(row.get("source") or "") != "beta_dashboard"
]
live_feedback = [row for row in feedback if str(row.get("session_id") or "") not in test_session_ids]

unique_visitors = {_visitor_key(r) for r in live_events if _visitor_key(r)}
assessment_viewers = {_visitor_key(r) for r in live_events if r.get("event") == "assessment_viewed"}
assessment_starters = {_visitor_key(r) for r in live_events if r.get("event") == "assessment_started"}
assessment_completers = {_visitor_key(r) for r in live_events if r.get("event") == "assessment_completed"}
assistant_viewers = {_visitor_key(r) for r in live_events if r.get("event") == "assistant_viewed"}
investigation_starters = {_visitor_key(r) for r in live_events if r.get("event") == "investigation_started"}
feedback_submitters = {_visitor_key(r) for r in live_events if r.get("event") == "feedback_submitted"}
ratings = [int(r["rating"]) for r in live_feedback if r.get("rating")]
avg_rating = (sum(ratings) / len(ratings)) if ratings else 0

st.subheader("Live product snapshot")
c1, c2, c3, c4, c5, c6 = st.columns(6)
c1.metric("Anonymous visitors", len(unique_visitors))
c2.metric("Assessment viewers", len(assessment_viewers))
c3.metric("Assessment starts", len(assessment_starters))
c4.metric("Assessment completions", len(assessment_completers))
c5.metric("Investigation starts", len(investigation_starters))
c6.metric("Avg feedback", f"{avg_rating:.1f}/5" if ratings else "—")

if assessment_starters:
    completion_rate = len(assessment_completers) / len(assessment_starters) * 100
    st.metric("Assessment start → completion", f"{completion_rate:.1f}%")

known_test_visitors = {_visitor_key(r) for r in events if _row_is_test(r) and _visitor_key(r)}
st.caption(
    f"Known test traffic excluded: {len(known_test_visitors)} anonymous visitor(s). "
    "Older events created before unified visitor tracking may fall back to their product session ID."
)


def _count_visitors_for_event(event_name, predicate=None):
    found = set()
    for row in live_events:
        if row.get("event") != event_name:
            continue
        meta = _metadata(row)
        if predicate is not None and not predicate(meta):
            continue
        key = _visitor_key(row)
        if key:
            found.add(key)
    return len(found)


st.subheader("Decision Gap funnel")
assessment_funnel = [
    {"Step": "Viewed assessment", "Visitors": len(assessment_viewers)},
    {"Step": "Started assessment", "Visitors": len(assessment_starters)},
]
for checkpoint in (5, 10, 15, 20, 25, 30):
    assessment_funnel.append(
        {
            "Step": f"Reached Q{checkpoint}",
            "Visitors": _count_visitors_for_event(
                "assessment_progress",
                lambda m, checkpoint=checkpoint: int(m.get("questions_checkpoint") or 0) >= checkpoint,
            ),
        }
    )
assessment_funnel.extend(
    [
        {"Step": "Completed assessment", "Visitors": len(assessment_completers)},
        {
            "Step": "Submitted assessment feedback",
            "Visitors": _count_visitors_for_event(
                "feedback_submitted",
                lambda m: True,
            ),
        },
    ]
)
st.dataframe(assessment_funnel, use_container_width=True, hide_index=True)
st.caption("Progress checkpoints store only stage/question counts — never the user's selected answers.")

st.subheader("HPLC Assistant funnel")
assistant_turn_1 = _count_visitors_for_event(
    "assistant_turn_completed", lambda m: int(m.get("assistant_turn") or 0) >= 1
)
assistant_turn_2 = _count_visitors_for_event(
    "assistant_turn_completed", lambda m: int(m.get("assistant_turn") or 0) >= 2
)
conclusion_visitors = _count_visitors_for_event(
    "feedback_prompted", lambda m: str(m.get("trigger") or "") == "investigation_conclusion"
)
hplc_feedback_submitters = set()
for row in live_events:
    if row.get("source") == "hplc_assistant" and row.get("event") == "feedback_submitted":
        key = _visitor_key(row)
        if key:
            hplc_feedback_submitters.add(key)

hplc_funnel = [
    {"Step": "Viewed assistant", "Visitors": len(assistant_viewers)},
    {"Step": "Started investigation", "Visitors": len(investigation_starters)},
    {"Step": "Received ≥1 assistant turn", "Visitors": assistant_turn_1},
    {"Step": "Received ≥2 assistant turns", "Visitors": assistant_turn_2},
    {"Step": "Reached investigation conclusion", "Visitors": conclusion_visitors},
    {"Step": "Submitted HPLC feedback", "Visitors": len(hplc_feedback_submitters)},
]
st.dataframe(hplc_funnel, use_container_width=True, hide_index=True)


def _campaign_breakdown(rows):
    buckets = {}
    tracked_visitors = set()
    linkedin_visitors = set()

    for row in rows:
        meta = _metadata(row)
        source = str(meta.get("utm_source") or "").strip()
        if not source:
            continue

        medium = str(meta.get("utm_medium") or "").strip() or "—"
        campaign = str(meta.get("utm_campaign") or "").strip() or "—"
        content = str(meta.get("utm_content") or "").strip() or "—"
        key = (source, medium, campaign, content)
        visitor_id = _visitor_key(row)
        event = str(row.get("event") or "")

        tracked_visitors.add(visitor_id)
        if source.lower() == "linkedin":
            linkedin_visitors.add(visitor_id)

        if key not in buckets:
            buckets[key] = {
                "Source": source,
                "Medium": medium,
                "Campaign": campaign,
                "Content": content,
                "Visitors": set(),
                "Assessment starts": set(),
                "Assessment completions": set(),
                "Investigation starts": set(),
                "Feedback submissions": set(),
            }

        bucket = buckets[key]
        bucket["Visitors"].add(visitor_id)
        if event == "assessment_started":
            bucket["Assessment starts"].add(visitor_id)
        elif event == "assessment_completed":
            bucket["Assessment completions"].add(visitor_id)
        elif event == "investigation_started":
            bucket["Investigation starts"].add(visitor_id)
        elif event == "feedback_submitted":
            bucket["Feedback submissions"].add(visitor_id)

    table = []
    for bucket in buckets.values():
        table.append(
            {
                "Source": bucket["Source"],
                "Medium": bucket["Medium"],
                "Campaign": bucket["Campaign"],
                "Content": bucket["Content"],
                "Visitors": len(bucket["Visitors"]),
                "Assessment starts": len(bucket["Assessment starts"]),
                "Assessment completions": len(bucket["Assessment completions"]),
                "Investigation starts": len(bucket["Investigation starts"]),
                "Feedback submissions": len(bucket["Feedback submissions"]),
            }
        )

    table.sort(key=lambda x: (-x["Visitors"], x["Source"], x["Campaign"], x["Content"]))
    return table, len(tracked_visitors), len(linkedin_visitors)


campaign_rows, tracked_campaign_visitors, linkedin_visitors = _campaign_breakdown(live_events)

st.subheader("Investigation outcomes")

conclusion_rows = [r for r in live_events if r.get("event") == "investigation_conclusion"]
resolution_rows = [r for r in live_events if r.get("event") == "resolution_confirmed"]

def _unique_latest(rows):
    latest = {}
    for row in rows:
        latest[str(row.get("session_id") or "")] = row
    return list(latest.values())

conclusion_rows = _unique_latest(conclusion_rows)
resolution_rows = _unique_latest(resolution_rows)
resolution_by_session = {str(r.get("session_id") or ""): _metadata(r) for r in resolution_rows}

outcome_counts = {"confirmed": 0, "probable": 0, "not_yet_identified": 0, "unspecified": 0}
category_counts = {}
turn_values = []
recent_cases = []

for row in conclusion_rows:
    meta = _metadata(row)
    outcome = str(meta.get("conclusion_type") or "unspecified")
    category = str(meta.get("case_category") or "Other / Unclassified")
    turns = int(meta.get("assistant_turns") or 0)
    outcome_counts[outcome if outcome in outcome_counts else "unspecified"] += 1
    category_counts[category] = category_counts.get(category, 0) + 1
    if turns:
        turn_values.append(turns)
    resolution = resolution_by_session.get(str(row.get("session_id") or ""), {})
    recent_cases.append({
        "Date": str(row.get("created_at") or "")[:19],
        "Case": str(row.get("session_id") or "")[:8],
        "Source": str(_metadata(row).get("utm_content") or _metadata(row).get("utm_source") or "direct"),
        "Category": category,
        "Conclusion": outcome.replace("_", " ").title(),
        "Resolution": str(resolution.get("resolution_status") or "awaiting confirmation").replace("_", " ").title(),
        "Turns": turns,
    })

resolved_yes = sum(1 for m in resolution_by_session.values() if m.get("resolution_status") == "yes")
resolved_partial = sum(1 for m in resolution_by_session.values() if m.get("resolution_status") == "partial")
resolved_no = sum(1 for m in resolution_by_session.values() if m.get("resolution_status") == "no")
resolved_not_tested = sum(1 for m in resolution_by_session.values() if m.get("resolution_status") == "not_tested")
avg_turns = (sum(turn_values) / len(turn_values)) if turn_values else 0

o1, o2, o3, o4, o5 = st.columns(5)
o1.metric("Investigations started", len(investigation_starters))
o2.metric("Reached conclusion", len(conclusion_rows))
o3.metric("Root cause confirmed", outcome_counts["confirmed"])
o4.metric("User-confirmed resolved", resolved_yes)
o5.metric("Avg turns to conclusion", f"{avg_turns:.1f}" if turn_values else "—")

left, right = st.columns(2)
with left:
    st.markdown("**Conclusion outcomes**")
    st.dataframe([
        {"Outcome": "Root Cause Confirmed", "Cases": outcome_counts["confirmed"]},
        {"Outcome": "Root Cause Probable", "Cases": outcome_counts["probable"]},
        {"Outcome": "Not Yet Identified", "Cases": outcome_counts["not_yet_identified"]},
        {"Outcome": "Unspecified", "Cases": outcome_counts["unspecified"]},
    ], use_container_width=True, hide_index=True)
    st.markdown("**Actual resolution confirmation**")
    st.dataframe([
        {"Status": "Resolved", "Cases": resolved_yes},
        {"Status": "Partially resolved", "Cases": resolved_partial},
        {"Status": "Not resolved", "Cases": resolved_no},
        {"Status": "Not tested yet", "Cases": resolved_not_tested},
    ], use_container_width=True, hide_index=True)
with right:
    st.markdown("**Case categories**")
    category_table = [
        {"Category": name, "Cases": count}
        for name, count in sorted(category_counts.items(), key=lambda item: (-item[1], item[0]))
    ]
    if category_table:
        st.dataframe(category_table, use_container_width=True, hide_index=True)
    else:
        st.info("No categorized conclusions recorded yet.")

st.markdown("**Recent investigations**")
if recent_cases:
    st.dataframe(list(reversed(recent_cases[-30:])), use_container_width=True, hide_index=True)
else:
    st.info("Outcome/category tracking starts with new investigations after this deployment.")

st.caption(
    "Privacy: category and outcome labels are stored, but the HPLC case text is not copied to analytics. "
    "Resolved means the user explicitly confirmed the real-world outcome; a model conclusion alone is not counted as resolved."
)

st.subheader("Investigation step viewer")
st.caption(
    "Submitted case dialogue is shown here so the founding-beta investigation flow can be reviewed step by step. "
    "Users are warned not to submit sensitive or confidential information."
)
if investigation_messages:
    case_ids = []
    for row in investigation_messages:
        sid = str(row.get("session_id") or "").strip()
        if sid and sid not in case_ids:
            case_ids.append(sid)
    selected_case = st.selectbox(
        "Choose investigation case",
        list(reversed(case_ids)),
        format_func=lambda x: f"Case {x[:8]}",
    )
    selected_steps = [
        row for row in investigation_messages
        if str(row.get("session_id") or "") == selected_case
    ]
    selected_steps.sort(key=lambda row: (int(row.get("sequence") or 0), str(row.get("created_at") or "")))
    step_table = []
    for row in selected_steps:
        step_table.append({
            "Step": int(row.get("sequence") or 0),
            "Role": str(row.get("role") or "").title(),
            "Submitted text": str(row.get("content") or ""),
            "Language": str(row.get("language") or ""),
            "Time": str(row.get("created_at") or "")[:19],
        })
    st.dataframe(step_table, use_container_width=True, hide_index=True)
else:
    st.info("No durably stored investigation dialogue yet. New submitted steps will appear here after the updated webhook is deployed.")

st.subheader("Campaign attribution")
a1, a2 = st.columns(2)
a1.metric("Tracked campaign visitors", tracked_campaign_visitors)
a2.metric("LinkedIn visitors", linkedin_visitors)

if campaign_rows:
    st.dataframe(campaign_rows, use_container_width=True, hide_index=True)
    st.caption(
        "First-touch attribution is mirrored inside metadata_json. Unified visitor IDs are anonymous and shared across app pages during the same Streamlit journey."
    )
else:
    st.info("No live UTM-tagged visits have been recorded on this running instance yet.")

st.caption("LinkedIn launch tracking link")
st.code(
    "https://yahiaqc.streamlit.app/?utm_source=linkedin&utm_medium=organic_social&utm_campaign=founding_beta_launch&utm_content=launch_post",
    language=None,
)
st.caption("Internal test link — excluded from live metrics")
st.code(
    "https://yahiaqc.streamlit.app/?utm_source=linkedin&utm_medium=organic_social&utm_campaign=founding_beta_launch&utm_content=internal_test&test=1",
    language=None,
)

st.subheader("Feedback")
if feedback:
    safe_feedback = []
    for row in feedback:
        item = dict(row)
        sid = str(item.get("session_id") or "")
        item["traffic"] = session_status.get(sid, "legacy")
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
