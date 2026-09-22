# Yahia QC Instrument Lifecycle — persistent-auth application shell
# v0.6: lifecycle-first navigation + performance intelligence + executive PDF + management cockpit + email escalation.

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
    initial_sidebar_state="auto",
)

RemoveEmptyElementContainer()
controller = CookieController(key="ilm_auth_cookie_controller")
COOKIE_NAME = "yahia_qc_ilm_refresh_v1"


# -----------------------------------------------------------------------------
# Mobile / Arabic reading polish. Technical IDs, tables and form values remain
# LTR unless their own component explicitly requests RTL.
# -----------------------------------------------------------------------------
st.markdown(
    """
<style>
.v03-guide-rtl, .ilm-rtl {
  direction: rtl !important;
  text-align: right !important;
  unicode-bidi: plaintext;
}
.v03-guide-rtl ul, .ilm-rtl ul {
  direction: rtl !important;
  text-align: right !important;
  padding-right: 1.4rem !important;
  padding-left: 0 !important;
}
.v03-guide-rtl li, .ilm-rtl li {
  direction: rtl !important;
  text-align: right !important;
  unicode-bidi: plaintext;
  margin:.35rem 0;
}

/* Practical User Guide: force Arabic reading order for all narrative Markdown
   inside the guide expander. The Excel widgets/tables keep their native layout. */
div[data-testid="stExpander"]:has(.v03-guide-flow) div[data-testid="stMarkdownContainer"] {
  direction: rtl !important;
  text-align: right !important;
  unicode-bidi: plaintext;
}
div[data-testid="stExpander"]:has(.v03-guide-flow) div[data-testid="stMarkdownContainer"] ul,
div[data-testid="stExpander"]:has(.v03-guide-flow) div[data-testid="stMarkdownContainer"] ol {
  direction: rtl !important;
  text-align: right !important;
  padding-right: 1.5rem !important;
  padding-left: 0 !important;
  margin-right: 0 !important;
}
div[data-testid="stExpander"]:has(.v03-guide-flow) div[data-testid="stMarkdownContainer"] li {
  direction: rtl !important;
  text-align: right !important;
  unicode-bidi: plaintext;
}
.v03-guide-flow {
  direction: rtl !important;
  text-align: right !important;
  unicode-bidi: plaintext !important;
  border-right: 4px solid #d4af37 !important;
  border-left: 0 !important;
  line-height: 1.9 !important;
}

@media(max-width:700px){
  .v03-guide-rtl, .ilm-rtl { line-height:1.85; }
  div[data-testid="stExpander"]:has(.v03-guide-flow) div[data-testid="stMarkdownContainer"] {
    line-height: 1.85 !important;
  }
  .v03-guide-flow {
    line-height: 2 !important;
    padding: .8rem .9rem !important;
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


# Restore the signed-in session before the core app reaches its auth gate.
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


_real_rerun = st.rerun


def _cookie_aware_rerun(*args, **kwargs):
    _write_auth_cookie()
    return _real_rerun(*args, **kwargs)


st.rerun = _cookie_aware_rerun


# Mobile navigation helper: after choosing a route, close the sidebar and
# return the main viewport to the first line of the newly selected workspace.
def _ilm_mobile_route_transition():
    try:
        import streamlit.components.v1 as components
        components.html(
            """<script>
            try {
              const w = window.parent;
              w.scrollTo({top: 0, behavior: 'instant'});
              const sidebar = w.document.querySelector('section[data-testid="stSidebar"]');
              const collapse = sidebar && sidebar.querySelector('button[data-testid="stSidebarCollapseButton"], button[aria-label*="Close sidebar"], button[aria-label*="Collapse sidebar"]');
              if (collapse && w.innerWidth <= 768) { collapse.click(); }
            } catch (e) {}
            </script>""",
            height=0,
            width=0,
        )
    except Exception:
        pass


# -----------------------------------------------------------------------------
# Role-aware onboarding + persistent workspace navigation.
# The role personalizes priorities; it does NOT change RLS permissions.
# -----------------------------------------------------------------------------
_signed_in_shell = bool((st.session_state.get("_ilm_auth") or {}).get("access_token"))

ROLE_OPTIONS = [
    ("QC Analyst", "Daily execution · events · investigations · evidence"),
    ("QC Supervisor", "Team control · exceptions · due work · investigations"),
    ("QC Manager", "Operations · performance · capacity · escalations"),
    ("QC Director / Head", "Business risk · capacity · investment · executive evidence"),
    ("Calibration / Maintenance", "Calibration · PM · qualification · components"),
    ("QA / Reviewer", "Evidence readiness · traceability · open quality signals"),
]
ROLE_LABELS = [item[0] for item in ROLE_OPTIONS]
ROLE_HELP = {item[0]: item[1] for item in ROLE_OPTIONS}

if _signed_in_shell and not st.session_state.get("ilm_user_role"):
    @st.dialog("Welcome · Set up your workspace")
    def _ilm_role_onboarding():
        st.markdown("### What is your role in QC?")
        st.caption("We will organize the workspace around the decisions you make. This does not change your database permissions.")
        role = st.selectbox(
            "Your role",
            options=ROLE_LABELS,
            key="ilm_role_onboarding_select",
        )
        role_label = str(role or "QC Analyst")
        role_help = ROLE_HELP.get(role_label, ROLE_HELP["QC Analyst"])
        st.info(role_help)
        if st.button("Enter my workspace →", type="primary", use_container_width=True, key="ilm_role_onboarding_go"):
            st.session_state.ilm_user_role = role_label
            st.session_state.ilm_route = "🏠 Dashboard"
            st.rerun()
    _ilm_role_onboarding()

_ALL_ROUTE_GROUPS = {
    "HOME": ["🏠 Dashboard"],
    "MY INSTRUMENTS": ["🪪 Passport", "↻ Lifecycle"],
    "CONTROL": ["◎ Cal & PM"],
    "QUALITY EVENTS": ["⚠ Events", "🔎 Investigate"],
    "INTELLIGENCE": ["📈 Performance"],
    "COMMUNICATION": ["🔔 Alerts"],
    "EVIDENCE": ["▦ Reports"],
    "MANAGEMENT": ["🎛 Cockpit"],
    "SYSTEM": ["ⓘ Guide"],
    "ADMIN": ["🛡 Admin"],
}

_ROLE_ROUTE_GROUPS = {
    "QC Analyst": ["HOME", "MY INSTRUMENTS", "QUALITY EVENTS", "EVIDENCE", "SYSTEM"],
    "QC Supervisor": ["HOME", "MY INSTRUMENTS", "CONTROL", "QUALITY EVENTS", "INTELLIGENCE", "COMMUNICATION", "EVIDENCE", "SYSTEM"],
    "QC Manager": ["HOME", "MY INSTRUMENTS", "CONTROL", "QUALITY EVENTS", "INTELLIGENCE", "COMMUNICATION", "EVIDENCE", "MANAGEMENT", "SYSTEM"],
    "QC Director / Head": ["HOME", "INTELLIGENCE", "COMMUNICATION", "EVIDENCE", "MANAGEMENT", "SYSTEM"],
    "Calibration / Maintenance": ["HOME", "MY INSTRUMENTS", "CONTROL", "QUALITY EVENTS", "EVIDENCE", "SYSTEM"],
    "QA / Reviewer": ["HOME", "MY INSTRUMENTS", "CONTROL", "QUALITY EVENTS", "COMMUNICATION", "EVIDENCE", "MANAGEMENT", "SYSTEM"],
}
_ilm_workspaces, _ilm_workspace_id, _ilm_membership = ([], None, None)
if _signed_in_shell and "_workspace_context" in globals():
    try:
        _ilm_workspaces, _ilm_workspace_id, _ilm_membership = _workspace_context()
    except Exception:
        pass
if _ilm_membership and _ilm_membership.get("job_role"):
    st.session_state.ilm_user_role = str(_ilm_membership.get("job_role"))
_active_role = st.session_state.get("ilm_user_role", "QC Analyst")
_allowed_groups = _ROLE_ROUTE_GROUPS.get(_active_role, _ROLE_ROUTE_GROUPS["QC Analyst"])
if _ilm_membership and _ilm_membership.get("is_admin") and "ADMIN" not in _allowed_groups:
    _allowed_groups = list(_allowed_groups) + ["ADMIN"]
_ROUTE_GROUPS = {name: _ALL_ROUTE_GROUPS[name] for name in _allowed_groups}

_ROUTE_ITEMS = [item for group in _ROUTE_GROUPS.values() for item in group]

if _signed_in_shell and st.session_state.get("ilm_user_role"):
    if st.session_state.pop("ilm_route_transition", False):
        _ilm_mobile_route_transition()
    with st.sidebar:
        st.markdown("## QC Intelligence")
        st.caption("From data → evidence → decision → action")
        st.markdown(f"**{st.session_state.ilm_user_role}**")
        st.caption(ROLE_HELP.get(st.session_state.ilm_user_role, ""))
        if _ilm_workspaces and _ilm_workspace_id:
            _ws_names = {str(w.get("id")): str(w.get("name") or "Workspace") for w in _ilm_workspaces}
            _ws_ids = list(_ws_names)
            if len(_ws_ids) > 1:
                _chosen_ws = st.selectbox("Workspace", _ws_ids, index=_ws_ids.index(_ilm_workspace_id), format_func=lambda x: _ws_names[x], key="ilm_workspace_picker")
                if _chosen_ws != _ilm_workspace_id:
                    st.session_state.ilm_workspace_id = _chosen_ws
                    st.session_state.ilm_route = "🏠 Dashboard"
                    st.rerun()
            else:
                st.caption("🏢 " + _ws_names.get(_ilm_workspace_id, "Workspace"))
            if _ilm_membership and _ilm_membership.get("is_admin"):
                st.caption("🛡 Workspace Admin")
        st.divider()
        current = st.session_state.get("ilm_route", "🏠 Dashboard")
        if current not in _ROUTE_ITEMS:
            current = "🏠 Dashboard"
        for group_name, group_items in _ROUTE_GROUPS.items():
            st.caption(group_name)
            for route_item in group_items:
                is_active = route_item == current
                if st.button(
                    route_item,
                    key="ilm_nav_" + route_item,
                    use_container_width=True,
                    type="primary" if is_active else "secondary",
                ):
                    if not is_active:
                        st.session_state.ilm_route = route_item
                        st.session_state.ilm_route_transition = True
                        st.rerun()
        st.divider()
        if st.button("Change my role", use_container_width=True, key="ilm_change_role"):
            st.session_state.pop("ilm_user_role", None)
            st.rerun()

    # Desktop: sidebar is the permanent navigation rail. Mobile: Streamlit's
    # responsive sidebar is collapsed; make the menu trigger self-explanatory.
    st.markdown("""
    <style>
    @media (min-width: 769px) {
      section[data-testid="stSidebar"] { min-width: 285px !important; max-width: 285px !important; }
      section[data-testid="stSidebar"] > div { width: 285px !important; }
    }
    </style>
    """, unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# Load extension definitions before the core is executed.
# -----------------------------------------------------------------------------
def _exec_extension(filename: str, error_key: str | None = None):
    try:
        module_path = Path(__file__).resolve().parent / filename
        if module_path.exists():
            exec(compile(module_path.read_text(encoding="utf-8"), str(module_path), "exec"), globals(), globals())
    except Exception as exc:
        if error_key:
            st.session_state[error_key] = type(exc).__name__


_exec_extension("instrument_v03_user_guide.py", "_ilm_guide_module_error")
_exec_extension("instrument_camera_capture.py", "_ilm_camera_module_error")
_exec_extension("instrument_monthly_performance.py", "_ilm_performance_module_error")
_exec_extension("instrument_pdf_reports.py", "_ilm_pdf_module_error")
_exec_extension("instrument_executive_performance_report.py", "_ilm_exec_report_module_error")
_exec_extension("instrument_notification_center.py", "_ilm_notification_module_error")
_exec_extension("instrument_admin_control.py", "_ilm_admin_module_error")


# -----------------------------------------------------------------------------
# Arabic PDF font hardening.
# Streamlit Cloud images do not guarantee system Arabic fonts. matplotlib ships
# DejaVu Sans with broad Arabic coverage, so use it as a deterministic embedded
# PDF font source before falling back to OS fonts. This patches both PDF engines
# loaded above without storing or exposing user font files.
# -----------------------------------------------------------------------------
def _ilm_pdf_font_paths():
    candidates = []
    try:
        import matplotlib
        mpl_fonts = Path(matplotlib.get_data_path()) / "fonts" / "ttf"
        candidates.extend([
            (mpl_fonts / "DejaVuSans.ttf", mpl_fonts / "DejaVuSans-Bold.ttf"),
        ])
    except Exception:
        pass
    candidates.extend([
        (Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"), Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf")),
        (Path("/usr/share/fonts/truetype/freefont/FreeSans.ttf"), Path("/usr/share/fonts/truetype/freefont/FreeSansBold.ttf")),
    ])
    for regular, bold in candidates:
        try:
            if regular.exists() and bold.exists():
                return str(regular), str(bold)
        except Exception:
            continue
    return None, None


# instrument_pdf_reports.py resolves _find_arabic_font at call time.
if "_find_arabic_font" in globals():
    _find_arabic_font = _ilm_pdf_font_paths
# instrument_executive_performance_report.py resolves _font_paths at call time.
if "_font_paths" in globals():
    _font_paths = _ilm_pdf_font_paths


# -----------------------------------------------------------------------------
# Convert the original six core tabs into the lifecycle-first navigation.
# -----------------------------------------------------------------------------
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


def _tabs_v04(labels, *args, **kwargs):
    global _core_main_tabs_seen
    items = list(labels)
    if items == _MAIN_TABS:
        _core_main_tabs_seen = True
        display_items = [
            "🏠 Dashboard", "↻ Lifecycle", "🪪 Passport", "◎ Cal & PM",
            "📈 Performance", "⚠ Events", "🔎 Investigate", "🔔 Alerts",
            "▦ Reports", "ⓘ Guide", "🎛 Cockpit",
        ]
        selected = st.session_state.get("ilm_route", "🏠 Dashboard")
        if selected not in _ROUTE_ITEMS:
            selected = "🏠 Dashboard"
            st.session_state.ilm_route = selected
        active_idx = display_items.index(selected)

        # The legacy core expects tab-like context managers. Use keyed containers
        # instead, then hide every inactive route by its stable Streamlit key class.
        # This makes the sidebar the ONLY navigation and guarantees one visible workspace.
        rendered = [
            st.container(key=f"ilm_workspace_{idx}")
            for idx, _route in enumerate(display_items)
        ]
        hide_rules = []
        for idx in range(len(display_items)):
            if idx != active_idx:
                hide_rules.append(f".st-key-ilm_workspace_{idx}{{display:none!important;}}")
        st.markdown(
            "<style>" + "".join(hide_rules) +
            ".st-key-ilm_workspace_" + str(active_idx) + "{display:block!important;}" +
            "</style>",
            unsafe_allow_html=True,
        )

        return [
            rendered[8], rendered[2], rendered[3], rendered[5], rendered[6],
            rendered[9], rendered[0], rendered[1], rendered[4], rendered[10],
            rendered[7],
        ]
    return _real_tabs(items, *args, **kwargs)

st.tabs = _tabs_v04


# Hide the old duplicate pre-navigation metrics/CTA. The new Dashboard owns them.
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


# The core configures the page too; this shell already did it.
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


# -----------------------------------------------------------------------------
# Decorative instrument imagery — strong in hero areas, never behind data entry.
# -----------------------------------------------------------------------------
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
.hero {{ min-height:220px;display:flex;flex-direction:column;justify-content:center; }}
@media(max-width:700px){{
  .hero {{ min-height:205px;background-position:58% center!important; }}
}}
</style>
""",
            unsafe_allow_html=True,
        )
except Exception:
    pass


main_tabs = globals().get("tabs")
_is_signed_in = bool(globals().get("_auth_token") and _auth_token())


# Dashboard -------------------------------------------------------------------
try:
    if isinstance(main_tabs, list) and len(main_tabs) >= 10 and _is_signed_in:
        dashboard_module = Path(__file__).resolve().parent / "instrument_v03_dashboard.py"
        with main_tabs[6]:
            exec(compile(dashboard_module.read_text(encoding="utf-8"), str(dashboard_module), "exec"), globals(), globals())
except Exception as exc:
    try:
        with main_tabs[6]:
            st.error("Dashboard could not load.")
            st.caption(f"Diagnostic: {type(exc).__name__}")
    except Exception:
        pass


# Full Lifecycle Navigator -----------------------------------------------------
try:
    if isinstance(main_tabs, list) and len(main_tabs) >= 10 and _is_signed_in:
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


# Performance: Availability + Utilization + target intelligence ----------------
try:
    if isinstance(main_tabs, list) and len(main_tabs) >= 10 and _is_signed_in:
        with main_tabs[8]:
            if callable(globals().get("render_instrument_performance")):
                render_instrument_performance()
            else:
                st.error("Monthly Performance module could not load.")
except Exception as exc:
    try:
        with main_tabs[8]:
            st.error("Monthly Performance module could not load.")
            st.caption(f"Diagnostic: {type(exc).__name__}")
    except Exception:
        pass


# Instrument Management Cockpit ------------------------------------------------
try:
    if isinstance(main_tabs, list) and len(main_tabs) >= 10 and _is_signed_in:
        cockpit_module = Path(__file__).resolve().parent / "instrument_management_cockpit.py"
        with main_tabs[9]:
            exec(compile(cockpit_module.read_text(encoding="utf-8"), str(cockpit_module), "exec"), globals(), globals())
            if callable(globals().get("render_instrument_management_cockpit")):
                render_instrument_management_cockpit()
            else:
                st.error("Instrument Management Cockpit could not load.")
except Exception as exc:
    try:
        with main_tabs[9]:
            st.error("Instrument Management Cockpit could not load.")
            st.caption(f"Diagnostic: {type(exc).__name__}")
    except Exception:
        pass


# Three-level email notification center ----------------------------------------
try:
    if isinstance(main_tabs, list) and len(main_tabs) >= 11 and _is_signed_in:
        with main_tabs[10]:
            if callable(globals().get("render_instrument_notification_center")):
                render_instrument_notification_center()
            else:
                st.error("Email Notification Center could not load.")
except Exception as exc:
    try:
        with main_tabs[10]:
            st.error("Email Notification Center could not load completely.")
            st.caption(f"Diagnostic: {type(exc).__name__}")
    except Exception:
        pass


# Reports: lifecycle evidence PDF + executive monthly performance intelligence --
try:
    if isinstance(main_tabs, list) and len(main_tabs) >= 1 and _is_signed_in:
        with main_tabs[0]:
            st.divider()
            if callable(globals().get("render_pdf_report_center")):
                render_pdf_report_center(globals(), ui_lang="ar")
            if callable(globals().get("render_executive_performance_report")):
                render_executive_performance_report()
except Exception as exc:
    try:
        with main_tabs[0]:
            st.error("Advanced Report Center could not load completely.")
            st.caption(f"Diagnostic: {type(exc).__name__}")
    except Exception:
        pass


# Detailed Calibration Control stays inside Cal & PM ---------------------------
try:
    if isinstance(main_tabs, list) and len(main_tabs) >= 3 and _is_signed_in:
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


# -----------------------------------------------------------------------------
# Final interaction polish — loaded last so it overrides module-local defaults.
# -----------------------------------------------------------------------------
st.markdown(
    """
<style>
/* Clean application shell. Primary navigation is rendered only in the sidebar. */\n\n/* Legacy signed-in preamble emitted by instrument_supabase_app.py */
section.main .hero:not(.v03-dashboard-hero){display:none!important;}
section.main .cta{display:none!important;}

/* The core emits four standalone metrics before the main tabs. They are legacy
   landing-page content; the role-aware Dashboard owns the signed-in summary. */
section.main div[data-testid="stMetric"]:not(.v03-dashboard-hero div[data-testid="stMetric"]){
  /* individual module metrics are intentionally not globally hidden */
}

/* Tactile controls */
.stButton > button,
.stFormSubmitButton > button,
.stDownloadButton > button{
  border-radius:13px!important;
  min-height:44px!important;
  font-weight:700!important;
  border:1px solid #dbe3ec!important;
  box-shadow:0 3px 10px rgba(15,23,42,.04)!important;
  transition:transform .12s ease, box-shadow .12s ease!important;
}
.stButton > button:hover,
.stFormSubmitButton > button:hover,
.stDownloadButton > button:hover{
  transform:translateY(-1px)!important;
  box-shadow:0 7px 16px rgba(15,23,42,.08)!important;
}

/* Lifecycle journey cards */
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
.v03-step.complete{border-left-color:#17a673!important;background:#fbfffd!important;}
.v03-step.current{border-left-color:#d6a92f!important;background:#fffdf5!important;box-shadow:0 7px 20px rgba(214,169,47,.10)!important;}
.v03-step.attention{border-left-color:#dc3545!important;background:#fffafa!important;}
.v03-step.ongoing{border-left-color:#2274a5!important;background:#f8fcff!important;}
.v03-step.future{opacity:.82;}

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
