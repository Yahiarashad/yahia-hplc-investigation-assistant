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
      .block-container {max-width: 820px; padding-top: 1.15rem; padding-bottom: 4rem;}
      .brand-title {
        font-size: 2rem;
        line-height: 1.12;
        font-weight: 800;
        margin: 0 0 .15rem 0;
        word-break: normal;
        overflow-wrap: normal;
      }
      .brand-ar {
        direction: rtl;
        text-align: left;
        font-size: 1.35rem;
        line-height: 1.3;
        font-weight: 700;
        margin: .15rem 0 .65rem 0;
      }
      .tagline {font-weight: 800; letter-spacing: .04em; margin: .35rem 0 .8rem 0;}
      .small-note {font-size: .88rem; opacity: .78;}
      .arabic-note {direction: rtl; text-align: right;}
      .language-spacer {height: .35rem;}
      @media (max-width: 640px) {
        .block-container {padding-left: 1rem; padding-right: 1rem; padding-top: 1rem;}
        .brand-title {font-size: 1.68rem; line-height: 1.15;}
        .brand-ar {font-size: 1.14rem; text-align: left;}
        .tagline {font-size: .98rem; letter-spacing: .025em;}
      }
    </style>
    """,
    unsafe_allow_html=True,
)

TEXT = {
    "en": {
        "title": "🧪 Yahia HPLC Investigation Assistant",
        "subtitle": "Evidence-based HPLC troubleshooting & analytical decision support for Pharmaceutical QC",
        "setup": "Investigation Setup",
        "area": "Closest investigation area",
        "scope": "v0.3 scope",
        "notice": "Decision-support only. Formal GMP investigations must follow approved SOPs, QA requirements, and applicable regulations.",
        "new": "Start new investigation",
        "start": "Start with the observation — not your diagnosis.",
        "example_label": "Example case",
        "example": "Pressure was normally 180 bar. Today it was 310 bar after about 25 injections. Same method, column, flow, and mobile phase.",
        "guidance": "The assistant should separate facts from assumptions, identify the critical missing evidence, and choose the next test that best separates the hypotheses.",
        "input": "Describe the HPLC observation, or answer the last diagnostic question...",
        "spinner": "Following the evidence...",
        "api_error": "I couldn't complete the API request. Please verify the API key, project billing/credits, and model access, then try again.",
        "no_text": "No text response was returned. Please try again.",
        "api_missing": "The app is not connected to the OpenAI API yet. Add OPENAI_API_KEY in Streamlit Secrets, then reboot the app.",
    },
    "ar": {
        "title": "🧪 مساعد يحيى لتحقيقات HPLC",
        "subtitle": "دعم اتخاذ القرار والتحقيق في مشكلات HPLC داخل معامل الرقابة الدوائية — بناءً على الأدلة",
        "setup": "إعداد التحقيق",
        "area": "أقرب نوع للمشكلة",
        "scope": "نطاق v0.3",
        "notice": "الأداة تدعم القرار ولا تستبدل إجراءات المعمل المعتمدة. أي تحقيق GMP رسمي يجب أن يتبع الـSOP ومتطلبات QA واللوائح المعمول بها.",
        "new": "بدء تحقيق جديد",
        "start": "ابدأ بالملاحظة… وليس بالتشخيص.",
        "example_label": "مثال",
        "example": "كان الضغط المعتاد 180 bar. اليوم أصبح 310 bar بعد حوالي 25 injection. نفس الـmethod والـcolumn والـflow والـmobile phase.",
        "guidance": "المساعد يجب أن يفصل بين الحقائق والافتراضات، يحدد أهم معلومة ناقصة، ثم يختار الاختبار التالي الذي يفرّق فعليًا بين الاحتمالات.",
        "input": "اكتب ملاحظة الـHPLC أو أجب عن آخر سؤال تشخيصي...",
        "spinner": "نتتبع الأدلة...",
        "api_error": "تعذر إكمال طلب الـAPI. راجع المفتاح، الرصيد/الفوترة، وصلاحية النموذج ثم حاول مرة أخرى.",
        "no_text": "لم يتم إرجاع رد نصي. حاول مرة أخرى.",
        "api_missing": "التطبيق غير متصل بـOpenAI API حتى الآن. أضف OPENAI_API_KEY داخل Streamlit Secrets ثم أعد تشغيل التطبيق.",
    },
}

if language == "auto":
    T = TEXT["en"]
    main_title = "🧪 Yahia HPLC Investigation Assistant"
    secondary_title = "مساعد تحقيقات HPLC"
    display_subtitle = "Evidence-based HPLC troubleshooting & analytical decision support | تحقيق وتحليل قائم على الأدلة"
elif language == "ar":
    T = TEXT["ar"]
    main_title = T["title"]
    secondary_title = ""
    display_subtitle = T["subtitle"]
else:
    T = TEXT["en"]
    main_title = T["title"]
    secondary_title = ""
    display_subtitle = T["subtitle"]

st.markdown(f'<div class="brand-title">{main_title}</div>', unsafe_allow_html=True)
if secondary_title:
    st.markdown(f'<div class="brand-ar">{secondary_title}</div>', unsafe_allow_html=True)
st.markdown(f'<div class="tagline">{TAGLINE}</div>', unsafe_allow_html=True)
if is_ar:
    st.markdown(f'<div class="arabic-note">{display_subtitle}</div>', unsafe_allow_html=True)
else:
    st.caption(display_subtitle)

st.markdown('<div class="language-spacer"></div>', unsafe_allow_html=True)
language_label = st.selectbox(
    "Language / اللغة",
    list(LANG_OPTIONS.keys()),
    index=list(LANG_OPTIONS.keys()).index(current_language_label),
    key="ui_language_label",
)

with st.sidebar:
    st.header(T["setup"])
    area = st.selectbox(
        T["area"],
        [
            "Auto-detect",
            "Pressure",
            "Retention Time",
            "Peak Shape",
            "Baseline",
            "Carryover / Ghost Peaks",
        ],
    )
    st.markdown("---")
    st.markdown(f"**{T['scope']}**")
    st.markdown("Pressure · RT · Peak Shape · Baseline · Carryover/Ghost Peaks")
    st.info(T["notice"])
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

    api_history = [
        {"role": m["role"], "content": m["content"]}
        for m in st.session_state.messages
    ]

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
            except Exception:
                answer = T["api_error"]
            st.markdown(answer)

    st.session_state.messages.append({"role": "assistant", "content": answer})

st.markdown("---")
footer = "v0.3 · Yahia HPLC Investigation Assistant · Bilingual Pharmaceutical QC decision support"
st.markdown(f'<div class="small-note">{footer}</div>', unsafe_allow_html=True)
