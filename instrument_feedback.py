from __future__ import annotations

import uuid
import inspect
import streamlit as st
from beta_feedback import external_storage_configured, save_feedback

_SESSION_KEY = "_ilm_product_feedback_session"
_DONE_KEY = "_ilm_product_feedback_done"


def _feedback_session_id() -> str:
    if not st.session_state.get(_SESSION_KEY):
        st.session_state[_SESSION_KEY] = f"ilm-{uuid.uuid4().hex}"
    return str(st.session_state[_SESSION_KEY])


def _caller_context():
    try:
        frame = inspect.currentframe()
        caller = frame.f_back.f_back if frame and frame.f_back else None
        return caller.f_globals if caller else {}
    except Exception:
        return {}


def _apply_guide_rtl_css():
    # Scope RTL to the detailed Arabic practical guide instead of reversing
    # technical tables / serial-number forms across the whole application.
    st.markdown(
        r"""
<style>
/* The guide banner is immediately followed by its Streamlit expander. */
div[data-testid="stElementContainer"]:has(.v03-guide-banner) + div[data-testid="stElementContainer"] div[data-testid="stExpander"] div[data-testid="stMarkdownContainer"],
div[data-testid="stElementContainer"]:has(.v03-guide-banner) + div[data-testid="stElementContainer"] div[data-testid="stExpander"] div[data-testid="stAlertContainer"],
div[data-testid="stElementContainer"]:has(.v03-guide-banner) + div[data-testid="stElementContainer"] div[data-testid="stExpander"] label,
div.element-container:has(.v03-guide-banner) + div.element-container div[data-testid="stExpander"] div[data-testid="stMarkdownContainer"],
div.element-container:has(.v03-guide-banner) + div.element-container div[data-testid="stExpander"] div[data-testid="stAlertContainer"],
div.element-container:has(.v03-guide-banner) + div.element-container div[data-testid="stExpander"] label {
  direction: rtl !important;
  text-align: right !important;
  unicode-bidi: plaintext;
}
div[data-testid="stElementContainer"]:has(.v03-guide-banner) + div[data-testid="stElementContainer"] div[data-testid="stExpander"] ul,
div[data-testid="stElementContainer"]:has(.v03-guide-banner) + div[data-testid="stElementContainer"] div[data-testid="stExpander"] ol,
div.element-container:has(.v03-guide-banner) + div.element-container div[data-testid="stExpander"] ul,
div.element-container:has(.v03-guide-banner) + div.element-container div[data-testid="stExpander"] ol {
  direction: rtl !important;
  text-align: right !important;
  padding-right: 1.45rem !important;
  padding-left: 0 !important;
}
div[data-testid="stElementContainer"]:has(.v03-guide-banner) + div[data-testid="stElementContainer"] div[data-testid="stExpander"] li,
div.element-container:has(.v03-guide-banner) + div.element-container div[data-testid="stExpander"] li {
  direction: rtl !important;
  text-align: right !important;
  unicode-bidi: plaintext;
}
@media(max-width:700px){
 div[data-testid="stElementContainer"]:has(.v03-guide-banner) + div[data-testid="stElementContainer"] div[data-testid="stExpander"] div[data-testid="stMarkdownContainer"],
 div.element-container:has(.v03-guide-banner) + div.element-container div[data-testid="stExpander"] div[data-testid="stMarkdownContainer"]{line-height:1.85;}
}
</style>
""",
        unsafe_allow_html=True,
    )


def render_instrument_feedback(*, compact: bool = True, language: str = "ar") -> None:
    ar = language == "ar"
    _apply_guide_rtl_css()

    # Premium product/user/management guide. It is generated without customer
    # instrument records, so users can safely download and share the brochure.
    try:
        from instrument_product_guide_rtl import render_product_guide_hub
        render_product_guide_hub()
    except Exception as exc:
        st.caption(f"Premium Product Guide is temporarily unavailable ({type(exc).__name__}).")

    # Report Center is intentionally shown before the feedback step so the user
    # can export a real lifecycle report, review it, then comment on the workflow.
    try:
        from instrument_pdf_reports import render_pdf_report_center
        render_pdf_report_center(_caller_context(), ui_lang="ar" if ar else "en")
    except Exception as exc:
        st.caption(f"PDF Report Center is temporarily unavailable ({type(exc).__name__}).")

    if st.session_state.get(_DONE_KEY):
        st.success("وصلت ملاحظتك 🙌 شكرًا لأنك بتساعد في بناء النسخة القادمة بصورة عملية." if ar else "Feedback received 🙌 Thank you for helping shape the next version.")
        return

    title = "💬 Feedback | ساعدني أطور النسخة القادمة" if ar else "💬 Feedback | Help shape the next version"
    with st.expander(title, expanded=not compact):
        if ar:
            st.markdown(
                """<div dir="rtl" style="text-align:right;line-height:1.85"><b>بعد ما تستخدم التطبيق فعليًا، قلّي أين وفر وقتك وأين عطّلك.</b><br>المطلوب ليس مجاملة؛ نريد ملاحظة عملية تجعل إدارة دورة حياة الأجهزة أسهل من الـExcel وأقوى في اتخاذ القرار.</div>""",
                unsafe_allow_html=True,
            )
        else:
            st.markdown("**After real use, tell us where the app saved time and where it slowed you down.** Practical criticism is more useful than praise.")
        st.caption("Do not enter confidential company, product, method, patient, password, or proprietary information.")

        with st.form("ilm_product_feedback_form", clear_on_submit=False):
            rating = st.radio(
                "تقييم التجربة | Overall experience" if ar else "Overall experience",
                [1, 2, 3, 4, 5], index=None, horizontal=True, key="ilm_feedback_rating",
            )
            outcome = st.radio(
                "هل التطبيق أضاف قيمة فعلية مقارنة بالـExcel Tracker؟" if ar else "Did the app add practical value beyond your Excel tracker?",
                ["نعم بوضوح", "جزئيًا", "ليس بعد"] if ar else ["Clearly yes", "Partly", "Not yet"],
                index=None, key="ilm_feedback_value",
            )
            accuracy = st.radio(
                "هل ترتيب Lifecycle والخطوة التالية يعكسان واقع العمل في المعمل؟" if ar else "Does the lifecycle order and next action reflect real laboratory work?",
                ["نعم", "إلى حد ما", "لا"] if ar else ["Yes", "Partly", "No"],
                index=None, key="ilm_feedback_reality",
            )
            most_useful = st.text_area(
                "أكثر جزء وفر وقتًا أو ساعدك في القرار؟" if ar else "What saved the most time or helped the decision most?",
                height=80, key="ilm_feedback_useful",
            )
            improvement = st.text_area(
                "لو هنصلّح أو نطوّر حاجة واحدة فورًا، تكون إيه؟" if ar else "If we improve one thing immediately, what should it be?",
                height=90, key="ilm_feedback_improve",
            )
            desired_feature = st.selectbox(
                "الميزة التالية الأكثر قيمة لك" if ar else "Most valuable next feature",
                [
                    "— اختر —" if ar else "— Select —",
                    "Smarter Excel import / column mapping",
                    "QR / barcode / camera-assisted entry",
                    "Automatic due-date alerts & reminders",
                    "Lifecycle PDF / management report",
                    "Supervisor / team dashboard",
                    "Audit trail / review & approval workflow",
                    "Advanced Investigation Intelligence",
                    "Other",
                ],
                key="ilm_feedback_feature",
            )
            c1, c2 = st.columns(2)
            name = c1.text_input("الاسم — اختياري" if ar else "Name — optional", key="ilm_feedback_name")
            contact = c2.text_input("LinkedIn / Email — اختياري" if ar else "LinkedIn / Email — optional", key="ilm_feedback_contact")
            consent = st.checkbox(
                "أوافق على استخدام ملاحظتي بصورة مجهولة لتحسين التطبيق." if ar else "I agree that my anonymized feedback may be used to improve the application.",
                key="ilm_feedback_consent",
            )
            submitted = st.form_submit_button("إرسال الملاحظة | Send feedback" if ar else "Send feedback", use_container_width=True)

        if submitted:
            if rating is None or outcome is None or accuracy is None:
                st.error("اختَر التقييم، القيمة العملية، ومدى واقعية دورة العمل قبل الإرسال." if ar else "Choose the rating, practical value, and lifecycle realism before submitting.")
                return
            empty_choice = desired_feature in {"— اختر —", "— Select —"}
            saved = save_feedback(
                session_id=_feedback_session_id(),
                source="instrument_lifecycle_v04",
                language="ar" if ar else "en",
                rating=rating,
                outcome=outcome,
                accuracy=accuracy,
                most_useful=most_useful,
                improvement=improvement,
                desired_feature="" if empty_choice else desired_feature,
                name=name,
                contact=contact,
                consent_research=consent,
            )
            if saved:
                st.session_state[_DONE_KEY] = True
                st.success("وصلت ملاحظتك 🙌 شكرًا لأنك جزء من تطوير المنتج." if ar else "Feedback received 🙌 Thank you for helping develop the product.")
            else:
                st.info("تم استلام Feedback لهذه الجلسة بالفعل." if ar else "Feedback for this session has already been received.")

        if not external_storage_configured():
            st.caption("Beta note: durable external feedback storage is not configured in this deployment yet.")
