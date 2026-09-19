# Product feedback panel for Yahia QC Instrument Lifecycle & Investigation Intelligence.
# Reuses the existing beta feedback storage/webhook layer without mixing feedback
# with regulated instrument records.

from __future__ import annotations

import uuid

import streamlit as st

from beta_feedback import external_storage_configured, save_feedback


_SESSION_KEY = "_ilm_product_feedback_session"
_DONE_KEY = "_ilm_product_feedback_done"


def _feedback_session_id() -> str:
    if not st.session_state.get(_SESSION_KEY):
        st.session_state[_SESSION_KEY] = f"ilm-{uuid.uuid4().hex}"
    return str(st.session_state[_SESSION_KEY])


def render_instrument_feedback(*, compact: bool = True) -> None:
    """Render a short, practical founding-user feedback step."""
    if st.session_state.get(_DONE_KEY):
        st.success("وصلت ملاحظتك 🙌 شكرًا لأنك بتساعد في بناء النسخة القادمة بصورة عملية.")
        return

    with st.expander(
        "💬 Feedback | ساعدني أطور النسخة القادمة",
        expanded=not compact,
    ):
        st.markdown(
            """
<div dir="rtl" style="text-align:right;line-height:1.85">
<b>بعد ما تستخدم التطبيق فعليًا، قلّي أين وفر وقتك وأين عطّلك.</b><br>
المطلوب ليس مجاملة؛ نريد ملاحظة عملية تساعدنا نجعل إدارة دورة حياة الأجهزة أسهل من الـExcel وأقوى في اتخاذ القرار.
</div>
""",
            unsafe_allow_html=True,
        )
        st.caption("Do not enter confidential company, product, method, patient, password, or proprietary information.")

        with st.form("ilm_product_feedback_form", clear_on_submit=False):
            rating = st.radio(
                "تقييم التجربة | Overall experience",
                [1, 2, 3, 4, 5],
                index=None,
                horizontal=True,
                key="ilm_feedback_rating",
            )
            outcome = st.radio(
                "هل التطبيق أضاف قيمة فعلية مقارنة بالـExcel Tracker؟",
                ["نعم بوضوح", "جزئيًا", "ليس بعد"],
                index=None,
                key="ilm_feedback_value",
            )
            accuracy = st.radio(
                "هل ترتيب Lifecycle والخطوة التالية يعكسان واقع العمل في المعمل؟",
                ["نعم", "إلى حد ما", "لا"],
                index=None,
                key="ilm_feedback_reality",
            )
            most_useful = st.text_area(
                "أكثر جزء وفر وقتًا أو ساعدك في القرار؟",
                height=80,
                key="ilm_feedback_useful",
            )
            improvement = st.text_area(
                "لو هنصلّح أو نطوّر حاجة واحدة فورًا، تكون إيه؟",
                height=90,
                key="ilm_feedback_improve",
            )
            desired_feature = st.selectbox(
                "الميزة التالية الأكثر قيمة لك",
                [
                    "— اختر —",
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
            name = c1.text_input("الاسم — اختياري", key="ilm_feedback_name")
            contact = c2.text_input("LinkedIn / Email — اختياري", key="ilm_feedback_contact")
            consent = st.checkbox(
                "أوافق على استخدام ملاحظتي بصورة مجهولة لتحسين التطبيق.",
                key="ilm_feedback_consent",
            )
            submitted = st.form_submit_button("إرسال الملاحظة | Send feedback", use_container_width=True)

        if submitted:
            if rating is None or outcome is None or accuracy is None:
                st.error("اختَر التقييم، القيمة العملية، ومدى واقعية دورة العمل قبل الإرسال.")
                return
            saved = save_feedback(
                session_id=_feedback_session_id(),
                source="instrument_lifecycle_v03",
                language="ar",
                rating=rating,
                outcome=outcome,
                accuracy=accuracy,
                most_useful=most_useful,
                improvement=improvement,
                desired_feature="" if desired_feature == "— اختر —" else desired_feature,
                name=name,
                contact=contact,
                consent_research=consent,
            )
            if saved:
                st.session_state[_DONE_KEY] = True
                st.success("وصلت ملاحظتك 🙌 شكرًا لأنك جزء من تطوير المنتج.")
            else:
                st.info("تم استلام Feedback لهذه الجلسة بالفعل.")

        if not external_storage_configured():
            st.caption("Beta note: durable external feedback storage is not configured in this deployment yet.")
