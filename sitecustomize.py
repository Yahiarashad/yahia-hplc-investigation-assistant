"""Application-wide startup customizations for Yahia QC Instrument Lifecycle.

Product shell decisions:
1) Keep the signed-in workspace focused on one page at a time.
2) Replace the crowded top-level tab strip with a persistent grouped sidebar.
3) Preserve the selected workspace across Streamlit reruns (including PDF generation).
4) Keep secondary expanders collapsed by default, except the active PDF Report Center.
5) Pre-register premium Arabic PDF typography using system-installed Noto fonts.

No font files are bundled with or exposed by the application.
"""

from pathlib import Path


# ---------------------------------------------------------------------------
# Streamlit application shell: persistent sidebar + one active workspace.
# ---------------------------------------------------------------------------
try:
    import streamlit as st

    _ilm_native_expander_default = st.expander
    _ilm_native_tabs = st.tabs
    _ilm_native_page_config = st.set_page_config

    _ILM_MAIN_TABS = [
        "🏠 Dashboard",
        "↻ Lifecycle",
        "🪪 Passport",
        "◎ Cal & PM",
        "📈 Performance",
        "⚠ Events",
        "🔎 Investigate",
        "🔔 Alerts",
        "▦ Reports",
        "ⓘ Guide",
        "🎛 Cockpit",
    ]
    _ILM_LEGACY_TAB = "__CORE_LEGACY__"

    _ILM_NAV_GROUPS = [
        ("", [
            ("🏠 Dashboard", "🏠 Dashboard"),
        ]),
        ("INSTRUMENT MANAGEMENT", [
            ("🪪 Instrument Passport", "🪪 Passport"),
            ("↻ Lifecycle", "↻ Lifecycle"),
            ("🎛 Decision Cockpit", "🎛 Cockpit"),
        ]),
        ("CONTROL & PERFORMANCE", [
            ("◎ Calibration & PM", "◎ Cal & PM"),
            ("📈 Monthly Performance", "📈 Performance"),
        ]),
        ("QUALITY & DECISIONS", [
            ("⚠ Events", "⚠ Events"),
            ("🔎 Investigation", "🔎 Investigate"),
            ("🔔 Email Alerts", "🔔 Alerts"),
        ]),
        ("REPORTS & SUPPORT", [
            ("▦ Reports", "▦ Reports"),
            ("ⓘ User Guide", "ⓘ Guide"),
        ]),
    ]

    def _ilm_page_config(*args, **kwargs):
        kwargs["initial_sidebar_state"] = "expanded"
        return _ilm_native_page_config(*args, **kwargs)

    st.set_page_config = _ilm_page_config

    def _ilm_collapsed_expander(label, *args, **kwargs):
        """Collapse secondary content, but keep the active report workflow open."""
        text = str(label)
        active = st.session_state.get("ilm_sidebar_page", "🏠 Dashboard")
        report_center = "PDF Report Center" in text or "مركز التقارير" in text
        kwargs["expanded"] = bool(active == "▦ Reports" and report_center)
        return _ilm_native_expander_default(label, *args, **kwargs)

    st.expander = _ilm_collapsed_expander

    def _ilm_sidebar_menu():
        active = st.session_state.get("ilm_sidebar_page", "🏠 Dashboard")
        if active not in _ILM_MAIN_TABS:
            active = "🏠 Dashboard"
            st.session_state["ilm_sidebar_page"] = active

        with st.sidebar:
            st.markdown(
                """
                <div class="ilm-side-brand">
                    <div class="ilm-side-kicker">PHARMACEUTICAL QC</div>
                    <div class="ilm-side-title">🧪 Yahia QC</div>
                    <div class="ilm-side-sub">Instrument Lifecycle & Decision Intelligence</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            try:
                auth = st.session_state.get("_ilm_auth") or {}
                email = str((auth.get("user") or {}).get("email") or "").strip()
                if email:
                    st.caption(email)
            except Exception:
                pass

            st.markdown("---")
            for heading, entries in _ILM_NAV_GROUPS:
                if heading:
                    st.markdown(f'<div class="ilm-nav-group">{heading}</div>', unsafe_allow_html=True)
                for label, route in entries:
                    clicked = st.button(
                        label,
                        key=f"ilm_sidebar_nav_{route}",
                        use_container_width=True,
                        type="primary" if active == route else "secondary",
                    )
                    if clicked:
                        active = route
                        st.session_state["ilm_sidebar_page"] = route

            st.markdown("---")
            st.caption("DON'T GUESS. FOLLOW THE EVIDENCE.")

        return active

    def _ilm_sidebar_tabs(labels, *args, **kwargs):
        """Route only the app's top-level workspaces through the sidebar.

        A hidden legacy core container may also be present. It receives obsolete
        Command Center output so those old tables never contaminate Reports.
        Nested tabs remain normal Streamlit tabs.
        """
        items = list(labels)
        visible = [item for item in items if item != _ILM_LEGACY_TAB]
        is_shell = len(visible) == len(_ILM_MAIN_TABS) and set(visible) == set(_ILM_MAIN_TABS)
        if is_shell:
            active = _ilm_sidebar_menu()
            if active not in visible:
                active = "🏠 Dashboard"

            st.markdown(
                """
                <style>
                /* Hide only the large application navigation strip. Nested tabs stay visible. */
                div[data-baseweb="tab-list"]:has(> button:nth-child(11)) {
                    display:none !important;
                }

                [data-testid="stSidebar"] {
                    border-right:1px solid rgba(128,128,128,.18);
                }
                [data-testid="stSidebar"] .stButton > button {
                    justify-content:flex-start !important;
                    text-align:left !important;
                    border-radius:10px !important;
                    min-height:2.45rem !important;
                    margin:.04rem 0 !important;
                    font-weight:700 !important;
                }
                .ilm-side-brand {padding:.2rem 0 .1rem;}
                .ilm-side-kicker {font-size:.66rem;font-weight:900;letter-spacing:.11em;color:#d4af37;}
                .ilm-side-title {font-size:1.28rem;font-weight:900;color:#102a43;margin:.1rem 0;}
                .ilm-side-sub {font-size:.74rem;color:#718096;line-height:1.35;}
                .ilm-nav-group {
                    font-size:.65rem;
                    font-weight:900;
                    letter-spacing:.08em;
                    color:#78889b;
                    margin:.82rem 0 .26rem;
                }

                @media (min-width: 801px) {
                    [data-testid="stSidebarCollapseButton"] {display:none !important;}
                }
                </style>
                """,
                unsafe_allow_html=True,
            )

            # Selected route becomes first so Streamlit keeps it active on every rerun.
            ordered = [active] + [item for item in visible if item != active]
            if _ILM_LEGACY_TAB in items:
                ordered.append(_ILM_LEGACY_TAB)
            rendered = _ilm_native_tabs(ordered, *args, **kwargs)
            by_label = dict(zip(ordered, rendered))
            return [by_label[item] for item in items]

        return _ilm_native_tabs(items, *args, **kwargs)

    st.tabs = _ilm_sidebar_tabs
except Exception:
    pass


# ---------------------------------------------------------------------------
# Arabic PDF typography.
# ---------------------------------------------------------------------------
try:
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont

    def _find_font(filename: str):
        roots = [
            Path("/usr/share/fonts/truetype/noto"),
            Path("/usr/share/fonts/opentype/noto"),
            Path("/usr/share/fonts"),
        ]
        for root in roots:
            try:
                direct = root / filename
                if direct.exists():
                    return direct
                if root.exists():
                    for match in root.rglob(filename):
                        if match.exists():
                            return match
            except Exception:
                continue
        return None

    _naskh_regular = _find_font("NotoNaskhArabic-Regular.ttf")
    _kufi_bold = _find_font("NotoKufiArabic-Bold.ttf")

    if _naskh_regular is None:
        _naskh_regular = _find_font("NotoSansArabic-Regular.ttf")
    if _kufi_bold is None:
        _kufi_bold = _find_font("NotoSansArabic-Bold.ttf")

    _protected_aliases = {"ILM", "ILMB", "EXECV2REG", "EXECV2BOLD"}

    if _naskh_regular is not None and _kufi_bold is not None:
        _native_register_font = pdfmetrics.registerFont

        if "ILM" not in pdfmetrics.getRegisteredFontNames():
            _native_register_font(TTFont("ILM", str(_naskh_regular)))
        if "ILMB" not in pdfmetrics.getRegisteredFontNames():
            _native_register_font(TTFont("ILMB", str(_kufi_bold)))

        if "EXECV2REG" not in pdfmetrics.getRegisteredFontNames():
            _native_register_font(TTFont("EXECV2REG", str(_naskh_regular)))
        if "EXECV2BOLD" not in pdfmetrics.getRegisteredFontNames():
            _native_register_font(TTFont("EXECV2BOLD", str(_kufi_bold)))

        def _ilm_register_font_once(font):
            try:
                name = str(getattr(font, "fontName", "") or "")
                if name in _protected_aliases and name in pdfmetrics.getRegisteredFontNames():
                    return None
            except Exception:
                pass
            return _native_register_font(font)

        pdfmetrics.registerFont = _ilm_register_font_once
except Exception:
    pass
