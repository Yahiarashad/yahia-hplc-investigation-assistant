from pathlib import Path
import importlib
import re
import secrets
import sys

import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import beta_feedback as _beta_feedback
_beta_feedback = importlib.reload(_beta_feedback)
record_event = _beta_feedback.record_event
render_feedback_form = _beta_feedback.render_feedback_form

st.set_page_config(page_title="Founding Beta Feedback", page_icon="💬", layout="centered")

st.markdown(
    """
    <style>
    .block-container {
        padding-top: 4.8rem !important;
        padding-bottom: 4rem !important;
    }
    @media (max-width: 768px) {
        .block-container {
            padding-top: 5.3rem !important;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

lang_label = st.radio("اختر اللغة / Choose language", ["العربية", "English"], horizontal=True)
lang = "ar" if lang_label == "العربية" else "en"

raw = st.query_params.get("feedback")
if isinstance(raw, list):
    raw = raw[0] if raw else None
if not isinstance(raw, str) or not re.fullmatch(r"BF-[A-Za-z0-9]{8}", raw):
    raw = "BF-" + secrets.token_hex(4).upper()
    st.query_params["feedback"] = raw

if not st.session_state.get("_generic_feedback_view_logged"):
    record_event(raw, "beta_feedback_page", "feedback_page_viewed", lang)
    st.session_state["_generic_feedback_view_logged"] = True

if lang == "ar":
    st.markdown(
        """
        <div dir="rtl" style="text-align:right; margin-top:.4rem; margin-bottom:1rem;">
          <div style="font-size:2.5rem;font-weight:900;line-height:1.2;color:#2f3140;">
            💬 ملاحظتك تبني النسخة القادمة
          </div>
          <div style="font-size:1.05rem;line-height:1.9;margin-top:1rem;color:#374151;">
            لو جرّبت اختبار <b>فجوة القرار لمحلل الجودة</b> أو
            <b>مساعد يحيى للتحقيق في <span dir="ltr" style="unicode-bidi:isolate;">HPLC</span></b>،
            شاركني ما الذي نجح فعلًا وما الذي يحتاج تطويرًا.
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(
        """
        <style>
        div[data-testid="stSelectbox"] label,
        div[data-testid="stSelectbox"] p {
            direction: rtl !important;
            text-align: right !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
    source_options = {
        "مساعد يحيى للتحقيق في \u2066HPLC\u2069": "hplc_assistant",
        "اختبار فجوة القرار لمحلل الجودة": "decision_gap",
    }
    source_label = st.selectbox("الأداة", list(source_options.keys()), index=None, placeholder="اختر الأداة")
else:
    st.markdown("# 💬 Your feedback shapes the next release")
    st.write(
        "If you tried the **QC Analyst Decision Gap** or **Yahia HPLC Investigation Assistant**, "
        "tell us what worked and what should improve."
    )
    source_options = {
        "Yahia HPLC Investigation Assistant": "hplc_assistant",
        "QC Analyst Decision Gap": "decision_gap",
    }
    source_label = st.selectbox("Tool", list(source_options.keys()), index=None, placeholder="Choose a tool")

if source_label is None:
    if lang == "ar":
        st.info("اختر الأداة أولًا، ثم سيظهر نموذج الملاحظات.")
    else:
        st.info("Choose a tool first, then the feedback form will appear.")
else:
    source = source_options[source_label]
    render_feedback_form(source=source, session_id=raw, language=lang, compact=False)
