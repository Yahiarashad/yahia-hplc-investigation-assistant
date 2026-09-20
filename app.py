import os
import re
import sqlite3
import uuid
from pathlib import Path

import streamlit as st
from openai import OpenAI

from beta_feedback import record_event, render_feedback_form
from evidence_engine import format_evidence_context, retrieve_evidence

APP_TITLE = "Yahia HPLC Investigation Assistant"
TAGLINE = "DON'T GUESS. FOLLOW THE EVIDENCE."
MODEL = "gpt-5.6-terra"
APP_VERSION = "v1.1"
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


def _assistant_turn_count(messages):
    return sum(1 for message in messages if message.get("role") == "assistant")


def _conclusion_detected(messages):
    last_answer = next(
        (message.get("content", "") for message in reversed(messages) if message.get("role") == "assistant"),
        "",
    )
    text = last_answer.casefold()
    markers = (
        "root cause confirmed",
        "root cause probable",
        "root cause not yet identified",
        "not yet identified",
        "السبب الجذري مؤكد",
        "السبب الجذري المرجح",
        "السبب الجذري محتمل",
        "لم يتم تحديد السبب الجذري",
        "السبب الجذري غير محدد",
    )
    return bool(last_answer) and any(marker.casefold() in text for marker in markers)

def _last_assistant_answer(messages):
    return next(
        (message.get("content", "") for message in reversed(messages) if message.get("role") == "assistant"),
        "",
    )


def _conclusion_type(messages):
    text = _last_assistant_answer(messages).casefold()
    if not text:
        return ""
    not_identified = ("root cause not yet identified", "not yet identified", "لم يتم تحديد السبب الجذري", "السبب الجذري غير محدد")
    confirmed = ("root cause confirmed", "السبب الجذري مؤكد")
    probable = ("root cause probable", "السبب الجذري المرجح", "السبب الجذري محتمل")
    if any(x.casefold() in text for x in not_identified):
        return "not_yet_identified"
    if any(x.casefold() in text for x in confirmed):
        return "confirmed"
    if any(x.casefold() in text for x in probable):
        return "probable"
    return ""


def _case_category(messages, selected_area="Auto-detect"):
    """Classify only the category label; never persist case text."""
    if selected_area and selected_area != "Auto-detect":
        return selected_area
    text = " ".join(
        m.get("content", "") for m in messages if m.get("role") == "user"
    ).casefold()
    rules = (
        ("Pressure", ("pressure", "bar", "psi", "ضغط")),
        ("Retention Time", ("retention time", "retention", " rt ", "زمن الاحتجاز", "زمن الاستبقاء")),
        ("Peak Shape", ("tailing", "fronting", "split peak", "peak shape", "broad peak", "شكل القمة", "تذييل", "قمة مشوه")),
        ("Baseline / Noise", ("baseline", "noise", "drift", "خط الأساس", "ضوضاء", "انحراف خط")),
        ("Carryover / Ghost Peaks", ("carryover", "ghost peak", "ghost peaks", "قمم وهم", "تداخل من الحقن")),
        ("Resolution / Separation", ("resolution", "separation", "co-elut", "فصل", "ريزوليوشن")),
        ("Injection / Autosampler", ("inject", "autosampler", "needle", "loop", "حقن", "اوتوسامبلر")),
        ("Pump / Flow", ("pump", "flow", "check valve", "seal", "مضخة", "معدل التدفق")),
        ("Detector", ("detector", "uv", "pda", "dad", "lamp", "كاشف")),
        ("Column", ("column", "guard", "عمود")),
        ("Mobile Phase", ("mobile phase", "buffer", "gradient", "طور متحرك", "بافر")),
    )
    for category, keywords in rules:
        if any(k in text for k in keywords):
            return category
    return "Other / Unclassified"


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
        "credit_balance_exhausted": "لا يوجد رصيد متاح لواجهة OpenAI API حاليًا. راجع صفحة الفوترة والرصيد.",
        "insufficient_quota": "لا توجد حصة أو رصيد كافٍ لإكمال الطلب. راجع صفحة الفوترة والرصيد.",
        "organization_usage_limit_exceeded": "تم الوصول إلى حد الاستخدام المسموح للمؤسسة.",
        "organization_spend_limit_exceeded": "تم الوصول إلى حد الإنفاق المحدد للمؤسسة.",
        "project_spend_limit_exceeded": "تم الوصول إلى حد الإنفاق المحدد للمشروع.",
        "model_not_found": "النموذج المحدد غير متاح لهذا المشروع أو الحساب.",
        "invalid_api_key": "مفتاح API غير صالح أو لم يعد فعالًا.",
        "rate_limit_exceeded": "تم الوصول مؤقتًا إلى حد معدل الطلبات. حاول بعد قليل.",
    }
    en_messages = {
        "credit_balance_exhausted": "No API credit is currently available. Check Billing / Credits.",
        "insufficient_quota": "There is not enough quota or credit to complete the request.",
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

if not st.session_state.get(f"_hplc_view_logged_{CASE_ID}"):
    record_event(CASE_ID, "hplc_assistant", "assistant_viewed", effective_language)
    st.session_state[f"_hplc_view_logged_{CASE_ID}"] = True

TEXT = {
    "en": {
        "setup": "Investigation Setup",
        "area": "Closest investigation area",
        "scope": f"{APP_VERSION} scope",
        "new": "Start new investigation",
        "input": "Describe the problem in detail: what was expected, what actually happened, what changed or stayed the same, and any evidence or test results...",
        "begin": "Start investigation →",
        "spinner": "Following the evidence...",
        "no_text": "No text response was returned. Please try again.",
        "api_missing": "The app is not connected to the OpenAI API yet. Add OPENAI_API_KEY in Streamlit Secrets, then reboot the app.",
        "language": "Language / اللغة",
        "autosave": "Auto-save is on. Refreshing this page will restore this investigation.",
        "case": "Case",
        "evidence_on": "Verified Evidence Engine: ON",
        "guide": "📘 How to use Yahia HPLC Investigation Assistant",
        "start_note": "Start with what you observed — not the diagnosis you suspect.",
        "finish": "I've finished this investigation — share feedback 💬",
    },
    "ar": {
        "setup": "إعداد التحقيق",
        "area": "أقرب نوع للمشكلة",
        "scope": f"نطاق {APP_VERSION}",
        "new": "بدء تحقيق جديد",
        "input": "اكتب المشكلة بالتفصيل: ما المتوقع؟ ماذا حدث فعليًا؟ ما الذي تغيّر أو ظل ثابتًا؟ وما النتائج أو الأدلة المتاحة؟",
        "begin": "ابدأ التحقيق الآن →",
        "spinner": "نتتبع الأدلة...",
        "no_text": "لم يتم إرجاع رد نصي. حاول مرة أخرى.",
        "api_missing": "التطبيق غير متصل بواجهة OpenAI API حتى الآن. أضف المفتاح داخل Streamlit Secrets ثم أعد تشغيل التطبيق.",
        "language": "اللغة / Language",
        "autosave": "الحفظ التلقائي مفعّل. تحديث الصفحة سيعيد هذا التحقيق.",
        "case": "رقم التحقيق",
        "evidence_on": "محرك الأدلة الموثقة: مفعّل",
        "guide": "📘 دليل استخدام مساعد يحيى للتحقيق في HPLC",
        "start_note": "ابدأ بما لاحظته فعليًا — وليس بالسبب الذي تتوقعه.",
        "finish": "أنهيت التحقيق — أرسل ملاحظتي 💬",
    },
}
T = TEXT[effective_language]

st.markdown(
    """
    <style>
      .block-container { max-width:820px; padding-top:4.8rem; padding-bottom:4.5rem; }
      .hero-card {
        position:relative; overflow:hidden; padding:1.3rem; margin:0 0 1rem 0;
        border-radius:22px; background:linear-gradient(145deg,#07101f 0%,#101b2d 58%,#161a22 100%);
        border:1px solid rgba(202,167,80,.48); box-shadow:0 16px 36px rgba(2,6,23,.16); color:#f8fafc;
      }
      .hero-card:before {
        content:""; position:absolute; width:170px; height:170px; border-radius:50%; top:-95px; right:-70px;
        background:radial-gradient(circle,rgba(202,167,80,.22) 0%,rgba(202,167,80,0) 72%);
      }
      .hero-eyebrow { font-size:.74rem; letter-spacing:.16em; text-transform:uppercase; color:#d6bd78; font-weight:800; margin-bottom:.45rem; }
      .hero-title { font-size:1.95rem; line-height:1.15; font-weight:850; color:#fff; }
      .hero-title-ar,.hero-description-ar { direction:rtl; unicode-bidi:plaintext; text-align:right; }
      .hero-tagline { font-size:.9rem; line-height:1.35; font-weight:850; letter-spacing:.045em; color:#d6bd78; margin:.55rem 0 .6rem; }
      .hero-description { font-size:.9rem; line-height:1.65; color:#cbd5e1; margin:0 0 .75rem; }
      .hero-byline { font-size:.78rem; color:#9fb0c5; margin-bottom:.78rem; }
      .badge-row { display:flex; flex-wrap:wrap; gap:.42rem; }
      .hero-badge { display:inline-flex; padding:.32rem .58rem; border-radius:999px; background:rgba(255,255,255,.07); border:1px solid rgba(255,255,255,.11); color:#eef2f7; font-size:.7rem; font-weight:700; }
      .ltr-term { direction:ltr; unicode-bidi:isolate; display:inline-block; }
      .section-label { font-size:.76rem; font-weight:800; color:#6b7280; margin:.15rem 0 .2rem; text-transform:uppercase; letter-spacing:.05em; }
      .section-label-ar { direction:rtl; text-align:right; text-transform:none; letter-spacing:0; }
      .welcome-card { margin:.9rem 0 .7rem; padding:1.05rem 1.1rem; border-radius:18px; border:1px solid rgba(202,167,80,.58); background:linear-gradient(145deg,#fffaf0,#ffffff); box-shadow:0 8px 24px rgba(15,23,42,.05); }
      .welcome-card-ar { direction:rtl; text-align:right; unicode-bidi:plaintext; }
      .welcome-kicker { color:#9a7a26; font-size:.77rem; font-weight:900; margin-bottom:.22rem; }
      .welcome-title { color:#111827; font-size:1.28rem; font-weight:900; line-height:1.48; margin-bottom:.3rem; }
      .welcome-copy { color:#556274; font-size:.91rem; line-height:1.72; }
      .prompt-label { margin:.9rem 0 .35rem; font-weight:900; color:#172033; font-size:1.02rem; }
      .prompt-label-ar { direction:rtl; text-align:right; }
      .quick-note { color:#6b7280; font-size:.8rem; line-height:1.55; margin:.25rem 0 .75rem; }
      .quick-note-ar { direction:rtl; text-align:right; }
      .start-card { margin:.9rem 0; padding:1rem 1.05rem; border-radius:18px; border:1px solid #d8e2ee; background:linear-gradient(145deg,#f8fbff,#ffffff); }
      .start-card-ar { direction:rtl; text-align:right; unicode-bidi:plaintext; }
      .start-kicker { color:#9a7a26; font-size:.75rem; font-weight:900; margin-bottom:.18rem; }
      .start-title { color:#111827; font-size:1.08rem; font-weight:900; line-height:1.45; }
      .start-grid { display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:.5rem; margin-top:.7rem; }
      .start-item { border-radius:14px; border:1px solid #e2e8f0; background:#fff; padding:.7rem .75rem; color:#4b5563; font-size:.79rem; line-height:1.5; }
      .start-item strong { display:block; color:#172033; margin-bottom:.18rem; font-size:.82rem; }
      .small-note { font-size:.82rem; opacity:.72; }
      .feedback-nudge { margin:1rem 0 .55rem; padding:.85rem 1rem; border-radius:16px; border:1px solid #dfc77c; background:#fffaf0; color:#374151; line-height:1.7; }
      .feedback-nudge-ar { direction:rtl; text-align:right; }
      div[data-baseweb="select"] > div { border-radius:14px; }
      [data-testid="stTextArea"] textarea { border-radius:16px !important; min-height:170px !important; }
      [data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] { unicode-bidi:plaintext; }
      [data-testid="stChatMessage"] code { direction:ltr; unicode-bidi:isolate; }
      @media (max-width:640px) {
        .block-container { padding-left:1rem; padding-right:1rem; padding-top:5.8rem; }
        .hero-card { border-radius:19px; padding:1.1rem 1rem; }
        .hero-title { font-size:1.55rem; }
        .hero-tagline { font-size:.79rem; }
        .hero-description { font-size:.84rem; }
        .welcome-title { font-size:1.12rem; }
        .start-grid { grid-template-columns:1fr; }
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
          [data-testid="stChatInput"] textarea,
          [data-testid="stChatInput"] textarea::placeholder,
          [data-testid="stTextArea"] textarea,
          [data-testid="stTextArea"] textarea::placeholder {
            direction:rtl; text-align:right; unicode-bidi:plaintext;
          }
          [data-testid="stSidebar"] { direction:rtl; text-align:right; }
          [data-testid="stExpander"] { direction:rtl; text-align:right; }
        </style>
        """,
        unsafe_allow_html=True,
    )

if is_ar:
    hero_title_html = '🧪 مساعد يحيى لتحقيق <span class="ltr-term">HPLC</span>'
    hero_description_html = 'دعم اتخاذ القرار والتحقيق في مشكلات <span class="ltr-term">HPLC</span> داخل معامل الرقابة الدوائية، بناءً على الأدلة.'
    title_class = "hero-title hero-title-ar"
    description_class = "hero-description hero-description-ar"
    language_label_html = '<div class="section-label section-label-ar">اختر اللغة</div>'
else:
    hero_title_html = "🧪 Yahia HPLC Investigation Assistant"
    hero_description_html = "Evidence-based HPLC troubleshooting & analytical decision support for Pharmaceutical QC"
    title_class = "hero-title"
    description_class = "hero-description"
    language_label_html = '<div class="section-label">Choose your language · اختر اللغة</div>' if language_mode == "auto" else '<div class="section-label">Choose your language</div>'

st.markdown(
    f"""
    <div class="hero-card">
      <div class="hero-eyebrow">Pharmaceutical QC · Analytical Decision Support</div>
      <div class="{title_class}">{hero_title_html}</div>
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
    st.caption("Pressure · RT · Peak Shape · Baseline · Carryover/Ghost Peaks")
    if is_ar:
        st.info("الأداة تدعم القرار ولا تستبدل SOP أو QA أو متطلبات GMP المعتمدة.")
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
user_input = None

if not st.session_state.messages:
    if is_ar:
        st.markdown(
            """
            <div class="welcome-card welcome-card-ar">
              <div class="welcome-kicker">أهلاً وسهلاً بك 👋</div>
              <div class="welcome-title">لا تقلق… مشكلتك هنحلها مع بعض خطوة بخطوة.</div>
              <div class="welcome-copy">اكتب اللي حصل بالتفصيل، ومساعد يحيى هيتتبع الأدلة معاك لحد ما نوصل لأقوى قرار ممكن — من غير تخمين.</div>
            </div>
            <div class="prompt-label prompt-label-ar">اكتب مشكلتك هنا 👇</div>
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
            <div class="prompt-label">Describe your problem here 👇</div>
            """,
            unsafe_allow_html=True,
        )

    with st.form("initial_case_form", clear_on_submit=False):
        initial_text = st.text_area(
            "Initial case",
            placeholder=T["input"],
            label_visibility="collapsed",
            height=180,
        )
        submitted = st.form_submit_button(T["begin"], use_container_width=True, type="primary")
        if submitted and initial_text.strip():
            user_input = initial_text.strip()

    if not user_input:
        note_class = "quick-note quick-note-ar" if is_ar else "quick-note"
        note_extra = "مش لازم تعرف السبب قبل ما تبدأ؛ اكتب فقط ما تعرفه." if is_ar else "You do not need to know the cause before you start."
        st.markdown(f'<div class="{note_class}">{T["start_note"]} {note_extra}</div>', unsafe_allow_html=True)

        if is_ar:
            st.markdown(
                """
                <div class="start-card start-card-ar">
                  <div class="start-kicker">لو محتار تكتب إيه</div>
                  <div class="start-title">ثلاث معلومات تجعل بداية التحقيق أقوى:</div>
                  <div class="start-grid">
                    <div class="start-item"><strong>1 · المتوقع</strong>RT أو Pressure أو Resolution أو SST المعتاد.</div>
                    <div class="start-item"><strong>2 · ما حدث</strong>الأرقام الحالية، شكل القمة، أو التغير الذي رأيته.</div>
                    <div class="start-item"><strong>3 · السياق</strong>ما تغيّر أو ظل ثابتًا وأي اختبار تم ونتيجته.</div>
                  </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                """
                <div class="start-card">
                  <div class="start-kicker">NOT SURE WHAT TO WRITE?</div>
                  <div class="start-title">Three details make the investigation much stronger:</div>
                  <div class="start-grid">
                    <div class="start-item"><strong>1 · Expected</strong>Normal RT, pressure, resolution, SST, or other target behavior.</div>
                    <div class="start-item"><strong>2 · Observed</strong>Current numbers, peak behavior, or the visible change.</div>
                    <div class="start-item"><strong>3 · Context</strong>What changed or stayed the same and any test already performed.</div>
                  </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with st.expander(T["guide"], expanded=False):
            if is_ar:
                st.markdown(
                    """
1. **ابدأ بالملاحظة وليس بالتشخيص.**
2. **استخدم أرقامًا كلما أمكن.**
3. **اذكر آخر حالة ناجحة إن كانت معروفة.**
4. **اذكر أي اختبار تم بالفعل والنتيجة التي أعطاها.**
5. **أجب خطوة بخطوة ولا تغيّر عدة متغيرات معًا دون مبرر.**
6. **احتفظ بالبيانات الأصلية والتزم بإجراءات SOP وQA وGMP المعتمدة.**

**مثال لبداية قوية:**  
المتوقع: RT نحو 6 دقائق وResolution لا يقل عن 4.  
الحاصل: RT نحو 3 دقائق وResolution نحو 2 والقمة مشوهة.  
الثابت: نفس الطريقة والعمود ومعدل التدفق.  
ما تم فحصه: تم تحضير طورين متحركين مستقلين وظهرت نفس النتيجة.
                    """
                )
            else:
                st.markdown(
                    """
1. **Start with the observation, not your suspected cause.**
2. **Use numbers whenever possible.**
3. **State the last-known-good condition when available.**
4. **Report any test already performed and its result.**
5. **Answer one step at a time; avoid changing several variables together without justification.**
6. **Preserve original data and follow approved SOP, QA, and GMP requirements.**

**Example of a strong first message:**  
Expected: RT about 6 min and resolution at least 4.  
Observed: RT about 3 min, resolution about 2, and the main peak is distorted.  
Unchanged: same method, column, and flow rate.  
Already checked: two independently prepared mobile phases produced the same result.
                    """
                )
else:
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    user_input = st.chat_input(T["input"])

if user_input:
    first_user_message = not any(message["role"] == "user" for message in st.session_state.messages)
    st.session_state.messages.append({"role": "user", "content": user_input})
    save_message(CASE_ID, "user", user_input)
    if first_user_message:
        record_event(CASE_ID, "hplc_assistant", "investigation_started", effective_language)

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
        with st.spinner(TEXT[response_language]["spinner"]):
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
                record_event(
                    CASE_ID,
                    "hplc_assistant",
                    "assistant_turn_completed",
                    response_language,
                    {"assistant_turn": _assistant_turn_count(st.session_state.messages)},
                )
            except Exception as exc:
                answer = format_api_error(exc, response_language)
                st.markdown(answer)

if st.session_state.messages:
    feedback_ready_key = f"_hplc_feedback_ready_{CASE_ID}"
    feedback_logged_key = f"_hplc_feedback_prompt_logged_{CASE_ID}"
    assistant_turns = _assistant_turn_count(st.session_state.messages)

    if _conclusion_detected(st.session_state.messages):
        st.session_state[feedback_ready_key] = True
        conclusion_key = f"_hplc_conclusion_logged_{CASE_ID}"
        conclusion_type = _conclusion_type(st.session_state.messages)
        case_category = _case_category(st.session_state.messages, area)
        if not st.session_state.get(conclusion_key):
            record_event(
                CASE_ID,
                "hplc_assistant",
                "investigation_conclusion",
                effective_language,
                {
                    "conclusion_type": conclusion_type or "unspecified",
                    "case_category": case_category,
                    "assistant_turns": assistant_turns,
                },
            )
            st.session_state[conclusion_key] = True
        if not st.session_state.get(feedback_logged_key):
            record_event(
                CASE_ID,
                "hplc_assistant",
                "feedback_prompted",
                effective_language,
                {
                    "trigger": "investigation_conclusion",
                    "assistant_turns": assistant_turns,
                    "conclusion_type": conclusion_type or "unspecified",
                    "case_category": case_category,
                },
            )
            st.session_state[feedback_logged_key] = True

    if not st.session_state.get(feedback_ready_key) and assistant_turns >= 2:
        nudge_class = "feedback-nudge feedback-nudge-ar" if is_ar else "feedback-nudge"
        nudge_text = (
            "لو وصلت للنقطة اللي كنت محتاجها، أنهِ التحقيق وسأظهر لك Feedback قصير لتحسين النسخة القادمة."
            if is_ar
            else "If you reached the decision you needed, finish the investigation and a short feedback form will open."
        )
        st.markdown(f'<div class="{nudge_class}">{nudge_text}</div>', unsafe_allow_html=True)
        if st.button(T["finish"], use_container_width=True, key=f"finish_investigation_{CASE_ID}"):
            st.session_state[feedback_ready_key] = True
            if not st.session_state.get(feedback_logged_key):
                record_event(
                    CASE_ID,
                    "hplc_assistant",
                    "feedback_prompted",
                    effective_language,
                    {"trigger": "user_finished", "assistant_turns": assistant_turns},
                )
                st.session_state[feedback_logged_key] = True
            st.rerun()

    resolution_key = f"_hplc_resolution_{CASE_ID}"
    resolution_logged_key = f"_hplc_resolution_logged_{CASE_ID}"
    if _conclusion_detected(st.session_state.messages) and not st.session_state.get(resolution_logged_key):
        if is_ar:
            st.markdown("### هل المشكلة اتحلت فعليًا بعد تنفيذ الإجراء؟")
            resolution_labels = {
                "نعم، اتحلت": "yes",
                "جزئيًا": "partial",
                "لا": "no",
                "لسه ما اختبرتش": "not_tested",
            }
        else:
            st.markdown("### Did the issue actually resolve after the action?")
            resolution_labels = {
                "Yes — resolved": "yes",
                "Partially": "partial",
                "No": "no",
                "Not tested yet": "not_tested",
            }
        resolution_choice = st.radio(
            "Resolution confirmation",
            list(resolution_labels.keys()),
            index=None,
            label_visibility="collapsed",
            key=resolution_key,
        )
        if resolution_choice and st.button(
            "تأكيد النتيجة" if is_ar else "Confirm outcome",
            use_container_width=True,
            key=f"confirm_resolution_{CASE_ID}",
        ):
            record_event(
                CASE_ID,
                "hplc_assistant",
                "resolution_confirmed",
                effective_language,
                {
                    "resolution_status": resolution_labels[resolution_choice],
                    "conclusion_type": _conclusion_type(st.session_state.messages) or "unspecified",
                    "case_category": _case_category(st.session_state.messages, area),
                    "assistant_turns": assistant_turns,
                },
            )
            st.session_state[resolution_logged_key] = True
            st.success("تم تسجيل النتيجة. شكرًا لك." if is_ar else "Outcome recorded. Thank you.")

    if st.session_state.get(feedback_ready_key):
        if is_ar:
            st.markdown(
                "<div class='feedback-nudge feedback-nudge-ar'><b>قبل ما تقفل التحقيق 👋</b><br>"
                "ملاحظتك دقيقة واحدة فقط، وبتدخل مباشرة في تطوير النسخة القادمة.</div>",
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                "<div class='feedback-nudge'><b>Before you close the investigation 👋</b><br>"
                "Your 60-second feedback directly helps shape the next release.</div>",
                unsafe_allow_html=True,
            )
        render_feedback_form(
            source="hplc_assistant",
            session_id=CASE_ID,
            language=effective_language,
            compact=False,
        )

    st.markdown("---")
    st.markdown(
        f'<div class="small-note">{APP_VERSION} · Yahia HPLC Investigation Assistant · Verified Evidence Engine · Evidence-first bilingual QC decision support</div>',
        unsafe_allow_html=True,
    )