from pathlib import Path


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if old not in text:
        raise SystemExit(f"Missing patch anchor: {label}")
    return text.replace(old, new, 1)


# App shell: reports follow the global interface language.
p = Path("app.py")
s = p.read_text(encoding="utf-8")
s = replace_once(
    s,
    'render_pdf_report_center(globals(), ui_lang="ar")',
    'render_pdf_report_center(globals(), ui_lang=_current_language())',
    "app report language",
)
p.write_text(s, encoding="utf-8")


# Report Center: unique widget namespace + English-clean labels.
p = Path("instrument_pdf_reports.py")
s = p.read_text(encoding="utf-8")
anchor = 'def render_pdf_report_center(context: dict, ui_lang: str = "ar") -> None:\n'
replacement = '''_ILM_PDF_REPORT_INSTANCE = 0\n\n\ndef render_pdf_report_center(context: dict, ui_lang: str = "ar") -> None:\n    global _ILM_PDF_REPORT_INSTANCE\n    _ILM_PDF_REPORT_INSTANCE += 1\n    _key = lambda name: f"ilm_pdf_report_{name}_{_ILM_PDF_REPORT_INSTANCE}"\n'''
s = replace_once(s, anchor, replacement, "report function")
s = s.replace('key="ilm_pdf_report_kind",', 'key=_key("kind"),')
s = s.replace('key="ilm_pdf_report_language",', 'key=_key("language"),')
s = s.replace('key="ilm_pdf_instrument",', 'key=_key("instrument"),')
s = s.replace('key="ilm_generate_pdf",', 'key=_key("generate"),')
s = s.replace('key="ilm_download_pdf",', 'key=_key("download"),')
s = replace_once(
    s,
    '["English", "العربية"],\n            index=1 if ui_lang == "ar" else 0,',
    '(["English", "Arabic"] if ui_lang == "en" else ["English", "العربية"]),\n            index=1 if ui_lang == "ar" else 0,',
    "report language options",
)
s = replace_once(
    s,
    'report_lang = "ar" if report_lang_label == "العربية" else "en"',
    'report_lang = "ar" if report_lang_label in ("العربية", "Arabic") else "en"',
    "report language mapping",
)
s = replace_once(
    s,
    'st.success("PDF ready · التقرير جاهز.")',
    'st.success("PDF ready." if ui_lang == "en" else "PDF ready · التقرير جاهز.")',
    "report success message",
)
p.write_text(s, encoding="utf-8")


# Executive report UI: inherit the global interface language.
p = Path("instrument_executive_performance_report.py")
s = p.read_text(encoding="utf-8")
import_anchor = "import streamlit as st\n"
import_line = "from instrument_i18n import current_language as _current_language\n"
if import_line not in s:
    s = replace_once(s, import_anchor, import_anchor + import_line, "executive i18n import")
s = replace_once(
    s,
    '    language = st.radio("العربية | English", ["العربية", "English"], horizontal=True, key="exec_v2_ui_language", label_visibility="collapsed")\n    lang = "ar" if language == "العربية" else "en"\n',
    '    lang = _current_language()\n',
    "executive language radio",
)
p.write_text(s, encoding="utf-8")


# Full English in-app Guide; existing Arabic-first guide remains intact.
p = Path("instrument_v03_user_guide.py")
s = p.read_text(encoding="utf-8")
old_import = "from instrument_i18n import ui_text as _ui_text\n"
new_import = "from instrument_i18n import current_language as _current_language, ui_text as _ui_text\n"
if old_import in s:
    s = s.replace(old_import, new_import, 1)
elif new_import not in s:
    raise SystemExit("Missing guide i18n import anchor")

english_guide = r'''
def _render_v03_user_guide_en():
    st.markdown("## 🧭 Product & User Guide")
    st.caption("Yahia QC Instrument Intelligence™ · English interface guide")
    st.info(
        "This is decision-support software, not a validated GxP system of record. "
        "Official GMP records remain in approved company systems and SOP-controlled forms."
    )
    st.caption(
        "The current Premium Visual-First PDF v1.4 is the RTL edition. "
        "This in-app guide is fully English; a dedicated English PDF edition can be published separately."
    )

    tabs = st.tabs([
        "🎯 Start here",
        "↻ Lifecycle",
        "🧾 Daily use",
        "🔎 Investigation",
        "🔐 Governance & privacy",
        "🧭 Practical workflows",
    ])

    with tabs[0]:
        st.markdown("### What is this application?")
        st.markdown(
            """
Yahia QC Instrument Intelligence™ is a connected instrument-lifecycle and decision-support workspace for Pharmaceutical QC.
It links instrument identity, lifecycle milestones, routine control, performance, events and evidence so the instrument story stays usable when a decision is needed.

**Main areas**
- **Dashboard** — current priorities, overdue controls, open quality signals and the attention queue.
- **Instruments** — registry, single-instrument entry, Excel import/export and Instrument 360.
- **Instrument 360** — Identity → Lifecycle → Control → Performance → Events → Evidence.
- **Lifecycle** — Need / URS through acquisition, qualification, first routine use, periodic review and retirement.
- **Cal & PM** — calibration, qualification, preventive maintenance, maintenance and component control.
- **Events** — record what happened before interpretation is added.
- **Investigation Intelligence** — separate observed/reported facts from inference and unknowns; identify the next evidence action.
- **Performance** — monthly Availability / Utilization and management signals.
- **Reports / Cockpit / Alerts** — decision-ready views for review and follow-up.
"""
        )
        st.markdown("### Recommended starting sequence")
        st.markdown(
            """
1. Open **Instruments** and create or import the instrument registry.
2. Open **Instrument 360** and confirm identity and lifecycle due dates.
3. Record **Need / URS** and acquisition milestones when evidence exists.
4. Record **Installation / IQ / OQ / PQ / Release / First Run** as controlled evidence becomes available.
5. Keep **Calibration / PM / Qualification / Components** current.
6. Record **Events** immediately when something changes.
7. Use **Investigation Intelligence** to test evidence, not assumptions.
8. Add monthly **Performance** data for Availability / Utilization trending.
9. Use **Reports / Cockpit / Alerts** for review and escalation.
10. Close the lifecycle with a controlled **Retirement / Decommissioning** record.
"""
        )
        st.warning("Do not complete missing fields by assumption. Missing evidence should remain visible as missing evidence.")

    with tabs[1]:
        st.markdown("### Instrument lifecycle — what to record")
        st.markdown(
            """
1. **Need / Initiation** — business or laboratory need, requester, intended use, criticality and target implementation date.
2. **URS** — approved User Requirements Specification reference and approval date.
3. **Quotation** — selected/evaluated quotation reference and date.
4. **PR** — Purchase Requisition number and approval date.
5. **PO** — Purchase Order number and issue/approval date.
6. **Receiving** — expected and actual receiving dates.
7. **Installation** — installation date, installation report, site readiness and utilities.
8. **IQ → OQ → PQ** — completion dates supported by available evidence.
9. **Release / Issuance** — controlled release of the qualified instrument for laboratory use.
10. **First approved routine run** — first approved routine analytical use, not an informal test.
11. **Routine Operation** — calibration, PM, requalification, components, events and maintenance.
12. **Performance Review** — reliability, downtime, capacity, utilization and recurring evidence signals.
13. **Retirement / Decommissioning** — reason, approval, effective date, archive/backup, access shutdown and replacement where applicable.
"""
        )
        st.warning("A later milestone does not prove that every earlier lifecycle gate was completed. Each gate requires its own recorded evidence.")

    with tabs[2]:
        st.markdown("### Start of shift / start of day")
        st.markdown(
            """
- Open **Dashboard** first.
- Review overdue Calibration / PM / Qualification, open events, open OOC signals and the Priority Attention Queue.
- Use the dashboard to decide **where to look first** instead of opening every instrument.

### When reviewing one instrument
- Go to **Instruments → Open Instrument 360**.
- Read **Health Score + Status + Open Events + Availability + Utilization**.
- Open **Why this score?** to see the evidence drivers.
- Review **Management Attention** when shown.
- Then inspect **Identity / Lifecycle / Control / Performance / Events / Evidence**.

### When something changes
- Record the event first.
- Preserve the observation and objective evidence.
- Add interpretation only after the facts are captured.
"""
        )

    with tabs[3]:
        st.markdown("### Evidence-first investigation workflow")
        st.markdown(
            """
**OBSERVE → PRESERVE EVIDENCE → LOCALIZE → HYPOTHESIZE → TEST → CONFIRM → DECIDE → DOCUMENT**

- **Observe:** describe what actually happened.
- **Preserve evidence:** keep chromatograms, logs, instrument messages, dates and relevant conditions before changing the system.
- **Localize:** determine where the abnormal behavior is most likely located.
- **Hypothesize:** create competing explanations; do not promote one to fact prematurely.
- **Test:** change one discriminating variable at a time where practical and approved.
- **Confirm:** require the expected response and reasonable exclusion of competing explanations.
- **Decide:** choose the controlled next action based on evidence and approved procedures.
- **Document:** keep observed/reported, inferred and unknown information clearly separated.
"""
        )
        st.warning("A repeated pattern, prior history or Health Score driver is not a confirmed root cause.")

    with tabs[4]:
        st.markdown("### Governance and evidence boundaries")
        st.markdown(
            """
- The application is **decision-support software**, not a validated GxP system of record.
- **Health Score** prioritizes attention; it is not a compliance verdict, release decision or qualification decision.
- **Management Attention** highlights evidence-consistency or review signals; it does not prove a missing GMP record or root cause.
- Official records remain in approved systems, controlled forms, certificates, protocols, deviations, CAPA and raw-data repositories.
- Workspace membership and **Row Level Security (RLS)** control data access.
- A QR Digital Passport reopens the instrument after authentication; it does not bypass permissions.
- Exported PDFs are uncontrolled decision-support copies unless your organization establishes a validated controlled process around them.
"""
        )
        st.success("Principle: DON'T GUESS. FOLLOW THE EVIDENCE.")

    with tabs[5]:
        st.markdown("### Practical workflows")
        workflows = [
            ("1. Start the shift", "Dashboard", "Review current priorities and due-date / event signals before opening individual records."),
            ("2. Add an instrument", "Instruments → Add one instrument", "Create identity and core lifecycle due dates from known evidence."),
            ("3. Import the registry", "Instruments → Import Instrument List", "Use the controlled Excel template; unknown columns are ignored rather than guessed."),
            ("4. Review Instrument 360", "Instruments → Open Instrument 360", "Read the connected asset story from Identity through Evidence."),
            ("5. Control due work", "Cal & PM", "Record calibration, qualification, PM, maintenance and components with references and dates."),
            ("6. Record a failure or abnormal event", "Events", "Capture observation first; diagnose later."),
            ("7. Investigate", "Investigate", "Separate observed/reported facts, inference and unknowns, then select the next evidence action."),
            ("8. Review monthly performance", "Performance", "Record scheduled, productive and downtime hours; interpret Availability / Utilization only from entered evidence."),
            ("9. Management review", "Reports / Cockpit / Alerts", "Use management views to prioritize review; confirm decisions in approved systems."),
            ("10. Retire an instrument", "Instrument 360 → Retire / delete instrument", "Export required evidence first and follow your approved retirement / data-retention process."),
        ]
        for title, route, value in workflows:
            st.markdown(f"**{title}**  \n`{route}`  \n{value}")
            st.divider()

'''

function_anchor = "def render_v03_user_guide():\n"
if "def _render_v03_user_guide_en():" not in s:
    s = replace_once(s, function_anchor, english_guide + function_anchor, "guide function")

branch_replacement = 'def render_v03_user_guide():\n    if _current_language() == "en":\n        return _render_v03_user_guide_en()\n'
if branch_replacement not in s:
    s = replace_once(s, function_anchor, branch_replacement, "guide language branch")

p.write_text(s, encoding="utf-8")

print("English-mode patch complete")
