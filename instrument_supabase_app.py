# Yahia QC Instrument Lifecycle & Investigation Intelligence
# Standalone Streamlit entrypoint — Supabase multi-user edition.
# Each authenticated user receives an isolated dataset enforced by Supabase RLS.

from __future__ import annotations

import json
import uuid
from pathlib import Path
from urllib import error as urlerror
from urllib import parse as urlparse
from urllib import request as urlrequest

import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Yahia QC Instrument Lifecycle & Investigation Intelligence",
    page_icon="🧪",
    layout="wide",
    initial_sidebar_state="collapsed",
)

INSTRUMENT_COLUMNS = [
    "instrument_id", "instrument_name", "instrument_type", "manufacturer", "model",
    "serial_number", "location", "status", "owner", "qualification_due",
    "pm_due", "calibration_due", "created_at"
]
EVENT_COLUMNS = [
    "event_id", "instrument_id", "event_date", "event_type", "severity", "subsystem",
    "status", "observed_facts", "immediate_action", "root_cause_status", "root_cause",
    "reference", "created_at"
]


def _secret(name: str) -> str:
    try:
        return str(st.secrets.get(name, "") or "").strip()
    except Exception:
        return ""


SUPABASE_URL = _secret("SUPABASE_URL").rstrip("/")
# Support both names so existing Streamlit Secrets do not have to be renamed.
SUPABASE_KEY = _secret("SUPABASE_PUBLISHABLE_KEY") or _secret("SUPABASE_KEY")


def _supabase_configured() -> bool:
    return bool(SUPABASE_URL and SUPABASE_KEY)


def _normalize_df(data, columns):
    if isinstance(data, pd.DataFrame):
        df = data.copy()
    elif isinstance(data, list):
        df = pd.DataFrame(data)
    else:
        df = pd.DataFrame()
    for col in columns:
        if col not in df.columns:
            df[col] = ""
    return df[columns].fillna("")


def _safe_json(raw: bytes | str):
    if isinstance(raw, bytes):
        raw = raw.decode("utf-8", errors="replace")
    if not raw:
        return None
    try:
        return json.loads(raw)
    except Exception:
        return None


def _http_json(url: str, *, method: str = "GET", payload=None, headers=None, timeout: int = 15):
    request_headers = dict(headers or {})
    data = None
    if payload is not None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        request_headers.setdefault("Content-Type", "application/json")

    req = urlrequest.Request(url, data=data, headers=request_headers, method=method)
    try:
        with urlrequest.urlopen(req, timeout=timeout) as response:
            raw = response.read()
            return True, _safe_json(raw), response.status, ""
    except urlerror.HTTPError as exc:
        try:
            body = _safe_json(exc.read())
            if isinstance(body, dict):
                message = body.get("msg") or body.get("message") or body.get("error_description") or body.get("error")
            else:
                message = None
        except Exception:
            message = None
        return False, None, exc.code, str(message or f"HTTP {exc.code}")
    except urlerror.URLError as exc:
        return False, None, 0, f"Connection error: {getattr(exc, 'reason', 'unreachable')}"
    except TimeoutError:
        return False, None, 0, "Connection timeout"
    except Exception as exc:
        return False, None, 0, type(exc).__name__


# -----------------------------------------------------------------------------
# Supabase Auth
# -----------------------------------------------------------------------------

def _auth_headers():
    return {"apikey": SUPABASE_KEY, "Content-Type": "application/json"}


def _auth_login(email: str, password: str):
    url = f"{SUPABASE_URL}/auth/v1/token?grant_type=password"
    ok, data, status, err = _http_json(
        url,
        method="POST",
        payload={"email": email.strip(), "password": password},
        headers=_auth_headers(),
    )
    if ok and isinstance(data, dict) and data.get("access_token"):
        st.session_state._ilm_auth = {
            "access_token": data.get("access_token", ""),
            "refresh_token": data.get("refresh_token", ""),
            "expires_at": data.get("expires_at"),
            "user": data.get("user") or {},
        }
        return True, ""
    return False, err or "Login failed"


def _auth_signup(email: str, password: str, display_name: str):
    url = f"{SUPABASE_URL}/auth/v1/signup"
    payload = {
        "email": email.strip(),
        "password": password,
        "data": {"display_name": display_name.strip()} if display_name.strip() else {},
    }
    ok, data, status, err = _http_json(url, method="POST", payload=payload, headers=_auth_headers())
    if not ok:
        return False, err or "Sign-up failed", False
    if isinstance(data, dict) and data.get("access_token"):
        st.session_state._ilm_auth = {
            "access_token": data.get("access_token", ""),
            "refresh_token": data.get("refresh_token", ""),
            "expires_at": data.get("expires_at"),
            "user": data.get("user") or {},
        }
        return True, "Account created and signed in.", True
    return True, "Account created. Check your email to confirm the account, then sign in.", False


def _auth_refresh() -> bool:
    auth = st.session_state.get("_ilm_auth") or {}
    refresh_token = str(auth.get("refresh_token") or "")
    if not refresh_token:
        return False
    url = f"{SUPABASE_URL}/auth/v1/token?grant_type=refresh_token"
    ok, data, status, err = _http_json(
        url,
        method="POST",
        payload={"refresh_token": refresh_token},
        headers=_auth_headers(),
    )
    if ok and isinstance(data, dict) and data.get("access_token"):
        st.session_state._ilm_auth = {
            "access_token": data.get("access_token", ""),
            "refresh_token": data.get("refresh_token") or refresh_token,
            "expires_at": data.get("expires_at"),
            "user": data.get("user") or auth.get("user") or {},
        }
        return True
    return False


def _auth_logout():
    auth = st.session_state.get("_ilm_auth") or {}
    token = str(auth.get("access_token") or "")
    if token:
        _http_json(
            f"{SUPABASE_URL}/auth/v1/logout",
            method="POST",
            payload={},
            headers={"apikey": SUPABASE_KEY, "Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        )
    for key in list(st.session_state.keys()):
        if key.startswith("ilm_") or key.startswith("_ilm_") or key == "inv_instrument":
            st.session_state.pop(key, None)


def _auth_user():
    auth = st.session_state.get("_ilm_auth") or {}
    user = auth.get("user") or {}
    return user if isinstance(user, dict) else {}


def _auth_token() -> str:
    return str((st.session_state.get("_ilm_auth") or {}).get("access_token") or "")


# -----------------------------------------------------------------------------
# PostgREST helpers. The user's JWT is always used so database RLS remains the
# authority for data isolation. No service-role/secret key is used in the app.
# -----------------------------------------------------------------------------

def _db_headers(prefer: str | None = None):
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {_auth_token()}",
        "Content-Type": "application/json",
    }
    if prefer:
        headers["Prefer"] = prefer
    return headers


def _db_request(path: str, *, method="GET", payload=None, prefer=None, retry_auth=True):
    url = f"{SUPABASE_URL}/rest/v1/{path.lstrip('/')}"
    ok, data, status, err = _http_json(
        url,
        method=method,
        payload=payload,
        headers=_db_headers(prefer),
    )
    if status == 401 and retry_auth and _auth_refresh():
        return _db_request(path, method=method, payload=payload, prefer=prefer, retry_auth=False)
    if not ok:
        st.session_state._ilm_db_error = err or f"Database HTTP {status}"
    else:
        st.session_state._ilm_db_error = ""
    return ok, data, status, err


def _instrument_to_db(row):
    def text(name):
        value = row.get(name, "")
        return "" if value is None else str(value)

    return {
        "instrument_code": text("instrument_id").strip().upper(),
        "instrument_name": text("instrument_name").strip(),
        "instrument_type": text("instrument_type"),
        "manufacturer": text("manufacturer"),
        "model": text("model"),
        "serial_number": text("serial_number"),
        "location": text("location"),
        "operational_status": text("status") or "Active",
        "responsible_team": text("owner"),
        "qualification_due": text("qualification_due") or None,
        "pm_due": text("pm_due") or None,
        "calibration_due": text("calibration_due") or None,
    }


def _event_to_db(row, instrument_uuid_by_code):
    def text(name):
        value = row.get(name, "")
        return "" if value is None else str(value)

    code = text("instrument_id").strip().upper()
    instrument_uuid = instrument_uuid_by_code.get(code)
    if not instrument_uuid:
        return None
    return {
        "instrument_id": instrument_uuid,
        "event_date": text("event_date") or None,
        "event_type": text("event_type") or "Other",
        "severity": text("severity") or "Medium",
        "subsystem": text("subsystem"),
        "event_status": text("status") or "Open",
        "observed_facts": text("observed_facts"),
        "immediate_action": text("immediate_action"),
        "root_cause_status": text("root_cause_status") or "Not identified",
        "root_cause": text("root_cause"),
        "investigation_reference": text("reference"),
    }


def _load_supabase_state() -> bool:
    ok, instruments, _, err = _db_request(
        "instruments?select=id,instrument_code,instrument_name,instrument_type,manufacturer,model,serial_number,location,operational_status,responsible_team,qualification_due,pm_due,calibration_due,created_at&order=created_at.asc"
    )
    if not ok or not isinstance(instruments, list):
        return False

    instrument_rows = []
    instrument_map = {}
    reverse_instrument_map = {}
    for row in instruments:
        code = str(row.get("instrument_code") or "").strip().upper()
        db_id = str(row.get("id") or "")
        if code and db_id:
            instrument_map[code] = db_id
            reverse_instrument_map[db_id] = code
        instrument_rows.append({
            "instrument_id": code,
            "instrument_name": row.get("instrument_name") or "",
            "instrument_type": row.get("instrument_type") or "",
            "manufacturer": row.get("manufacturer") or "",
            "model": row.get("model") or "",
            "serial_number": row.get("serial_number") or "",
            "location": row.get("location") or "",
            "status": row.get("operational_status") or "Active",
            "owner": row.get("responsible_team") or "",
            "qualification_due": row.get("qualification_due") or "",
            "pm_due": row.get("pm_due") or "",
            "calibration_due": row.get("calibration_due") or "",
            "created_at": row.get("created_at") or "",
        })

    ok, events, _, err = _db_request(
        "instrument_events?select=id,instrument_id,event_date,event_type,severity,subsystem,event_status,observed_facts,immediate_action,root_cause_status,root_cause,investigation_reference,created_at&order=event_date.desc"
    )
    if not ok or not isinstance(events, list):
        return False

    event_rows = []
    event_map = {}
    for row in events:
        db_id = str(row.get("id") or "")
        ui_event_id = "EVT-" + db_id.replace("-", "")[:10].upper() if db_id else "EVT-" + uuid.uuid4().hex[:10].upper()
        if db_id:
            event_map[ui_event_id] = db_id
        event_rows.append({
            "event_id": ui_event_id,
            "instrument_id": reverse_instrument_map.get(str(row.get("instrument_id") or ""), ""),
            "event_date": row.get("event_date") or "",
            "event_type": row.get("event_type") or "",
            "severity": row.get("severity") or "",
            "subsystem": row.get("subsystem") or "",
            "status": row.get("event_status") or "Open",
            "observed_facts": row.get("observed_facts") or "",
            "immediate_action": row.get("immediate_action") or "",
            "root_cause_status": row.get("root_cause_status") or "Not identified",
            "root_cause": row.get("root_cause") or "",
            "reference": row.get("investigation_reference") or "",
            "created_at": row.get("created_at") or "",
        })

    st.session_state.ilm_instruments = _normalize_df(instrument_rows, INSTRUMENT_COLUMNS)
    st.session_state.ilm_events = _normalize_df(event_rows, EVENT_COLUMNS)
    st.session_state._ilm_instrument_db_ids = instrument_map
    st.session_state._ilm_event_db_ids = event_map

    # Restore the most recent investigation brief/result for continuity.
    ok, investigations, _, _ = _db_request(
        "investigations?select=generated_brief,identified_patterns,risk_notes,unknowns,next_actions,conclusion,created_at&order=created_at.desc&limit=1"
    )
    if ok and isinstance(investigations, list) and investigations:
        latest = investigations[0]
        brief = latest.get("generated_brief") or ""
        if brief:
            st.session_state.ilm_last_brief = brief
            st.session_state.ilm_last_result = {
                "patterns": latest.get("identified_patterns") or [],
                "risks": latest.get("risk_notes") or [],
                "unknowns": latest.get("unknowns") or [],
                "next_actions": latest.get("next_actions") or [],
                "conclusion": latest.get("conclusion") or "ROOT CAUSE NOT YET IDENTIFIED",
            }
            st.session_state._ilm_last_persisted_brief = brief

    st.session_state._ilm_loaded_user_id = str(_auth_user().get("id") or "")
    st.session_state._ilm_last_snapshot = _state_snapshot()
    return True


def _state_snapshot():
    instruments = _normalize_df(st.session_state.get("ilm_instruments"), INSTRUMENT_COLUMNS)
    events = _normalize_df(st.session_state.get("ilm_events"), EVENT_COLUMNS)
    payload = {
        "instruments": instruments.astype(str).to_dict(orient="records"),
        "events": events.astype(str).to_dict(orient="records"),
    }
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _save_supabase_state() -> bool:
    if not _auth_token():
        return False

    current_snapshot = _state_snapshot()
    previous_snapshot = st.session_state.get("_ilm_last_snapshot")

    # No instrument/event changes: only persist a new investigation if needed.
    data_changed = current_snapshot != previous_snapshot

    instrument_df = _normalize_df(st.session_state.get("ilm_instruments"), INSTRUMENT_COLUMNS)
    event_df = _normalize_df(st.session_state.get("ilm_events"), EVENT_COLUMNS)
    instrument_map = dict(st.session_state.get("_ilm_instrument_db_ids") or {})
    event_map = dict(st.session_state.get("_ilm_event_db_ids") or {})

    if data_changed:
        current_codes = set(instrument_df["instrument_id"].astype(str).str.strip().str.upper().tolist())

        # Delete instruments removed in the UI. FK cascade removes their events.
        for code, db_id in list(instrument_map.items()):
            if code not in current_codes:
                ok, _, _, _ = _db_request(f"instruments?id=eq.{urlparse.quote(db_id)}", method="DELETE", prefer="return=minimal")
                if not ok:
                    return False
                instrument_map.pop(code, None)

        # Upsert/update instruments one at a time so we retain a stable UUID map.
        for _, row in instrument_df.iterrows():
            body = _instrument_to_db(row)
            code = body["instrument_code"]
            if not code:
                continue
            db_id = instrument_map.get(code)
            if db_id:
                ok, data, _, _ = _db_request(
                    f"instruments?id=eq.{urlparse.quote(db_id)}",
                    method="PATCH",
                    payload=body,
                    prefer="return=representation",
                )
            else:
                ok, data, _, _ = _db_request(
                    "instruments",
                    method="POST",
                    payload=body,
                    prefer="return=representation",
                )
            if not ok:
                return False
            if isinstance(data, list) and data and data[0].get("id"):
                instrument_map[code] = str(data[0]["id"])

        current_event_ids = set(event_df["event_id"].astype(str).tolist())
        for ui_event_id, db_id in list(event_map.items()):
            if ui_event_id not in current_event_ids:
                ok, _, _, _ = _db_request(
                    f"instrument_events?id=eq.{urlparse.quote(db_id)}",
                    method="DELETE",
                    prefer="return=minimal",
                )
                if not ok:
                    return False
                event_map.pop(ui_event_id, None)

        for _, row in event_df.iterrows():
            ui_event_id = str(row.get("event_id") or "").strip()
            body = _event_to_db(row, instrument_map)
            if not ui_event_id or body is None:
                continue
            db_id = event_map.get(ui_event_id)
            if db_id:
                ok, data, _, _ = _db_request(
                    f"instrument_events?id=eq.{urlparse.quote(db_id)}",
                    method="PATCH",
                    payload=body,
                    prefer="return=representation",
                )
            else:
                ok, data, _, _ = _db_request(
                    "instrument_events",
                    method="POST",
                    payload=body,
                    prefer="return=representation",
                )
            if not ok:
                return False
            if isinstance(data, list) and data and data[0].get("id"):
                event_map[ui_event_id] = str(data[0]["id"])

        st.session_state._ilm_instrument_db_ids = instrument_map
        st.session_state._ilm_event_db_ids = event_map
        st.session_state._ilm_last_snapshot = _state_snapshot()

    # Persist each newly generated evidence brief into the investigations table.
    brief = st.session_state.get("ilm_last_brief")
    if isinstance(brief, str) and brief.strip() and brief != st.session_state.get("_ilm_last_persisted_brief"):
        result = st.session_state.get("ilm_last_result") or {}
        instrument_code = str(st.session_state.get("inv_instrument") or "").strip().upper()
        instrument_uuid = instrument_map.get(instrument_code)
        body = {
            "instrument_id": instrument_uuid,
            "title": f"QC Investigation — {instrument_code or 'Instrument'}",
            "identified_patterns": result.get("patterns") or [],
            "risk_notes": result.get("risks") or [],
            "unknowns": result.get("unknowns") or [],
            "next_actions": result.get("next_actions") or [],
            "conclusion": result.get("conclusion") or "ROOT CAUSE NOT YET IDENTIFIED",
            "generated_brief": brief,
        }
        ok, data, _, _ = _db_request(
            "investigations",
            method="POST",
            payload=body,
            prefer="return=representation",
        )
        if not ok:
            return False
        st.session_state._ilm_last_persisted_brief = brief

    return True


# -----------------------------------------------------------------------------
# Configuration / login gate
# -----------------------------------------------------------------------------
st.markdown(
    """
    <style>
      .block-container { max-width: 1180px; padding-top: 3.2rem !important; padding-bottom: 4rem; }
      div[data-baseweb="tab-list"] { overflow-x:auto !important; flex-wrap:nowrap !important; scrollbar-width:none; }
      div[data-baseweb="tab-list"]::-webkit-scrollbar { display:none; }
      button[data-baseweb="tab"] { white-space:nowrap !important; flex:0 0 auto !important; }
      @media (max-width:700px) {
        .block-container { padding-top: 3.8rem !important; padding-left: 1rem !important; padding-right: 1rem !important; }
      }
    </style>
    """,
    unsafe_allow_html=True,
)

if not _supabase_configured():
    st.title("🧪 Yahia QC Instrument Lifecycle")
    st.error("Secure multi-user storage is not configured yet.")
    st.code(
        'SUPABASE_URL = "https://YOUR-PROJECT.supabase.co"\n'
        'SUPABASE_KEY = "sb_publishable_..."',
        language="toml",
    )
    st.caption("Add the values in Streamlit → Manage app → Settings → Secrets. Do not put a service-role/secret key in the app.")
    st.stop()

if not _auth_token():
    st.title("🧪 Yahia QC Instrument Lifecycle")
    st.caption("Secure instrument lifecycle & investigation intelligence · Each account sees only its own data.")
    login_tab, signup_tab = st.tabs(["Sign in", "Create account"])

    with login_tab:
        with st.form("ilm_login"):
            email = st.text_input("Email", autocomplete="email")
            password = st.text_input("Password", type="password", autocomplete="current-password")
            submit_login = st.form_submit_button("Sign in", use_container_width=True)
        if submit_login:
            if not email.strip() or not password:
                st.error("Email and password are required.")
            else:
                ok, message = _auth_login(email, password)
                if ok:
                    st.rerun()
                else:
                    st.error(message)

    with signup_tab:
        with st.form("ilm_signup"):
            display_name = st.text_input("Name")
            new_email = st.text_input("Email", key="signup_email", autocomplete="email")
            new_password = st.text_input("Password", type="password", key="signup_password", autocomplete="new-password")
            confirm_password = st.text_input("Confirm password", type="password", autocomplete="new-password")
            submit_signup = st.form_submit_button("Create account", use_container_width=True)
        if submit_signup:
            if not new_email.strip() or not new_password:
                st.error("Email and password are required.")
            elif len(new_password) < 8:
                st.error("Use a password of at least 8 characters.")
            elif new_password != confirm_password:
                st.error("Passwords do not match.")
            else:
                ok, message, signed_in = _auth_signup(new_email, new_password, display_name)
                if ok and signed_in:
                    st.rerun()
                elif ok:
                    st.success(message)
                else:
                    st.error(message)
    st.stop()

user = _auth_user()
user_id = str(user.get("id") or "")
user_email = str(user.get("email") or "")

# Ensure app data never carries over when a different user logs in on the same
# Streamlit worker/session.
if st.session_state.get("_ilm_loaded_user_id") != user_id:
    for key in [
        "ilm_instruments", "ilm_events", "ilm_last_brief", "ilm_last_result",
        "_ilm_instrument_db_ids", "_ilm_event_db_ids", "_ilm_last_snapshot",
        "_ilm_last_persisted_brief", "inv_instrument"
    ]:
        st.session_state.pop(key, None)
    if not _load_supabase_state():
        st.session_state.ilm_instruments = _normalize_df([], INSTRUMENT_COLUMNS)
        st.session_state.ilm_events = _normalize_df([], EVENT_COLUMNS)
        st.session_state._ilm_instrument_db_ids = {}
        st.session_state._ilm_event_db_ids = {}
        st.session_state._ilm_loaded_user_id = user_id
        st.session_state._ilm_last_snapshot = _state_snapshot()

account_left, account_right = st.columns([5, 1])
account_left.caption(f"🔐 Signed in as {user_email or 'authenticated user'} · Data isolated by Row Level Security")
if account_right.button("Log out", use_container_width=True):
    _save_supabase_state()
    _auth_logout()
    st.rerun()

_original_rerun = st.rerun


def _persistent_rerun(*args, **kwargs):
    if not _save_supabase_state():
        st.session_state._ilm_save_warning = st.session_state.get("_ilm_db_error") or "Could not sync with Supabase"
    return _original_rerun(*args, **kwargs)


st.rerun = _persistent_rerun

# The UI source calls set_page_config itself. We already configured the page
# before the auth gate, so temporarily no-op the duplicate call.
_original_set_page_config = st.set_page_config
st.set_page_config = lambda *args, **kwargs: None

_ui_source = Path(__file__).resolve().parent / "instrument_lifecycle_app.py"
try:
    exec(
        compile(_ui_source.read_text(encoding="utf-8"), str(_ui_source), "exec"),
        globals(),
        globals(),
    )
finally:
    st.set_page_config = _original_set_page_config
    _save_supabase_state()

if st.session_state.get("_ilm_db_error"):
    st.caption(f"⚠️ Supabase sync diagnostic: {st.session_state.get('_ilm_db_error')}")
else:
    st.caption("☁️ Secure storage: Supabase · 🔒 Row Level Security enabled")
