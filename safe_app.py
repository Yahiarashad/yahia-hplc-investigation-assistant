"""Stable Streamlit entrypoint for Yahia QC Instrument Intelligence.

Why this exists
---------------
The application shell historically monkeypatched ``st.rerun`` so every rerun could
flush the encrypted refresh-token cookie first. Streamlit reuses the imported
``streamlit`` module between script reruns. If the shell is executed again while a
previous wrapper is still installed, the wrapper can end up calling itself and
produce a RecursionError.

This entrypoint keeps the *real* Streamlit rerun callable authoritative. The app is
still free to use its other temporary UI wrappers, but assignments that try to
replace ``st.rerun`` are ignored. Authentication persistence is still written by
``app.py`` at the end of normal runs; native reruns no longer recurse.
"""

from __future__ import annotations

import types
from pathlib import Path

import streamlit as st
from streamlit.delta_generator import DeltaGenerator


# Capture pristine callables once per Python interpreter. These attributes remain
# on the imported Streamlit module across script reruns.
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


class _YQIIStreamlitModule(types.ModuleType):
    """Keep rerun native even if legacy shell code tries to wrap it again."""

    def __setattr__(self, name, value):
        if name == "rerun" and hasattr(self, "_yqii_native_rerun"):
            native = types.ModuleType.__getattribute__(self, "_yqii_native_rerun")
            # Allow restoring the real function, but reject wrapper replacement.
            if value is not native:
                return
        return types.ModuleType.__setattr__(self, name, value)


# Upgrade the existing module object in place. Imports elsewhere keep pointing to
# the same object, but rerun replacement becomes impossible.
if not isinstance(st, _YQIIStreamlitModule):
    st.__class__ = _YQIIStreamlitModule

# Repair anything left by a previous failed run before executing the shell.
st.markdown = st._yqii_native_markdown
st.rerun = st._yqii_native_rerun
DeltaGenerator.metric = DeltaGenerator._yqii_native_metric
st.tabs = st._yqii_native_tabs
st.set_page_config = st._yqii_native_set_page_config

_app = Path(__file__).resolve().with_name("app.py")
exec(compile(_app.read_text(encoding="utf-8"), str(_app), "exec"), globals(), globals())
