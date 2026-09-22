import os
import re
import base64
import sqlite3
import tempfile
import time
import uuid
from pathlib import Path

import streamlit as st
from openai import OpenAI

from beta_feedback import record_event, render_feedback_form
from evidence_engine import format_evidence_context, retrieve_evidence

APP_TITLE = "Yahia HPLC Investigation Assistant"
TAGLINE = "DON'T GUESS. FOLLOW THE EVIDENCE."
MODEL = "gpt-5.6-terra"
TRANSCRIBE_MODEL = "gpt-4o-mini-transcribe"
TTS_MODEL = "gpt-4o-mini-tts"
TTS_VOICE = "alloy"
APP_VERSION = "v1.1"
DB_PATH = Path("/tmp/yahia_hplc_investigations.db")
LINKEDIN_URL = "https://www.linkedin.com/in/yahia-rashad-mohamed"
PORTRAIT_PATH = Path(__file__).with_name("assets") / "yahia_profile.png"

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

def portrait_data_uri():
    if not PORTRAIT_PATH.exists():
        return ""
    encoded = base64.b64encode(PORTRAIT_PATH.read_bytes()).decode("ascii")
    return f"data:image/png;base64,{encoded}"


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
        "السبب الجذري مؤكد",
        "السبب الجذري المرجح",
        "السبب الجذري محتمل",
    )
    return bool(last_answer) and any(marker.casefold() in text for marker in markers)

def _last_assistant_answer(messages):
    return next(
        (message.get("content", "") for message in reversed(messages) if message.get("role") == "assistant"),
        "",
    )


def _investigation_status(messages):
    last = _last_assistant_answer(messages)
    match = re.search(r"INVESTIGATION_STATUS\s*:\s*(INVESTIGATING|AWAITING_USER|AWAITING_TEST|PROBABLE|CONFIRMED)", last, re.I)
    return match.group(1).upper() if match else "INVESTIGATING"


def _display_answer(answer):
    return re.sub(
        r"\n?INVESTIGATION_STATUS\s*:\s*(?:INVESTIGATING|AWAITING_USER|AWAITING_TEST|PROBABLE|CONFIRMED)\s*$",
        "",
        answer or "",
        flags=re.I,
    ).strip()


def _resolution_check_ready(messages):
    return _investigation_status(messages) in ("PROBABLE", "CONFIRMED")


def _conclusion_type(messages):
    status = _investigation_status(messages)
    if status == "CONFIRMED":
        return "confirmed"
    if status == "PROBABLE":
        return "probable"
    text = _last_assistant_answer(messages).casefold()
    if any(x in text for x in ("root cause not yet identified", "not yet identified", "لم يتم تحديد السبب الجذري", "السبب الجذري غير محدد")):
        return "not_yet_identified"
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
        "your_turn": "Your turn — continue the investigation",
        "your_turn_copy": "Answer the question above or tell me the result of the requested check. You can type or use the microphone below.",
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
        "your_turn": "دورك الآن — كمّل التحقيق",
        "your_turn_copy": "جاوب على السؤال اللي فوق أو اكتب نتيجة الفحص المطلوب. تقدر تكتب أو تستخدم الميكروفون بالأسفل.",
    },
}
T = TEXT[effective_language]

st.markdown(
    """
    <style>
      .block-container { max-width:900px; padding-top:4.2rem; padding-bottom:4.5rem; }
      .brand-hero { position:relative; overflow:hidden; min-height:350px; border-radius:26px; padding:2rem 2rem 1.55rem; margin-bottom:1rem; color:#fff; background:radial-gradient(circle at 78% 20%,rgba(16,132,214,.32),transparent 34%),linear-gradient(135deg,#06152b 0%,#082b50 55%,#061425 100%); border:1px solid rgba(214,181,90,.52); box-shadow:0 22px 48px rgba(2,12,27,.22); }
      .brand-hero:after { content:""; position:absolute; inset:auto -8% -35% 35%; height:65%; background:radial-gradient(circle,rgba(30,144,255,.18),transparent 65%); pointer-events:none; }
      .brand-copy { position:relative; z-index:2; width:54%; }
      .brand-logo { font-size:3rem; line-height:.95; font-weight:950; letter-spacing:.02em; margin-bottom:.6rem; }
      .brand-logo span { color:#e8bd58; }
      .brand-kicker { font-size:.72rem; letter-spacing:.22em; color:#c7d5e8; font-weight:800; margin-bottom:1.25rem; }
      .brand-rule { width:145px; height:2px; background:#e8bd58; margin-bottom:1.25rem; }
      .brand-tagline { font-size:1.65rem; line-height:1.12; font-weight:900; margin-bottom:.7rem; }
      .brand-tagline span { color:#efc65f; }
      .brand-sub { color:#d3deeb; font-size:.92rem; line-height:1.55; max-width:390px; }
      .brand-values { display:flex; gap:.55rem; flex-wrap:wrap; margin-top:1.15rem; }
      .brand-value { padding:.35rem .6rem; border-radius:999px; border:1px solid rgba(255,255,255,.18); background:rgba(255,255,255,.07); font-size:.68rem; font-weight:800; }
      .brand-portrait { position:absolute; z-index:1; right:-1%; bottom:0; width:48%; height:96%; object-fit:cover; object-position:center 15%; mask-image:linear-gradient(to bottom,#000 76%,transparent 100%); -webkit-mask-image:linear-gradient(to bottom,#000 76%,transparent 100%); }
      .brand-glow { position:absolute; right:8%; top:7%; width:34%; aspect-ratio:1; border-radius:50%; border:2px solid rgba(35,172,255,.45); box-shadow:0 0 55px rgba(0,148,255,.2); }
      .linkedin-card { margin:1rem 0 1.1rem; padding:1rem; border-radius:18px; border:1px solid #dbe5f0; background:linear-gradient(145deg,#fff,#f5f9ff); box-shadow:0 10px 26px rgba(15,23,42,.06); }
      .linkedin-head { display:flex; align-items:center; gap:.85rem; }
      .linkedin-avatar { width:68px; height:68px; border-radius:50%; object-fit:cover; border:3px solid #fff; box-shadow:0 4px 16px rgba(15,23,42,.14); }
      .linkedin-name { font-size:1.05rem; font-weight:900; color:#10213e; }
      .linkedin-role { color:#53657c; font-size:.82rem; line-height:1.45; }
      .linkedin-copy { margin-top:.7rem; padding:.65rem .75rem; border-radius:12px; background:#edf5ff; color:#314a6b; font-size:.8rem; line-height:1.55; }
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
      .continue-card { margin:1rem 0 .65rem; padding:.9rem 1rem; border-radius:16px; border:1px solid rgba(202,167,80,.58); background:linear-gradient(145deg,#fffaf0,#ffffff); color:#374151; line-height:1.65; }
      .continue-card strong { display:block; color:#172033; font-size:1rem; margin-bottom:.15rem; }
      .continue-card-ar { direction:rtl; text-align:right; unicode-bidi:plaintext; }
      .feedback-nudge { margin:1rem 0 .55rem; padding:.85rem 1rem; border-radius:16px; border:1px solid #dfc77c; background:#fffaf0; color:#374151; line-height:1.7; }
      .feedback-nudge-ar { direction:rtl; text-align:right; }
      div[data-baseweb="select"] > div { border-radius:14px; }
      .primary-nav-anchor { height:0; margin:0; padding:0; }
      div[data-testid="stHorizontalBlock"]:has(.primary-nav-anchor) {
        gap:.55rem;
        margin:.35rem 0 1rem;
      }
      div[data-testid="stHorizontalBlock"]:has(.primary-nav-anchor) button {
        min-height:3.35rem;
        border-radius:14px;
        font-weight:800;
        line-height:1.25;
      }
      [data-testid="stTextArea"] textarea { border-radius:16px !important; min-height:170px !important; }
      [data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] { unicode-bidi:plaintext; }
      [data-testid="stChatMessage"] code { direction:ltr; unicode-bidi:isolate; }
      .thinking-card { margin:.45rem 0 .75rem; padding:.7rem .85rem; border-radius:14px; border:1px solid #d8e2ee; background:#f8fbff; color:#526173; font-size:.82rem; line-height:1.6; }
      .thinking-card-ar { direction:rtl; text-align:right; unicode-bidi:plaintext; }
      @media (max-width:640px) {
        .block-container { padding-left:1rem; padding-right:1rem; padding-top:5.8rem; }
        .brand-hero { min-height:430px; padding:1.25rem 1.1rem; border-radius:20px; }
        .brand-copy { width:100%; position:relative; z-index:3; }
        .brand-logo { font-size:2.25rem; }
        .brand-tagline { font-size:1.35rem; max-width:62%; }
        .brand-sub { max-width:58%; font-size:.8rem; }
        .brand-kicker { font-size:.62rem; }
        .brand-values { max-width:58%; }
        .brand-value { font-size:.6rem; }
        .brand-portrait { width:66%; height:82%; right:-16%; object-position:center 10%; opacity:.94; }
        .brand-glow { width:55%; right:-2%; top:16%; }
        .linkedin-avatar { width:58px; height:58px; }
        .hero-card { border-radius:19px; padding:1.1rem 1rem; }
        .hero-title { font-size:1.55rem; }
        .hero-tagline { font-size:.79rem; }
        .hero-description { font-size:.84rem; }
        .welcome-title { font-size:1.12rem; }
        .start-grid { grid-template-columns:1fr; }
        div[data-testid="stHorizontalBlock"]:has(.primary-nav-anchor) {
          flex-direction:column !important;
          gap:.5rem !important;
        }
        div[data-testid="stHorizontalBlock"]:has(.primary-nav-anchor) > div[data-testid="stColumn"] {
          width:100% !important;
          flex:1 1 100% !important;
          min-width:100% !important;
        }
        div[data-testid="stHorizontalBlock"]:has(.primary-nav-anchor) button {
          width:100% !important;
          min-height:3.6rem;
          font-size:.96rem;
        }
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

portrait_uri = portrait_data_uri()
hero_direction = "rtl" if is_ar else "ltr"
hero_sub = (
    "أدوات عملية تساعد محللي الرقابة الدوائية على اتخاذ قرارات معملية أفضل."
    if is_ar else
    "Practical tools that help pharmaceutical analysts make better laboratory decisions."
)
hero_values = (
    ("تعلّم", "حلّل", "اتخذ قرارًا", "مجتمع QC أقوى")
    if is_ar else
    ("LEARN", "SOLVE", "DECIDE", "A STRONGER QC COMMUNITY")
)
portrait_html = f'<img class="brand-portrait" src="{portrait_uri}" alt="Yahia Abdelhalim">' if portrait_uri else ""
st.markdown(
    f"""
    <section class="brand-hero" dir="{hero_direction}">
      <div class="brand-glow"></div>
      {portrait_html}
      <div class="brand-copy">
        <div class="brand-logo">YAHIA <span>QC</span></div>
        <div class="brand-kicker">PHARMACEUTICAL QUALITY CONTROL</div>
        <div class="brand-rule"></div>
        <div class="brand-tagline">DON'T GUESS.<br><span>FOLLOW THE EVIDENCE.</span></div>
        <div class="brand-sub">{hero_sub}</div>
        <div class="brand-values">
          {''.join(f'<span class="brand-value">{x}</span>' for x in hero_values)}
        </div>
      </div>
    </section>
    """,
    unsafe_allow_html=True,
)
language_label_html = (
    '<div class="section-label section-label-ar">🌐 اختر اللغة</div>'
    if is_ar else
    '<div class="section-label">🌐 Choose your language · اختر اللغة</div>'
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

# Primary navigation — deliberately visible on the main screen, not hidden in the sidebar.
nav1, nav2, nav3 = st.columns(3)
with nav1:
    st.markdown('<div class="primary-nav-anchor"></div>', unsafe_allow_html=True)
if nav1.button("ابدأ اختبار فجوة اتخاذ القرار" if is_ar else "Start Decision Gap Assessment", use_container_width=True, key="nav_decision_gap"):
    st.switch_page("pages/01_QC_Decision_Gap.py")
if nav2.button("ابدأ حل مشكلة جديدة" if is_ar else "Start a New Investigation", use_container_width=True, key="nav_new_case"):
    new_case_id = uuid.uuid4().hex[:16]
    st.query_params["case"] = new_case_id
    st.session_state.case_id = new_case_id
    st.session_state.messages = []
    st.rerun()
if nav3.button("شاركنا رأيك" if is_ar else "Share Your Feedback", use_container_width=True, key="nav_feedback"):
    st.switch_page("pages/03_Founding_Beta_Feedback.py")

linkedin_copy = (
    "تابعني على LinkedIn للتواصل، إرسال اقتراحاتك، متابعة التحديثات، والتعرف على التطبيقات والأدوات الجديدة."
    if is_ar else
    "Connect with me on LinkedIn to share ideas, follow updates, and discover new QC applications and tools."
)
st.markdown(
    f"""
    <div class="linkedin-card" dir="{'rtl' if is_ar else 'ltr'}">
      <div class="linkedin-head">
        {f'<img class="linkedin-avatar" src="{portrait_uri}" alt="Yahia Abdelhalim">' if portrait_uri else ''}
        <div>
          <div class="linkedin-name">Yahia Abdelhalim</div>
          <div class="linkedin-role">Pharmaceutical QC Expert<br>Helping Pharmaceutical Analysts Make Better Laboratory Decisions</div>
        </div>
      </div>
      <div class="linkedin-copy">{linkedin_copy}</div>
    </div>
    """,
    unsafe_allow_html=True,
)
st.link_button(
    "تابع وتواصل معي على LinkedIn ↗" if is_ar else "Follow & Connect on LinkedIn ↗",
    LINKEDIN_URL,
    use_container_width=True,
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

area = "Auto-detect"
if not API_KEY:
    st.error(T["api_missing"])
    st.stop()

client = OpenAI(api_key=API_KEY)

def transcribe_audio(uploaded_audio, language_hint=None):
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        tmp.write(uploaded_audio.getvalue())
        tmp_path = tmp.name
    try:
        with open(tmp_path, "rb") as audio_file:
            kwargs = {"model": TRANSCRIBE_MODEL, "file": audio_file}
            if language_hint in ("ar", "en"):
                kwargs["language"] = language_hint
            result = client.audio.transcriptions.create(**kwargs)
        return (getattr(result, "text", "") or "").strip()
    finally:
        try:
            os.remove(tmp_path)
        except OSError:
            pass

def synthesize_speech(text):
    clean = re.sub(r"[*#_`>]+", " ", text or "")
    clean = re.sub(r"\\s+", " ", clean).strip()
    if not clean:
        return None
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
        tmp_path = tmp.name
    try:
        with client.audio.speech.with_streaming_response.create(model=TTS_MODEL, voice=TTS_VOICE, input=clean[:4096]) as response:
            response.stream_to_file(tmp_path)
        with open(tmp_path, "rb") as fh:
            return fh.read()
    finally:
        try:
            os.remove(tmp_path)
        except OSError:
            pass

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

    voice_label = "🎙️ أو سجّل المشكلة بصوتك" if is_ar else "🎙️ Or describe the problem by voice"
    audio_case = st.audio_input(voice_label, key=f"initial_voice_{CASE_ID}")
    if audio_case is not None:
        audio_sig = str(len(audio_case.getvalue()))
        if st.session_state.get(f"_voice_sig_{CASE_ID}") != audio_sig:
            with st.spinner("بنحوّل كلامك لنص للمراجعة..." if is_ar else "Transcribing your voice for review..."):
                try:
                    transcript = transcribe_audio(audio_case, effective_language)
                    if transcript:
                        st.session_state[f"voice_transcript_{CASE_ID}"] = transcript
                        st.session_state[f"_voice_sig_{CASE_ID}"] = audio_sig
                        record_event(CASE_ID, "hplc_assistant", "voice_transcribed", effective_language)
                except Exception as exc:
                    st.warning(format_api_error(exc, effective_language))
    default_initial = st.session_state.get(f"voice_transcript_{CASE_ID}", "")
    if default_initial:
        st.info("راجع النص المستخرج من صوتك وعدّله لو لزم قبل بدء التحقيق." if is_ar else "Review the transcript and correct anything needed before starting.")
    with st.form("initial_case_form", clear_on_submit=False):
        initial_text = st.text_area(
            "Initial case", value=default_initial, placeholder=T["input"],
            label_visibility="collapsed", height=180,
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
            st.markdown(_display_answer(message["content"]))
    continue_class = "continue-card continue-card-ar" if is_ar else "continue-card"
    st.markdown(
        f'<div class="{continue_class}"><strong>{T["your_turn"]}</strong>{T["your_turn_copy"]}</div>',
        unsafe_allow_html=True,
    )
    chat_text = st.chat_input(
        "اكتب ردك هنا لمواصلة التحقيق..." if is_ar else "Type your reply here to continue the investigation..."
    )
    voice_reply = st.audio_input("🎙️ رد بصوتك" if is_ar else "🎙️ Reply by voice", key=f"reply_voice_{CASE_ID}_{len(st.session_state.messages)}")
    if chat_text:
        user_input = chat_text
    elif voice_reply is not None:
        audio_sig = str(len(voice_reply.getvalue()))
        sig_key = f"_reply_voice_sig_{CASE_ID}"
        if st.session_state.get(sig_key) != audio_sig:
            with st.spinner("بنحوّل كلامك لنص..." if is_ar else "Transcribing..."):
                try:
                    transcript = transcribe_audio(voice_reply, effective_language)
                    if transcript:
                        st.session_state[sig_key] = audio_sig
                        st.session_state[f"_pending_voice_{CASE_ID}"] = transcript
                        record_event(CASE_ID, "hplc_assistant", "voice_transcribed", effective_language)
                except Exception as exc:
                    st.warning(format_api_error(exc, effective_language))
        pending_voice = st.session_state.get(f"_pending_voice_{CASE_ID}", "")
        if pending_voice:
            st.markdown(
                "**راجع وعدّل النص قبل الإرسال:**" if is_ar
                else "**Review and edit the transcript before sending:**"
            )
            edit_key = f"_voice_edit_{CASE_ID}_{len(st.session_state.messages)}"
            if edit_key not in st.session_state:
                st.session_state[edit_key] = pending_voice
            edited_voice = st.text_area(
                "Voice transcript",
                key=edit_key,
                label_visibility="collapsed",
                height=130,
                placeholder="عدّل النص هنا قبل الإرسال..." if is_ar else "Edit the transcript here before sending...",
            )
            c1, c2 = st.columns(2)
            if c1.button("✓ أرسل بعد المراجعة" if is_ar else "✓ Send reviewed text", key=f"send_voice_{CASE_ID}_{len(st.session_state.messages)}", use_container_width=True):
                if edited_voice.strip():
                    user_input = edited_voice.strip()
                    st.session_state.pop(f"_pending_voice_{CASE_ID}", None)
            if c2.button("إلغاء" if is_ar else "Cancel", key=f"cancel_voice_{CASE_ID}_{len(st.session_state.messages)}", use_container_width=True):
                st.session_state.pop(f"_pending_voice_{CASE_ID}", None)
                st.session_state.pop(edit_key, None)
                st.rerun()

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
        reasoning_summary_instruction = (
            "At the start of every reply, include a very short section titled '🧭 كيف أفكر في الحالة الآن' with no more than 2 concise bullets. "
            "Show only a useful investigation summary: what is observed, what remains unknown, the current hypothesis direction, and why the next question/test is discriminating. "
            "Do not reveal hidden chain-of-thought, private reasoning, or internal deliberation. "
        )
        language_instruction = (
            "Respond in natural professional Arabic and address the user consistently in masculine singular form (أنت/اكتب/راجع/نفّذ/أرسل), never feminine forms. "
            "Begin headings and bullets in Arabic. "
            "Keep useful standard HPLC/QC abbreviations in English only when they improve precision, preferably in parentheses after the Arabic term. "
            "Avoid awkward mixed Arabic-English constructions such as Arabic definite articles attached to English terms. "
            "Keep paragraphs short and mobile-friendly. "
            "This is an interactive investigation chat, not a report: end every non-final turn with exactly one explicit NEXT STEP for the user—either one question to answer OR one test/check to perform, not several at once. "
            "Make that final instruction unmistakable under the Arabic heading '🎯 المطلوب منك الآن'. "
            "Do not show closure, outcome confirmation, or feedback language while the root cause is not yet identified."
        )
    else:
        reasoning_summary_instruction = (
            "At the start of every reply, include a short section titled '🧭 How I am approaching this case' with 2–4 concise bullets. "
            "Show only a useful investigation summary: what is observed, what remains unknown, the current hypothesis direction, and why the next question/test is discriminating. "
            "Do not reveal hidden chain-of-thought, private reasoning, or internal deliberation. "
        )
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
        + f"LANGUAGE BEHAVIOR: {language_instruction}\n"
        + f"VISIBLE INVESTIGATION SUMMARY: {reasoning_summary_instruction}\n"
        + "STATE CONTRACT: End every reply with exactly one machine-readable line: INVESTIGATION_STATUS: INVESTIGATING, AWAITING_USER, AWAITING_TEST, PROBABLE, or CONFIRMED. Use AWAITING_USER when one answer is needed; AWAITING_TEST when one test/check result is needed; PROBABLE only when a probable root cause is supported and no further investigation step is requested; CONFIRMED only after discriminating evidence confirms the root cause and no further investigation step is requested. Never use PROBABLE or CONFIRMED in a reply that asks the user for another investigative action. Do not explain this status line.\n\n"
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

                visible_answer = _display_answer(answer)
                placeholder = st.empty()
                rendered = ""
                chunks = re.findall(r"\S+\s*", visible_answer)
                for i, chunk in enumerate(chunks):
                    rendered += chunk
                    placeholder.markdown(rendered + ("▌" if i < len(chunks) - 1 else ""))
                    time.sleep(0.018)
                placeholder.markdown(visible_answer)

                st.session_state.messages.append({"role": "assistant", "content": answer})
                save_message(CASE_ID, "assistant", answer)
                try:
                    spoken = synthesize_speech(visible_answer)
                    if spoken:
                        st.session_state[f"_last_spoken_{CASE_ID}"] = spoken
                        st.audio(spoken, format="audio/mp3")
                        record_event(CASE_ID, "hplc_assistant", "voice_reply_generated", response_language)
                except Exception:
                    pass
                record_event(
                    CASE_ID,
                    "hplc_assistant",
                    "assistant_turn_completed",
                    response_language,
                    {"assistant_turn": _assistant_turn_count(st.session_state.messages)},
                )
                if first_user_message:
                    st.rerun()
            except Exception as exc:
                answer = format_api_error(exc, response_language)
                st.markdown(answer)

if st.session_state.messages:
    feedback_ready_key = f"_hplc_feedback_ready_{CASE_ID}"
    feedback_logged_key = f"_hplc_feedback_prompt_logged_{CASE_ID}"
    assistant_turns = _assistant_turn_count(st.session_state.messages)

    if _conclusion_detected(st.session_state.messages):
        if _resolution_check_ready(st.session_state.messages):
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

    # Keep unresolved investigations focused on continuation.
    # Feedback is offered only after a true probable/confirmed conclusion,
    # not simply because the chat has reached two assistant turns.

    resolution_key = f"_hplc_resolution_{CASE_ID}"
    resolution_logged_key = f"_hplc_resolution_logged_{CASE_ID}"
    if _resolution_check_ready(st.session_state.messages) and not st.session_state.get(resolution_logged_key):
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
    if is_ar:
        st.markdown("### 🔗 تابع تطوير Yahia QC")
        st.caption("للتواصل، إرسال اقتراحاتك، متابعة التحديثات، والتعرف على التطبيقات والأدوات الجديدة.")
        st.link_button("تابع وتواصل معي على LinkedIn ↗", "https://www.linkedin.com/in/yahia-rashad-mohamed", use_container_width=True)
    else:
        st.markdown("### 🔗 Stay connected with Yahia QC")
        st.caption("Connect, suggest improvements, follow updates, and discover new QC applications and tools.")
        st.link_button("Follow & Connect on LinkedIn ↗", "https://www.linkedin.com/in/yahia-rashad-mohamed", use_container_width=True)
    st.markdown(
        f'<div class="small-note">{APP_VERSION} · Yahia HPLC Investigation Assistant · Verified Evidence Engine · Evidence-first bilingual QC decision support</div>',
        unsafe_allow_html=True,
    )