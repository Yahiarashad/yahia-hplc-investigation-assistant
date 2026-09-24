# Yahia QC Instrument Intelligence — UI language architecture v1.1
# Internal route IDs, database values and evidence records remain unchanged.
# Localization is presentation-only so the same data/logic serves every language.
# Language is persisted in the URL so same-tab mobile navigation cannot reset it.

from __future__ import annotations

import streamlit as st

LANG_BILINGUAL = "bilingual"
LANG_ENGLISH = "en"
LANGUAGE_OPTIONS = (LANG_BILINGUAL, LANG_ENGLISH)
LANGUAGE_LABELS = {
    LANG_BILINGUAL: "العربية + English",
    LANG_ENGLISH: "English",
}


def _query_language() -> str:
    try:
        value = str(st.query_params.get("lang", "") or "").strip().lower()
    except Exception:
        value = ""
    return value if value in LANGUAGE_OPTIONS else ""


def current_language() -> str:
    """Resolve language from session first, then the persistent URL parameter."""
    value = str(st.session_state.get("ilm_language") or "").strip().lower()
    if value in LANGUAGE_OPTIONS:
        return value
    value = _query_language()
    if value in LANGUAGE_OPTIONS:
        st.session_state.ilm_language = value
        return value
    st.session_state.ilm_language = LANG_BILINGUAL
    return LANG_BILINGUAL


def is_english() -> bool:
    return current_language() == LANG_ENGLISH


def ui_text(english: str, bilingual: str | None = None) -> str:
    """Return localized presentation text without changing stored data or logic."""
    if is_english():
        return english
    return bilingual if bilingual is not None else english


def _sync_language_choice(widget_key: str) -> None:
    selected = str(st.session_state.get(widget_key) or LANG_BILINGUAL)
    if selected not in LANGUAGE_OPTIONS:
        selected = LANG_BILINGUAL
    st.session_state.ilm_language = selected
    try:
        st.query_params["lang"] = selected
    except Exception:
        pass


def render_language_selector(*, key: str = "global") -> str:
    current = current_language()
    widget_key = f"ilm_language_selector_{key}"
    if widget_key not in st.session_state:
        st.session_state[widget_key] = current

    selected = st.selectbox(
        "🌐 Interface language",
        options=list(LANGUAGE_OPTIONS),
        format_func=lambda value: LANGUAGE_LABELS.get(value, value),
        key=widget_key,
        on_change=_sync_language_choice,
        args=(widget_key,),
        help="Changes interface wording only. Instrument data, evidence, permissions and calculations are unchanged.",
    )
    st.session_state.ilm_language = selected
    return selected
