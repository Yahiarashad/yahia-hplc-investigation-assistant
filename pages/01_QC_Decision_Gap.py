from pathlib import Path
import runpy
import streamlit as st
import streamlit.components.v1 as components

# Thin wrapper around the assessment core.
# It adds mobile-friendly scroll behavior after stage navigation without
# changing the scoring or bilingual analytical logic in the core file.

CORE_PATH = Path(__file__).resolve().parents[1] / "qc_gap_core.py"

_pending_target = st.session_state.pop("_qc_gap_scroll_target", None)
if _pending_target:
    target = _pending_target
    components.html(
        f"""
        <script>
        (function() {{
          const target = {target!r};
          let attempts = 0;
          function scrollWhenReady() {{
            const doc = window.parent.document;

            if (target === 'question') {{
              const radios = doc.querySelectorAll('[data-testid="stRadio"]');
              // Radio 0 = language selector. Radio 1 = first assessment question.
              if (radios.length > 1) {{
                radios[1].scrollIntoView({{behavior:'smooth', block:'start'}});
                return;
              }}
            }} else if (target === 'result') {{
              const headings = Array.from(doc.querySelectorAll('h1,h2,h3'));
              const resultHeading = headings.find(el => {{
                const t = (el.innerText || '').trim();
                return t.startsWith('Your result') || t.startsWith('نتيجتك');
              }});
              if (resultHeading) {{
                resultHeading.scrollIntoView({{behavior:'smooth', block:'start'}});
                return;
              }}
            }} else if (target === 'top') {{
              window.parent.scrollTo({{top:0, behavior:'smooth'}});
              return;
            }}

            attempts += 1;
            if (attempts < 16) {{
              setTimeout(scrollWhenReady, 120);
            }} else {{
              window.parent.scrollTo({{top:0, behavior:'smooth'}});
            }}
          }}
          setTimeout(scrollWhenReady, 120);
        }})();
        </script>
        """,
        height=0,
        width=0,
    )

_original_rerun = st.rerun

def _rerun_with_scroll(*args, **kwargs):
    if st.session_state.get("gap_done"):
        st.session_state["_qc_gap_scroll_target"] = "result"
    elif st.session_state.get("gap_started"):
        st.session_state["_qc_gap_scroll_target"] = "question"
    else:
        st.session_state["_qc_gap_scroll_target"] = "top"
    return _original_rerun(*args, **kwargs)

st.rerun = _rerun_with_scroll
try:
    runpy.run_path(str(CORE_PATH), run_name="__main__")
finally:
    st.rerun = _original_rerun
