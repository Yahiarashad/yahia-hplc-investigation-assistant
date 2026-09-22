"""Runtime bridge for the legacy direct Streamlit entrypoint.

When Streamlit runs instrument_supabase_app.py directly, the newer application shell
is bypassed. This bridge makes the premium Product/User/Management guide visible in
the legacy Guide tab as well, so the downloadable PDF is always reachable.
"""

try:
    import streamlit as st

    if not hasattr(st, "_yqii_native_header"):
        st._yqii_native_header = st.header

    _native_header = st._yqii_native_header

    def _yqii_header(body, *args, **kwargs):
        result = _native_header(body, *args, **kwargs)
        try:
            if str(body).strip() == "How to Use | دليل الاستخدام":
                from instrument_product_guide import render_product_guide_hub
                render_product_guide_hub()
        except Exception as exc:
            st.caption(f"Premium Product Guide is temporarily unavailable ({type(exc).__name__}).")
        return result

    st.header = _yqii_header
except Exception:
    pass
