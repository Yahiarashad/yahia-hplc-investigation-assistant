import os
import re
import sqlite3
import uuid
from pathlib import Path

import streamlit as st
from openai import OpenAI

from evidence_engine import format_evidence_context, retrieve_evidence

APP_TITLE = "Yahia HPLC Investigation Assistant"
TAGLINE = "DON'T GUESS. FOLLOW THE EVIDENCE."
MODEL = "gpt-5.6-terra"
APP_VERSION = "v0.9"
DB_PATH = Path("/tmp/yahia_hplc_investigations.db")

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


def contains_arabic(text: str) -> bool:
    return bool(re.search(r"[\u0600-\u06FF]", text or ""))


def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS messages (
                case_id TEXT NOT NULL,
                seq INTEGER NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                PRIMARY KEY (case_id, seq)
            )
            """
        )
        conn.commit()


def load_messages(case_id: str):
    with sqlite3.connect(DB_PATH) as conn:
        rows = conn.execute(
            "SELECT role, content FROM messages WHERE case_id = ? ORDER BY seq",
            (case_id,),
        ).fetchall()
    return [{"role": role, "content": content} for role, content in rows]


def save_message(case_id: str, role: str, content: str):
    with sqlite3.connect(DB_PATH) as conn:
        row = conn.execute(
            "SELECT COALESCE(MAX(seq), 0) FROM messages WHERE case_id = ?",
            (case_id,),
        ).fetchone()
        next_seq = int(row[0]) + 1
        conn.execute(
            "INSERT INTO messages (case_id, seq, role, content) VALUES (?, ?, ?, ?)",
            (case_id, next_seq, role, content),
        )
        conn.commit()


def get_case_id() -> str:
    raw = st.query_params.get("case")
    if isinstance(raw, list):
        raw = raw[0] if raw else None
    if isinstance(raw, str) and re.fullmatch(r"[A-Za-z0-9_-]{8,64}", raw):
        return raw
    new_id = uuid.uuid4().hex[:16]
    st.query_params["case"] = new_id
    return new_id


def format_api_error(exc, language: str) -> str:
    status = getattr(exc, "status_code", None)
    code = getattr(exc, "code", None)
    body = getattr(exc, "body", None)

    if not code and isinstance(body, dict):
        error_body = body.get("error", body)
        if isinstance(error_body, dict):
            code = error_body.get("code") or error_body.get("type")

    code = str(code or exc.__class__.__name__)

    ar_messages = {
        "credit_balance_exhausted": "لا يوجد رصيد متاح لواجهة OpenAI API حاليًا. راجع صفحة الفوترة والرصيد في OpenAI Platform.",
        "insufficient_quota": "لا توجد حصة أو رصيد كافٍ لإكمال الطلب. راجع صفحة الفوترة والرصيد.",
        "organization_usage_limit_exceeded": "تم الوصول إلى حد الاستخدام المسموح للمؤسسة.",
        "organization_spend_limit_exceeded": "تم الوصول إلى حد الإنفاق المحدد للمؤسسة.",
        "project_spend_limit_exceeded": "تم الوصول إلى حد الإنفاق المحدد للمشروع.",
        "model_not_found": "النموذج المحدد غير متاح لهذا المشروع أو الحساب.",
        "invalid_api_key": "مفتاح API غير صالح أو لم يعد فعالًا.",
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

    messages = ar_messages if language == "ar" else en_messages
    fallback = (
        "تعذر إكمال طلب API. استخدم رمز الخطأ أدناه لتحديد السبب."
        if language == "ar"
        else "The API request could not be completed. Use the error code below to identify the cause."
    )
    explanation = messages.get(code, fallback)
    code_label = "رمز الخطأ" if language == "ar" else "Error code"
    status_label = "حالة HTTP" if language == "ar" else "HTTP status"
    result = f"{explanation}\n\n**{code_label}:** `{code}`"
    if status:
        result += f"\n\n**{status_label}:** `{status}`"
    return result


init_db()
CORE_PROMPT = load_core_prompt()
API_KEY = get_api_key()
CASE_ID = get_case_id()

if st.session_state.get("case_id") != CASE_ID:
    st.session_state.case_id = CASE_ID
    st.session_state.messages = load_messages(CASE_ID)
elif "messages" not in st.session_state:
    st.session_state.messages = load_messages(CASE_ID)

LANG_OPTIONS = {
    "Auto — لغة المستخدم": "auto",
    "العربية": "ar",
    "English": "en",
}
LANG_LABEL_BY_CODE = {value: key for key, value in LANG_OPTIONS.items()}

query_lang = st.query_params.get("lang")
if isinstance(query_lang, list):
    query_lang = query_lang[0] if query_lang else None

if "ui_language_label" not in st.session_state:
    st.session_state.ui_language_label = LANG_LABEL_BY_CODE.get(query_lang, "Auto — لغة المستخدم")

current_language_label = st.session_state.ui_language_label
language_mode = LANG_OPTIONS[current_language_label]

last_user_message = next(
    (m["content"] for m in reversed(st.session_state.messages) if m["role"] == "user"),
    "",
)
if language_mode == "auto":
    effective_language = "ar" if contains_arabic(last_user_message) else "en"
else:
    effective_language = language_mode

is_ar = effective_language == "ar"

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
      .welcome-card {
        margin: 1rem 0 .7rem;
        padding: 1.05rem 1.1rem;
        border-radius: 18px;
        border: 1px solid rgba(202,167,80,.58);
        background: linear-gradient(145deg,#fffaf0,#ffffff);
        box-shadow: 0 8px 24px rgba(15,23,42,.05);
      }
      .welcome-card-ar {
        direction: rtl;
        text-align: right;
        unicode-bidi: plaintext;
      }
      .welcome-kicker {
        color: #9a7a26;
        font-size: .76rem;
        font-weight: 900;
        letter-spacing: .05em;
        margin-bottom: .22rem;
      }
      .welcome-title {
        color: #111827;
        font-size: 1.24rem;
        font-weight: 900;
        line-height: 1.5;
        margin-bottom: .35rem;
      }
      .welcome-copy {
        color: #556274;
        font-size: .91rem;
        line-height: 1.75;
      }
      .start-card {
        margin: .85rem 0;
        padding: 1.05rem 1.1rem;
        border-radius: 18px;
        border: 1px solid #d8e2ee;
        background: linear-gradient(145deg,#f8fbff,#ffffff);
        box-shadow: 0 8px 24px rgba(15,23,42,.05);
      }
      .start-card-ar {
        direction: rtl;
        text-align: right;
        unicode-bidi: plaintext;
      }
      .start-kicker {
        color: #9a7a26;
        font-size: .76rem;
        font-weight: 900;
        letter-spacing: .05em;
        margin-bottom: .2rem;
      }
      .start-title {
        color: #111827;
        font-size: 1.18rem;
        font-weight: 900;
        line-height: 1.45;
        margin-bottom: .35rem;
      }
      .start-copy {
        color: #556274;
        font-size: .91rem;
        line-height: 1.75;
      }
      .start-grid {
        display: grid;
        grid-template-columns: repeat(3, minmax(0,1fr));
        gap: .55rem;
        margin-top: .85rem;
      }
      .start-item {
        border-radius: 14px;
        border: 1px solid #e2e8f0;
        background: #fff;
        padding: .72rem .78rem;
        color: #4b5563;
        font-size: .79rem;
        line-height: 1.55;
      }
      .start-item strong {
        display: block;
        color: #172033;
        margin-bottom: .22rem;
        font-size: .82rem;
      }
      .guide-note {
        color: #6b7280;
        font-size: .82rem;
        line-height: 1.6;
      }
      .sidebar-note-ar {
        direction: rtl;
        unicode-bidi: plaintext;
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
      .sidebar-note-ar strong { color: #084d80; }
      .sidebar-list { margin: .45rem 0 0 0; padding: 0 1.15rem 0 0; }
      .sidebar-list li { margin: .14rem 0; }
      .small-note { font-size: .88rem; opacity: .78; }
      div[data-baseweb="select"] > div { border-radius: 14px; }
      [data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] { unicode-bidi: plaintext; }
      [data-testid="stChatMessage"] code { direction: ltr; unicode-bidi: isolate; }
      @media (max-width: 640px) {
        .block-container {
          padding-left: 1rem;
          padding-right: 1rem;
          padding-top: 5.8rem;
        }
        .hero-card { border-radius: 19px; padding: 1.15rem 1.05rem; }
        .hero-title { font-size: 1.58rem; line-height: 1.22; }
        .hero-ar { font-size: 1.06rem; line-height: 1.5; }
        .hero-tagline { font-size: .80rem; letter-spacing: .035em; }
        .hero-description { font-size: .84rem; line-height: 1.7; }
        .hero-byline { font-size: .74rem; }
        .welcome-title { font-size: 1.10rem; }
        .start-grid { grid-template-columns: 1fr; }
        .start-title { font-size: 1.06rem; }
      }
    </style>
    """,
    unsafe_allow_html=True,
)

if is_ar:
    st.markdown(
        """
        <style>
          [data-testid="stChatMessage"] [data-testid="stMarkdownContainer"],
          [data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] p,
          [data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] li,
          [data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] h1,
          [data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] h2,
          [data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] h3,
          [data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] h4 {
            direction: rtl;
            text-align: right;
            unicode-bidi: plaintext;
          }
          [data-testid="stChatInput"] textarea,
          [data-testid="stChatInput"] textarea::placeholder {
            direction: rtl;
            text-align: right;
            unicode-bidi: plaintext;
          }
          [data-testid="stSidebar"] { direction: rtl; text-align: right; }
          [data-testid="stExpander"] { direction: rtl; text-align: right; }
        </style>
        """,
        unsafe_allow_html=True,
    )

TEXT = {
    "en": {
        "setup": "Investigation Setup",
        "area": "Closest investigation area",
        "scope": f"{APP_VERSION} scope",
        "new": "Start new investigation",
        "start": "Start with the observation — not your diagnosis.",
        "example_label": "Example case",
        "example": "Pressure was normally 180 bar. Today it was 310 bar after about 25 injections. Same method, column, flow, and mobile phase.",
        "guidance": "The assistant separates facts from assumptions, identifies the critical missing evidence, and selects the next test that best separates the hypotheses.",
        "input": "Describe the problem in detail: expected behavior, what actually happened, what changed or stayed the same, and any available evidence or results...",
        "spinner": "Following the evidence...",
        "no_text": "No text response was returned. Please try again.",
        "api_missing": "The app is not connected to the OpenAI API yet. Add OPENAI_API_KEY in Streamlit Secrets, then reboot the app.",
        "language": "Language / اللغة",
        "autosave": "Auto-save is on. Refreshing this page will restore this investigation.",
        "case": "Case",
        "evidence_on": "Verified Evidence Engine: ON",
        "guide": "📘 How to use Yahia HPLC Investigation Assistant",
    },
    "ar": {
        "setup": "إعداد التحقيق",
        "area": "أقرب نوع للمشكلة",
        "scope": f"نطاق {APP_VERSION}",
        "new": "بدء تحقيق جديد",
        "start": "ابدأ بالملاحظة، وليس بالتشخيص.",
        "example_label": "مثال",
        "example": "كان ضغط النظام المعتاد 180 bar. اليوم وصل إلى 310 bar بعد نحو 25 حقنة. طريقة التحليل والعمود ومعدل التدفق والطور المتحرك كما هي.",
        "guidance": "يفصل المساعد بين الحقائق والافتراضات، ويحدد أهم معلومة ناقصة، ثم يختار الاختبار التالي الذي يفرّق فعليًا بين الاحتمالات.",
        "input": "اكتب المشكلة بالتفصيل: ما المتوقع، ماذا حدث فعليًا، ما الذي تغيّر أو ظل ثابتًا، وأي نتائج أو أدلة متاحة...",
        "spinner": "نتتبع الأدلة...",
        "no_text": "لم يتم إرجاع رد نصي. حاول مرة أخرى.",
        "api_missing": "التطبيق غير متصل بواجهة OpenAI API حتى الآن. أضف المفتاح داخل Streamlit Secrets ثم أعد تشغيل التطبيق.",
        "language": "اللغة / Language",
        "autosave": "الحفظ التلقائي مفعّل. تحديث الصفحة سيعيد هذا التحقيق.",
        "case": "رقم التحقيق",
        "evidence_on": "محرك الأدلة الموثقة: مفعّل",
        "guide": "📘 دليل استخدام مساعد يحيى للتحقيق في HPLC",
    },
}
T = TEXT[effective_language]

if is_ar:
    hero_title_html = '🧪 مساعد يحيى لتحقيق <span class="ltr-term">HPLC</span>'
    hero_secondary_html = ""
    hero_description_html = 'دعم اتخاذ القرار والتحقيق في مشكلات <span class="ltr-term">HPLC</span> داخل معامل الرقابة الدوائية، بناءً على الأدلة.'
    title_class = "hero-title hero-title-ar"
    description_class = "hero-description hero-description-ar"
    language_label_html = '<div class="section-label section-label-ar">اختر اللغة</div>'
else:
    hero_title_html = "🧪 Yahia HPLC Investigation Assistant"
    hero_secondary_html = ""
    if language_mode == "auto":
        hero_secondary_html = '<div class="hero-ar">مساعد يحيى لتحقيق <span class="ltr-term">HPLC</span></div>'
    hero_description_html = "Evidence-based HPLC troubleshooting & analytical decision support for Pharmaceutical QC"
    title_class = "hero-title"
    description_class = "hero-description"
    language_label_html = (
        '<div class="section-label">Choose your language · اختر اللغة</div>'
        if language_mode == "auto"
        else '<div class="section-label">Choose your language</div>'
    )

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
        <span class="hero-badge">Verified Sources</span>
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

selected_language_code = LANG_OPTIONS[st.session_state.ui_language_label]
if st.query_params.get("lang") != selected_language_code:
    st.query_params["lang"] = selected_language_code

if is_ar:
    st.markdown(
        """
        <div class="welcome-card welcome-card-ar">
          <div class="welcome-kicker">أهلاً وسهلاً بك 👋</div>
          <div class="welcome-title">لا تقلق… مشكلتك هنحلها مع بعض خطوة بخطوة.</div>
          <div class="welcome-copy">اكتب اللي حصل بالتفصيل، ومساعد يحيى هيتتبع الأدلة معاك لحد ما نوصل لأقوى قرار ممكن — من غير تخمين.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
else:
    st.markdown(
        """
        <div class="welcome-card">
          <div class="welcome-kicker">WELCOME 👋</div>
          <div class="welcome-title">Don't worry — we'll work through your problem together, step by step.</div>
          <div class="welcome-copy">Describe exactly what happened. Yahia's assistant will follow the evidence with you and guide the investigation toward the strongest defensible next decision — without guessing.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

if is_ar:
    st.markdown(
        """
        <div class="start-card start-card-ar">
          <div class="start-kicker">ابدأ من هنا</div>
          <div class="start-title">اكتب مشكلة HPLC كما حدثت بالتفصيل — واترك التشخيص للمحقق.</div>
          <div class="start-copy">لا تحتاج إلى معرفة السبب قبل أن تبدأ. اكتب الوقائع المتاحة فقط، وكلما كانت الأرقام والسياق أوضح كانت الخطوة التالية أقوى.</div>
          <div class="start-grid">
            <div class="start-item"><strong>1 · ما المتوقع؟</strong>اذكر القيم أو الأداء المعتاد مثل RT، Resolution، Pressure أو SST.</div>
            <div class="start-item"><strong>2 · ماذا حدث فعليًا؟</strong>اكتب الملاحظة الحالية والأرقام وشكل القمة أو أي اختلاف واضح.</div>
            <div class="start-item"><strong>3 · ما السياق المتاح؟</strong>اذكر ما تغيّر أو ظل ثابتًا، وأي اختبار تم بالفعل والنتيجة التي أعطاها.</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
else:
    st.markdown(
        """
        <div class="start-card">
          <div class="start-kicker">START HERE</div>
          <div class="start-title">Describe the HPLC problem exactly as it happened — let the investigation determine the cause.</div>
          <div class="start-copy">You do not need a diagnosis before you start. Report the available facts; specific numbers and context make the next diagnostic step stronger.</div>
          <div class="start-grid">
            <div class="start-item"><strong>1 · Expected</strong>State the normal or specified behavior: RT, resolution, pressure, SST, or other relevant values.</div>
            <div class="start-item"><strong>2 · Observed</strong>Describe what actually happened, including numbers, peak behavior, or any visible change.</div>
            <div class="start-item"><strong>3 · Context</strong>State what changed or stayed the same and any test already performed with its result.</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with st.expander(T["guide"], expanded=False):
    if is_ar:
        st.markdown(
            """
### أفضل طريقة لاستخدام مساعد يحيى

1. **ابدأ بالملاحظة وليس بالسبب الذي تتوقعه.** بدلًا من «العمود تالف»، اكتب ماذا تغيّر فعلًا.
2. **استخدم أرقامًا كلما أمكن.** مثل زمن الاحتجاز، الضغط، الفصل، شكل القمة، نتائج SST أو مساحات القمم.
3. **اذكر آخر حالة ناجحة إن كانت معروفة.** وما الذي تغيّر منذ ذلك الوقت: جهاز، عمود، طور متحرك، تحضير، محلل، Sequence أو إعدادات.
4. **اذكر أي اختبار قمت به بالفعل ونتيجته.** لا تكتفِ بقول «جرّبت كل شيء»؛ النتيجة نفسها دليل.
5. **أجب عن أسئلة المساعد خطوة بخطوة.** لا تغيّر عدة متغيرات معًا إلا إذا كان الإجراء المعتمد يتطلب ذلك.
6. **احتفظ بالبيانات الأصلية.** أي تحقيق رسمي يجب أن يلتزم بـ SOP وQA ومتطلبات GMP المعتمدة.

**مثال لبداية قوية:**  
المتوقع: RT نحو 6 دقائق وResolution لا يقل عن 4.  
الحاصل: RT نحو 3 دقائق وResolution نحو 2 والقمة مشوهة.  
الثابت: نفس الطريقة والعمود ومعدل التدفق.  
ما تم فحصه: تم تحضير طورين متحركين مستقلين وظهرت نفس النتيجة.

<div class="guide-note">ليس مطلوبًا أن تكون كل المعلومات متاحة من البداية. اكتب ما تعرفه فقط، والمساعد سيحدد أهم معلومة ناقصة قبل الانتقال للحل.</div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            """
### Best way to use the assistant

1. **Start with the observation, not your suspected cause.** Instead of “the column is bad,” state what actually changed.
2. **Use numbers whenever possible.** Include retention time, pressure, resolution, peak shape, SST results, or peak areas.
3. **State the last-known-good condition when available.** Note anything that changed since then: instrument, column, mobile phase, preparation, analyst, sequence, or settings.
4. **Report any test already performed and its result.** The result itself is evidence.
5. **Answer the assistant one step at a time.** Avoid changing several variables together unless the approved procedure requires it.
6. **Preserve original data.** Formal investigations must follow approved SOPs, QA requirements, and GMP expectations.

**Example of a strong first message:**  
Expected: RT about 6 min and resolution at least 4.  
Observed: RT about 3 min, resolution about 2, and the main peak is distorted.  
Unchanged: same method, column, and flow rate.  
Already checked: two independently prepared mobile phases produced the same result.

<div class="guide-note">You do not need to know everything before starting. Report what you know; the assistant will identify the highest-value missing evidence before moving toward a solution.</div>
            """,
            unsafe_allow_html=True,
        )

AREA_EN = {
    "Auto-detect": "Auto-detect",
    "Pressure": "Pressure",
    "Retention Time": "Retention Time",
    "Peak Shape": "Peak Shape",
    "Baseline": "Baseline",
    "Carryover / Ghost Peaks": "Carryover / Ghost Peaks",
}
AREA_AR = {
    "تحديد تلقائي": "Auto-detect",
    "الضغط": "Pressure",
    "زمن الاحتجاز (RT)": "Retention Time",
    "شكل القمة": "Peak Shape",
    "خط الأساس": "Baseline",
    "التداخل من الحقن السابق / القمم الوهمية": "Carryover / Ghost Peaks",
}
area_options = AREA_AR if is_ar else AREA_EN

with st.sidebar:
    st.header(T["setup"])
    area_label = st.selectbox(T["area"], list(area_options.keys()))
    area = area_options[area_label]

    st.markdown("---")
    st.markdown(f"**{T['scope']}**")
    if is_ar:
        st.markdown("الضغط · زمن الاحتجاز · شكل القمة · خط الأساس · التداخل والقمم الوهمية")
    else:
        st.markdown("Pressure · RT · Peak Shape · Baseline · Carryover/Ghost Peaks")

    if is_ar:
        st.markdown(
            """
            <div class="sidebar-note-ar">
              <strong>الأداة تدعم القرار، ولا تستبدل إجراءات المعمل المعتمدة.</strong><br>
              أي تحقيق رسمي ضمن <span class="ltr-term">GMP</span> يجب أن يلتزم بـ:
              <ul class="sidebar-list">
                <li>إجراء العمل المعتمد (<span class="ltr-term">SOP</span>)</li>
                <li>متطلبات ضمان الجودة (<span class="ltr-term">QA</span>)</li>
                <li>اللوائح والإجراءات المعمول بها</li>
              </ul>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.info("Decision-support only. Formal GMP investigations must follow approved SOPs, QA requirements, and applicable regulations.")

    st.success(f"✓ {T['evidence_on']}")
    st.caption("Waters · Agilent · Shimadzu · Thermo Fisher · USP · FDA · ICH")
    st.caption(f"💾 {T['autosave']}")
    st.caption(f"{T['case']}: `{CASE_ID}`")

    if st.button(T["new"], use_container_width=True):
        new_case_id = uuid.uuid4().hex[:16]
        st.query_params["case"] = new_case_id
        st.session_state.case_id = new_case_id
        st.session_state.messages = []
        st.rerun()

if not API_KEY:
    st.error(T["api_missing"])
    st.stop()

client = OpenAI(api_key=API_KEY)

if not st.session_state.messages:
    if is_ar:
        st.markdown(
            f"""
            <div dir="rtl" style="text-align:right; unicode-bidi:plaintext; margin-top:.35rem;">
              <p><strong>{T['start']}</strong> {T['guidance']}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown(f"**{T['start']}** {T['guidance']}")

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

user_input = st.chat_input(T["input"])

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    save_message(CASE_ID, "user", user_input)

    with st.chat_message("user"):
        st.markdown(user_input)

    response_language = effective_language
    if language_mode == "auto":
        response_language = "ar" if contains_arabic(user_input) else "en"

    if response_language == "ar":
        language_instruction = (
            "Respond in natural professional Arabic. Begin headings and bullets in Arabic. "
            "Keep useful standard HPLC/QC abbreviations in English only when they improve precision, preferably in parentheses after the Arabic term. "
            "Avoid awkward mixed Arabic-English constructions such as Arabic definite articles attached to English terms. "
            "Keep paragraphs short and mobile-friendly."
        )
    else:
        language_instruction = "Respond in clear professional English. Keep the response concise and mobile-friendly."

    recent_user_context = "\n".join(
        m["content"]
        for m in st.session_state.messages[-12:]
        if m["role"] == "user"
    )
    evidence_cards = retrieve_evidence(recent_user_context, area=area, limit=4)
    evidence_context = format_evidence_context(evidence_cards)

    instructions = (
        CORE_PROMPT
        + f"\n\nCURRENT UI INVESTIGATION AREA: {area}\n"
        + "Treat this selected area only as a hint. If the evidence points to another area, say so.\n"
        + f"LANGUAGE BEHAVIOR: {language_instruction}\n\n"
        + evidence_context
    )

    api_history = [
        {"role": m["role"], "content": m["content"]}
        for m in st.session_state.messages
    ]

    with st.chat_message("assistant"):
        spinner_text = TEXT[response_language]["spinner"]
        with st.spinner(spinner_text):
            try:
                response = client.responses.create(
                    model=MODEL,
                    instructions=instructions,
                    input=api_history,
                )
                answer = response.output_text.strip()
                if not answer:
                    answer = TEXT[response_language]["no_text"]
                st.markdown(answer)
                st.session_state.messages.append({"role": "assistant", "content": answer})
                save_message(CASE_ID, "assistant", answer)
            except Exception as exc:
                answer = format_api_error(exc, response_language)
                st.markdown(answer)

st.markdown("---")
st.markdown(
    f'<div class="small-note">{APP_VERSION} · Yahia HPLC Investigation Assistant · Verified Evidence Engine · Evidence-first bilingual QC decision support</div>',
    unsafe_allow_html=True,
)
