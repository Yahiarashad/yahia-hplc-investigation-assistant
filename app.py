# Persistent-auth wrapper for Yahia QC Instrument Lifecycle.
# Keeps the Supabase refresh token in an encrypted browser cookie so a normal
# page refresh or Streamlit worker reboot does not force the user to sign in again.

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
        # Supabase may rotate refresh tokens; persist the newest one.
        _write_auth_cookie()
    elif cookie_value:
        try:
            controller.remove(COOKIE_NAME)
        except Exception:
            pass


# The core app calls st.rerun after login and logout. Persist/remove the cookie
# immediately before that rerun so the browser and server session stay aligned.
_real_rerun = st.rerun


def _cookie_aware_rerun(*args, **kwargs):
    _write_auth_cookie()
    return _real_rerun(*args, **kwargs)


st.rerun = _cookie_aware_rerun

# Add one dedicated main tab without changing the core tab indexes. Login and
# nested tab groups are left untouched.
_real_tabs = st.tabs
_MAIN_TABS = [
    "Command Center",
    "Instrument Passport",
    "Lifecycle",
    "Events",
    "Investigation Intelligence",
    "Guide",
]


def _tabs_with_acquisition(labels, *args, **kwargs):
    items = list(labels)
    if items == _MAIN_TABS:
        items = items + ["Acquisition Journey"]
    return _real_tabs(items, *args, **kwargs)


st.tabs = _tabs_with_acquisition

# The core file configures the page too; this wrapper already did it.
_real_set_page_config = st.set_page_config
st.set_page_config = lambda *args, **kwargs: None

_core = Path(__file__).resolve().parent / "instrument_supabase_app.py"
try:
    exec(compile(_core.read_text(encoding="utf-8"), str(_core), "exec"), globals(), globals())
finally:
    st.set_page_config = _real_set_page_config
    st.tabs = _real_tabs
    # Keep the latest rotated refresh token after any successful app run.
    _write_auth_cookie()

# The core main tab list is stored in `tabs`. The wrapper appends one empty tab;
# fill it here using the same authenticated database helpers and RLS context.
try:
    main_tabs = globals().get("tabs")
    if isinstance(main_tabs, list) and len(main_tabs) >= 7 and globals().get("_auth_token"):
        if _auth_token():
            journey_module = Path(__file__).resolve().parent / "instrument_acquisition_journey.py"
            with main_tabs[-1]:
                exec(
                    compile(journey_module.read_text(encoding="utf-8"), str(journey_module), "exec"),
                    globals(),
                    globals(),
                )
except Exception as exc:
    try:
        with main_tabs[-1]:
            st.error("Acquisition Journey could not load.")
            st.caption(f"Diagnostic: {type(exc).__name__}")
    except Exception:
        pass
