import os
from pathlib import Path

import streamlit as st
from openai import OpenAI

APP_TITLE = "Yahia HPLC Investigation Assistant"
TAGLINE = "DON'T GUESS. FOLLOW THE EVIDENCE."
MODEL = "gpt-5.6-terra"

st.set_page_config(
    page_title=APP_TITLE,
    page_icon="🧪",
    layout="centered",
    initial_sidebar_state="collapsed",
)


def load_core_prompt() -> str:
    return Path(__file__).with_name("core_prompt.txt").read_text(encoding="utf-8")


def get_api_key():
    try:
        key = st.secrets.get("OPENAI_API_KEY")
        if key:
            return key
    except Exception:
        pass
    return os.environ.get("OPENAI_API_KEY")


def format_api_error(exc, language: str) -> str:
    """Return a safe diagnostic error without exposing secrets."""
    status = getattr(exc, "status_code", None)
    code = getattr(exc, "code", None)
    body = getattr(exc, "body", None)

    if not code and isinstance(body, dict):
        error_body = body.get("error", body)
        if isinstance(error_body, dict):
            code = error_body.get("code") or error_body.get("type")

    code = str(code or exc.__class__.__name__)

    ar_messages = {
        "credit_balance_exhausted": "لا يوجد رصيد API متاح حاليًا. راجع Billing / Credits في OpenAI Platform.",
        "insufficient_quota": "لا توجد حصة أو رصيد كافٍ لإكمال الطلب. راجع Billing / Credits.",
        "organization_usage_limit_exceeded": "تم الوصول إلى حد الاستخدام المسموح للمؤسسة.",
        "organization_spend_limit_exceeded": "تم الوصول إلى حد الإنفاق المحدد للمؤسسة.",
        "project_spend_limit_exceeded": "تم الوصول إلى حد الإنفاق المحدد للمشروع.",
        "model_not_found": "النموذج المحدد غير متاح لهذا المشروع أو الحساب.",
        "invalid_api_key": "مفتاح الـAPI غير صالح أو لم يعد فعالًا.",
        "rate_limit_exceeded": "تم الوصول مؤقتًا إلى حد معدل الطلبات. حاول بعد قليل.",
    }
    en_messages = {
        "credit_balance_exhausted": "No API credit is currently available. Check Billing / Credits in OpenAI Platform.",
        "insufficient_quota": "There is not enough quota or credit to complete the request. Check Billing / Credits.",
        "organization_usage_limit_exceeded": "The organization usage limit has been reached.",
        "organization_spend_limit_exceeded": "The organization spend limit has been reached.",
        "project_spend_limit_exceeded": "The project spend limit has been reached.",
        "model_not_found": "The selected model is not available to this project or account.",
        "invalid_api_key": "The API key is invalid or no longer active.",
        "rate_limit_exceeded": "The request rate limit was reached. Try again shortly.",
    }

    if language == "ar":
        explanation = ar_messages.get(code, "تعذر إكمال طلب الـAPI. استخدم رمز الخطأ أدناه لتحديد السبب.")
        result = f"{explanation}\n\n**Error code:** `{code}`"
        if status:
            result += f"\n\n**HTTP status:** `{status}`"
        return result

    explanation = en_messages.get(code, "The API request could not be completed. Use the error code below to identify the cause.")
    result = f"{explanation}\n\n**Error code:** `{code}`"
    if status:
        result += f"\n\n**HTTP status:** `{status}`"
    return result


CORE_PROMPT = load_core_prompt()
API_KEY = get_api_key()

LANG_OPTIONS = {
    "Auto — لغة المستخدم": "auto",
    "العربية": "ar",
    "English": "en",
}

if "ui_language_label" not in st.session_state:
    st.session_state.ui_language_label = "Auto — لغة المستخدم"

current_language_label = st.session_state.ui_language_label
language = LANG_OPTIONS[current_language_label]
is_ar = language == "ar"

st.markdown(
    """
    <style>
      .block-container {
        max-width: 820px;
        padding-top: 4.6rem;
        padding-bottom: 4.5rem;
      }

      .hero-card {
        position: relative;
        overflow: hidden;
        padding: 1.35rem;
        margin: 0 0 1.1rem 0;
        border-radius: 22px;
        background: linear-gradient(145deg, #07101f 0%, #101b2d 58%, #161a22 100%);
        border: 1px solid rgba(202, 167, 80, 0.48);
        box-shadow: 0 16px 36px rgba(2, 6, 23, 0.16);
        color: #f8fafc;
      }

      .hero-card:before {
        content: "";
        position: absolute;
        width: 170px;
        height: 170px;
        border-radius: 50%;
        top: -95px;
        right: -70px;
        background: radial-gradient(circle, rgba(202,167,80,.22) 0%, rgba(202,167,80,0) 72%);
        pointer-events: none;
      }

      .hero-eyebrow {
        font-size: .74rem;
        letter-spacing: .16em;
        text-transform: uppercase;
        color: #d6bd78;
        font-weight: 800;
        margin-bottom: .45rem;
      }

      .hero-title {
        font-size: 2rem;
        line-height: 1.12;
        font-weight: 850;
        margin: 0;
        color: #fff;
      }

      .hero-title-ar, .hero-ar, .hero-description-ar {
        direction: rtl;
        unicode-bidi: plaintext;
        text-align: right;
        letter-spacing: 0;
      }

      .hero-ar {
        font-size: 1.25rem;
        line-height: 1.45;
        font-weight: 750;
        margin: .38rem 0 .7rem 0;
        color: #e8edf5;
      }

      .ltr-term {
        direction: ltr;
        unicode-bidi: isolate;
        display: inline-block;
      }

      .hero-tagline {
        font-size: .92rem;
        line-height: 1.35;
        font-weight: 850;
        letter-spacing: .055em;
        color: #d6bd78;
        margin: .15rem 0 .65rem 0;
      }

      .hero-description {
        font-size: .9rem;
        line-height: 1.65;
        color: #cbd5e1;
        margin: 0 0 .85rem 0;
      }

      .hero-byline {
        font-size: .78rem;
        color: #9fb0c5;
        margin-bottom: .85rem;
      }

      .badge-row {
        display: flex;
        flex-wrap: wrap;
        gap: .45rem;
      }

      .hero-badge {
        display: inline-flex;
        align-items: center;
        padding: .34rem .62rem;
        border-radius: 999px;
        background: rgba(255,255,255,.07);
        border: 1px solid rgba(255,255,255,.11);
        color: #eef2f7;
        font-size: .72rem;
        font-weight: 700;
        white-space: nowrap;
      }

      .section-label {
        font-size: .77rem;
        font-weight: 800;
        letter-spacing: .06em;
        color: #6b7280;
        margin: .2rem 0 .2rem 0;
        text-transform: uppercase;
      }

      .section-label-ar {
        direction: rtl;
        text-align: right;
        letter-spacing: 0;
        text-transform: none;
      }

      .sidebar-note-ar {
        direction: rtl;
        text-align: right;
        background: #dcecff;
        border: 1px solid #c5ddf8;
        border-radius: 14px;
        padding: 1rem 1rem .9rem 1rem;
        color: #0b5f9d;
        line-height: 1.8;
        font-size: .94rem;
        margin: .65rem 0 1rem 0;
      }

      .sidebar-note-ar strong {
        color: #084d80;
      }

      .sidebar-list {
        margin: .45rem 0 0 0;
        padding: 0 1.15rem 0 0;
      }

      .sidebar-list li {
        margin: .14rem 0;
      }

      .small-note {font-size: .88rem; opacity: .78;}

      div[data-baseweb="select"] > div {
        border-radius: 14px;
      }

      @media (max-width: 640px) {
        .block-container {
          padding-left: 1rem;
          padding-right: 1rem;
          padding-top: 5.8rem;
        }
        .hero-card {
          border-radius: 19px;
          padding: 1.15rem 1.05rem;
        }
        .hero-title {
          font-size: 1.58rem;
          line-height: 1.22;
        }
        .hero-ar {
          font-size: 1.06rem;
          line-height: 1.5;
        }
        .hero-tagline {
          font-size: .80rem;
          letter-spacing: .035em;
        }
        .hero-description {
          font-size: .84rem;
          line-height: 1.7;
        }
        .hero-byline {
          font-size: .74rem;
        }
      }
    </style>
    """,
    unsafe_allow_html=True,
)

TEXT = {
    "en": {
        "setup": "Investigation Setup",
        "area": "Closest investigation area",
        "scope": "v0.4 scope",
        "notice": "Decision-support only. Formal GMP investigations must follow approved SOPs, QA requirements, and applicable regulations.",
        "new": "Start new investigation",
        "start": "Start with the observation — not your diagnosis.",
        "example_label": "Example case",
        "example": "Pressure was normally 180 bar. Today it was 310 bar after about 25 injections. Same method, column, flow, and mobile phase.",
        "guidance": "The assistant should separate facts from assumptions, identify the critical missing evidence, and choose the next test that best separates the hypotheses.",
        "input": "Describe the HPLC observation, or answer the last diagnostic question...",
        "spinner": "Following the evidence...",
        "no_text": "No text response was returned. Please try again.",
        "api_missing": "The app is not connected to the OpenAI API yet. Add OPENAI_API_KEY in Streamlit Secrets, then reboot the app.",
        "language": "Language / اللغة",
    },
    "ar": {
        "setup": "إعداد التحقيق",
        "area": "أقرب نوع للمشكلة",
        "scope": "نطاق v0.4",
        "new": "بدء تحقيق جديد",
        "start": "ابدأ بالملاحظة… وليس بالتشخيص.",
        "example_label": "مثال",
        "example": "كان الضغط المعتاد 180 bar. اليوم أصبح 310 bar بعد حوالي 25 injection. نفس الـmethod والـcolumn والـflow والـmobile phase.",
        "guidance": "المساعد يفصل بين الحقائق والافتراضات، يحدد أهم معلومة ناقصة، ثم يختار الاختبار التالي الذي يفرّق فعليًا بين الاحتمالات.",
        "input": "اكتب ملاحظة الـHPLC أو أجب عن آخر سؤال تشخيصي...",
        "spinner": "نتتبع الأدلة...",
        "no_text": "لم يتم إرجاع رد نصي. حاول مرة أخرى.",
        "api_missing": "التطبيق غير متصل بـOpenAI API حتى الآن. أضف OPENAI_API_KEY داخل Streamlit Secrets ثم أعد تشغيل التطبيق.",
        "language": "اللغة / Language",
    },
}

if language == "ar":
    T = TEXT["ar"]
    hero_title_html = '🧪 مساعد يحيى لتحقيق <span class="ltr-term">HPLC</span>'
    hero_secondary_html = ""
    hero_description_html = 'دعم اتخاذ القرار والتحقيق في مشكلات <span class="ltr-term">HPLC</span> داخل معامل الرقابة الدوائية، بناءً على الأدلة.'
    title_class = "hero-title hero-title-ar"
    description_class = "hero-description hero-description-ar"
    language_label_html = '<div class="section-label section-label-ar">اختر اللغة</div>'
elif language == "en":
    T = TEXT["en"]
    hero_title_html = "🧪 Yahia HPLC Investigation Assistant"
    hero_secondary_html = ""
    hero_description_html = "Evidence-based HPLC troubleshooting & analytical decision support for Pharmaceutical QC"
    title_class = "hero-title"
    description_class = "hero-description"
    language_label_html = '<div class="section-label">Choose your language</div>'
else:
    T = TEXT["en"]
    hero_title_html = "🧪 Yahia HPLC Investigation Assistant"
    hero_secondary_html = '<div class="hero-ar">مساعد يحيى لتحقيق <span class="ltr-term">HPLC</span></div>'
    hero_description_html = 'Evidence-based HPLC troubleshooting & analytical decision support<br><span dir="rtl" style="display:block;text-align:right;margin-top:.3rem;">دعم اتخاذ القرار والتحقيق في مشكلات <span class="ltr-term">HPLC</span> داخل معامل الرقابة الدوائية، بناءً على الأدلة.</span>'
    title_class = "hero-title"
    description_class = "hero-description"
    language_label_html = '<div class="section-label">Choose your language · اختر اللغة</div>'

st.markdown(
    f"""
    <div class="hero-card">
      <div class="hero-eyebrow">Pharmaceutical QC · Analytical Decision Support</div>
      <div class="{title_class}">{hero_title_html}</div>
      {hero_secondary_html}
      <div class="hero-tagline">{TAGLINE}</div>
      <div class="{description_class}">{hero_description_html}</div>
      <div class="hero-byline">Yahia Abdelhalim · Pharmaceutical QC Expert</div>
      <div class="badge-row">
        <span class="hero-badge">Evidence-Driven</span>
        <span class="hero-badge">Investigation-First</span>
        <span class="hero-badge">Arabic + English</span>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown(language_label_html, unsafe_allow_html=True)
st.selectbox(
    T["language"],
    list(LANG_OPTIONS.keys()),
    index=list(LANG_OPTIONS.keys()).index(current_language_label),
    key="ui_language_label",
    label_visibility="collapsed",
)

with st.sidebar:
    st.header(T["setup"])
    area = st.selectbox(
        T["area"],
        ["Auto-detect", "Pressure", "Retention Time", "Peak Shape", "Baseline", "Carryover / Ghost Peaks"],
    )
    st.markdown("---")
    st.markdown(f"**{T['scope']}**")
    st.markdown("Pressure · RT · Peak Shape · Baseline · Carryover/Ghost Peaks")

    if language == "ar":
        st.markdown(
            """
            <div class="sidebar-note-ar">
              <strong>الأداة تدعم القرار، ولا تستبدل إجراءات المعمل المعتمدة.</strong><br>
              أي تحقيق رسمي ضمن <span class="ltr-term">GMP</span> يجب أن يلتزم بـ:
              <ul class="sidebar-list">
                <li><span class="ltr-term">SOP</span> المعتمد</li>
                <li>متطلبات <span class="ltr-term">QA</span></li>
                <li>اللوائح والإجراءات المعمول بها</li>
              </ul>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.info(TEXT["en"]["notice"])

    if st.button(T["new"], use_container_width=True):
        st.session_state.messages = []
        st.rerun()

if not API_KEY:
    st.error(T["api_missing"])
    st.stop()

client = OpenAI(api_key=API_KEY)

if "messages" not in st.session_state:
    st.session_state.messages = []

if not st.session_state.messages:
    if is_ar:
        st.markdown(
            f"""
            <div dir="rtl" style="text-align:right">
              <h3>{T['start']}</h3>
              <strong>{T['example_label']}</strong>
              <blockquote>{T['example']}</blockquote>
              {T['guidance']}
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f"""
### {T['start']}

**{T['example_label']}**  
> {T['example']}

{T['guidance']}
            """
        )

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

user_input = st.chat_input(T["input"])

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    if language == "ar":
        language_instruction = (
            "Respond in clear professional Arabic. Keep standard HPLC/QC technical terms in English when that is more precise or natural. "
            "Do not translate technical terms into awkward Arabic equivalents."
        )
    elif language == "en":
        language_instruction = "Respond in clear professional English."
    else:
        language_instruction = (
            "Respond in the same primary language as the user's latest message. "
            "If Arabic, use clear professional Arabic while preserving standard HPLC/QC technical terms in English where useful. "
            "If English, respond in English. Do not switch languages unexpectedly."
        )

    instructions = (
        CORE_PROMPT
        + f"\n\nCURRENT UI INVESTIGATION AREA: {area}\n"
        + "Treat this selected area only as a hint. If the evidence points to another area, say so.\n"
        + f"LANGUAGE BEHAVIOR: {language_instruction}"
    )

    api_history = [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]

    with st.chat_message("assistant"):
        with st.spinner(T["spinner"]):
            try:
                response = client.responses.create(
                    model=MODEL,
                    instructions=instructions,
                    input=api_history,
                )
                answer = response.output_text.strip()
                if not answer:
                    answer = T["no_text"]
            except Exception as exc:
                answer = format_api_error(exc, language)
            st.markdown(answer)

    st.session_state.messages.append({"role": "assistant", "content": answer})

st.markdown("---")
st.markdown(
    '<div class="small-note">v0.4 · Yahia HPLC Investigation Assistant · Bilingual Pharmaceutical QC decision support</div>',
    unsafe_allow_html=True,
)
