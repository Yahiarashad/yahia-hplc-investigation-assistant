# Yahia QC Instrument Lifecycle & Investigation Intelligence™
# v0.2 — multi-user, evidence-first instrument lifecycle platform.
# Supabase Auth + Row Level Security are the authority for user data isolation.

from __future__ import annotations

# _ILM_APP_SHELL_BOOTSTRAPPED
# Compatibility bootstrap: if Streamlit Cloud still points directly to this
# legacy core file, hand execution to app.py so the current application shell,
# workspace navigation, admin controls and premium Product/User Guide are used.
if __name__ == "__main__" and not globals().get("_ILM_APP_SHELL_BOOTSTRAPPED"):
    globals()["_ILM_APP_SHELL_BOOTSTRAPPED"] = True
    from pathlib import Path as _ILMBootstrapPath
    import streamlit as _ilm_bootstrap_st
    _ilm_shell = _ILMBootstrapPath(__file__).resolve().with_name("app.py")
    exec(compile(_ilm_shell.read_text(encoding="utf-8"), str(_ilm_shell), "exec"), globals(), globals())
    _ilm_bootstrap_st.stop()

import io
import json
from datetime import date, timedelta
from urllib import error as urlerror
from urllib import parse as urlparse
from urllib import request as urlrequest

import pandas as pd
import streamlit as st

try:
    import qrcode
except Exception:
    qrcode = None

st.set_page_config(
    page_title="Yahia QC Instrument Lifecycle & Investigation Intelligence",
    page_icon="🧪",
    layout="wide",
    initial_sidebar_state="collapsed",
)

APP_VERSION = "v0.2"
PRODUCT_NAME = "Yahia QC Instrument Lifecycle & Investigation Intelligence™"
TAGLINE = "DON'T GUESS. FOLLOW THE EVIDENCE."
HPLC_ASSISTANT_URL = "https://yahiaqc.streamlit.app"


def _secret(name: str) -> str:
    try:
        return str(st.secrets.get(name, "") or "").strip()
    except Exception:
        return ""


SUPABASE_URL = _secret("SUPABASE_URL").rstrip("/")
SUPABASE_KEY = _secret("SUPABASE_PUBLISHABLE_KEY") or _secret("SUPABASE_KEY")


def _supabase_configured() -> bool:
    return bool(SUPABASE_URL and SUPABASE_KEY)


def _safe_json(raw):
    if isinstance(raw, bytes):
        raw = raw.decode("utf-8", errors="replace")
    if not raw:
        return None
    try:
        return json.loads(raw)
    except Exception:
        return None


def _http_json(url: str, *, method="GET", payload=None, headers=None, timeout=15):
    req_headers = dict(headers or {})
    data = None
    if payload is not None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        req_headers.setdefault("Content-Type", "application/json")
    req = urlrequest.Request(url, data=data, headers=req_headers, method=method)
    try:
        with urlrequest.urlopen(req, timeout=timeout) as response:
            return True, _safe_json(response.read()), response.status, ""
    except urlerror.HTTPError as exc:
        body = _safe_json(exc.read())
        msg = None
        if isinstance(body, dict):
            msg = body.get("msg") or body.get("message") or body.get("error_description") or body.get("error") or body.get("hint")
        return False, body, exc.code, str(msg or f"HTTP {exc.code}")
    except urlerror.URLError as exc:
        return False, None, 0, f"Connection error: {getattr(exc, 'reason', 'unreachable')}"
    except TimeoutError:
        return False, None, 0, "Connection timeout"
    except Exception as exc:
        return False, None, 0, type(exc).__name__


# Authentication --------------------------------------------------------------
def _auth_headers():
    return {"apikey": SUPABASE_KEY, "Content-Type": "application/json"}


def _set_auth(data: dict):
    st.session_state._ilm_auth = {
        "access_token": data.get("access_token", ""),
        "refresh_token": data.get("refresh_token", ""),
        "expires_at": data.get("expires_at"),
        "user": data.get("user") or {},
    }


def _auth_login(email: str, password: str):
    ok, data, _, err = _http_json(
        f"{SUPABASE_URL}/auth/v1/token?grant_type=password",
        method="POST",
        payload={"email": email.strip(), "password": password},
        headers=_auth_headers(),
    )
    if ok and isinstance(data, dict) and data.get("access_token"):
        _set_auth(data)
        return True, ""
    return False, err or "Login failed."


def _auth_signup(email: str, password: str, display_name: str):
    ok, data, _, err = _http_json(
        f"{SUPABASE_URL}/auth/v1/signup",
        method="POST",
        payload={
            "email": email.strip(),
            "password": password,
            "data": {"display_name": display_name.strip()} if display_name.strip() else {},
        },
        headers=_auth_headers(),
    )
    if not ok:
        return False, err or "Sign-up failed.", False
    if isinstance(data, dict) and data.get("access_token"):
        _set_auth(data)
        return True, "Account created and signed in.", True
    return True, "Account created. Check your email to confirm the account, then sign in.", False


def _auth_refresh() -> bool:
    auth = st.session_state.get("_ilm_auth") or {}
    token = str(auth.get("refresh_token") or "")
    if not token:
        return False
    ok, data, _, _ = _http_json(
        f"{SUPABASE_URL}/auth/v1/token?grant_type=refresh_token",
        method="POST",
        payload={"refresh_token": token},
        headers=_auth_headers(),
    )
    if ok and isinstance(data, dict) and data.get("access_token"):
        _set_auth(data)
        return True
    return False


def _auth_token() -> str:
    return str((st.session_state.get("_ilm_auth") or {}).get("access_token") or "")


def _auth_user() -> dict:
    user = (st.session_state.get("_ilm_auth") or {}).get("user") or {}
    return user if isinstance(user, dict) else {}


def _auth_logout():
    token = _auth_token()
    if token:
        _http_json(
            f"{SUPABASE_URL}/auth/v1/logout",
            method="POST",
            payload={},
            headers={"apikey": SUPABASE_KEY, "Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        )
    for key in list(st.session_state.keys()):
        if key.startswith("_ilm_") or key.startswith("ilm_") or key.startswith("form_"):
            st.session_state.pop(key, None)


# Database --------------------------------------------------------------------
def _db_headers(prefer=None):
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {_auth_token()}",
        "Content-Type": "application/json",
    }
    if prefer:
        headers["Prefer"] = prefer
    return headers


def _db_request(path: str, *, method="GET", payload=None, prefer=None, retry_auth=True):
    ok, data, status, err = _http_json(
        f"{SUPABASE_URL}/rest/v1/{path.lstrip('/')}",
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


def _db_list(table: str, select="*", order=None):
    path = f"{table}?select={urlparse.quote(select, safe=',()*')}"
    if order:
        path += f"&order={urlparse.quote(order, safe='.,')}"
    ok, data, _, err = _db_request(path)
    return (data if ok and isinstance(data, list) else []), err, ok


def _db_insert(table: str, payload: dict):
    return _db_request(table, method="POST", payload=payload, prefer="return=representation")


def _db_patch(table: str, row_id: str, payload: dict):
    return _db_request(
        f"{table}?id=eq.{urlparse.quote(str(row_id))}",
        method="PATCH", payload=payload, prefer="return=representation"
    )


def _db_delete(table: str, row_id: str):
    return _db_request(
        f"{table}?id=eq.{urlparse.quote(str(row_id))}",
        method="DELETE", prefer="return=minimal"
    )


# Date + intelligence helpers --------------------------------------------------
def _parse_date(value):
    if not value:
        return None
    try:
        return pd.to_datetime(value).date()
    except Exception:
        return None


def _days_to(value):
    d = _parse_date(value)
    return (d - date.today()).days if d else None


def _due_label(value):
    days = _days_to(value)
    if days is None: return "Not set"
    if days < 0: return f"OVERDUE by {abs(days)}d"
    if days == 0: return "Due today"
    if days <= 30: return f"Due in {days}d"
    return f"{days}d remaining"


def _severity_weight(severity: str) -> int:
    return {"Critical": 15, "High": 8, "Medium": 3, "Low": 1}.get(str(severity), 2)


def health_score_v2(inst, events, components):
    score = 100
    reasons = []
    status = str(inst.get("operational_status") or "Active")
    if status == "Out of Service":
        score -= 35; reasons.append("Instrument is Out of Service")
    elif status == "Restricted":
        score -= 15; reasons.append("Instrument use is Restricted")
    elif status == "Under Maintenance":
        score -= 10; reasons.append("Instrument is Under Maintenance")

    for label, field in [("Qualification","qualification_due"),("Preventive maintenance","pm_due"),("Calibration","calibration_due")]:
        days = _days_to(inst.get(field))
        if days is None:
            score -= 2; reasons.append(f"{label} due date is not set")
        elif days < 0:
            score -= 12; reasons.append(f"{label} overdue by {abs(days)} days")
        elif days <= 30:
            score -= 5; reasons.append(f"{label} due within {days} days")

    inst_events = [e for e in events if str(e.get("instrument_id")) == str(inst.get("id"))]
    open_events = [e for e in inst_events if str(e.get("event_status")) != "Closed"]
    penalty = min(30, sum(_severity_weight(e.get("severity")) for e in open_events))
    if penalty:
        score -= penalty; reasons.append(f"{len(open_events)} open event(s) require attention")

    cutoff = date.today() - timedelta(days=90)
    recent = [e for e in inst_events if (_parse_date(e.get("event_date")) or date.min) >= cutoff]
    counts = {}
    for e in recent:
        key = str(e.get("subsystem") or "Unknown")
        counts[key] = counts.get(key, 0) + 1
    repeated = [(k,v) for k,v in counts.items() if v >= 3 and k not in ("", "Unknown", "General / Unknown")]
    if repeated:
        score -= 8
        reasons.append("Repeated 90-day subsystem pattern: " + ", ".join(f"{k} ×{v}" for k,v in repeated[:2]))

    overdue_components = 0
    for comp in components:
        if str(comp.get("instrument_id")) != str(inst.get("id")): continue
        days = _days_to(comp.get("replacement_due"))
        if days is not None and days < 0 and str(comp.get("status") or "Active") == "Active":
            overdue_components += 1
    if overdue_components:
        score -= min(20, overdue_components * 10)
        reasons.append(f"{overdue_components} component lifecycle item(s) overdue")
    return max(0, min(100, score)), reasons


def health_state(score):
    if score >= 90: return "Healthy"
    if score >= 75: return "Attention"
    if score >= 55: return "At Risk"
    return "Critical"


def _instrument_code_maps(instruments):
    return (
        {str(x.get("id")): str(x.get("instrument_code") or "") for x in instruments},
        {str(x.get("instrument_code") or ""): str(x.get("id")) for x in instruments},
    )


# Visual identity --------------------------------------------------------------
st.markdown(
    """
<style>
.block-container { max-width: 1180px; padding-top: 4.0rem !important; padding-bottom: 4rem; }
div[data-baseweb="tab-list"] { overflow-x:auto !important; flex-wrap:nowrap !important; scrollbar-width:none; gap:.15rem; }
div[data-baseweb="tab-list"]::-webkit-scrollbar { display:none; }
button[data-baseweb="tab"] { white-space:nowrap !important; flex:0 0 auto !important; }
.hero { background:linear-gradient(145deg,#07111f,#111827); color:white; border:1px solid rgba(201,165,74,.55); border-radius:26px; padding:28px 28px 24px; margin:8px 0 18px; }
.hero-kicker { color:#d6b85f; font-weight:800; letter-spacing:.12em; font-size:.82rem; }
.hero h1 { color:white; font-size:2.15rem; line-height:1.08; margin:.55rem 0 .5rem; }
.hero p { color:#d1d5db; font-size:1.02rem; margin:.3rem 0; }
.gold { color:#d6b85f; font-weight:800; }
.cta { border:1px solid #cbd5e1; border-left:5px solid #d6b85f; border-radius:16px; padding:15px 16px; background:#f8fafc; margin:.6rem 0 1rem; }
@media (max-width:700px) {
 .block-container { padding-top:3.8rem !important; padding-left:.9rem !important; padding-right:.9rem !important; }
 .hero { padding:20px 18px; border-radius:22px; }
 .hero h1 { font-size:1.72rem; }
 .hero p { font-size:.95rem; }
 h1 { font-size:2rem !important; }
 h2 { font-size:1.55rem !important; }
}
</style>
""",
    unsafe_allow_html=True,
)


# Configuration / login --------------------------------------------------------
if not _supabase_configured():
    st.title("🧪 Yahia QC Instrument Lifecycle")
    st.error("Secure multi-user storage is not configured.")
    st.code('SUPABASE_URL = "https://YOUR-PROJECT.supabase.co"\nSUPABASE_KEY = "sb_publishable_..."', language="toml")
    st.stop()

if not _auth_token():
    st.markdown(
        f"""<div class="hero"><div class="hero-kicker">PHARMACEUTICAL QC · INSTRUMENT LIFECYCLE · INVESTIGATION INTELLIGENCE</div><h1>🧪 Yahia QC Instrument Lifecycle</h1><p>Turn instrument history into better laboratory decisions.</p><p class="gold">{TAGLINE}</p></div>""",
        unsafe_allow_html=True,
    )
    st.info("🔐 Each account has its own isolated dataset protected by Supabase Row Level Security.")
    login_tab, signup_tab = st.tabs(["Sign in", "Create account"])
    with login_tab:
        with st.form("login_form"):
            email = st.text_input("Email", autocomplete="email")
            password = st.text_input("Password", type="password", autocomplete="current-password")
            login = st.form_submit_button("Sign in", use_container_width=True)
        if login:
            if not email.strip() or not password: st.error("Email and password are required.")
            else:
                ok, msg = _auth_login(email, password)
                if ok: st.rerun()
                else: st.error(msg)
    with signup_tab:
        with st.form("signup_form"):
            display_name = st.text_input("Name")
            new_email = st.text_input("Email", key="signup_email", autocomplete="email")
            new_password = st.text_input("Password", type="password", key="signup_password", autocomplete="new-password")
            confirm = st.text_input("Confirm password", type="password", autocomplete="new-password")
            create = st.form_submit_button("Create account", use_container_width=True)
        if create:
            if not new_email.strip() or not new_password: st.error("Email and password are required.")
            elif len(new_password) < 8: st.error("Use a password of at least 8 characters.")
            elif new_password != confirm: st.error("Passwords do not match.")
            else:
                ok, msg, signed_in = _auth_signup(new_email, new_password, display_name)
                if ok and signed_in: st.rerun()
                elif ok: st.success(msg)
                else: st.error(msg)
    st.stop()

user = _auth_user()
user_email = str(user.get("email") or "")
meta = user.get("user_metadata") or {}
display_name = str(meta.get("display_name") or user_email.split("@")[0] or "QC Analyst")

with st.sidebar:
    st.markdown(f"### 👤 {display_name}")
    st.caption(user_email)
    st.caption("🔒 Private dataset · RLS protected")
    if st.button("Log out", use_container_width=True):
        _auth_logout(); st.rerun()
    st.divider()
    st.caption(f"{APP_VERSION} · Founding build")
    st.caption(TAGLINE)

st.caption(f"🔐 Signed in as **{user_email}** · Your data is isolated by Row Level Security")


# Load data -------------------------------------------------------------------
instrument_select = "id,instrument_code,instrument_name,instrument_type,manufacturer,model,serial_number,location,operational_status,responsible_team,qualification_due,pm_due,calibration_due,notes,created_at,updated_at"
event_select = "id,instrument_id,event_date,event_type,severity,subsystem,event_status,observed_facts,immediate_action,root_cause_status,root_cause,investigation_reference,created_at,updated_at"
instruments, _, inst_ok = _db_list("instruments", instrument_select, "created_at.asc")
events, _, evt_ok = _db_list("instrument_events", event_select, "event_date.desc")

OPTIONAL_TABLES = {
    "maintenance_records": "id,instrument_id,maintenance_date,maintenance_type,provider,work_order,actions_taken,parts_replaced,result,next_due,notes,created_at",
    "lifecycle_records": "id,instrument_id,record_type,performed_date,result,provider,reference,next_due,notes,created_at",
    "instrument_components": "id,instrument_id,component_name,component_type,part_number,serial_number,installed_date,replacement_due,status,notes,created_at",
}
optional = {}
migration_ready = True
for table, select in OPTIONAL_TABLES.items():
    rows, err, ok = _db_list(table, select, "created_at.desc")
    optional[table] = rows
    if not ok: migration_ready = False
maintenance = optional["maintenance_records"]
lifecycle_records = optional["lifecycle_records"]
components = optional["instrument_components"]

if not (inst_ok and evt_ok):
    st.error("Could not load your core dataset from Supabase.")
    if st.session_state.get("_ilm_db_error"): st.caption(f"Diagnostic: {st.session_state._ilm_db_error}")
    st.stop()

id_to_code, code_to_id = _instrument_code_maps(instruments)
deep_code = ""
try: deep_code = str(st.query_params.get("instrument", "") or "").upper()
except Exception: pass
valid_codes = [str(i.get("instrument_code") or "") for i in instruments]
if deep_code and deep_code not in valid_codes: deep_code = ""


# Welcome / importance / CTA ---------------------------------------------------
st.markdown(
    f"""<div class="hero"><div class="hero-kicker">PHARMACEUTICAL QC · INSTRUMENT LIFECYCLE · INVESTIGATION INTELLIGENCE</div><h1>Welcome, {display_name} 👋</h1><p><b>{PRODUCT_NAME}</b></p><p>Bring lifecycle dates, maintenance, failures, components, and investigations into one evidence-first view.</p><p class="gold">{TAGLINE}</p></div>""",
    unsafe_allow_html=True,
)

with st.expander("Why this application matters | لماذا هذا التطبيق مهم؟", expanded=(len(instruments) == 0)):
    st.markdown("""
**The problem:** instrument information is often scattered across logbooks, spreadsheets, work orders, emails, and individual memory.

**This application helps you:**
- see what is due before it becomes overdue,
- preserve a usable instrument history,
- detect repeated failure patterns without calling them root cause,
- connect maintenance and component history to investigations,
- prioritize attention with an explainable Health Score,
- keep each user's data private and isolated.

**Important:** this is decision-support software, not a validated GxP system of record. Official GMP records remain in your approved systems and SOP-controlled forms.

**ببساطة:** الهدف ليس تخزين بيانات أكثر؛ الهدف أن تصبح بيانات الجهاز مفيدة عند اتخاذ القرار.
""")

open_events = [e for e in events if str(e.get("event_status")) != "Closed"]
overdue_items = 0
due_30 = 0
for inst in instruments:
    for f in ("qualification_due","pm_due","calibration_due"):
        days = _days_to(inst.get(f))
        if days is not None and days < 0: overdue_items += 1
        elif days is not None and days <= 30: due_30 += 1
for comp in components:
    days = _days_to(comp.get("replacement_due"))
    if days is not None and str(comp.get("status") or "Active") == "Active":
        if days < 0: overdue_items += 1
        elif days <= 30: due_30 += 1

m1,m2 = st.columns(2); m1.metric("Instruments", len(instruments)); m2.metric("Open events", len(open_events))
m3,m4 = st.columns(2); m3.metric("Overdue items", overdue_items); m4.metric("Due ≤30 days", due_30)

if len(instruments) == 0:
    cta = "Recommended next action → Create your first Instrument Passport.|Start with identity, location, ownership, and the three critical lifecycle dates: qualification, PM, and calibration."
elif overdue_items:
    cta = f"Recommended next action → Review {overdue_items} overdue lifecycle item(s).|Resolve the due-date picture before relying on Health Score for prioritization."
elif open_events:
    cta = f"Recommended next action → Review {len(open_events)} open event(s).|Use Investigation Intelligence when evidence is incomplete or recurrence may matter."
else:
    cta = "Recommended next action → Keep the history alive.|Log maintenance, qualification/calibration, component changes, and failures when they occur."
cta_title, cta_text = cta.split("|",1)
st.markdown(f'<div class="cta"><b>{cta_title}</b><br>{cta_text}</div>', unsafe_allow_html=True)

if not migration_ready:
    st.warning("v0.2 lifecycle modules are not installed yet. Core Instruments / Events / Investigation remain available. Run `supabase_v02_migration.sql` in Supabase SQL Editor to enable Maintenance, Qualification/Calibration, and Components.")

tabs = st.tabs(["Command Center","Instrument Passport","Lifecycle","Events","Investigation Intelligence","Guide"])


# Command Center ---------------------------------------------------------------
with tabs[0]:
    st.header("Instrument Command Center")
    if not instruments:
        st.info("No instruments yet. Open **Instrument Passport** and create your first instrument.")
    else:
        rows=[]; attention=[]
        for inst in instruments:
            score,reasons = health_score_v2(inst, events, components)
            rows.append({"Instrument":inst.get("instrument_code"),"Name":inst.get("instrument_name"),"Type":inst.get("instrument_type"),"Status":inst.get("operational_status"),"Health":score,"State":health_state(score),"Primary signal":reasons[0] if reasons else "No major signal detected"})
            if score < 90 or reasons: attention.append((score,inst,reasons))
        st.dataframe(pd.DataFrame(rows).sort_values(["Health","Instrument"]), use_container_width=True, hide_index=True)
        st.subheader("Priority attention queue")
        if not attention: st.success("No major lifecycle or event signal is currently detected.")
        else:
            for score,inst,reasons in sorted(attention,key=lambda x:x[0])[:8]:
                with st.expander(f"{inst.get('instrument_code')} · {health_state(score)} · {score}/100"):
                    for reason in reasons: st.write(f"• {reason}")
                    st.caption("Health Score prioritizes attention. It does not determine compliance, release, or qualification validity.")
        st.subheader("Upcoming lifecycle actions")
        due_rows=[]
        for inst in instruments:
            for label,field in [("Qualification","qualification_due"),("PM","pm_due"),("Calibration","calibration_due")]:
                days=_days_to(inst.get(field))
                if days is not None and days <= 60: due_rows.append({"Instrument":inst.get("instrument_code"),"Action":label,"Due date":inst.get(field),"Days":days,"Status":"OVERDUE" if days<0 else "Upcoming"})
        for comp in components:
            days=_days_to(comp.get("replacement_due"))
            if days is not None and days <= 60 and str(comp.get("status") or "Active") == "Active":
                due_rows.append({"Instrument":id_to_code.get(str(comp.get("instrument_id")),""),"Action":f"Component: {comp.get('component_name')}","Due date":comp.get("replacement_due"),"Days":days,"Status":"OVERDUE" if days<0 else "Upcoming"})
        if due_rows: st.dataframe(pd.DataFrame(due_rows).sort_values("Days"),use_container_width=True,hide_index=True)
        else: st.success("No lifecycle item is due within the next 60 days.")


# Instrument Passport ----------------------------------------------------------
with tabs[1]:
    st.header("Instrument Registry & Passport")
    st.caption("Add one instrument, import an instrument list, then open any asset's Digital Passport.")
    with st.expander("➕ Add one instrument | إضافة جهاز", expanded=(len(instruments)==0)):
        with st.form("add_instrument", clear_on_submit=True):
            c1,c2=st.columns(2); code=c1.text_input("Instrument ID *",placeholder="HPLC-001"); name=c2.text_input("Instrument name *",placeholder="Waters Alliance")
            c1,c2,c3=st.columns(3); inst_type=c1.selectbox("Type",["HPLC","UHPLC","GC","LC-MS","LC-MS/MS","UV-Vis","Dissolution","Balance","pH Meter","Other"]); manufacturer=c2.text_input("Manufacturer"); model=c3.text_input("Model")
            c1,c2,c3=st.columns(3); serial=c1.text_input("Serial number"); location=c2.text_input("Location"); owner=c3.text_input("Responsible team")
            status=st.selectbox("Operational status",["Active","Restricted","Under Maintenance","Out of Service","Retired"])
            c1,c2,c3=st.columns(3); q_due=c1.date_input("Qualification due",value=date.today()+timedelta(days=365)); pm_due=c2.date_input("PM due",value=date.today()+timedelta(days=180)); cal_due=c3.date_input("Calibration due",value=date.today()+timedelta(days=180))
            notes=st.text_area("Notes"); submit=st.form_submit_button("Create Instrument Passport",use_container_width=True)
        if submit:
            clean=code.strip().upper()
            if not clean or not name.strip(): st.error("Instrument ID and name are required.")
            elif clean in code_to_id: st.error("This Instrument ID already exists in your account.")
            else:
                ok,_,_,err=_db_insert("instruments",{"instrument_code":clean,"instrument_name":name.strip(),"instrument_type":inst_type,"manufacturer":manufacturer.strip(),"model":model.strip(),"serial_number":serial.strip(),"location":location.strip(),"operational_status":status,"responsible_team":owner.strip(),"qualification_due":q_due.isoformat(),"pm_due":pm_due.isoformat(),"calibration_due":cal_due.isoformat(),"notes":notes.strip()})
                if ok: st.success(f"{clean} created."); st.rerun()
                else: st.error(err or "Could not create instrument.")

    with st.expander("📥 إضافة / استيراد قائمة أجهزة | Import Instrument List", expanded=False):
        if callable(globals().get("_render_excel_import")):
            _render_excel_import()
        else:
            st.error("Instrument list import is temporarily unavailable.")

    if instruments:
        with st.expander("📋 سجل الأجهزة الحالي | Current Instrument Registry", expanded=False):
            st.caption("Search the live registry, then export the complete current list in the same controlled format used by Import Instrument List.")
            registry_rows = [{
                "Instrument ID": x.get("instrument_code") or "",
                "Instrument name": x.get("instrument_name") or "",
                "Type": x.get("instrument_type") or "",
                "Manufacturer": x.get("manufacturer") or "",
                "Model": x.get("model") or "",
                "Location": x.get("location") or "",
                "Status": x.get("operational_status") or "",
            } for x in instruments]
            registry_df = pd.DataFrame(registry_rows)

            if callable(globals().get("_excel_export_bytes")):
                st.download_button(
                    "⬇️ Download Current Instrument List (.xlsx)",
                    data=_excel_export_bytes(instruments),
                    file_name="Yahia_QC_Current_Instrument_Registry.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True,
                    key="download_current_instrument_registry",
                )
                st.caption("Template-compatible export: edit approved fields, then preview and re-upload through Import Instrument List when needed.")

            q = st.text_input(
                "Search registry",
                placeholder="Instrument ID, name, model, manufacturer, location…",
                key="instrument_registry_search",
            ).strip().lower()
            status_values = sorted([str(v) for v in registry_df["Status"].dropna().unique() if str(v).strip()])
            selected_statuses = st.multiselect(
                "Status filter",
                status_values,
                default=[],
                key="instrument_registry_status_filter",
            )

            filtered_df = registry_df.copy()
            if q:
                mask = filtered_df.astype(str).apply(
                    lambda col: col.str.lower().str.contains(q, regex=False)
                ).any(axis=1)
                filtered_df = filtered_df[mask]
            if selected_statuses:
                filtered_df = filtered_df[filtered_df["Status"].isin(selected_statuses)]

            st.caption(f"Showing {len(filtered_df)} of {len(registry_df)} instruments")
            st.dataframe(filtered_df, use_container_width=True, hide_index=True)

        codes=[str(x.get("instrument_code")) for x in instruments]; default_index=codes.index(deep_code) if deep_code in codes else 0
        selected_code=st.selectbox("Open Instrument 360",codes,index=default_index,key="passport_selected")
        inst=next(x for x in instruments if str(x.get("instrument_code"))==selected_code); inst_id=str(inst.get("id")); score,reasons=health_score_v2(inst,events,components)

        # Instrument 360 assembles the connected story without inventing missing evidence.
        inst_events=[e for e in events if str(e.get("instrument_id"))==inst_id]
        open_inst_events=[e for e in inst_events if str(e.get("event_status"))!="Closed"]
        inst_maintenance=[r for r in maintenance if str(r.get("instrument_id"))==inst_id]
        inst_lifecycle=[r for r in lifecycle_records if str(r.get("instrument_id"))==inst_id]
        inst_components=[r for r in components if str(r.get("instrument_id"))==inst_id]

        perf_rows=[]
        perf_ok=False
        try:
            _all_perf, _perf_err, perf_ok = _db_list(
                "instrument_monthly_performance",
                "id,instrument_id,month_start,scheduled_hours,planned_downtime_hours,unplanned_downtime_hours,productive_run_hours,notes,created_at,updated_at",
                "month_start.desc",
            )
            if perf_ok:
                perf_rows=[r for r in _all_perf if str(r.get("instrument_id"))==inst_id]
        except Exception:
            perf_rows=[]
            perf_ok=False

        def _i360_perf_metrics(row):
            if not row:
                return None, None, None, None
            scheduled=float(row.get("scheduled_hours") or 0)
            planned=float(row.get("planned_downtime_hours") or 0)
            unplanned=float(row.get("unplanned_downtime_hours") or 0)
            productive=float(row.get("productive_run_hours") or 0)
            planned_operating=max(0.0,scheduled-planned)
            available=max(0.0,planned_operating-unplanned)
            availability=(available/planned_operating*100.0) if planned_operating>0 else None
            utilization=(productive/available*100.0) if available>0 else None
            return planned_operating,available,availability,utilization

        latest_perf=perf_rows[0] if perf_rows else None
        latest_planned,latest_available,latest_availability,latest_utilization=_i360_perf_metrics(latest_perf)

        st.markdown(
            f'''<div style="border:1px solid rgba(201,165,74,.65);border-radius:22px;padding:1rem 1.05rem;background:linear-gradient(145deg,#071422,#10263a);margin:.65rem 0 1rem;color:#e7eef5">
            <div style="font-size:.76rem;letter-spacing:.12em;color:#d6b85f;font-weight:800">INSTRUMENT 360 · CONNECTED ASSET STORY</div>
            <div style="font-size:1.35rem;font-weight:800;color:#fff;margin:.28rem 0">{selected_code} · {inst.get('instrument_name') or 'Unnamed instrument'}</div>
            <div style="color:#b8c6d3;font-size:.92rem">{inst.get('instrument_type') or 'Type not set'} · {inst.get('manufacturer') or 'Manufacturer not set'} · {inst.get('model') or 'Model not set'}</div>
            <div style="margin-top:.45rem;color:#d6b85f;font-size:.84rem;font-weight:700">IDENTITY → LIFECYCLE → CONTROL → PERFORMANCE → EVENTS → EVIDENCE</div>
            </div>''',
            unsafe_allow_html=True,
        )

        _health_label=health_state(score)
        _health_color="#59d98e" if score>=85 else ("#f3c969" if score>=70 else "#ff7b7b")
        _availability_text="—" if latest_availability is None else f"{latest_availability:.1f}%"
        _utilization_text="—" if latest_utilization is None else f"{latest_utilization:.1f}%"
        st.markdown(
            f'''<div style="margin:-.35rem 0 .9rem;padding:.85rem 1rem;border:1px solid {_health_color};border-radius:18px;background:rgba(255,255,255,.025)">
                <div style="font-size:.72rem;letter-spacing:.12em;color:#aebdca;font-weight:800">INSTRUMENT HEALTH SCORE</div>
                <div style="display:flex;align-items:baseline;gap:.55rem;flex-wrap:wrap;margin-top:.15rem">
                    <span style="font-size:2rem;line-height:1;font-weight:900;color:{_health_color}">{score}/100</span>
                    <span style="font-size:.95rem;font-weight:800;color:{_health_color}">{_health_label}</span>
                </div>
            </div>
            <div style="display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:.55rem;margin-bottom:.75rem">
                <div style="padding:.7rem .8rem;border:1px solid #344252;border-radius:14px;background:#111923"><div style="font-size:.72rem;color:#8fa0af">STATUS</div><div style="font-size:1rem;font-weight:800;color:#f6f8fb">{inst.get('operational_status') or '—'}</div></div>
                <div style="padding:.7rem .8rem;border:1px solid #344252;border-radius:14px;background:#111923"><div style="font-size:.72rem;color:#8fa0af">OPEN EVENTS</div><div style="font-size:1rem;font-weight:800;color:#f6f8fb">{len(open_inst_events)}</div></div>
                <div style="padding:.7rem .8rem;border:1px solid #344252;border-radius:14px;background:#111923"><div style="font-size:.72rem;color:#8fa0af">AVAILABILITY</div><div style="font-size:1rem;font-weight:800;color:#f6f8fb">{_availability_text}</div></div>
                <div style="padding:.7rem .8rem;border:1px solid #344252;border-radius:14px;background:#111923"><div style="font-size:.72rem;color:#8fa0af">UTILIZATION</div><div style="font-size:1rem;font-weight:800;color:#f6f8fb">{_utilization_text}</div></div>
            </div>''',
            unsafe_allow_html=True,
        )
        st.caption("Decision-support signal only — not a GMP disposition or root-cause conclusion.")

        # Put score explainability immediately beside the score so users do not
        # need to hunt inside Control to understand why a device needs attention.
        # Keep it collapsed on mobile: the score is the primary signal; detail is on demand.
        _score_driver_count = len(reasons)
        with st.expander(f"Why {score}/100? · {_score_driver_count} score driver(s)", expanded=False):
            if reasons:
                for _reason in reasons:
                    st.write(f"• {_reason}")
            else:
                st.success("No current lifecycle, status, event, recurrence, or overdue-component penalty is affecting this score.")
            st.caption("The Health Score is an explainable prioritization signal. It is not a release decision, compliance verdict, or root-cause conclusion.")

        # Evidence-consistency attention signal. Keep the first-layer message short
        # for mobile and place governance wording behind an on-demand explanation.
        _status_value = str(inst.get("operational_status") or "Active")
        if _status_value in ("Out of Service", "Restricted", "Under Maintenance") and not open_inst_events:
            st.warning(
                f"⚠ Management Attention\n\n{_status_value} with no active linked event. "
                "Confirm the reason, reference, and current control decision are documented."
            )
            with st.expander("Why am I seeing this?", expanded=False):
                st.write(
                    "The instrument status indicates a controlled condition, while no active instrument event is currently linked in this application. "
                    "That mismatch is surfaced so the team can confirm traceability to the appropriate approved record."
                )
                st.caption(
                    "Evidence-consistency signal only — not a GMP compliance conclusion, not proof of a missing record, and not a root-cause determination."
                )

        with st.expander("🪪 IDENTITY | الهوية", expanded=True):
            identity_rows=[
                {"Field":"Instrument ID","Value":selected_code},
                {"Field":"Instrument name","Value":inst.get("instrument_name") or "Missing Evidence"},
                {"Field":"Type","Value":inst.get("instrument_type") or "Missing Evidence"},
                {"Field":"Manufacturer","Value":inst.get("manufacturer") or "Missing Evidence"},
                {"Field":"Model","Value":inst.get("model") or "Missing Evidence"},
                {"Field":"Serial number","Value":inst.get("serial_number") or "Missing Evidence"},
                {"Field":"Location","Value":inst.get("location") or "Missing Evidence"},
                {"Field":"Responsible team","Value":inst.get("responsible_team") or "Missing Evidence"},
            ]
            st.dataframe(pd.DataFrame(identity_rows),use_container_width=True,hide_index=True)

        with st.expander("↻ LIFECYCLE | دورة حياة الجهاز", expanded=False):
            l1,l2,l3=st.columns(3)
            l1.metric("Maintenance records",len(inst_maintenance))
            l2.metric("Calibration / Qualification",len(inst_lifecycle))
            l3.metric("Tracked components",len(inst_components))
            if inst_maintenance:
                st.markdown("**Latest maintenance**")
                maint_view=[]
                for r in sorted(inst_maintenance,key=lambda x:str(x.get("maintenance_date") or ""),reverse=True)[:5]:
                    maint_view.append({"Date":r.get("maintenance_date"),"Type":r.get("maintenance_type"),"Result":r.get("result"),"Provider":r.get("provider"),"Next due":r.get("next_due")})
                st.dataframe(pd.DataFrame(maint_view),use_container_width=True,hide_index=True)
            if inst_lifecycle:
                st.markdown("**Latest calibration / qualification evidence**")
                life_view=[]
                for r in sorted(inst_lifecycle,key=lambda x:str(x.get("performed_date") or ""),reverse=True)[:5]:
                    life_view.append({"Date":r.get("performed_date"),"Record":r.get("record_type"),"Result":r.get("result"),"Reference":r.get("reference"),"Next due":r.get("next_due")})
                st.dataframe(pd.DataFrame(life_view),use_container_width=True,hide_index=True)
            if not inst_maintenance and not inst_lifecycle:
                st.info("No maintenance / calibration / qualification history has been recorded for this instrument yet.")

        with st.expander("◎ CONTROL | حالة التحكم الحالية", expanded=False):
            control_rows=[]
            for _label,_field in [("Qualification","qualification_due"),("Preventive Maintenance","pm_due"),("Calibration","calibration_due")]:
                _value=inst.get(_field)
                control_rows.append({"Control":_label,"Due date":_value or "Missing Evidence","Status":_due_label(_value) if _value else "Missing Evidence"})
            st.dataframe(pd.DataFrame(control_rows),use_container_width=True,hide_index=True)
            if reasons:
                st.caption("Health Score drivers are shown above under ‘Why this score?’ so the Control view stays focused on current due-date and component control.")
            if inst_components:
                st.markdown("**Component control**")
                comp_view=[]
                for r in inst_components:
                    comp_view.append({"Component":r.get("component_name"),"Type":r.get("component_type"),"Status":r.get("status"),"Replacement / review due":r.get("replacement_due"),"Due signal":_due_label(r.get("replacement_due"))})
                st.dataframe(pd.DataFrame(comp_view),use_container_width=True,hide_index=True)
            else:
                st.caption("No components are currently tracked for this instrument.")

        with st.expander("📈 PERFORMANCE | Availability & Utilization", expanded=False):
            if not perf_ok:
                st.info("Monthly performance storage is not available in this workspace yet.")
            elif not perf_rows:
                st.info("No monthly Availability / Utilization record has been entered for this instrument yet. Open Performance to record the first month.")
            else:
                p1,p2,p3,p4=st.columns(4)
                p1.metric("Month",str(latest_perf.get("month_start") or "—")[:7])
                p2.metric("Availability","—" if latest_availability is None else f"{latest_availability:.1f}%")
                p3.metric("Utilization","—" if latest_utilization is None else f"{latest_utilization:.1f}%")
                p4.metric("Available time","—" if latest_available is None else f"{latest_available:.1f} h")
                trend=[]
                for r in sorted(perf_rows,key=lambda x:str(x.get("month_start") or ""))[-6:]:
                    _po,_av,_a,_u=_i360_perf_metrics(r)
                    trend.append({"Month":str(r.get("month_start") or "")[:7],"Availability %":None if _a is None else round(_a,1),"Utilization %":None if _u is None else round(_u,1)})
                if trend:
                    trend_df=pd.DataFrame(trend)
                    st.line_chart(trend_df.set_index("Month")[["Availability %","Utilization %"]],use_container_width=True)
                    st.dataframe(trend_df.sort_values("Month",ascending=False),use_container_width=True,hide_index=True)
            if callable(globals().get("_ilm_route_href")):
                st.markdown(f'<a href="{_ilm_route_href("📈 Performance")}#ilm-top" style="display:block;text-align:center;padding:.7rem;border:1px solid #c9a54d;border-radius:14px;text-decoration:none;font-weight:800">Open full Performance Intelligence →</a>',unsafe_allow_html=True)

        with st.expander("⚠ EVENTS | الأعطال والإشارات", expanded=False):
            e1,e2=st.columns(2)
            e1.metric("All events",len(inst_events))
            e2.metric("Open / active",len(open_inst_events))
            if inst_events:
                event_view=[]
                for r in sorted(inst_events,key=lambda x:str(x.get("event_date") or ""),reverse=True)[:8]:
                    event_view.append({"Date":r.get("event_date"),"Event":r.get("event_type"),"Severity":r.get("severity"),"Subsystem":r.get("subsystem"),"Status":r.get("event_status"),"Root cause status":r.get("root_cause_status")})
                st.dataframe(pd.DataFrame(event_view),use_container_width=True,hide_index=True)
            else:
                st.success("No instrument events are currently recorded for this asset.")
            if callable(globals().get("_ilm_route_href")):
                st.markdown(f'<a href="{_ilm_route_href("⚠ Events")}#ilm-top" style="display:block;text-align:center;padding:.7rem;border:1px solid #cbd5e1;border-radius:14px;text-decoration:none;font-weight:700">Open Event / Failure Log →</a>',unsafe_allow_html=True)

        with st.expander("▦ EVIDENCE | Passport & traceability", expanded=False):
            missing=[]
            for _label,_field in [("Manufacturer","manufacturer"),("Model","model"),("Serial number","serial_number"),("Location","location"),("Responsible team","responsible_team"),("Qualification due","qualification_due"),("PM due","pm_due"),("Calibration due","calibration_due")]:
                if not inst.get(_field):
                    missing.append(_label)
            if missing:
                st.warning("Missing Evidence: "+", ".join(missing))
            else:
                st.success("Core identity and due-date evidence is populated for this instrument.")

            refs=[]
            for r in inst_lifecycle:
                if r.get("reference"):
                    refs.append({"Evidence":r.get("record_type") or "Lifecycle record","Date":r.get("performed_date"),"Reference":r.get("reference")})
            for r in inst_maintenance:
                if r.get("work_order"):
                    refs.append({"Evidence":r.get("maintenance_type") or "Maintenance","Date":r.get("maintenance_date"),"Reference":r.get("work_order")})
            for r in inst_events:
                if r.get("investigation_reference"):
                    refs.append({"Evidence":"Event / investigation","Date":r.get("event_date"),"Reference":r.get("investigation_reference")})
            if refs:
                st.markdown("**Connected references**")
                st.dataframe(pd.DataFrame(refs).sort_values("Date",ascending=False),use_container_width=True,hide_index=True)
            else:
                st.caption("No certificate / protocol / work-order / investigation reference is currently connected to this asset.")

            st.markdown("**QR Digital Passport**")
            st.write("Scan the QR to reopen this instrument after authentication. RLS still controls access.")
            try: app_url=str(st.context.url)
            except Exception: app_url=""
            if app_url:
                link=app_url.split("?")[0]+f"?instrument={urlparse.quote(selected_code)}"; st.code(link)
                if qrcode:
                    qr=qrcode.make(link); buf=io.BytesIO(); qr.save(buf,format="PNG"); st.image(buf.getvalue(),width=190); st.download_button("Download QR",buf.getvalue(),file_name=f"{selected_code}_passport_qr.png",mime="image/png",key=f"i360_qr_{inst_id}")
                else: st.caption("QR rendering package is not installed; the deep link above is ready to use.")
            else: st.caption("Open the deployed app URL to generate a QR deep link.")
        with st.expander("✏️ Edit instrument"):
            with st.form(f"edit_{inst_id}"):
                c1,c2=st.columns(2); e_name=c1.text_input("Instrument name",value=str(inst.get("instrument_name") or "")); types=["HPLC","UHPLC","GC","LC-MS","LC-MS/MS","UV-Vis","Dissolution","Balance","pH Meter","Other"]; cur_type=str(inst.get("instrument_type") or "Other"); e_type=c2.selectbox("Type",types,index=types.index(cur_type) if cur_type in types else len(types)-1)
                c1,c2,c3=st.columns(3); e_manu=c1.text_input("Manufacturer",value=str(inst.get("manufacturer") or "")); e_model=c2.text_input("Model",value=str(inst.get("model") or "")); e_serial=c3.text_input("Serial number",value=str(inst.get("serial_number") or ""))
                c1,c2,c3=st.columns(3); e_loc=c1.text_input("Location",value=str(inst.get("location") or "")); statuses=["Active","Restricted","Under Maintenance","Out of Service","Retired"]; cur_status=str(inst.get("operational_status") or "Active"); e_status=c2.selectbox("Operational status",statuses,index=statuses.index(cur_status) if cur_status in statuses else 0); e_owner=c3.text_input("Responsible team",value=str(inst.get("responsible_team") or ""))
                def valdate(v,fallback): return _parse_date(v) or fallback
                c1,c2,c3=st.columns(3); e_q=c1.date_input("Qualification due",value=valdate(inst.get("qualification_due"),date.today())); e_pm=c2.date_input("PM due",value=valdate(inst.get("pm_due"),date.today())); e_cal=c3.date_input("Calibration due",value=valdate(inst.get("calibration_due"),date.today()))
                e_notes=st.text_area("Notes",value=str(inst.get("notes") or "")); save=st.form_submit_button("Save changes",use_container_width=True)
            if save:
                ok,_,_,err=_db_patch("instruments",inst_id,{"instrument_name":e_name.strip(),"instrument_type":e_type,"manufacturer":e_manu.strip(),"model":e_model.strip(),"serial_number":e_serial.strip(),"location":e_loc.strip(),"operational_status":e_status,"responsible_team":e_owner.strip(),"qualification_due":e_q.isoformat(),"pm_due":e_pm.isoformat(),"calibration_due":e_cal.isoformat(),"notes":e_notes.strip()})
                if ok: st.success("Instrument updated."); st.rerun()
                else: st.error(err or "Could not update instrument.")
        with st.expander("🗑️ Retire / delete instrument"):
            st.warning("Deleting an instrument also removes linked event history through database cascade rules. Export first if needed.")
            confirm_code=st.text_input("Type the Instrument ID to confirm deletion",key=f"delete_confirm_{inst_id}")
            if st.button("Delete instrument permanently",key=f"delete_{inst_id}",use_container_width=True):
                if confirm_code.strip().upper()!=selected_code.upper(): st.error("Instrument ID confirmation does not match.")
                else:
                    ok,_,_,err=_db_delete("instruments",inst_id)
                    if ok: st.success("Instrument deleted."); st.rerun()
                    else: st.error(err or "Could not delete instrument.")


# Lifecycle -------------------------------------------------------------------
with tabs[2]:
    st.header("Lifecycle Control")
    st.caption("Maintenance, calibration/qualification, and component life — connected to the same instrument history.")
    if not instruments: st.info("Create an Instrument Passport first.")
    elif not migration_ready: st.error("v0.2 lifecycle tables are not installed. Run `supabase_v02_migration.sql` in Supabase SQL Editor.")
    else:
        codes=[str(x.get("instrument_code")) for x in instruments]; lifecycle_code=st.selectbox("Instrument",codes,key="lifecycle_instrument"); lifecycle_inst_id=code_to_id[lifecycle_code]
        sub1,sub2,sub3=st.tabs(["Maintenance","Calibration & Qualification","Components"])
        with sub1:
            with st.form("maintenance_form",clear_on_submit=True):
                c1,c2=st.columns(2); m_date=c1.date_input("Maintenance date",value=date.today()); m_type=c2.selectbox("Maintenance type",["Preventive Maintenance","Corrective Maintenance","Inspection","Cleaning / Service","Vendor Service","Other"])
                c1,c2=st.columns(2); provider=c1.text_input("Provider / technician"); wo=c2.text_input("Work-order / service reference")
                actions=st.text_area("Actions taken *"); parts=st.text_area("Parts replaced")
                c1,c2=st.columns(2); result=c1.selectbox("Result",["Completed / Pass","Completed with observation","Pending","Failed / Follow-up required"]); next_due=c2.date_input("Next due",value=date.today()+timedelta(days=180))
                notes=st.text_area("Notes",key="maint_notes"); save=st.form_submit_button("Save maintenance record",use_container_width=True)
            if save:
                if not actions.strip(): st.error("Actions taken are required.")
                else:
                    ok,_,_,err=_db_insert("maintenance_records",{"instrument_id":lifecycle_inst_id,"maintenance_date":m_date.isoformat(),"maintenance_type":m_type,"provider":provider.strip(),"work_order":wo.strip(),"actions_taken":actions.strip(),"parts_replaced":parts.strip(),"result":result,"next_due":next_due.isoformat(),"notes":notes.strip()})
                    if ok:
                        if m_type=="Preventive Maintenance": _db_patch("instruments",lifecycle_inst_id,{"pm_due":next_due.isoformat()})
                        st.success("Maintenance record saved."); st.rerun()
                    else: st.error(err or "Could not save maintenance record.")
            rows=[x for x in maintenance if str(x.get("instrument_id"))==lifecycle_inst_id]
            if rows: st.dataframe(pd.DataFrame(rows),use_container_width=True,hide_index=True)
            else: st.info("No maintenance history yet.")
        with sub2:
            with st.form("lifecycle_record_form",clear_on_submit=True):
                c1,c2=st.columns(2); record_type=c1.selectbox("Record type",["Calibration","Qualification","Requalification","IQ","OQ","PQ","Verification","Other"]); performed=c2.date_input("Performed date",value=date.today())
                c1,c2=st.columns(2); lc_result=c1.selectbox("Result",["Pass","Pass with observation","Pending","Fail"]); lc_provider=c2.text_input("Provider / executed by")
                reference=st.text_input("Certificate / protocol / report reference"); next_due=st.date_input("Next due",value=date.today()+timedelta(days=365),key="lc_next_due"); lc_notes=st.text_area("Notes",key="lc_notes"); save_lc=st.form_submit_button("Save lifecycle record",use_container_width=True)
            if save_lc:
                ok,_,_,err=_db_insert("lifecycle_records",{"instrument_id":lifecycle_inst_id,"record_type":record_type,"performed_date":performed.isoformat(),"result":lc_result,"provider":lc_provider.strip(),"reference":reference.strip(),"next_due":next_due.isoformat(),"notes":lc_notes.strip()})
                if ok:
                    if record_type=="Calibration": _db_patch("instruments",lifecycle_inst_id,{"calibration_due":next_due.isoformat()})
                    elif record_type in ("Qualification","Requalification","IQ","OQ","PQ"): _db_patch("instruments",lifecycle_inst_id,{"qualification_due":next_due.isoformat()})
                    st.success("Lifecycle record saved."); st.rerun()
                else: st.error(err or "Could not save lifecycle record.")
            rows=[x for x in lifecycle_records if str(x.get("instrument_id"))==lifecycle_inst_id]
            if rows: st.dataframe(pd.DataFrame(rows),use_container_width=True,hide_index=True)
            else: st.info("No calibration / qualification history yet.")
        with sub3:
            with st.form("component_form",clear_on_submit=True):
                c1,c2=st.columns(2); comp_name=c1.text_input("Component name *",placeholder="Pump seal / lamp / check valve"); comp_type=c2.selectbox("Component type",["Consumable","Wear part","Critical component","Detector component","Pump component","Injector component","Other"])
                c1,c2=st.columns(2); part_no=c1.text_input("Part number"); comp_serial=c2.text_input("Serial number")
                c1,c2=st.columns(2); installed=c1.date_input("Installed date",value=date.today()); replacement=c2.date_input("Replacement / review due",value=date.today()+timedelta(days=365))
                comp_status=st.selectbox("Status",["Active","Monitor","Replace soon","Replaced","Retired"]); comp_notes=st.text_area("Notes",key="comp_notes"); save_comp=st.form_submit_button("Add component",use_container_width=True)
            if save_comp:
                if not comp_name.strip(): st.error("Component name is required.")
                else:
                    ok,_,_,err=_db_insert("instrument_components",{"instrument_id":lifecycle_inst_id,"component_name":comp_name.strip(),"component_type":comp_type,"part_number":part_no.strip(),"serial_number":comp_serial.strip(),"installed_date":installed.isoformat(),"replacement_due":replacement.isoformat(),"status":comp_status,"notes":comp_notes.strip()})
                    if ok: st.success("Component added."); st.rerun()
                    else: st.error(err or "Could not add component.")
            rows=[x for x in components if str(x.get("instrument_id"))==lifecycle_inst_id]
            if rows:
                comp_df=pd.DataFrame(rows); comp_df["Due status"]=comp_df["replacement_due"].apply(_due_label); st.dataframe(comp_df,use_container_width=True,hide_index=True)
                st.caption("Component due dates are planning signals. Confirm replacement criteria against approved procedures and manufacturer recommendations.")
            else: st.info("No tracked components yet.")


# Events ----------------------------------------------------------------------
with tabs[3]:
    st.header("Instrument Event / Failure Log")
    st.caption("Record observations first. Diagnosis comes later.")
    if not instruments: st.info("Create an Instrument Passport first.")
    else:
        codes=[str(x.get("instrument_code")) for x in instruments]
        with st.form("event_form",clear_on_submit=True):
            c1,c2=st.columns(2); event_code=c1.selectbox("Instrument *",codes); event_date=c2.date_input("Event date",value=date.today())
            c1,c2,c3=st.columns(3); event_type=c1.selectbox("Event type",["High Pressure","Low Pressure","Leak","Retention Time Shift","Peak Shape","Baseline","Carryover","SST Failure","Communication / Software","Temperature","Autosampler / Injector","Detector","Pump","Other"]); severity=c2.selectbox("Severity",["Low","Medium","High","Critical"]); subsystem=c3.selectbox("Subsystem",["Flow Path","Pump","Injector / Autosampler","Column Compartment","Detector","Degasser","Software / CDS","Electrical","Gas Supply","General / Unknown","Other"])
            status=st.selectbox("Status",["Open","Under Investigation","Monitoring","Closed"]); observed=st.text_area("Observed facts *",placeholder="What was actually observed or reported? Avoid embedding the suspected diagnosis."); immediate=st.text_area("Immediate action / containment")
            c1,c2=st.columns(2); rc_status=c1.selectbox("Root cause status",["Not identified","Probable","Confirmed"]); root_cause=c2.text_input("Root cause / hypothesis")
            reference=st.text_input("Deviation / investigation / work-order reference"); save_event=st.form_submit_button("Save event",use_container_width=True)
        if save_event:
            if not observed.strip(): st.error("Observed facts are required.")
            elif rc_status=="Confirmed" and not root_cause.strip(): st.error("A confirmed root cause must include the confirmed cause.")
            else:
                ok,_,_,err=_db_insert("instrument_events",{"instrument_id":code_to_id[event_code],"event_date":event_date.isoformat(),"event_type":event_type,"severity":severity,"subsystem":subsystem,"event_status":status,"observed_facts":observed.strip(),"immediate_action":immediate.strip(),"root_cause_status":rc_status,"root_cause":root_cause.strip(),"investigation_reference":reference.strip()})
                if ok: st.success("Event saved."); st.rerun()
                else: st.error(err or "Could not save event.")
        if events:
            event_rows=[]
            for e in events:
                row=dict(e); row["instrument"]=id_to_code.get(str(e.get("instrument_id")),""); event_rows.append(row)
            st.dataframe(pd.DataFrame(event_rows),use_container_width=True,hide_index=True)
        else: st.info("No instrument events yet.")


# Investigation Intelligence ---------------------------------------------------
with tabs[4]:
    st.header("QC Investigation Intelligence™")
    st.caption("Evidence-first decision support. Recurrence is a clue — never automatic proof of root cause.")
    if not instruments: st.info("Create an Instrument Passport first.")
    else:
        codes=[str(x.get("instrument_code")) for x in instruments]; inv_code=st.selectbox("Instrument under investigation",codes,key="inv_code"); inv_id=code_to_id[inv_code]; inst=next(x for x in instruments if str(x.get("id"))==inv_id); score,score_reasons=health_score_v2(inst,events,components)
        c1,c2=st.columns(2); c1.metric("Current Health",f"{score}/100",health_state(score)); c2.metric("Open events",len([e for e in events if str(e.get("instrument_id"))==inv_id and str(e.get("event_status"))!="Closed"]))
        with st.form("investigation_form"):
            expected=st.text_area("1) What was expected?"); observed=st.text_area("2) What happened actually?"); changed=st.text_area("3) What changed recently?"); unchanged=st.text_area("4) What stayed unchanged?"); evidence=st.text_area("5) Objective evidence available"); analyze=st.form_submit_button("Build evidence brief",use_container_width=True)
        if analyze:
            inst_events=[e for e in events if str(e.get("instrument_id"))==inv_id]; cutoff=date.today()-timedelta(days=90); recent=[e for e in inst_events if (_parse_date(e.get("event_date")) or date.min)>=cutoff]
            patterns=[]; by_type={}; by_sub={}
            for e in recent:
                t=str(e.get("event_type") or "Unknown"); s=str(e.get("subsystem") or "Unknown"); by_type[t]=by_type.get(t,0)+1; by_sub[s]=by_sub.get(s,0)+1
            for k,v in sorted(by_type.items(),key=lambda x:-x[1]):
                if v>=2: patterns.append(f"{k} appeared {v} times in the last 90 days.")
            for k,v in sorted(by_sub.items(),key=lambda x:-x[1]):
                if v>=3 and k not in ("Unknown","General / Unknown",""): patterns.append(f"{k} subsystem appears in {v} recent events.")
            if score_reasons: patterns.extend([f"Lifecycle / health signal: {x}" for x in score_reasons[:4]])
            inst_components=[c for c in components if str(c.get("instrument_id"))==inv_id]; overdue_comps=[c for c in inst_components if (_days_to(c.get("replacement_due")) if _days_to(c.get("replacement_due")) is not None else 99999)<0 and str(c.get("status") or "Active")=="Active"]
            if overdue_comps: patterns.append("Overdue component lifecycle: "+", ".join(str(c.get("component_name")) for c in overdue_comps[:3]))
            risks=[]
            for label,field in [("Qualification","qualification_due"),("PM","pm_due"),("Calibration","calibration_due")]:
                d=_days_to(inst.get(field))
                if d is not None and d<0: risks.append(f"{label} is overdue by {abs(d)} days.")
                elif d is not None and d<=30: risks.append(f"{label} is due within {d} days.")
            if any(str(e.get("severity")) in ("High","Critical") and str(e.get("event_status"))!="Closed" for e in inst_events): risks.append("There is an open High/Critical event in this instrument history.")
            unknowns=[]
            if not expected.strip(): unknowns.append("Expected behavior / acceptance target is not documented in this brief.")
            if not observed.strip(): unknowns.append("Actual observed behavior is not sufficiently described.")
            if not changed.strip(): unknowns.append("Recent changes are unknown or not documented.")
            if not unchanged.strip(): unknowns.append("Controls / factors that stayed unchanged are not documented.")
            if not evidence.strip(): unknowns.append("Objective evidence has not been listed.")
            next_actions=["Preserve the current objective evidence before changing the system.","Separate observed/reported facts from hypotheses and unknowns."]
            if patterns: next_actions.append("Use the strongest historical pattern to choose one discriminating test — do not treat recurrence as proof.")
            else: next_actions.append("Localize the problem by subsystem before replacing parts or changing multiple variables.")
            text=(observed+" "+expected).lower()
            if "pressure" in text: next_actions.append("For a pressure symptom, localize restriction stepwise across the flow path under approved conditions before blaming the column.")
            if "carryover" in text: next_actions.append("For carryover, discriminate sample-path memory from wash / needle / seat / sequence effects with one controlled test at a time.")
            next_actions.append("Only call the root cause confirmed when a targeted intervention changes the outcome as predicted and credible alternatives are reasonably excluded.")
            conclusion="ROOT CAUSE NOT YET IDENTIFIED"
            brief=f"""# QC Investigation Evidence Brief — {inv_code}\n\n## OBSERVED / REPORTED\n**Expected:** {expected.strip() or 'Not provided'}\n**Actual:** {observed.strip() or 'Not provided'}\n**Changed:** {changed.strip() or 'Not established'}\n**Unchanged:** {unchanged.strip() or 'Not established'}\n**Objective evidence:** {evidence.strip() or 'Not listed'}\n\n## HISTORICAL PATTERNS / SIGNALS\n{chr(10).join('- '+x for x in patterns) if patterns else '- No repeated pattern detected from current history.'}\n\n## RISK / ATTENTION NOTES\n{chr(10).join('- '+x for x in risks) if risks else '- No lifecycle alert detected from current data.'}\n\n## UNKNOWN / MISSING EVIDENCE\n{chr(10).join('- '+x for x in unknowns) if unknowns else '- No major evidence gap flagged by the current rule set.'}\n\n## NEXT EVIDENCE ACTION\n{chr(10).join('- '+x for x in next_actions)}\n\n## CONCLUSION\n**{conclusion}**\n\n> Recurrence, overdue maintenance, or a component lifecycle signal can strengthen a hypothesis. None of them independently confirms root cause.\n"""
            st.session_state.ilm_last_brief=brief; st.session_state.ilm_last_result={"patterns":patterns,"risks":risks,"unknowns":unknowns,"next_actions":next_actions,"conclusion":conclusion}
            ok,_,_,err=_db_insert("investigations",{"instrument_id":inv_id,"title":f"QC Investigation — {inv_code}","expected_behavior":expected.strip(),"observed_behavior":observed.strip(),"what_changed":changed.strip(),"what_stayed_unchanged":unchanged.strip(),"objective_evidence":evidence.strip(),"identified_patterns":patterns,"risk_notes":risks,"unknowns":unknowns,"next_actions":next_actions,"conclusion":conclusion,"generated_brief":brief})
            if not ok: st.warning(f"Brief generated, but database save did not complete: {err or 'unknown error'}")
        if st.session_state.get("ilm_last_brief"):
            result=st.session_state.get("ilm_last_result") or {}; st.subheader("Evidence Map"); c1,c2=st.columns(2)
            with c1:
                st.markdown("**Patterns / signals**"); [st.write(f"• {x}") for x in (result.get("patterns") or ["No repeat pattern detected."])]
                st.markdown("**Risk notes**"); [st.write(f"• {x}") for x in (result.get("risks") or ["No current lifecycle alert detected."])]
            with c2:
                st.markdown("**Unknown / missing evidence**"); [st.write(f"• {x}") for x in (result.get("unknowns") or ["No major evidence gap flagged."])]
                st.markdown("**Next evidence action**"); [st.write(f"• {x}") for x in (result.get("next_actions") or [])]
            st.warning(result.get("conclusion") or "ROOT CAUSE NOT YET IDENTIFIED")
            with st.expander("Full investigation brief"): st.markdown(st.session_state.ilm_last_brief)
            st.download_button("Download investigation brief (.md)",data=st.session_state.ilm_last_brief.encode("utf-8"),file_name=f"{inv_code}_investigation_brief.md",mime="text/markdown",use_container_width=True)
            st.link_button("Open Yahia HPLC Investigation Assistant ↗",HPLC_ASSISTANT_URL,use_container_width=True)


# Guide -----------------------------------------------------------------------
with tabs[5]:
    if callable(globals().get("render_v03_user_guide")):
        render_v03_user_guide()
    else:
        st.header("Guide")
        st.error("Premium Product & User Guide module could not load.")

st.divider()
st.caption(f"Yahia Abdelhalim · Pharmaceutical QC Expert · {APP_VERSION} · Helping Pharmaceutical Analysts Make Better Laboratory Decisions")
