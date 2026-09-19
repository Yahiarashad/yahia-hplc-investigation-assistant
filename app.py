# Persistent-auth wrapper for Yahia QC Instrument Lifecycle.
# v0.3 shell: persistent Supabase auth + interactive lifecycle navigation.

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

# Re-map the original six core tabs into the v0.3 lifecycle-first navigation.
# The two extra returned containers are populated after the core file executes.
_real_tabs = st.tabs
_MAIN_TABS = [
    "Command Center",
    "Instrument Passport",
    "Lifecycle",
    "Events",
    "Investigation Intelligence",
    "Guide",
]


def _tabs_v03(labels, *args, **kwargs):
    items = list(labels)
    if items == _MAIN_TABS:
        display_items = [
            "Dashboard",
            "Lifecycle",
            "Instrument Passport",
            "Calibration & PM",
            "Events",
            "Investigation Intelligence",
            "Reports",
            "Guide / About",
        ]
        rendered = _real_tabs(display_items, *args, **kwargs)
        # Core content mapping:
        # Command Center -> Reports
        # Passport -> Instrument Passport
        # old Lifecycle -> Calibration & PM
        # Events / Investigation / Guide keep their role.
        # Index 6 and 7 are custom v0.3 Dashboard and Lifecycle containers.
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

# The core file configures the page too; this wrapper already did it.
_real_set_page_config = st.set_page_config
st.set_page_config = lambda *args, **kwargs: None

_core = Path(__file__).resolve().parent / "instrument_supabase_app.py"
try:
    exec(compile(_core.read_text(encoding="utf-8"), str(_core), "exec"), globals(), globals())
finally:
    st.set_page_config = _real_set_page_config
    st.tabs = _real_tabs
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
    linear-gradient(90deg, rgba(4,12,25,.96) 0%, rgba(6,20,38,.88) 44%, rgba(8,28,49,.78) 100%),
    url("data:image/svg+xml;base64,{hero_b64}") !important;
  background-size: cover !important;
  background-position: center !important;
}}
.hero {{ min-height: 220px; display:flex; flex-direction:column; justify-content:center; }}
@media(max-width:700px) {{
  .hero {{ min-height: 205px; background-position: 58% center !important; }}
  div[data-baseweb="tab-list"] {{ gap:.05rem !important; }}
  button[data-baseweb="tab"] {{ padding-left:.72rem !important; padding-right:.72rem !important; font-size:.92rem !important; }}
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

# Populate the new full lifecycle navigator. This replaces the isolated
# URS/PR/PO tab and gives one journey from Need through Retirement.
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

# Keep the detailed calibration module inside the dedicated Calibration & PM tab.
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
