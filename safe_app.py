"""Idempotent Streamlit entrypoint guard for Yahia QC Instrument Intelligence.

The application shell temporarily monkeypatches a few Streamlit callables while it
executes the legacy core. Streamlit reruns reuse the imported `streamlit` module,
so a failed/interrupted run can otherwise leave a wrapper installed and cause a
wrapper-to-wrapper recursion on the next rerun.

This entrypoint captures the true runtime callables once per interpreter and
restores them before every execution of app.py.
"""

from __future__ import annotations

from pathlib import Path

import streamlit as st
from streamlit.delta_generator import DeltaGenerator


# Capture pristine runtime callables once. These attributes live on the imported
# Streamlit module across reruns, while this script itself is re-executed.
if not hasattr(st, "_yqii_native_markdown"):
    st._yqii_native_markdown = st.markdown
if not hasattr(st, "_yqii_native_rerun"):
    st._yqii_native_rerun = st.rerun
if not hasattr(st, "_yqii_native_tabs"):
    st._yqii_native_tabs = st.tabs
if not hasattr(st, "_yqii_native_set_page_config"):
    st._yqii_native_set_page_config = st.set_page_config
if not hasattr(DeltaGenerator, "_yqii_native_metric"):
    DeltaGenerator._yqii_native_metric = DeltaGenerator.metric

# Repair any wrapper left behind by an interrupted previous rerun.
st.markdown = st._yqii_native_markdown
st.rerun = st._yqii_native_rerun
DeltaGenerator.metric = DeltaGenerator._yqii_native_metric

# Preserve sitecustomize's intentional navigation/page-config wrappers when they
# are the interpreter baseline; app.py will temporarily patch and restore them.
st.tabs = st._yqii_native_tabs
st.set_page_config = st._yqii_native_set_page_config

_app = Path(__file__).resolve().with_name("app.py")
exec(compile(_app.read_text(encoding="utf-8"), str(_app), "exec"), globals(), globals())
