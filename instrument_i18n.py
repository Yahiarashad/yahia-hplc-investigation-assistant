# Yahia QC Instrument Intelligence — UI language architecture v1
# Internal route IDs, database values and evidence records remain unchanged.
# Localization is presentation-only so the same data/logic serves every language.

from __future__ import annotations

import streamlit as st

LANG_BILINGUAL = "bilingual"
LANG_ENGLISH = "en"
LANGUAGE_OPTIONS = (LANG_BILINGUAL, LANG_ENGLISH)
LANGUAGE_LABELS = {
    LANG_BILINGUAL: "العربية + English",
    LANG_ENGLISH: "English",
}


def current_language() -> str:
    value = str(st.session_state.get("ilm_language") or LANG_BILINGUAL)
    return value if value in LANGUAGE_OPTIONS else LANG_BILINGUAL


def is_english() -> bool:
    return current_language() == LANG_ENGLISH


def ui_text(english: str, bilingual: str | None = None) -> str:
    """Return localized presentation text without changing stored data or logic."""
    if is_english():
        return english
    return bilingual if bilingual is not None else english


def render_language_selector(*, key: str = "global") -> str:
    current = current_language()
    selected = st.selectbox(
        "🌐 Interface language",
        options=list(LANGUAGE_OPTIONS),
        index=list(LANGUAGE_OPTIONS).index(current),
        format_func=lambda value: LANGUAGE_LABELS.get(value, value),
        key=f"ilm_language_selector_{key}",
        help="Changes interface wording only. Instrument data, evidence, permissions and calculations are unchanged.",
    )
    st.session_state.ilm_language = selected
    return selected
