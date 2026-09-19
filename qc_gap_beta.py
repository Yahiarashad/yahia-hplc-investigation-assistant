import secrets
import streamlit as st

from qc_gap_runtime import run_assessment_page

DISPLAY_VERSION = "v0.4 · Founding Beta Calibration"


def _beta_id():
    if "_qc_gap_beta_tester_id" not in st.session_state:
        st.session_state["_qc_gap_beta_tester_id"] = f"FB-{secrets.randbelow(1_000_000):06d}"
    return st.session_state["_qc_gap_beta_tester_id"]


def _lang():
    return "ar" if st.session_state.get("gap_lang", "العربية") == "العربية" else "en"


def _beta_banner_html(lang):
    if lang == "ar":
        eyebrow = "النسخة التأسيسية · وصول مبكر"
        title = "أنت تختبر النسخة التأسيسية"
        copy = "ساعدنا في بناء معيار أقوى لاتخاذ القرار داخل معامل الرقابة الدوائية. هذا الاختبار لا يقيس الحفظ؛ بل يقيس جودة القرار تحت الغموض."
        direction = "rtl"
        align = "right"
    else:
        eyebrow = "FOUNDING BETA · EARLY ACCESS"
        title = "You are testing the founding release"
        copy = "Help shape a stronger benchmark for QC decision-making. This assessment measures judgment under ambiguity, not memorization."
        direction = "ltr"
        align = "left"
    return f"""
    <div style="margin:.35rem 0 1rem;padding:1rem 1.05rem;border-radius:18px;
                background:linear-gradient(135deg,#fffaf0,#f7fbff);border:1px solid #dfc77c;
                box-shadow:0 8px 22px rgba(15,23,42,.05);direction:{direction};text-align:{align};">
      <div style="font-size:.72rem;font-weight:900;letter-spacing:.06em;color:#8a6d22;direction:{direction};text-align:{align};">{eyebrow}</div>
      <div style="font-size:1.05rem;font-weight:900;margin:.35rem 0 .25rem;color:#111827;direction:{direction};text-align:{align};">{title}</div>
      <div style="font-size:.88rem;line-height:1.8;color:#5f6b7a;direction:{direction};text-align:{align};unicode-bidi:plaintext;">{copy}</div>
    </div>
    """


def _tester_card_html(lang, tester_id):
    if lang == "ar":
        title = "FOUNDING BETA TESTER"
        subtitle = "معرّف مشاركتك في النسخة التأسيسية"
        note = "احتفظ بالمعرّف مع لقطة نتيجتك عند مشاركة ملاحظاتك عن النسخة التجريبية."
    else:
        title = "FOUNDING BETA TESTER"
        subtitle = "Your founding-release tester ID"
        note = "Keep this ID with your result screenshot when sharing feedback about the beta."
    direction = "rtl" if lang == "ar" else "ltr"
    align = "right" if lang == "ar" else "left"
    return f"""
    <div style="direction:{direction};text-align:{align};margin:.7rem 0 1rem;padding:1.15rem 1.2rem;
                border-radius:20px;background:linear-gradient(145deg,#0b1526,#152238);color:white;
                border:1px solid rgba(202,167,80,.55);box-shadow:0 10px 26px rgba(2,6,23,.12);">
      <div style="font-size:.74rem;font-weight:900;letter-spacing:.08em;color:#d6bd78;direction:ltr;text-align:left;">{title}</div>
      <div style="font-size:.9rem;margin-top:.4rem;color:#dbe4ef;">{subtitle}</div>
      <div style="font-size:1.55rem;font-weight:950;margin:.22rem 0;direction:ltr;unicode-bidi:isolate;color:#fff;">{tester_id}</div>
      <div style="font-size:.78rem;line-height:1.65;color:#9fb0c4;">{note}</div>
    </div>
    """


def _share_suffix(lang, tester_id):
    if lang == "ar":
        return (
            f"\nFounding Beta Tester: {tester_id}"
            "\n\nالاختبار لا يقيس الحفظ؛ يقيس جودة القرار عندما تبدو أكثر من إجابة منطقية."
            "\nDON'T GUESS. FOLLOW THE EVIDENCE."
            "\n#PharmaceuticalQC #HPLC #QualityControl"
        )
    return (
        f"\nFounding Beta Tester: {tester_id}"
        "\n\nThis assessment does not test memorization; it tests decision quality when several options look reasonable."
        "\nDON'T GUESS. FOLLOW THE EVIDENCE."
        "\n#PharmaceuticalQC #HPLC #QualityControl"
    )


def run_beta_assessment_page():
    tester_id = _beta_id()

    base_markdown = st.markdown
    base_code = st.code
    base_button = st.button
    base_page_link = st.page_link

    state = {"banner": False, "tester_card": False}

    def beta_markdown(body, *args, **kwargs):
        text = body
        if isinstance(text, str):
            text = text.replace("v0.3 · Bilingual Analytical Calibration", DISPLAY_VERSION)

            if "gap-hero" in text and not state["banner"]:
                base_markdown(_beta_banner_html(_lang()), unsafe_allow_html=True)
                state["banner"] = True

        result = base_markdown(text, *args, **kwargs)

        if (
            isinstance(text, str)
            and not state["tester_card"]
            and "section-card" in text
            and "/100" in text
            and ("Your result" in text or "نتيجتك" in text)
        ):
            base_markdown(_tester_card_html(_lang(), tester_id), unsafe_allow_html=True)
            state["tester_card"] = True

        return result

    def beta_code(body, *args, **kwargs):
        text = body
        if isinstance(text, str) and "The QC Analyst Decision Gap" in text:
            text = text.replace("v0.3 · Bilingual Analytical Calibration", DISPLAY_VERSION)
            if f"Founding Beta Tester: {tester_id}" not in text:
                text = text.rstrip() + _share_suffix(_lang(), tester_id)
        return base_code(text, *args, **kwargs)

    def beta_button(label, *args, **kwargs):
        display_label = label
        if label == "ابدأ Expert Calibration ←":
            display_label = "ابدأ Founding Beta Calibration ←"
        elif label == "Start Expert Calibration →":
            display_label = "Start Founding Beta Calibration →"
        return base_button(display_label, *args, **kwargs)

    def beta_page_link(page, *args, **kwargs):
        label = kwargs.get("label")
        if label == "🧪 عندك مشكلة HPLC الآن؟ افتح مساعد يحيى للتحقيق":
            kwargs["label"] = "\u2067عندك مشكلة في \u2066HPLC\u2069؟ افتح مساعد يحيى للتحقيق الآن 🧪\u2069"
        elif label == "🧪 Have an HPLC problem now? Open Yahia Investigation Assistant":
            kwargs["label"] = "\u2066🧪 Have an HPLC problem? Open Yahia HPLC Investigation Assistant\u2069"
        return base_page_link(page, *args, **kwargs)

    st.markdown = beta_markdown
    st.code = beta_code
    st.button = beta_button
    st.page_link = beta_page_link
    try:
        run_assessment_page()
    finally:
        st.markdown = base_markdown
        st.code = base_code
        st.button = base_button
        st.page_link = base_page_link
