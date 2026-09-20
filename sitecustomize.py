"""Application-wide Streamlit UI default: keep expanders collapsed until clicked.

This is intentionally tiny and safe: it only changes the default/open state.
Any section can still be opened normally by the user, and callers do not need
individual code changes.
"""

try:
    import streamlit as st

    _ilm_native_expander_default = st.expander

    def _ilm_collapsed_expander(label, *args, **kwargs):
        # Product decision: every accordion/expander starts closed.
        # Explicit expanded=True in older modules is intentionally overridden.
        kwargs["expanded"] = False
        return _ilm_native_expander_default(label, *args, **kwargs)

    st.expander = _ilm_collapsed_expander
except Exception:
    # Never block application startup if Streamlit is unavailable during
    # interpreter bootstrap.
    pass
