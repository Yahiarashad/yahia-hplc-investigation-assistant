from pathlib import Path


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if old not in text:
        raise SystemExit(f"{label} anchor not found")
    return text.replace(old, new, 1)


# app.py: isolate report engines from the shared exec() namespace.
p = Path("app.py")
s = p.read_text(encoding="utf-8")
s = replace_once(
    s,
    '_exec_extension("instrument_pdf_reports.py", "_ilm_pdf_module_error")\n_exec_extension("instrument_executive_performance_report.py", "_ilm_exec_report_module_error")\n',
    '# Report engines are imported in isolated module namespaces after the core loads.\n',
    "app report extension isolation",
)
old = '''# Reports: lifecycle evidence PDF + executive monthly performance intelligence --
try:
    if isinstance(main_tabs, list) and len(main_tabs) >= 1 and _is_signed_in:
        with main_tabs[0]:
            st.divider()
            if callable(globals().get("render_pdf_report_center")):
                render_pdf_report_center(globals(), ui_lang=_current_language())
            if callable(globals().get("render_executive_performance_report")):
                render_executive_performance_report()
except Exception as exc:
    try:
        with main_tabs[0]:
            st.error("Advanced Report Center could not load completely.")
            st.caption(f"Diagnostic: {type(exc).__name__}")
    except Exception:
        pass
'''
new = '''# Reports: lifecycle evidence PDF + executive monthly performance intelligence --
try:
    if isinstance(main_tabs, list) and len(main_tabs) >= 1 and _is_signed_in:
        with main_tabs[0]:
            st.divider()
            import instrument_pdf_reports as _ilm_pdf_reports_mod
            _ilm_pdf_reports_mod._find_arabic_font = _ilm_pdf_font_paths
            _ilm_report_lang = "en" if _current_language() == "en" else "ar"
            _ilm_pdf_reports_mod.render_pdf_report_center(globals(), ui_lang=_ilm_report_lang)
except Exception as exc:
    try:
        with main_tabs[0]:
            st.error("PDF Report Center could not load completely.")
            st.caption(f"Diagnostic: {type(exc).__name__}")
    except Exception:
        pass

try:
    if isinstance(main_tabs, list) and len(main_tabs) >= 1 and _is_signed_in:
        with main_tabs[0]:
            import instrument_executive_performance_report as _ilm_exec_reports_mod
            _ilm_exec_reports_mod._db_list = globals().get("_db_list")
            _ilm_exec_reports_mod._font_paths = _ilm_pdf_font_paths
            _ilm_exec_reports_mod.render_executive_performance_report()
except Exception as exc:
    try:
        with main_tabs[0]:
            st.error("Executive Performance Intelligence could not load completely.")
            st.caption(f"Diagnostic: {type(exc).__name__}")
    except Exception:
        pass
'''
s = replace_once(s, old, new, "app reports block")
p.write_text(s, encoding="utf-8")


# Executive report expects ar/en, while the global selector uses bilingual/en.
p = Path("instrument_executive_performance_report.py")
s = p.read_text(encoding="utf-8")
s = replace_once(
    s,
    '    lang = _current_language()\n',
    '    lang = "en" if _current_language() == "en" else "ar"\n',
    "executive language mapping",
)
p.write_text(s, encoding="utf-8")


# Camera/guide extension: when English is selected, render an English Excel
# explainer and English feedback, then return before the legacy Arabic appendices.
p = Path("instrument_camera_capture.py")
s = p.read_text(encoding="utf-8")
anchor = '''    def render_v03_user_guide():
        _existing_user_guide()
        with st.expander("⭐ عندي Excel Tracker بالفعل — لماذا أستخدم التطبيق؟", expanded=False):
'''
replacement = '''    def render_v03_user_guide():
        _existing_user_guide()
        from instrument_i18n import current_language as _current_language
        if _current_language() == "en":
            with st.expander("⭐ I already have an Excel Tracker — what does this app add?", expanded=False):
                st.markdown(
                    """
### Excel stores rows. The application turns instrument history into a decision-ready story.

If you already have a good Excel Tracker, **keep it**. Use it as a controlled input, then let the application add the decision-support layer.

- **Next Action, not just a row** — Current Stage, Missing Evidence and the Next Controlled Milestone.
- **One connected lifecycle** — Need → URS → Quotation → PR → PO → Receiving → Installation → IQ/OQ/PQ → Release → First Run → Routine Control → Performance Review → Retirement.
- **Priority Attention Queue** — combines overdue controls, OOC, open events, receiving delays and missing lifecycle evidence by priority.
- **Instrument Memory** — maintenance, calibration, components, failures and investigations remain connected to the same asset.
- **Investigation Intelligence** — separates Observed / Inferred / Unknown and supports the next evidence action instead of trial-and-error.
- **Camera-assisted entry** — reduces Manufacturer / Model / S/N transcription errors with user review before saving.
- **Multi-user isolation** — workspace data remains protected through Supabase Row Level Security.

**Recommended workflow:** Existing Excel Tracker → Import → Lifecycle Intelligence → Priorities / Decisions → Investigation Memory / Reports.

> **Excel tracks instruments. Yahia QC Instrument Intelligence helps you decide what needs attention next — and why.**
"""
                )
                st.info("Decision quality depends on the quality of the recorded evidence. Keep Passport, Lifecycle, Calibration/PM, Components and Events current.")
            try:
                from instrument_feedback import render_instrument_feedback
                render_instrument_feedback(compact=True, language="en")
            except Exception as exc:
                st.caption(f"Feedback module is temporarily unavailable ({type(exc).__name__}).")
            return
        with st.expander("⭐ عندي Excel Tracker بالفعل — لماذا أستخدم التطبيق؟", expanded=False):
'''
s = replace_once(s, anchor, replacement, "camera English guide branch")
p.write_text(s, encoding="utf-8")


# Monthly performance guide extension: English users should never fall through
# to the Arabic calculation appendix.
p = Path("instrument_monthly_performance.py")
s = p.read_text(encoding="utf-8")
anchor = '''    def render_v03_user_guide():
        _existing_perf_guide()
        with st.expander("📈 Instrument Utilization & Monthly Availability | طريقة الحساب", expanded=False):
'''
replacement = '''    def render_v03_user_guide():
        _existing_perf_guide()
        from instrument_i18n import current_language as _current_language
        if _current_language() == "en":
            with st.expander("📈 Instrument Utilization & Monthly Availability | Calculation method", expanded=False):
                st.markdown(
                    """
### Why both metrics?
**Availability %** asks whether the instrument was ready during the time it was planned to be available.  
**Utilization %** asks how much of the actually available time was used productively.

**Planned Operating Time** = Scheduled Service Hours − Planned Downtime Hours  
**Available Time** = Planned Operating Time − Unplanned Downtime Hours  
**Availability %** = Available Time ÷ Planned Operating Time × 100  
**Utilization %** = Productive Run Hours ÷ Available Time × 100

**Example:** Scheduled 176 h, Planned Downtime 8 h, Unplanned Downtime 12 h, Productive Run 100 h → Planned Operating Time 168 h → Available Time 156 h → Availability **92.9%** → Utilization **64.1%**.

Targets are instrument-specific management inputs. The app does not invent a universal target. **Target Gap = Actual % − Target %**, shown in percentage points (pp).

When Availability is below target while Utilization is on/above target, **Capacity Risk** means demand is strong while reliability/downtime is compressing available capacity. It is a review signal, not a confirmed root cause.
"""
                )
                st.warning("Portfolio Availability and Utilization are weighted by hours, not a simple average. Targets are operational / management indicators, not GMP release criteria.")
            return
        with st.expander("📈 Instrument Utilization & Monthly Availability | طريقة الحساب", expanded=False):
'''
s = replace_once(s, anchor, replacement, "performance English guide branch")
p.write_text(s, encoding="utf-8")


# Feedback: English mode must not inject the RTL premium guide hub, and RTL CSS
# should apply only to Arabic/bilingual presentation.
p = Path("instrument_feedback.py")
s = p.read_text(encoding="utf-8")
if 'from instrument_i18n import current_language as _current_language\n' not in s:
    s = replace_once(
        s,
        'import streamlit as st\n',
        'import streamlit as st\nfrom instrument_i18n import current_language as _current_language\n',
        "feedback i18n import",
    )
s = replace_once(
    s,
    'def render_instrument_feedback(*, compact: bool = True, language: str = "ar") -> None:\n    ar = language == "ar"\n    _apply_guide_rtl_css()\n',
    'def render_instrument_feedback(*, compact: bool = True, language: str | None = None) -> None:\n    resolved_language = language or ("en" if _current_language() == "en" else "ar")\n    ar = resolved_language == "ar"\n    if ar:\n        _apply_guide_rtl_css()\n',
    "feedback language resolution",
)
old = '''    # Premium product/user/management guide. It is generated without customer
    # instrument records, so users can safely download and share the brochure.
    try:
        from instrument_product_guide_rtl import render_product_guide_hub
        render_product_guide_hub()
    except Exception as exc:
        st.caption(f"Premium Product Guide is temporarily unavailable ({type(exc).__name__}).")
'''
new = '''    # The current premium brochure hub is RTL; keep it out of English mode.
    if ar:
        try:
            from instrument_product_guide_rtl import render_product_guide_hub
            render_product_guide_hub()
        except Exception as exc:
            st.caption(f"Premium Product Guide is temporarily unavailable ({type(exc).__name__}).")
'''
s = replace_once(s, old, new, "feedback premium guide gating")
p.write_text(s, encoding="utf-8")


# Static checks for the intended fixes.
checks = {
    "app.py": ["import instrument_pdf_reports as _ilm_pdf_reports_mod", "import instrument_executive_performance_report as _ilm_exec_reports_mod"],
    "instrument_camera_capture.py": ["I already have an Excel Tracker", 'language="en"'],
    "instrument_monthly_performance.py": ["Calculation method"],
    "instrument_feedback.py": ["resolved_language", "if ar:"],
}
for filename, needles in checks.items():
    text = Path(filename).read_text(encoding="utf-8")
    for needle in needles:
        if needle not in text:
            raise SystemExit(f"post-patch assertion failed: {filename}: {needle}")

print("English guide/report runtime patch applied")
