# v0.3 practical user guide + strict Excel bulk import
# Executed inside the authenticated app context immediately before main navigation.

from __future__ import annotations

from io import BytesIO
from pathlib import Path
from datetime import date, datetime

import pandas as pd
import streamlit as st
from instrument_i18n import ui_text as _ui_text
from instrument_product_guide_pdf import build_product_user_guide_pdf
from instrument_guide_visuals import guide_visual_bytes


OFFICIAL_GUIDE_V14 = Path(__file__).resolve().parent / "official_guides" / "Yahia_QC_Instrument_Intelligence_Premium_Guide_v1.4_VISUAL_FIRST.pdf"

@st.cache_data(show_spinner=False)
def _premium_product_guide_pdf_bytes():
    """Serve the approved Visual-First v1.4 when deployed; retain the generated
    guide only as a safe fallback so the Guide page never breaks."""
    if OFFICIAL_GUIDE_V14.exists():
        return OFFICIAL_GUIDE_V14.read_bytes()
    return build_product_user_guide_pdf()

def _official_guide_is_v14() -> bool:
    return OFFICIAL_GUIDE_V14.exists()


# Exact visible application labels -> Supabase instrument columns.
# Excel import is intentionally strict: only headers matching these labels are read.
V03_EXCEL_FIELD_MAP = {
    # Instrument Passport
    "Instrument ID": "instrument_code",
    "Instrument name": "instrument_name",
    "Type": "instrument_type",
    "Manufacturer": "manufacturer",
    "Model": "model",
    "Serial number": "serial_number",
    "Location": "location",
    "Responsible team": "responsible_team",
    "Operational status": "operational_status",
    "Qualification due": "qualification_due",
    "PM due": "pm_due",
    "Calibration due": "calibration_due",
    "Notes": "notes",
    # Need / initiation
    "Need / request title": "need_title",
    "Need identified date": "need_identified_date",
    "Department / laboratory section": "department",
    "Requested by": "requested_by",
    "Business / laboratory justification": "need_justification",
    "Intended analytical use": "intended_use",
    "Criticality": "criticality",
    "Target implementation date": "target_implementation_date",
    # Acquisition / qualification
    "URS reference": "urs_reference",
    "URS approval date": "urs_approval_date",
    "Quotation reference": "quotation_reference",
    "Quotation date": "quotation_date",
    "PR number": "pr_number",
    "PR approval date": "pr_approval_date",
    "PO number": "po_number",
    "PO approval / issue date": "po_approval_date",
    "Expected receiving date": "expected_receiving_date",
    "Actual receiving date": "receiving_date",
    "Installation date": "installation_date",
    "Installation report reference": "installation_reference",
    "Site readiness confirmed": "site_readiness_confirmed",
    "Utilities confirmed": "utilities_confirmed",
    "IQ completion date": "iq_date",
    "OQ completion date": "oq_date",
    "PQ completion date": "pq_date",
    "Release / issuance date": "issuance_date",
    "First approved routine run": "first_run_date",
}

V03_EXCEL_DATE_FIELDS = {
    "Qualification due", "PM due", "Calibration due", "Need identified date",
    "Target implementation date", "URS approval date", "Quotation date",
    "PR approval date", "PO approval / issue date", "Expected receiving date",
    "Actual receiving date", "Installation date", "IQ completion date",
    "OQ completion date", "PQ completion date", "Release / issuance date",
    "First approved routine run",
}

V03_EXCEL_BOOL_FIELDS = {"Site readiness confirmed", "Utilities confirmed"}
V03_EXCEL_REQUIRED = {"Instrument ID", "Instrument name"}


# -----------------------------------------------------------------------------
# RTL polish for the later Excel-vs-app expander added by camera_capture.py.
# We keep the English product term isolated so the browser does not reorder it.
# -----------------------------------------------------------------------------
if not hasattr(st, "_ilm_native_expander"):
    st._ilm_native_expander = st.expander
_native_expander = st._ilm_native_expander


class _ExcelTrackerExpanderProxy:
    def __init__(self, inner):
        self.inner = inner

    def __enter__(self):
        entered = self.inner.__enter__()
        st.markdown('<div class="ilm-excel-tracker-marker"></div>', unsafe_allow_html=True)
        return entered

    def __exit__(self, exc_type, exc, tb):
        return self.inner.__exit__(exc_type, exc, tb)


def _guide_expander(label, *args, **kwargs):
    text = str(label)
    if "Excel Tracker" in text and ("لماذا أستخدم التطبيق" in text or "فائدة التطبيق" in text):
        polished = "⭐ عندي \u2066Excel Tracker\u2069 بالفعل — فما فائدة التطبيق؟"
        return _ExcelTrackerExpanderProxy(_native_expander(polished, *args, **kwargs))
    return _native_expander(label, *args, **kwargs)


st.expander = _guide_expander


def _excel_blank(value) -> bool:
    if value is None:
        return True
    try:
        if pd.isna(value):
            return True
    except Exception:
        pass
    return str(value).strip() == ""


def _excel_date_to_iso(value):
    if _excel_blank(value):
        return None
    try:
        parsed = pd.to_datetime(value, errors="raise")
        if hasattr(parsed, "date"):
            return parsed.date().isoformat()
    except Exception:
        return None
    return None


def _excel_bool(value):
    if _excel_blank(value):
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)) and not pd.isna(value):
        return bool(int(value))
    text = str(value).strip().lower()
    if text in {"true", "yes", "y", "1", "confirmed", "نعم", "مؤكد"}:
        return True
    if text in {"false", "no", "n", "0", "not confirmed", "لا", "غير مؤكد"}:
        return False
    return None


def _excel_scalar(header, value):
    if _excel_blank(value):
        return None
    if header in V03_EXCEL_DATE_FIELDS:
        return _excel_date_to_iso(value)
    if header in V03_EXCEL_BOOL_FIELDS:
        return _excel_bool(value)
    if header == "Instrument ID":
        return str(value).strip().upper()
    return str(value).strip()


def _excel_template_bytes():
    columns = list(V03_EXCEL_FIELD_MAP.keys())
    sample = {c: "" for c in columns}
    sample.update({
        "Instrument ID": "HPLC-001",
        "Instrument name": "Waters Alliance",
        "Type": "HPLC",
        "Manufacturer": "Waters",
        "Model": "Alliance",
        "Operational status": "Active",
        "Need / request title": "New HPLC for routine QC testing",
        "Need identified date": date.today().isoformat(),
        "Business / laboratory justification": "Capacity / replacement / new analytical need",
        "Intended analytical use": "Routine assay and related substances",
        "Criticality": "High",
        "Site readiness confirmed": "Yes",
        "Utilities confirmed": "Yes",
    })
    instructions = pd.DataFrame([
        ["Rule", "Only headers with exactly the same visible name used in the application are imported."],
        ["Required", "Instrument ID and Instrument name are required for a new instrument."],
        ["Dates", "Use real Excel dates or YYYY-MM-DD."],
        ["Booleans", "Use Yes/No, True/False, 1/0 for Site readiness confirmed and Utilities confirmed."],
        ["Unknown columns", "Ignored. They are shown to you before import and are never silently mapped."],
        ["Blank cells", "Blank cells do not overwrite existing values when Update mode is used."],
        ["Security", "Rows are written through the signed-in Supabase session and remain protected by Row Level Security."],
        ["Scope", "Bulk import currently targets Instrument Passport + Need/Acquisition/Qualification fields. Maintenance, calibration event history, failures and investigations should be logged in their dedicated modules."],
    ], columns=["Item", "Instruction"])
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        pd.DataFrame([sample], columns=columns).to_excel(writer, index=False, sheet_name="Instruments")
        instructions.to_excel(writer, index=False, sheet_name="Instructions")
    output.seek(0)
    return output.getvalue()


def _excel_export_bytes(instruments):
    """Export the current registry using the exact import-template headers.

    This makes the downloaded registry round-trip compatible with the controlled
    bulk importer: users can export, update approved fields, preview, then
    re-import without manual header remapping.
    """
    columns = list(V03_EXCEL_FIELD_MAP.keys())
    rows = []
    for inst in instruments or []:
        row = {}
        for header, db_field in V03_EXCEL_FIELD_MAP.items():
            value = inst.get(db_field)
            if header in V03_EXCEL_BOOL_FIELDS and value is not None:
                value = "Yes" if bool(value) else "No"
            row[header] = "" if value is None else value
        rows.append(row)

    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        pd.DataFrame(rows, columns=columns).to_excel(writer, index=False, sheet_name="Instruments")
        ws = writer.book["Instruments"]
        ws.freeze_panes = "A2"
        ws.auto_filter.ref = ws.dimensions
        for cell in ws[1]:
            cell.font = cell.font.copy(bold=True)
        for column_cells in ws.columns:
            max_len = max((len(str(c.value)) if c.value is not None else 0) for c in column_cells)
            ws.column_dimensions[column_cells[0].column_letter].width = min(max(max_len + 2, 12), 32)

        pd.DataFrame([
            ["Purpose", "Current instrument registry exported with the exact controlled import headers."],
            ["Round trip", "You may update approved fields in this workbook, then upload it through Instruments → Import Instrument List."],
            ["Evidence rule", "Do not fill unknown or missing evidence by assumption. Leave unavailable evidence blank."],
            ["History", "Maintenance, calibration event history, failures and investigations remain in their dedicated modules and are not replaced by this registry export."],
        ], columns=["Item", "Instruction"]).to_excel(writer, index=False, sheet_name="Read Me")
    output.seek(0)
    return output.getvalue()


def _render_excel_import():
    st.markdown(_ui_text("#### 📥 Bulk import from Excel", "#### 📥 إدخال البيانات من Excel | Bulk import"))
    st.info(_ui_text(
        "Import rule: the app reads only columns whose headers exactly match the visible field names used in the application. Any other column is ignored; its meaning is never guessed.",
        "قاعدة الاستيراد متعمدة وبسيطة: التطبيق يقرأ فقط الأعمدة التي يحمل عنوانها **نفس اسم الحقل الظاهر داخل التطبيق**. أي عمود آخر يتم تجاهله ولا يتم تخمين معناه."
    ))
    st.download_button(
        "⬇️ Download exact Excel template",
        data=_excel_template_bytes(),
        file_name="Yahia_QC_Instrument_Lifecycle_Import_Template.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
        key="v03_download_excel_template",
    )
    st.caption(_ui_text(
        "Best practice: download the template, keep the column names unchanged, fill only the evidence you have, then upload the file. Blank cells do not mean the app will invent missing data.",
        "أفضل طريقة: حمّل القالب، لا تغيّر أسماء الأعمدة، املأ ما لديك فقط، ثم ارفع الملف. الخلايا الفارغة لا تعني أن التطبيق سيخترع بيانات مفقودة."
    ))

    uploaded = st.file_uploader(
        "Upload .xlsx file",
        type=["xlsx"],
        key="v03_excel_import_file",
        help="The importer reads the Instruments sheet if present; otherwise it reads the first sheet.",
    )
    if not uploaded:
        return

    try:
        xls = pd.ExcelFile(uploaded)
        sheet = "Instruments" if "Instruments" in xls.sheet_names else xls.sheet_names[0]
        df = pd.read_excel(xls, sheet_name=sheet, dtype=object)
    except Exception as exc:
        st.error("Could not read this Excel file. Use a standard .xlsx workbook and try again.")
        st.caption(f"Diagnostic: {type(exc).__name__}")
        return

    # Trim only leading/trailing spaces in headers; otherwise matching remains exact.
    df.columns = [str(c).strip() for c in df.columns]
    recognized = [c for c in df.columns if c in V03_EXCEL_FIELD_MAP]
    ignored = [c for c in df.columns if c not in V03_EXCEL_FIELD_MAP]

    c1, c2, c3 = st.columns(3)
    c1.metric("Rows", len(df))
    c2.metric("Recognized columns", len(recognized))
    c3.metric("Ignored columns", len(ignored))

    if recognized:
        st.success("Recognized → " + " · ".join(recognized))
    else:
        st.error("No recognized application column names were found.")
        return
    if ignored:
        st.warning("Ignored → " + " · ".join(ignored))

    missing_required_headers = [c for c in V03_EXCEL_REQUIRED if c not in recognized]
    if missing_required_headers:
        st.error("For creating new instruments, the file must contain: " + " + ".join(sorted(missing_required_headers)))

    st.markdown("**Preview — only recognized columns are shown**")
    st.dataframe(df[recognized].head(10), use_container_width=True, hide_index=True)

    mode = st.radio(
        "Import mode",
        [
            "Create new instruments only — skip existing Instrument ID",
            "Update existing Instrument ID + create new instruments",
        ],
        index=0,
        key="v03_excel_import_mode",
    )
    confirm = st.checkbox(
        "I reviewed the recognized and ignored columns and want to import these rows.",
        key="v03_excel_import_confirm",
    )
    if not st.button("Import recognized Excel data", use_container_width=True, disabled=not confirm, key="v03_excel_import_run"):
        return

    existing = {str(i.get("instrument_code") or "").strip().upper(): str(i.get("id")) for i in globals().get("instruments", [])}
    seen_in_file = set()
    created = updated = skipped = failed = 0
    messages = []

    for row_no, (_, row) in enumerate(df.iterrows(), start=2):
        raw_code = row.get("Instrument ID") if "Instrument ID" in df.columns else None
        code = _excel_scalar("Instrument ID", raw_code)
        if not code:
            skipped += 1
            messages.append(f"Row {row_no}: skipped — Instrument ID is blank.")
            continue
        if code in seen_in_file:
            skipped += 1
            messages.append(f"Row {row_no}: skipped — duplicate Instrument ID {code} inside the same file.")
            continue
        seen_in_file.add(code)

        payload = {}
        invalid_dates = []
        for header in recognized:
            value = row.get(header)
            if _excel_blank(value):
                continue
            clean = _excel_scalar(header, value)
            if header in V03_EXCEL_DATE_FIELDS and clean is None:
                invalid_dates.append(header)
                continue
            if header in V03_EXCEL_BOOL_FIELDS and clean is None:
                continue
            payload[V03_EXCEL_FIELD_MAP[header]] = clean

        if invalid_dates:
            skipped += 1
            messages.append(f"Row {row_no} ({code}): skipped — invalid date in {', '.join(invalid_dates)}.")
            continue

        payload["instrument_code"] = code
        existing_id = existing.get(code)
        if existing_id:
            if mode.startswith("Create new"):
                skipped += 1
                messages.append(f"Row {row_no} ({code}): skipped — already exists.")
                continue
            patch_payload = {k: v for k, v in payload.items() if k != "instrument_code"}
            if not patch_payload:
                skipped += 1
                messages.append(f"Row {row_no} ({code}): skipped — no recognized nonblank data to update.")
                continue
            ok, _, _, err = _db_patch("instruments", existing_id, patch_payload)
            if ok:
                updated += 1
            else:
                failed += 1
                messages.append(f"Row {row_no} ({code}): update failed — {err or 'database error'}.")
            continue

        name = payload.get("instrument_name")
        if not name:
            skipped += 1
            messages.append(f"Row {row_no} ({code}): skipped — Instrument name is required for a new instrument.")
            continue
        ok, data, _, err = _db_insert("instruments", payload)
        if ok:
            created += 1
            try:
                new_id = str((data or [{}])[0].get("id") or "")
                if new_id:
                    existing[code] = new_id
            except Exception:
                pass
        else:
            failed += 1
            messages.append(f"Row {row_no} ({code}): create failed — {err or 'database error'}.")

    st.success(f"Excel import finished · Created {created} · Updated {updated} · Skipped {skipped} · Failed {failed}")
    if messages:
        with st.expander("Import details"):
            for msg in messages[:100]:
                st.write("• " + msg)
    if created or updated:
        st.caption("Refresh / rerun to reload the latest instrument dataset from Supabase.")
        if st.button("Reload imported data", use_container_width=True, key="v03_excel_import_reload"):
            st.rerun()


def render_v03_user_guide():
    st.markdown(
        """
<style>
.v03-guide-banner{
  direction:rtl;text-align:right;
  font-family:Inter,"Segoe UI","Noto Sans Arabic",Tahoma,Arial,sans-serif;
  border:1px solid #d8e2ec;border-right:6px solid #d4af37;border-left:1px solid #d8e2ec;
  border-radius:18px;padding:.9rem 1rem;margin:.25rem 0 .75rem;
  background:linear-gradient(135deg,#ffffff,#f8fafc);box-shadow:0 5px 18px rgba(15,23,42,.045)
}
.v03-guide-banner b{color:#0f2742;font-size:1.08rem}.v03-guide-banner span{display:block;color:#64748b;font-size:.94rem;margin-top:.22rem;line-height:1.7}
.v03-guide-rtl{direction:rtl;text-align:right;line-height:1.95;unicode-bidi:plaintext;font-size:1.02rem;font-family:Inter,"Segoe UI","Noto Sans Arabic",Tahoma,Arial,sans-serif}
.v03-guide-rtl h3{font-size:1.30rem;line-height:1.5;margin:.9rem 0 .45rem;font-weight:850}
.v03-guide-rtl h4{font-size:1.12rem;line-height:1.55;margin:.8rem 0 .35rem;font-weight:800}
.v03-guide-rtl ul{padding-right:1.35rem;padding-left:0}
.v03-guide-rule{direction:rtl;text-align:right;border-right:4px solid #d4af37;border-left:0;background:#fffaf0;border-radius:14px;padding:.9rem 1rem;margin:.7rem 0;line-height:1.95;font-size:1rem;font-family:Inter,"Segoe UI","Noto Sans Arabic",Tahoma,Arial,sans-serif}
.v03-guide-flow{
  direction:rtl;text-align:right;color:#0f2742;background:#f8fafc;border:1px solid #dde5ee;
  border-right:6px solid #d4af37;border-radius:20px;padding:.35rem 1rem;margin:.65rem 0 1rem;
  box-shadow:0 8px 24px rgba(15,23,42,.07);overflow:hidden
}
.v03-flow-step{display:grid;grid-template-columns:42px 1fr;gap:.75rem;align-items:center;padding:.72rem 0;border-bottom:1px solid #e8edf3}
.v03-flow-step:last-child{border-bottom:0}
.v03-flow-num{width:34px;height:34px;border-radius:50%;display:flex;align-items:center;justify-content:center;background:#0f2742;color:#fff;font-weight:900;font-size:.9rem;box-shadow:0 3px 10px rgba(15,39,66,.18)}
.v03-flow-main{font-weight:850;color:#102a45;font-size:1.04rem;line-height:1.55}
.v03-flow-sub{color:#66778a;font-size:.91rem;margin-top:.16rem;line-height:1.6}
.v03-flow-main [dir="ltr"],.v03-flow-sub [dir="ltr"]{unicode-bidi:isolate}
.v03-guide-tip{direction:rtl;text-align:right;border:1px solid #344354;border-radius:16px;background:rgba(255,255,255,.035);padding:.85rem 1rem;line-height:1.9;margin:.7rem 0}
.v03-guide-tip b{color:inherit}
.v03-guide-banner-brand{direction:ltr;text-align:left;color:#0f2742;font-weight:900;font-size:1.08rem;unicode-bidi:isolate}
.v03-guide-banner-title{direction:rtl;text-align:right;color:#0f2742;font-weight:900;font-size:1.22rem;margin-top:.42rem}

/* The practical guide is Arabic-first. Keep widgets/data tables native, but
   force narrative markdown and tab labels to read naturally right-to-left. */
div[data-testid="stExpander"]:has(.v03-guide-shell-marker) summary,
div[data-testid="stExpander"]:has(.v03-guide-shell-marker) summary *{
  direction:rtl!important;text-align:right!important;unicode-bidi:plaintext!important
}
div[data-testid="stExpander"]:has(.v03-guide-shell-marker) div[data-testid="stMarkdownContainer"]{
  direction:rtl!important;text-align:right!important;unicode-bidi:plaintext!important;line-height:1.9
}
div[data-testid="stExpander"]:has(.v03-guide-shell-marker) div[data-baseweb="tab-list"]{
  direction:rtl!important;justify-content:flex-start!important
}
div[data-testid="stExpander"]:has(.v03-guide-shell-marker) button[data-baseweb="tab"],
div[data-testid="stExpander"]:has(.v03-guide-shell-marker) button[data-baseweb="tab"] *{
  direction:rtl!important;text-align:right!important;unicode-bidi:plaintext!important
}
div[data-testid="stExpander"]:has(.v03-guide-shell-marker) ul,
div[data-testid="stExpander"]:has(.v03-guide-shell-marker) ol{
  direction:rtl!important;text-align:right!important;padding-right:1.45rem!important;padding-left:0!important
}

/* Excel-vs-app expander added later by the camera module. */
div[data-testid="stExpander"]:has(.ilm-excel-tracker-marker) summary,
div[data-testid="stExpander"]:has(.ilm-excel-tracker-marker) summary *{
  direction:rtl!important;text-align:right!important;unicode-bidi:plaintext!important
}
div[data-testid="stExpander"]:has(.ilm-excel-tracker-marker) div[data-testid="stMarkdownContainer"],
div[data-testid="stExpander"]:has(.ilm-excel-tracker-marker) div[data-testid="stAlertContainer"]{
  direction:rtl!important;text-align:right!important;unicode-bidi:plaintext!important;line-height:1.9
}
div[data-testid="stExpander"]:has(.ilm-excel-tracker-marker) ul,
div[data-testid="stExpander"]:has(.ilm-excel-tracker-marker) ol{
  direction:rtl!important;text-align:right!important;padding-right:1.4rem!important;padding-left:0!important
}
div[data-testid="stExpander"]:has(.ilm-excel-tracker-marker) li{direction:rtl!important;text-align:right!important;unicode-bidi:plaintext!important}

.v03-workflow-card{
  direction:rtl;text-align:right;border:1px solid rgba(128,128,128,.30);border-radius:16px;
  padding:.9rem 1rem;margin:.65rem 0;background:var(--secondary-background-color);
  color:var(--text-color);font-family:Inter,"Segoe UI","Noto Sans Arabic",Tahoma,Arial,sans-serif;line-height:1.9
}
.v03-workflow-card b{font-size:1.03rem}
.v03-workflow-route{display:inline-block;direction:ltr;unicode-bidi:isolate;font-weight:800;color:#c9a54d;margin:.2rem 0}
.v03-workflow-outcome{margin-top:.45rem;padding:.55rem .7rem;border-radius:10px;background:rgba(201,165,77,.10);border:1px solid rgba(201,165,77,.28)}

@media(max-width:700px){
  .v03-guide-banner{padding:.82rem .88rem}.v03-guide-banner span{font-size:.90rem}.v03-guide-rtl{line-height:1.9;font-size:1rem}
  .v03-guide-flow{padding:.28rem .8rem;border-radius:18px}
  .v03-flow-step{grid-template-columns:38px 1fr;gap:.62rem;padding:.66rem 0}
  .v03-flow-num{width:31px;height:31px;font-size:.82rem}
  .v03-flow-main{font-size:1rem}.v03-flow-sub{font-size:.88rem}
}
</style>
<div class="v03-guide-banner">
  <div class="v03-guide-banner-brand">🚀 Yahia QC Instrument Intelligence™</div>
  <div class="v03-guide-banner-title">دليل الاستخدام العملي</div>
  <span>افهم المنصة، دورة العمل الصحيحة، وكيف تستخدمها يوميًا قبل أن تبدأ.</span>
</div>
""",
        unsafe_allow_html=True,
    )

    st.markdown(
        """
<div style="border:1px solid rgba(201,165,77,.65);border-radius:18px;padding:1rem 1.05rem;margin:.35rem 0 1rem;background:linear-gradient(135deg,#0b1f33,#12324f);color:white;box-shadow:0 8px 24px rgba(0,0,0,.12)">
  <div style="color:#d8bc68;font-weight:900;letter-spacing:.08em;font-size:.76rem">PRODUCT · USER · MANAGEMENT GUIDE</div>
  <div style="font-size:1.25rem;font-weight:900;margin:.28rem 0">Yahia QC Instrument Intelligence™</div>
  <div style="color:#dce5ec;line-height:1.65">From Instrument Data to Evidence-Based Decisions</div>
  <div style="margin-top:.65rem;font-weight:800">STOP MANAGING INSTRUMENT DATA. START MANAGING INSTRUMENT DECISIONS.</div>
</div>
""",
        unsafe_allow_html=True,
    )
    try:
        st.download_button(
            "⬇️ Download Official Premium Visual-First Guide v1.4 (PDF)" if _official_guide_is_v14() else "⬇️ Download Product & User Guide (fallback PDF)",
            data=_premium_product_guide_pdf_bytes(),
            file_name="Yahia_QC_Instrument_Intelligence_Premium_Guide_v1.4_VISUAL_FIRST.pdf" if _official_guide_is_v14() else "Yahia_QC_Instrument_Intelligence_Official_Guide_fallback.pdf",
            mime="application/pdf",
            use_container_width=True,
            key="v03_download_premium_product_guide",
        )
        if _official_guide_is_v14():
            st.success("Official Guide v1.4 · Premium Visual-First · Navy + Gold · RTL · approved baseline")
        else:
            st.warning("Premium Visual-First v1.4 is not present in this deployment yet. The generated fallback guide is available temporarily.")
    except Exception as exc:
        st.error("Premium PDF could not be generated on this deployment.")
        st.caption(f"PDF diagnostic: {type(exc).__name__}")

    with st.expander("📘 دليل الاستخدام العملي", expanded=True):
        st.markdown('<div class="v03-guide-shell-marker"></div>', unsafe_allow_html=True)
        guide_tabs = st.tabs([
            "🎯 ابدأ من هنا",
            "↻ دورة الحياة",
            "🧾 الاستخدام اليومي",
            "🔎 التحقيق",
            "🔐 الحوكمة والخصوصية",
            "🧭 خطوات العمل الفعلية",
        ])

        with guide_tabs[0]:
            st.markdown(
                """
<div class="v03-guide-rtl">
<h3>ما هو التطبيق؟</h3>
<p>هذا التطبيق هو <b>ذاكرة تشغيلية ودورة حياة للأجهزة داخل Pharmaceutical QC</b>. الفكرة ليست تخزين بيانات فقط، بل ربط هوية الجهاز بمراحل شرائه وتأهيله وتشغيله وصيانته ومعايرته وأعطاله وتحقيقاته حتى التكهين.</p>
<h4>المكونات الرئيسية التي ستستخدمها</h4>
<ul>
<li><b><span dir="ltr">Dashboard</span></b> — أين توجد المخاطر والمواعيد والـOOC والإشارات التي تحتاج قرارًا الآن.</li>
<li><b><span dir="ltr">Instruments</span></b> — سجل الأجهزة، إضافة جهاز، استيراد/تصدير القائمة، ثم فتح <span dir="ltr">Instrument 360</span> لأي جهاز.</li>
<li><b><span dir="ltr">Instrument 360</span></b> — القصة المتصلة للجهاز: <span dir="ltr">Identity → Lifecycle → Control → Performance → Events → Evidence</span> مع <span dir="ltr">Health Score</span> قابل للتفسير.</li>
<li><b><span dir="ltr">Lifecycle</span></b> — الرحلة الفعلية من <span dir="ltr">Need / URS</span> حتى <span dir="ltr">First Run</span> ثم <span dir="ltr">Performance Review / Retirement</span>.</li>
<li><b><span dir="ltr">Cal & PM</span></b> — <span dir="ltr">Calibration / Qualification / PM / Maintenance / Components</span> وتواريخ الاستحقاق.</li>
<li><b><span dir="ltr">Events</span></b> — تسجيل العطل أو الحدث كما حدث فعلًا قبل كتابة أي تفسير.</li>
<li><b><span dir="ltr">Investigation Intelligence</span></b> — ربط المشكلة بتاريخ الجهاز وفصل <span dir="ltr">Observed / Inferred / Unknown</span> وتحديد الخطوة التالية للحصول على دليل.</li>
<li><b><span dir="ltr">Performance</span></b> — تسجيل وتحليل <span dir="ltr">Availability / Utilization</span> واتجاه الأداء الشهري.</li>
<li><b><span dir="ltr">Reports / Cockpit / Alerts</span></b> — التقارير، الرؤية الإدارية، والإشارات التي تحتاج متابعة حسب الدور.</li>
<li><b><span dir="ltr">Guide</span></b> — مرجع للمبادئ، طريقة الاستخدام، وحدود النظام.</li>
</ul>

<div class="v03-guide-rule"><b>التنقل الحالي:</b><br><span dir="ltr">Desktop</span>: استخدم الـSidebar الثابتة واختر القسم.<br><span dir="ltr">Mobile</span>: اضغط <span dir="ltr">☰ Menu · [Current Page]</span> أعلى الشاشة ثم اختر القسم؛ القائمة تغلق ويُفتح القسم المحدد من أعلى الصفحة.<br><br><b>لإضافة عدة أجهزة:</b> استخدم <span dir="ltr">Instruments → Import Instrument List</span>. ويمكنك تنزيل السجل الحالي من <span dir="ltr">Current Instrument Registry</span> ثم تحديث الحقول المعتمدة وإعادة استيراده بعد المراجعة.</div>

<h3 style="margin-top:1.1rem">أفضل طريقة تبدأ بها</h3>
<div class="v03-guide-flow">
  <div class="v03-flow-step"><div class="v03-flow-num">1</div><div><div class="v03-flow-main">افتح <span dir="ltr">Instruments</span> وأنشئ الجهاز أو استورد القائمة</div><div class="v03-flow-sub">ثبّت الهوية الأساسية أولًا، ثم افتح <span dir="ltr">Instrument 360</span> للجهاز.</div></div></div>
  <div class="v03-flow-step"><div class="v03-flow-num">2</div><div><div class="v03-flow-main">سجّل <span dir="ltr">Need / URS</span></div><div class="v03-flow-sub">وثّق الحاجة، الاستخدام المقصود، ومتطلبات المستخدم.</div></div></div>
  <div class="v03-flow-step"><div class="v03-flow-num">3</div><div><div class="v03-flow-main"><span dir="ltr">Quotation / PR / PO / Receiving</span></div><div class="v03-flow-sub">تابع رحلة الشراء والاستلام بدون فقد التسلسل.</div></div></div>
  <div class="v03-flow-step"><div class="v03-flow-num">4</div><div><div class="v03-flow-main"><span dir="ltr">Installation / IQ / OQ / PQ</span></div><div class="v03-flow-sub">سجّل التركيب والتأهيل بناءً على الدليل المتاح.</div></div></div>
  <div class="v03-flow-step"><div class="v03-flow-num">5</div><div><div class="v03-flow-main"><span dir="ltr">Release / Issuance</span></div><div class="v03-flow-sub">وثّق إصدار الجهاز للاستخدام المنضبط بعد التأهيل.</div></div></div>
  <div class="v03-flow-step"><div class="v03-flow-num">6</div><div><div class="v03-flow-main"><span dir="ltr">First Run</span></div><div class="v03-flow-sub">سجّل أول تشغيل روتيني معتمد — وليس تجربة غير رسمية.</div></div></div>
  <div class="v03-flow-step"><div class="v03-flow-num">7</div><div><div class="v03-flow-main"><span dir="ltr">Routine Control</span></div><div class="v03-flow-sub">حافظ على <span dir="ltr">Calibration / PM / Qualification / Components</span> محدثة.</div></div></div>
  <div class="v03-flow-step"><div class="v03-flow-num">8</div><div><div class="v03-flow-main"><span dir="ltr">Events / Investigation</span></div><div class="v03-flow-sub">سجّل ما حدث أولًا، ثم اتبع الدليل في التحقيق.</div></div></div>
  <div class="v03-flow-step"><div class="v03-flow-num">9</div><div><div class="v03-flow-main"><span dir="ltr">Performance Review</span></div><div class="v03-flow-sub">راجع الاعتمادية، التوقفات، السعة، والاستخدام قبل القرار.</div></div></div>
  <div class="v03-flow-step"><div class="v03-flow-num">10</div><div><div class="v03-flow-main"><span dir="ltr">Retirement</span></div><div class="v03-flow-sub">أغلق دورة الحياة مع الاحتفاظ بتاريخ الجهاز كدليل.</div></div></div>
</div>

<div class="v03-guide-tip"><b>نصيحة عملية:</b> لا تحاول إدخال كل شيء في جلسة واحدة إذا كانت البيانات غير متاحة. أدخل فقط ما لديك كدليل فعلي، واترك الناقص ظاهرًا. قيمة التطبيق تأتي من إظهار <b><span dir="ltr">Missing Evidence</span></b> بوضوح بدل تحويل الفراغات إلى افتراضات.</div>
</div>
""",
                unsafe_allow_html=True,
            )

        with guide_tabs[1]:
            st.markdown("### دورة حياة الجهاز — ماذا أسجل ومتى؟")
            st.markdown(
                """
1. **Need / Initiation** — لماذا نحتاج الجهاز؟ من طلبه؟ الاستخدام المقصود؟ درجة الـCriticality؟ ومتى نحتاجه جاهزًا؟
2. **URS** — سجل رقم/مرجع الـURS وتاريخ اعتماده. لا تعتبر مرحلة التخطيط مكتملة لمجرد وجود جهاز مطلوب.
3. **Quotation** — سجل العرض المختار أو المرجع الذي تم تقييمه وتاريخه.
4. **PR** — رقم Purchase Requisition وتاريخ الاعتماد.
5. **PO** — رقم Purchase Order وتاريخ الإصدار/الاعتماد.
6. **Receiving** — Expected Receiving Date ثم Actual Receiving Date. التطبيق يستطيع إظهار التأخير عندما يمر الموعد المتوقع بدون تسجيل الاستلام.
7. **Installation** — تاريخ التركيب، مرجع تقرير التركيب، Site Readiness وUtilities.
8. **IQ → OQ → PQ** — سجل تاريخ اكتمال كل مرحلة حسب الدليل المتاح.
9. **Release / Issuance** — متى تم تسليم/إصدار الجهاز للاستخدام المنضبط بعد التأهيل.
10. **First approved routine run** — أول تشغيل روتيني معتمد، وليس مجرد Test أو Trial غير رسمي.
11. **Routine Operation** — حافظ على Calibration / PM / Qualification / Components محدثة أثناء عمر الجهاز.
12. **Performance Review** — راجع الأداء التاريخي، الأعطال، تكرار المشكلات، الالتزام بالمواعيد والحاجة إلى Upgrade/Replacement.
13. **Retirement / Decommission** — سبب التكهن، الاعتماد، تاريخ الإيقاف، Archive/Backup، تعطيل الوصول، التخلص/النقل، والجهاز البديل إن وجد.
"""
            )
            st.warning("لا تستخدم وجود تاريخ في مرحلة متأخرة كدليل تلقائي على اكتمال المراحل السابقة. كل Milestone يجب أن يستند إلى Evidence مسجل.")

        with guide_tabs[2]:
            st.markdown("### كيف تستخدمه في الشغل اليومي؟")
            st.markdown(
                """
**بداية اليوم / بداية الشيفت**
- افتح **Dashboard** أولًا. على الهاتف: **☰ Menu → Dashboard**. على الكمبيوتر: اختر **Dashboard** من الـSidebar.
- راجع Calibration overdue، PM overdue، Qualification due، Open OOC، Open Events وPriority Attention Queue.
- لا تبدأ بالبحث داخل كل جهاز؛ دع الـDashboard يحدد أين تحتاج أن تنظر أولًا.

**عند مراجعة جهاز محدد**
- اذهب إلى **Instruments → Open Instrument 360** واختر الجهاز.
- اقرأ أولًا **Health Score + Status + Open Events + Availability + Utilization**.
- افتح **Why this score?** لفهم العوامل المؤثرة بدون تحويل الإشارة إلى حكم GMP.
- راجع **Management Attention** إذا ظهر تعارض بين الحالة التشغيلية والدليل المرتبط داخل التطبيق.

**عند عمل Calibration أو PM**
- سجل الحدث في نفس يوم تنفيذه أو بمجرد اعتماد السجل.
- احتفظ بمرجع Certificate / Protocol / Work Order / Service report.
- أدخل Next Due المعتمد؛ لا تستخدم موعدًا تقديريًا إذا لم يكن معتمدًا.

**عند تغيير جزء**
- سجل Component name، Part number / Serial إن وجد، Installed date وReplacement/Review due.
- الهدف أن تعرف لاحقًا: هل المشكلة تكررت قبل أم بعد تغيير الجزء؟

**عند حدوث عطل**
- اذهب إلى **Events** وسجل ما حدث فعليًا: التاريخ، النوع، الشدة، الـSubsystem، الحالة، والـObserved facts.
- لا تكتب "Pump failure" كحقيقة إذا الذي تعرفه فقط هو "Pressure fluctuation".

**عند إغلاق المشكلة**
- اربط Investigation reference / evidence والنتيجة النهائية.
- حافظ على الفرق بين Confirmed Root Cause وProbable وNot Yet Identified.

**عند تسجيل الأداء الشهري**
- افتح **Performance**، اختر الجهاز والشهر، ثم أدخل: Scheduled Service Hours، Planned Downtime، Unplanned Downtime، Productive Run Hours.
- التطبيق يحسب تلقائيًا Planned Operating Time، Available Time، Availability وUtilization.
- يمكن مراجعة أحدث القيم والاتجاه من داخل **Instrument 360 → PERFORMANCE** لنفس الجهاز.
"""
            )
            st.markdown("<div class='v03-guide-rule'><b>أفضل استفادة:</b> استخدم التطبيق باستمرار كـ instrument memory، وليس فقط عندما تظهر مشكلة. جودة التحقيق غدًا تعتمد على جودة التاريخ الذي تسجله اليوم.</div>", unsafe_allow_html=True)

        with guide_tabs[3]:
            st.markdown("### Investigation Intelligence — كيف تستخدمه صح؟")
            st.markdown(
                """
ابدأ دائمًا بالترتيب التالي:

1. **Expected** — ما الذي كان يجب أن يحدث؟ Acceptance criteria / normal behavior.
2. **Actual / Observed** — ماذا حدث فعلًا؟ أرقام، Chromatogram behavior، pressure، response، error message، إلخ.
3. **Changed** — ما الذي تغير مؤخرًا؟ Column / mobile phase / analyst / maintenance / part / lot / method / environment.
4. **Unchanged** — ما الذي ظل ثابتًا ويساعدك على استبعاد فرضيات؟
5. **Objective Evidence** — Logs، chromatograms، calibration history، maintenance records، component dates، sequence information.

التطبيق بعدها يربط الحالة بتاريخ الجهاز ويقترح **Next Evidence Action**. الهدف ليس أن يعطيك Root Cause سريع، بل أن يقلل مساحة التخمين.
"""
            )
            st.markdown("<div class='v03-guide-rule'><b>قاعدة التحقيق:</b> Repeated pattern strengthens a hypothesis. It does not independently prove root cause.</div>", unsafe_allow_html=True)
            st.markdown(
                """
**لا تفعل:** تغيّر 3 متغيرات مرة واحدة، تكرر الحقن حتى Pass، أو تسجل unofficial injections كطريقة لحل المشكلة.  
**افعل:** حافظ على الدليل، Localize، اختبر متغيرًا discriminating واحدًا، ثم Confirm قبل القرار.
"""
            )

        with guide_tabs[4]:
            st.markdown("### GMP / Data Integrity / Privacy")
            st.markdown(
                """
- البيانات منظمة داخل **Workspaces** منفصلة، و**Supabase Row Level Security** هو أساس طبقة العزل. التطبيق يواصل تقوية enforcement على مستوى كل business action قبل اعتباره Security Authority مكتملة.
- Excel import يكتب من خلال جلسة المستخدم الحالية وداخل الـWorkspace النشط؛ لا تستخدم الاستيراد كبديل عن مراجعة الصلاحيات والحوكمة.
- التطبيق **Decision-Support Software** وليس حاليًا نظام GxP validated system of record.
- احتفظ بالسجلات الرسمية المعتمدة — SOP forms، certificates، deviations، CAPA، approvals، raw data — داخل الأنظمة الرسمية المعتمدة بالشركة.
- Health Score أو Lifecycle signal لا يساوي تلقائيًا قرار Release / Reject / Fitness for use.
- التطبيق لا يجب أن يملأ Evidence غير موجود ولا يحوّل inference إلى fact.
"""
            )
            st.markdown("<div class='v03-guide-rule'><b>DON'T GUESS. FOLLOW THE EVIDENCE.</b><br>لو لم يوجد دليل، سجّل أن المعلومة Unknown بدل أن تستنتجها.</div>", unsafe_allow_html=True)

        with guide_tabs[5]:
            st.markdown("### 🧭 خطوات العمل الفعلية داخل التطبيق")
            st.caption("اتبع المسار كما هو ظاهر في التطبيق. Desktop: Sidebar. Mobile: ☰ Menu · Current Page.")

            st.markdown("""
<div class="v03-workflow-card"><b>1) بداية اليوم / بداية الشيفت</b><br><span class="v03-workflow-route">Dashboard</span><br>
راجع الإشارات ذات الأولوية: overdue controls، open events، OOC، restrictions، والـattention queue المتاحة لدورك.
<div class="v03-workflow-outcome"><b>النتيجة:</b> تعرف أين تبدأ قبل أن تدخل إلى تفاصيل أي جهاز.</div></div>

<div class="v03-workflow-card"><b>2) إضافة جهاز واحد</b><br><span class="v03-workflow-route">Instruments → Add one instrument</span><br>
أدخل Instrument ID، الاسم، النوع، الشركة، الموديل، Serial Number، Location، Responsible Team والحالة التشغيلية. استخدم Camera Assist عند الحاجة لتقليل أخطاء النقل. احفظ السجل ثم افتح الجهاز من <span dir="ltr">Open Instrument 360</span>.
<div class="v03-workflow-outcome"><b>النتيجة:</b> يصبح للجهاز Digital Identity ثابتة يمكن ربط كل التاريخ بها.</div></div>

<div class="v03-workflow-card"><b>3) استيراد أو تحديث قائمة أجهزة</b><br><span class="v03-workflow-route">Instruments → Import Instrument List</span><br>
حمّل القالب أو نزّل Current Instrument Registry، لا تغيّر أسماء الأعمدة، املأ فقط البيانات المعروفة، ارفع الملف، راجع Recognized / Ignored Columns ثم اختر Create أو Update وبعدها Confirm Import.
<div class="v03-workflow-outcome"><b>النتيجة:</b> انتقال منظم من Excel بدون تخمين في Mapping أو ملء Evidence غير موجود.</div></div>

<div class="v03-workflow-card"><b>4) مراجعة جهاز محدد</b><br><span class="v03-workflow-route">Instruments → Open Instrument 360</span><br>
ابدأ بـ Health Score، Status، Open Events، Availability وUtilization. بعد ذلك افتح: Identity → Lifecycle → Control → Performance → Events → Evidence. افتح <span dir="ltr">Why XX/100?</span> لفهم عوامل السكور.
<div class="v03-workflow-outcome"><b>النتيجة:</b> ترى قصة الجهاز المتصلة قبل اتخاذ أي قرار أو بدء تحقيق.</div></div>

<div class="v03-workflow-card"><b>5) تسجيل Calibration / Qualification / PM / Maintenance</b><br><span class="v03-workflow-route">Cal & PM</span><br>
اختر الجهاز، سجل نوع العمل وتاريخ التنفيذ ومرجع Certificate / Protocol / Work Order / Service Report، ثم أدخل Next Due المعتمد. عند تغيير Component سجل Part / Serial / Installed Date / Review or Replacement Due إن توفرت.
<div class="v03-workflow-outcome"><b>النتيجة:</b> Control history يظل مرتبطًا بنفس الجهاز ويظهر أثره في Dashboard وInstrument 360.</div></div>

<div class="v03-workflow-card"><b>6) تسجيل عطل أو Quality Event</b><br><span class="v03-workflow-route">Events</span><br>
اختر الجهاز وسجل التاريخ، Event Type، Severity، Subsystem، الحالة وObserved Facts. اكتب ما حدث فعلًا؛ لا تحول Pressure fluctuation إلى Pump failure بدون Evidence.
<div class="v03-workflow-outcome"><b>النتيجة:</b> تبدأ التحقيق من Observation موثق وليس من تشخيص مسبق.</div></div>

<div class="v03-workflow-card"><b>7) تشغيل Investigation Intelligence</b><br><span class="v03-workflow-route">Investigate</span><br>
رتب الحالة: Expected → Actual / Observed → Changed → Unchanged → Objective Evidence → Next Evidence Action. اختبر متغيرًا discriminating واحدًا عندما يكون ذلك مناسبًا، ثم Confirm قبل رفع الفرضية إلى Root Cause.
<div class="v03-workflow-outcome"><b>النتيجة:</b> تقل مساحة التخمين وتبقى Unknowns واضحة بدل دفنها داخل narrative.</div></div>

<div class="v03-workflow-card"><b>8) تسجيل Availability & Utilization</b><br><span class="v03-workflow-route">Performance</span><br>
اختر الجهاز والشهر وأدخل 4 قيم: Scheduled Service Hours، Planned Downtime، Unplanned Downtime، Productive Run Hours. التطبيق يحسب Planned Operating، Available Time، Availability وUtilization ثم يعرض الاتجاه الشهري.
<div class="v03-workflow-outcome"><b>النتيجة:</b> أحدث القيم تظهر أيضًا داخل Instrument 360 وتدعم capacity / reliability review.</div></div>

<div class="v03-workflow-card"><b>9) التقارير والرؤية الإدارية</b><br><span class="v03-workflow-route">Reports / Cockpit / Alerts</span><br>
استخدم Reports عندما تحتاج Evidence Pack أو مخرجًا قابلًا للمشاركة، Cockpit للرؤية الإدارية والمخاطر والسعة، وAlerts لمتابعة الإشارات التي تحتاج action حسب الدور.
<div class="v03-workflow-outcome"><b>النتيجة:</b> تتحول البيانات إلى Attention → Decision → Action بدل قائمة تواريخ فقط.</div></div>

<div class="v03-workflow-card"><b>10) تغيير الدور أو تسجيل الخروج</b><br><span class="v03-workflow-route">Mobile: ☰ Menu → ACCOUNT · Desktop: Sidebar → ACCOUNT</span><br>
استخدم Change role لتغيير ترتيب الواجهة والأولويات، واستخدم Log out لإنهاء جلسة Supabase ومسح تسجيل الدخول المستمر. Job Role يخص تجربة الاستخدام؛ الصلاحيات الأمنية الفعلية تُدار بشكل منفصل.
<div class="v03-workflow-outcome"><b>النتيجة:</b> واجهة مناسبة للمسؤولية بدون الخلط بين Role وPrivilege.</div></div>
""", unsafe_allow_html=True)

            st.markdown("### 📸 Visual walkthrough من التطبيق")
            st.caption("لقطات Demo نظيفة توضح أين تقرأ الإشارة وكيف تنتقل من Overview إلى Attention. الصور للتدريب ولا تمثل سجل GMP رسمي.")
            _shot_overview = guide_visual_bytes("instrument_360_overview")
            if _shot_overview:
                st.image(_shot_overview, caption="Step 4 · Instruments → Open Instrument 360: اقرأ Health Score وStatus وOpen Events وAvailability وUtilization أولًا.", width=260)

            st.info("قاعدة الاستخدام: ENTER LESS. DECIDE BETTER. KEEP THE INSTRUMENT STORY CONNECTED.")
