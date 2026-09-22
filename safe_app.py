"""Stable Streamlit entrypoint for Yahia QC Instrument Intelligence.

This file repairs any stale Streamlit monkeypatches left in the running interpreter
before executing app.py. Do not cache previously wrapped callables: import the
canonical Streamlit commands directly on every run.
"""

from __future__ import annotations

from pathlib import Path

import streamlit as st
from streamlit.commands.execution_control import rerun as _native_rerun
from streamlit.commands.page_config import set_page_config as _native_set_page_config


# Always restore authoritative Streamlit callables from their source modules.
# This deliberately ignores any stale _yqii_* attributes that may survive a hot reload.
st.rerun = _native_rerun
st.set_page_config = _native_set_page_config

# Top-level element functions are bound to Streamlit's main DeltaGenerator.
# Rebind them from _main so an interrupted previous run cannot leave recursive wrappers.
try:
    st.markdown = st._main.markdown
    st.tabs = st._main.tabs
except Exception:
    pass

# Overwrite stale compatibility aliases as well, so subsequent hot reloads start clean.
st._yqii_native_rerun = _native_rerun
try:
    st._yqii_native_markdown = st._main.markdown
    st._yqii_native_tabs = st._main.tabs
except Exception:
    pass
st._yqii_native_set_page_config = _native_set_page_config

_app = Path(__file__).resolve().with_name("app.py")
exec(compile(_app.read_text(encoding="utf-8"), str(_app), "exec"), globals(), globals())
