import secrets

import streamlit as st

VISITOR_STATE_KEY = "_analytics_visitor_id"
TRAFFIC_STATE_KEY = "_analytics_traffic_type"


def _query_param_value(name):
    try:
        value = st.query_params.get(name)
    except Exception:
        return ""
    if isinstance(value, list):
        value = value[0] if value else ""
    if value in (None, ""):
        return ""
    return str(value).strip()[:160]


def get_visitor_id():
    """Return one anonymous ID shared across pages for the current Streamlit journey."""
    current = st.session_state.get(VISITOR_STATE_KEY)
    if isinstance(current, str) and current:
        return current
    visitor_id = f"V-{secrets.token_hex(8)}"
    st.session_state[VISITOR_STATE_KEY] = visitor_id
    return visitor_id


def get_traffic_type():
    """Classify current traffic as live or test without collecting identity data."""
    explicit_test = _query_param_value("test").lower()
    utm_content = _query_param_value("utm_content").lower()

    if explicit_test in {"1", "true", "yes", "test"}:
        st.session_state[TRAFFIC_STATE_KEY] = "test"
        return "test"

    if (
        "feedback_retest" in utm_content
        or utm_content.startswith("test_")
        or utm_content.startswith("internal_")
    ):
        st.session_state[TRAFFIC_STATE_KEY] = "test"
        return "test"

    current = st.session_state.get(TRAFFIC_STATE_KEY)
    if current in {"live", "test"}:
        return current

    st.session_state[TRAFFIC_STATE_KEY] = "live"
    return "live"


def analytics_metadata(metadata=None):
    """Add anonymous visitor and traffic classification to analytics metadata."""
    merged = dict(metadata or {})
    merged.setdefault("visitor_id", get_visitor_id())
    merged.setdefault("traffic_type", get_traffic_type())
    return merged
