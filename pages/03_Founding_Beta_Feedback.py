from pathlib import Path
import re
import secrets
import sys

import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from beta_feedback import record_event, render_feedback_form

st.set_page_config(page_title="Founding Beta Feedback", page_icon="💬", layout="centered")

lang_label = st.radio("Language / اللغة", ["العربية", "English"], horizontal=True)
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
    st.markdown("# 💬 ملاحظتك تبني النسخة القادمة")
    st.write("لو جرّبت اختبار **QC Analyst Decision Gap** أو **مساعد يحيى للتحقيق في HPLC**، قل لنا ما الذي نجح وما الذي يحتاج تطويرًا.")
else:
    st.markdown("# 💬 Your feedback shapes the next release")
    st.write("If you tried the **QC Analyst Decision Gap** or **Yahia HPLC Investigation Assistant**, tell us what worked and what should improve.")

source_label = st.selectbox(
    "الأداة / Tool" if lang == "ar" else "Tool",
    ["Yahia HPLC Investigation Assistant", "QC Analyst Decision Gap"],
)
source = "hplc_assistant" if source_label.startswith("Yahia") else "decision_gap"

render_feedback_form(source=source, session_id=raw, language=lang, compact=False)
