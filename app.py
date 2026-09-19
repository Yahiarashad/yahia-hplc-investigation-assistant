# Persistent-auth wrapper for Yahia QC Instrument Lifecycle.
# v0.3 Sprint 2 shell: persistent Supabase auth + compact mobile navigation.

from __future__ import annotations

import base64
import hashlib
import json
from pathlib import Path
from urllib import error as urlerror
from urllib import request as urlrequest

import streamlit as st
from cryptography.fernet import Fernet, InvalidToken
from streamlit_cookies_controller import CookieController, RemoveEmptyElementContainer
from streamlit.delta_generator import DeltaGenerator

st.set_page_config(
    page_title="Yahia QC Instrument Lifecycle & Investigation Intelligence",
    page_icon="🧪",
    layout="wide",
    initial_sidebar_state="collapsed",
)

RemoveEmptyElementContainer()
controller = CookieController(key="ilm_auth_cookie_controller")
COOKIE_NAME = "yahia_qc_ilm_refresh_v1"

# Mobile RTL polish for Arabic guidance blocks.
st.markdown(
    """
<style>
div[data-testid="stMarkdownContainer"] > h3:has(+ ul:last-child) {
    direction: rtl !important;
    text-align: right !important;
}
div[data-testid="stMarkdownContainer"] > ul:last-child {
    direction: rtl !important;
    text-align: right !important;
    padding-right: 1.45rem !important;
    padding-left: 0 !important;
    margin-right: 0 !important;
}
div[data-testid="stMarkdownContainer"] > ul:last-child > li {
    direction: rtl !important;
    text-align: right !important;
    unicode-bidi: plaintext;
    padding-right: .15rem;
    margin: .38rem 0;
}
div[data-testid="stMarkdownContainer"] > ul:last-child strong {
    unicode-bidi: isolate;
}
@media (max-width: 700px) {
    div[data-testid="stMarkdownContainer"] > ul:last-child {
        padding-right: 1.25rem !important;
        line-height: 1.9;
    }
}
</style>
""",
    unsafe_allow_html=True,
)


def _secret(name: str) -> str:
    try:
        return str(st.secrets.get(name, "") or "").strip()
    except Exception:
        return ""


SUPABASE_URL = _secret("SUPABASE_URL").rstrip("/")
SUPABASE_KEY = _secret("SUPABASE_PUBLISHABLE_KEY") or _secret("SUPABASE_KEY")
COOKIE_SECRET = _secret("AUTH_COOKIE_SECRET") or _secret("INSTRUMENT_LIFECYCLE_TOKEN")


def _fernet() -> Fernet | None:
    if not COOKIE_SECRET:
        return None
    key = base64.urlsafe_b64encode(hashlib.sha256(COOKIE_SECRET.encode("utf-8")).digest())
    return Fernet(key)


def _encrypt_refresh_token(token: str) -> str:
    f = _fernet()
    if not f or not token:
        return ""
    return f.encrypt(token.encode("utf-8")).decode("utf-8")


def _decrypt_refresh_token(value: str) -> str:
    f = _fernet()
    if not f or not value:
        return ""
    try:
        return f.decrypt(value.encode("utf-8")).decode("utf-8")
    except (InvalidToken, ValueError, TypeError):
        return ""


def _refresh_supabase(refresh_token: str):
    if not SUPABASE_URL or not SUPABASE_KEY or not refresh_token:
        return None
    url = f"{SUPABASE_URL}/auth/v1/token?grant_type=refresh_token"
    body = json.dumps({"refresh_token": refresh_token}).encode("utf-8")
    req = urlrequest.Request(
        url,
        data=body,
        headers={"apikey": SUPABASE_KEY, "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlrequest.urlopen(req, timeout=15) as response:
            data = json.loads(response.read().decode("utf-8"))
        if isinstance(data, dict) and data.get("access_token"):
            return {
                "access_token": data.get("access_token", ""),
                "refresh_token": data.get("refresh_token") or refresh_token,
                "expires_at": data.get("expires_at"),
                "user": data.get("user") or {},
            }
    except (urlerror.URLError, urlerror.HTTPError, TimeoutError, ValueError, json.JSONDecodeError):
        return None
    except Exception:
        return None
    return None


def _write_auth_cookie() -> None:
    auth = st.session_state.get("_ilm_auth") or {}
    refresh_token = str(auth.get("refresh_token") or "")
    encrypted = _encrypt_refresh_token(refresh_token)
    if encrypted:
        controller.set(COOKIE_NAME, encrypted)
    else:
        try:
            controller.remove(COOKIE_NAME)
        except Exception:
            pass


# Restore a Supabase session from the encrypted browser cookie before the main
# application reaches its authentication gate.
if not st.session_state.get("_ilm_auth"):
    try:
        cookie_value = controller.get(COOKIE_NAME)
    except Exception:
        cookie_value = None
    if isinstance(cookie_value, dict):
        cookie_value = cookie_value.get("value")
    refresh_token = _decrypt_refresh_token(str(cookie_value or ""))
    restored = _refresh_supabase(refresh_token)
    if restored:
        st.session_state._ilm_auth = restored
        _write_auth_cookie()
    elif cookie_value:
        try:
            controller.remove(COOKIE_NAME)
        except Exception:
            pass


# Persist/remove the auth cookie immediately before Streamlit reruns.
_real_rerun = st.rerun


def _cookie_aware_rerun(*args, **kwargs):
    _write_auth_cookie()
    return _real_rerun(*args, **kwargs)


st.rerun = _cookie_aware_rerun

# Load the detailed top-of-page practical user guide. It is rendered later,
# immediately before the main navigation, after the core database helpers exist.
try:
    _guide_module = Path(__file__).resolve().parent / "instrument_v03_user_guide.py"
    if _guide_module.exists():
        exec(compile(_guide_module.read_text(encoding="utf-8"), str(_guide_module), "exec"), globals(), globals())
except Exception:
    pass

# Re-map the original six core tabs into compact lifecycle-first navigation.
_real_tabs = st.tabs
_MAIN_TABS = [
    "Command Center",
    "Instrument Passport",
    "Lifecycle",
    "Events",
    "Investigation Intelligence",
    "Guide",
]
_core_main_tabs_seen = False


def _tabs_v03(labels, *args, **kwargs):
    global _core_main_tabs_seen
    items = list(labels)
    if items == _MAIN_TABS:
        _core_main_tabs_seen = True
        # The detailed guide deliberately sits above the primary navigation so a
        # new user can understand the product and import data before opening tabs.
        try:
            if callable(globals().get("render_v03_user_guide")):
                render_v03_user_guide()
        except Exception as exc:
            st.warning("The practical user guide could not load completely.")
            st.caption(f"Guide diagnostic: {type(exc).__name__}")
        display_items = [
            "🏠 Dashboard",
            "↻ Lifecycle",
            "🪪 Passport",
            "◎ Cal & PM",
            "⚠ Events",
            "🔎 Investigate",
            "▦ Reports",
            "ⓘ Guide",
        ]
        rendered = _real_tabs(display_items, *args, **kwargs)
        # Core content mapping:
        # Command Center -> Reports
        # Passport -> Passport
        # old Lifecycle -> Cal & PM
        # Events / Investigation / Guide keep their role.
        # Index 6 and 7 are custom Dashboard and Lifecycle containers.
        return [
            rendered[6],
            rendered[2],
            rendered[3],
            rendered[4],
            rendered[5],
            rendered[7],
            rendered[0],
            rendered[1],
        ]
    return _real_tabs(items, *args, **kwargs)


st.tabs = _tabs_v03

# Hide the old pre-tab summary metrics / duplicate CTA from the v0.2 core while
# keeping the rest of the core forms untouched. The new Dashboard owns summary UI.
_real_dg_metric = DeltaGenerator.metric
_real_markdown = st.markdown


def _metric_until_main_tabs(self, *args, **kwargs):
    if not _core_main_tabs_seen:
        return None
    return _real_dg_metric(self, *args, **kwargs)


def _markdown_until_main_tabs(body, *args, **kwargs):
    if (
        not _core_main_tabs_seen
        and isinstance(body, str)
        and '<div class="cta">' in body
        and "Recommended next action" in body
    ):
        return None
    return _real_markdown(body, *args, **kwargs)


DeltaGenerator.metric = _metric_until_main_tabs
st.markdown = _markdown_until_main_tabs

# The core file configures the page too; this wrapper already did it.
_real_set_page_config = st.set_page_config
st.set_page_config = lambda *args, **kwargs: None

_core = Path(__file__).resolve().parent / "instrument_supabase_app.py"
try:
    exec(compile(_core.read_text(encoding="utf-8"), str(_core), "exec"), globals(), globals())
finally:
    st.set_page_config = _real_set_page_config
    st.tabs = _real_tabs
    st.markdown = _real_markdown
    DeltaGenerator.metric = _real_dg_metric
    _write_auth_cookie()

# Apply the requested instrument imagery to hero areas without placing strong
# images behind forms/tables. The SVG is decorative and receives a navy overlay.
try:
    hero_asset = Path(__file__).resolve().parent / "assets" / "instrument_lifecycle_hero.svg"
    hero_b64 = base64.b64encode(hero_asset.read_bytes()).decode("ascii") if hero_asset.exists() else ""
    if hero_b64:
        st.markdown(
            f"""
<style>
.hero, .v03-dashboard-hero {{
  background-image:
    linear-gradient(90deg, rgba(4,12,25,.97) 0%, rgba(6,20,38,.90) 44%, rgba(8,28,49,.76) 100%),
    url("data:image/svg+xml;base64,{hero_b64}") !important;
  background-size: cover !important;
  background-position: center !important;
}}
.hero {{ min-height: 220px; display:flex; flex-direction:column; justify-content:center; }}
@media(max-width:700px) {{
  .hero {{ min-height: 205px; background-position: 58% center !important; }}
}}
</style>
""",
            unsafe_allow_html=True,
        )
except Exception:
    pass

main_tabs = globals().get("tabs")

# Populate the new Dashboard.
try:
    if isinstance(main_tabs, list) and len(main_tabs) >= 8 and globals().get("_auth_token") and _auth_token():
        dashboard_module = Path(__file__).resolve().parent / "instrument_v03_dashboard.py"
        with main_tabs[6]:
            exec(compile(dashboard_module.read_text(encoding="utf-8"), str(dashboard_module), "exec"), globals(), globals())
except Exception as exc:
    try:
        with main_tabs[6]:
            st.error("v0.3 Dashboard could not load.")
            st.caption(f"Diagnostic: {type(exc).__name__}")
    except Exception:
        pass

# Populate the new full lifecycle navigator.
try:
    if isinstance(main_tabs, list) and len(main_tabs) >= 8 and globals().get("_auth_token") and _auth_token():
        lifecycle_module = Path(__file__).resolve().parent / "instrument_v03_lifecycle.py"
        with main_tabs[7]:
            exec(compile(lifecycle_module.read_text(encoding="utf-8"), str(lifecycle_module), "exec"), globals(), globals())
except Exception as exc:
    try:
        with main_tabs[7]:
            st.error("Full Lifecycle module could not load.")
            st.caption(f"Diagnostic: {type(exc).__name__}")
    except Exception:
        pass

# Keep detailed calibration control inside Cal & PM.
try:
    if isinstance(main_tabs, list) and len(main_tabs) >= 3 and globals().get("_auth_token") and _auth_token():
        calibration_module = Path(__file__).resolve().parent / "instrument_calibration_control.py"
        with main_tabs[2]:
            st.divider()
            exec(compile(calibration_module.read_text(encoding="utf-8"), str(calibration_module), "exec"), globals(), globals())
except Exception as exc:
    try:
        with main_tabs[2]:
            st.error("Calibration Control Center could not load.")
            st.caption(f"Diagnostic: {type(exc).__name__}")
    except Exception:
        pass

# Sprint 2 interaction polish. Added last so it overrides module-local styles.
st.markdown(
    """
<style>
/* Compact horizontal navigation */
div[data-baseweb="tab-list"]{
  overflow-x:auto!important;
  flex-wrap:nowrap!important;
  scrollbar-width:none!important;
  gap:.12rem!important;
  scroll-snap-type:x proximity;
  padding-bottom:.15rem;
}
div[data-baseweb="tab-list"]::-webkit-scrollbar{display:none!important;}
button[data-baseweb="tab"]{
  white-space:nowrap!important;
  flex:0 0 auto!important;
  scroll-snap-align:start;
  border-radius:10px 10px 0 0!important;
}

/* More tactile controls */
.stButton > button,
.stFormSubmitButton > button{
  border-radius:13px!important;
  min-height:44px!important;
  font-weight:700!important;
  border:1px solid #dbe3ec!important;
  box-shadow:0 3px 10px rgba(15,23,42,.04)!important;
  transition:transform .12s ease, box-shadow .12s ease!important;
}
.stButton > button:hover,
.stFormSubmitButton > button:hover{
  transform:translateY(-1px)!important;
  box-shadow:0 7px 16px rgba(15,23,42,.08)!important;
}

/* Lifecycle cards feel like a journey instead of a document */
.v03-loop-card{
  transition:transform .14s ease, box-shadow .14s ease, border-color .14s ease!important;
}
.v03-loop-card:hover{
  transform:translateY(-2px)!important;
  box-shadow:0 9px 22px rgba(15,23,42,.08)!important;
  border-color:#d6b85f!important;
}
.v03-step{
  border:1px solid #e7edf3!important;
  border-left:4px solid #dbe3ec!important;
  border-radius:14px!important;
  padding:.75rem .8rem .75rem 1rem!important;
  margin:.45rem 0!important;
  background:#fff!important;
  box-shadow:0 3px 10px rgba(15,23,42,.035)!important;
}
.v03-step:before{left:-9px!important;top:14px!important;}
.v03-step.complete{border-left-color:#17a673!important;background:#fbfffd!important;}
.v03-step.current{border-left-color:#d6a92f!important;background:#fffdf5!important;box-shadow:0 7px 20px rgba(214,169,47,.10)!important;}
.v03-step.attention{border-left-color:#dc3545!important;background:#fffafa!important;}
.v03-step.ongoing{border-left-color:#2274a5!important;background:#f8fcff!important;}
.v03-step.future{opacity:.82;}

/* Mobile density */
@media(max-width:700px){
  .block-container{padding-left:.8rem!important;padding-right:.8rem!important;}
  button[data-baseweb="tab"]{padding-left:.58rem!important;padding-right:.58rem!important;font-size:.84rem!important;}
  .v03-loop{grid-template-columns:1fr 1fr!important;gap:.45rem!important;}
  .v03-loop-card{min-height:78px!important;padding:.62rem!important;}
  .v03-step{padding:.7rem .7rem .7rem .9rem!important;}
  .v03-step-title{font-size:.95rem!important;}
  .v03-step-action{font-size:.79rem!important;}
}
</style>
""",
    unsafe_allow_html=True,
)
