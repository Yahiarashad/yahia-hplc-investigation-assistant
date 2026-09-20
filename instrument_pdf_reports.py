from __future__ import annotations

from io import BytesIO
from datetime import datetime, timezone
from pathlib import Path
from xml.sax.saxutils import escape as xml_escape

import streamlit as st

try:
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_LEFT, TA_RIGHT, TA_CENTER
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
except Exception:
    colors = None

try:
    import arabic_reshaper
    from bidi.algorithm import get_display as bidi_get_display
except Exception:
    arabic_reshaper = None
    bidi_get_display = None

V03_REPORT_SELECT = (
    "id,instrument_code,instrument_name,instrument_type,manufacturer,model,serial_number,location,"
    "operational_status,responsible_team,qualification_due,pm_due,calibration_due,notes,"
    "need_title,need_identified_date,requested_by,department,need_justification,intended_use,"
    "criticality,target_implementation_date,urs_reference,urs_approval_date,quotation_reference,"
    "quotation_date,pr_number,pr_approval_date,po_number,po_approval_date,expected_receiving_date,"
    "receiving_date,installation_date,installation_reference,site_readiness_confirmed,utilities_confirmed,"
    "iq_date,oq_date,pq_date,issuance_date,first_run_date,created_at,updated_at"
)

_STAGE_FIELDS = [
    ("Need", "need_identified_date"), ("URS", "urs_approval_date"),
    ("Quotation", "quotation_date"), ("PR", "pr_approval_date"),
    ("PO", "po_approval_date"), ("Receiving", "receiving_date"),
    ("Installation", "installation_date"), ("IQ", "iq_date"),
    ("OQ", "oq_date"), ("PQ", "pq_date"),
    ("Release / Issuance", "issuance_date"), ("First Run", "first_run_date"),
]

AR_LABELS = {
    "Instrument Lifecycle Evidence Report": "تقرير أدلة دورة حياة الجهاز",
    "Portfolio Management Snapshot": "ملخص محفظة الأجهزة للإدارة",
    "Instrument identity": "هوية الجهاز", "Lifecycle readiness": "جاهزية دورة الحياة",
    "Acquisition & qualification": "الشراء والتأهيل", "Routine control": "التحكم أثناء التشغيل",
    "Events & investigation": "الأحداث والتحقيق", "Components": "المكونات",
    "Current stage": "المرحلة الحالية", "Completion": "نسبة الاكتمال",
    "Next controlled action": "الخطوة التالية المنضبطة", "Missing evidence": "الأدلة الناقصة",
    "Health score": "درجة صحة الجهاز", "Open events": "الأحداث المفتوحة",
    "Operational status": "حالة التشغيل", "Instrument ID": "كود الجهاز",
    "Instrument name": "اسم الجهاز", "Type": "النوع", "Manufacturer": "الشركة المصنعة",
    "Model": "الموديل", "Serial number": "الرقم التسلسلي", "Location": "الموقع",
    "Responsible team": "الفريق المسؤول", "Qualification due": "موعد التأهيل",
    "PM due": "موعد الصيانة الوقائية", "Calibration due": "موعد المعايرة",
    "Generated": "تاريخ الإنشاء", "Decision-support copy": "نسخة دعم قرار غير خاضعة للضبط كسجل GMP",
    "Evidence note": "ملاحظة الدليل", "Recorded": "مسجل",
}


def _ar_text(value: str) -> str:
    text = str(value or "")
    if not text:
        return ""
    if arabic_reshaper is None or bidi_get_display is None:
        return text
    try:
        return bidi_get_display(arabic_reshaper.reshape(text))
    except Exception:
        return text


def _find_arabic_font():
    candidates = [
        ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
        ("/usr/share/fonts/truetype/freefont/FreeSans.ttf", "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf"),
    ]
    for regular, bold in candidates:
        if Path(regular).exists() and Path(bold).exists():
            return regular, bold
    return None, None


def _register_fonts():
    regular, bold = _find_arabic_font()
    if regular and bold:
        try:
            pdfmetrics.registerFont(TTFont("ILM", regular))
            pdfmetrics.registerFont(TTFont("ILMB", bold))
            return "ILM", "ILMB", True
        except Exception:
            pass
    return "Helvetica", "Helvetica-Bold", False


def _v(value):
    if value in (None, "", []):
        return "—"
    if isinstance(value, bool):
        return "Yes" if value else "No"
    return str(value)


def _stage_summary(inst: dict):
    completed, missing = [], []
    for label, field in _STAGE_FIELDS:
        (completed if inst.get(field) else missing).append(label)
    completion = int(round((len(completed) / len(_STAGE_FIELDS)) * 100)) if _STAGE_FIELDS else 0
    current = missing[0] if missing else "Routine Operation"
    next_action = {
        "Need": "Record the laboratory need, justification, intended use and criticality.",
        "URS": "Approve and record the User Requirements Specification.",
        "Quotation": "Record the selected/evaluated quotation and date.",
        "PR": "Record Purchase Requisition approval.",
        "PO": "Record Purchase Order issue / approval.",
        "Receiving": "Record actual receipt and compare with the expected receiving date.",
        "Installation": "Document installation, site readiness and utilities.",
        "IQ": "Complete and document Installation Qualification.",
        "OQ": "Complete and document Operational Qualification.",
        "PQ": "Complete and document Performance Qualification.",
        "Release / Issuance": "Release / issue the qualified instrument for controlled laboratory use.",
        "First Run": "Record the first approved routine analytical run.",
        "Routine Operation": "Keep calibration, PM, requalification, events, components and periodic review current.",
    }.get(current, "Review the next missing evidence item.")
    return completion, current, missing, next_action


def _build_styles(lang="en"):
    font, bold, ar_font = _register_fonts()
    right = lang == "ar"
    base = getSampleStyleSheet()
    return {
        "font": font, "bold": bold, "arabic_font": ar_font,
        "title": ParagraphStyle("ILMTitle", parent=base["Title"], fontName=bold, fontSize=20, leading=24, textColor=colors.HexColor("#08233f"), alignment=TA_RIGHT if right else TA_LEFT, spaceAfter=8),
        "h1": ParagraphStyle("ILMH1", parent=base["Heading1"], fontName=bold, fontSize=13, leading=17, textColor=colors.HexColor("#08233f"), alignment=TA_RIGHT if right else TA_LEFT, spaceBefore=8, spaceAfter=6),
        "body": ParagraphStyle("ILMBody", parent=base["BodyText"], fontName=font, fontSize=8.8, leading=12, textColor=colors.HexColor("#263445"), alignment=TA_RIGHT if right else TA_LEFT),
        "small": ParagraphStyle("ILMSmall", parent=base["BodyText"], fontName=font, fontSize=7.5, leading=10, textColor=colors.HexColor("#65758b"), alignment=TA_RIGHT if right else TA_LEFT),
    }


def _label(label, lang):
    return AR_LABELS.get(label, label) if lang == "ar" else label


def _paragraph(text, style, lang="en"):
    value = _ar_text(text) if lang == "ar" else str(text or "")
    return Paragraph(xml_escape(value).replace("\n", "<br/>"), style)


def _page_header(canvas, doc, styles):
    canvas.saveState()
    w, h = doc.pagesize
    canvas.setFillColor(colors.HexColor("#07111f"))
    canvas.rect(0, h - 17 * mm, w, 17 * mm, fill=1, stroke=0)
    canvas.setFillColor(colors.HexColor("#d6b85f"))
    canvas.setFont(styles["bold"], 8)
    canvas.drawString(14 * mm, h - 10.5 * mm, "YAHIA QC INSTRUMENT LIFECYCLE · EVIDENCE FIRST")
    canvas.setFillColor(colors.HexColor("#7b8794"))
    canvas.setFont(styles["font"], 7)
    canvas.drawRightString(w - 14 * mm, 8 * mm, f"Page {doc.page}")
    canvas.restoreState()


def _kv_table(rows, styles, lang="en", widths=(47 * mm, 118 * mm)):
    data = []
    for key, value in rows:
        k = _label(key, lang)
        if lang == "ar":
            k, val_text = _ar_text(k), _ar_text(_v(value))
        else:
            val_text = _v(value)
        data.append([Paragraph(xml_escape(str(k)), styles["body"]), Paragraph(xml_escape(str(val_text)), styles["body"])])
    table = Table(data, colWidths=list(widths))
    table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"), ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f4f7fa")),
        ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#dce4ec")),
        ("LEFTPADDING", (0, 0), (-1, -1), 6), ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    return table


def _section(story, title, rows, styles, lang="en"):
    story.append(_paragraph(_label(title, lang), styles["h1"], lang))
    story.append(_kv_table(rows, styles, lang))
    story.append(Spacer(1, 4 * mm))


def _instrument_pdf(inst, context, report_lang="en"):
    styles = _build_styles(report_lang)
    lang = report_lang
    events = context.get("events") or []
    maintenance = context.get("maintenance") or []
    lifecycle_records = context.get("lifecycle_records") or []
    components = context.get("components") or []
    iid = str(inst.get("id") or "")
    inst_events = [e for e in events if str(e.get("instrument_id")) == iid]
    inst_maintenance = [r for r in maintenance if str(r.get("instrument_id")) == iid]
    inst_lifecycle = [r for r in lifecycle_records if str(r.get("instrument_id")) == iid]
    inst_components = [r for r in components if str(r.get("instrument_id")) == iid]
    open_events = [e for e in inst_events if str(e.get("event_status") or "") != "Closed"]
    completion, current, missing, next_action = _stage_summary(inst)
    score = None
    try:
        score, _ = context["health_score_v2"](inst, events, components)
    except Exception:
        pass

    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, rightMargin=14*mm, leftMargin=14*mm, topMargin=23*mm, bottomMargin=15*mm, title="Instrument Lifecycle Evidence Report", author="Yahia QC Instrument Lifecycle")
    story = []
    story.append(_paragraph(_label("Instrument Lifecycle Evidence Report", lang), styles["title"], lang))
    story.append(_paragraph(f"{_v(inst.get('instrument_code'))} · {_v(inst.get('instrument_name'))}", styles["h1"], lang))
    generated = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    story.append(_paragraph(f"{_label('Generated', lang)}: {generated}", styles["small"], lang))
    story.append(_paragraph(_label("Decision-support copy", lang), styles["small"], lang))
    story.append(Spacer(1, 5*mm))

    _section(story, "Instrument identity", [
        ("Instrument ID", inst.get("instrument_code")), ("Instrument name", inst.get("instrument_name")),
        ("Type", inst.get("instrument_type")), ("Manufacturer", inst.get("manufacturer")),
        ("Model", inst.get("model")), ("Serial number", inst.get("serial_number")),
        ("Location", inst.get("location")), ("Responsible team", inst.get("responsible_team")),
        ("Operational status", inst.get("operational_status")),
    ], styles, lang)
    _section(story, "Lifecycle readiness", [
        ("Completion", f"{completion}%"), ("Current stage", current),
        ("Next controlled action", next_action), ("Missing evidence", ", ".join(missing) if missing else "None"),
        ("Health score", f"{score}/100" if score is not None else "Not available"), ("Open events", len(open_events)),
    ], styles, lang)
    _section(story, "Acquisition & qualification", [
        ("Need identified", inst.get("need_identified_date")), ("URS reference", inst.get("urs_reference")),
        ("URS approval date", inst.get("urs_approval_date")), ("Quotation reference", inst.get("quotation_reference")),
        ("Quotation date", inst.get("quotation_date")), ("PR number", inst.get("pr_number")),
        ("PR approval date", inst.get("pr_approval_date")), ("PO number", inst.get("po_number")),
        ("PO approval / issue date", inst.get("po_approval_date")), ("Expected receiving date", inst.get("expected_receiving_date")),
        ("Actual receiving date", inst.get("receiving_date")), ("Installation date", inst.get("installation_date")),
        ("IQ completion date", inst.get("iq_date")), ("OQ completion date", inst.get("oq_date")),
        ("PQ completion date", inst.get("pq_date")), ("Release / issuance date", inst.get("issuance_date")),
        ("First approved routine run", inst.get("first_run_date")),
    ], styles, lang)
    _section(story, "Routine control", [
        ("Qualification due", inst.get("qualification_due")), ("PM due", inst.get("pm_due")),
        ("Calibration due", inst.get("calibration_due")), ("Maintenance records", len(inst_maintenance)),
        ("Calibration / qualification records", len(inst_lifecycle)),
    ], styles, lang)

    if inst_events:
        story.append(_paragraph(_label("Events & investigation", lang), styles["h1"], lang))
        event_data = [[Paragraph(x, styles["small"]) for x in ["Date", "Event", "Severity", "Status", "Observed facts"]]]
        for e in inst_events[:15]:
            vals = [e.get("event_date"), e.get("event_type"), e.get("severity"), e.get("event_status"), e.get("observed_facts")]
            event_data.append([Paragraph(xml_escape(_ar_text(_v(v)) if lang == "ar" else _v(v)), styles["small"]) for v in vals])
        t = Table(event_data, colWidths=[22*mm, 30*mm, 22*mm, 24*mm, 67*mm], repeatRows=1)
        t.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#08233f")), ("TEXTCOLOR", (0,0), (-1,0), colors.white),
            ("GRID", (0,0), (-1,-1), .3, colors.HexColor("#dce4ec")), ("VALIGN", (0,0), (-1,-1), "TOP"),
            ("LEFTPADDING", (0,0), (-1,-1), 4), ("RIGHTPADDING", (0,0), (-1,-1), 4),
            ("TOPPADDING", (0,0), (-1,-1), 4), ("BOTTOMPADDING", (0,0), (-1,-1), 4),
        ]))
        story.append(t); story.append(Spacer(1, 4*mm))

    if inst_components:
        _section(story, "Components", [
            ("Recorded", len(inst_components)),
            ("Evidence note", "; ".join(f"{_v(c.get('component_name'))}: {_v(c.get('status'))}" for c in inst_components[:10])),
        ], styles, lang)

    boundary_en = "This PDF is generated from the current application dataset as decision-support evidence. It is not a validated GxP record and does not replace approved certificates, qualification protocols, deviations, CAPA, raw data, or SOP-controlled records."
    boundary_ar = "هذا التقرير مولد من بيانات التطبيق الحالية كأداة لدعم القرار. لا يعد سجل GxP معتمدًا، ولا يستبدل الشهادات أو بروتوكولات التأهيل أو الانحرافات أو CAPA أو البيانات الخام أو السجلات الخاضعة لإجراءات العمل المعتمدة."
    story.append(_paragraph("Evidence boundary", styles["h1"], lang))
    story.append(_paragraph(boundary_ar if lang == "ar" else boundary_en, styles["body"], lang))
    doc.build(story, onFirstPage=lambda c,d: _page_header(c,d,styles), onLaterPages=lambda c,d: _page_header(c,d,styles))
    return buf.getvalue(), styles["arabic_font"]


def _portfolio_pdf(instruments, context, report_lang="en"):
    styles = _build_styles(report_lang); lang = report_lang
    events = context.get("events") or []; components = context.get("components") or []
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=landscape(A4), rightMargin=12*mm, leftMargin=12*mm, topMargin=23*mm, bottomMargin=14*mm, title="Portfolio Management Snapshot", author="Yahia QC Instrument Lifecycle")
    story = [_paragraph(_label("Portfolio Management Snapshot", lang), styles["title"], lang)]
    generated = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    story.append(_paragraph(f"{_label('Generated', lang)}: {generated}", styles["small"], lang)); story.append(Spacer(1, 4*mm))
    headers = ["Instrument ID", "Instrument name", "Operational status", "Current stage", "Completion", "Health score", "Open events", "Calibration due", "PM due"]
    data = [[Paragraph(xml_escape(_ar_text(_label(h, lang)) if lang == "ar" else _label(h, lang)), styles["small"]) for h in headers]]
    for inst in instruments:
        completion, current, _, _ = _stage_summary(inst); iid = str(inst.get("id") or "")
        open_events = sum(1 for e in events if str(e.get("instrument_id")) == iid and str(e.get("event_status") or "") != "Closed")
        try: score, _ = context["health_score_v2"](inst, events, components)
        except Exception: score = "—"
        vals = [inst.get("instrument_code"), inst.get("instrument_name"), inst.get("operational_status"), current, f"{completion}%", score, open_events, inst.get("calibration_due"), inst.get("pm_due")]
        data.append([Paragraph(xml_escape(_ar_text(_v(v)) if lang == "ar" else _v(v)), styles["small"]) for v in vals])
    table = Table(data, colWidths=[24*mm,42*mm,30*mm,30*mm,21*mm,21*mm,20*mm,27*mm,27*mm], repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#08233f")), ("TEXTCOLOR", (0,0), (-1,0), colors.white),
        ("GRID", (0,0), (-1,-1), .3, colors.HexColor("#dce4ec")), ("VALIGN", (0,0), (-1,-1), "TOP"),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, colors.HexColor("#f7f9fb")]),
        ("LEFTPADDING", (0,0), (-1,-1), 4), ("RIGHTPADDING", (0,0), (-1,-1), 4),
        ("TOPPADDING", (0,0), (-1,-1), 4), ("BOTTOMPADDING", (0,0), (-1,-1), 4),
    ]))
    story.append(table); story.append(Spacer(1,4*mm))
    boundary = "Decision-support portfolio snapshot. Official GMP records remain in approved company systems." if lang == "en" else "ملخص لدعم القرار فقط. تظل السجلات الرسمية الخاصة بـGMP داخل الأنظمة المعتمدة بالشركة."
    story.append(_paragraph(boundary, styles["small"], lang))
    doc.build(story, onFirstPage=lambda c,d: _page_header(c,d,styles), onLaterPages=lambda c,d: _page_header(c,d,styles))
    return buf.getvalue(), styles["arabic_font"]


def _load_full_instruments(context):
    db_list = context.get("_db_list")
    if not callable(db_list):
        return context.get("instruments") or [], "", True
    return db_list("instruments", V03_REPORT_SELECT, "created_at.asc")


def render_pdf_report_center(context: dict, ui_lang: str = "ar") -> None:
    if colors is None:
        st.warning("PDF export dependency is not installed yet. Install reportlab to enable the Report Center.")
        return
    title = "📄 مركز التقارير | PDF Report Center" if ui_lang == "ar" else "📄 PDF Report Center"
    intro = "حوّل بيانات الجهاز الحالية إلى تقرير Evidence-first يمكن مشاركته للمراجعة أو المتابعة الإدارية، مع بقاء السجلات الرسمية داخل الأنظمة المعتمدة." if ui_lang == "ar" else "Turn the current instrument dataset into an evidence-first review or management PDF while keeping official GMP records in approved systems."
    with st.expander(title, expanded=False):
        st.markdown(f"**{intro}**")
        st.caption("Generated on demand · No PDF is stored automatically · Decision-support / uncontrolled copy")
        instruments, err, ok = _load_full_instruments(context)
        if not ok:
            st.error("Could not load the full lifecycle dataset for reporting.")
            if err: st.caption(f"Diagnostic: {err}")
            return
        if not instruments:
            st.info("Create an Instrument Passport first, then return here to generate reports."); return
        c1, c2 = st.columns(2)
        report_kind = c1.selectbox("نوع التقرير | Report type" if ui_lang == "ar" else "Report type", ["Instrument Lifecycle Evidence Report", "Portfolio Management Snapshot"], key="ilm_pdf_report_kind")
        report_lang_label = c2.selectbox("لغة التقرير | Report language" if ui_lang == "ar" else "Report language", ["English", "العربية"], index=1 if ui_lang == "ar" else 0, key="ilm_pdf_report_language")
        report_lang = "ar" if report_lang_label == "العربية" else "en"
        selected = None
        if report_kind.startswith("Instrument"):
            options = {f"{i.get('instrument_code')} · {i.get('instrument_name') or 'Unnamed'}": i for i in instruments}
            label = st.selectbox("الجهاز | Instrument" if ui_lang == "ar" else "Instrument", list(options.keys()), key="ilm_pdf_instrument")
            selected = options[label]
            completion, current, missing, next_action = _stage_summary(selected)
            a,b,c,d = st.columns(4); a.metric("Lifecycle", f"{completion}%"); b.metric("Current stage", current); c.metric("Missing evidence", len(missing))
            iid = str(selected.get("id") or ""); open_evt = sum(1 for e in (context.get("events") or []) if str(e.get("instrument_id")) == iid and str(e.get("event_status") or "") != "Closed"); d.metric("Open events", open_evt)
            st.info(("الخطوة التالية: " if ui_lang == "ar" else "Next controlled action: ") + next_action)
        else:
            st.info(f"سيتم إنشاء ملخص إداري لـ {len(instruments)} جهاز/أجهزة." if ui_lang == "ar" else f"A management snapshot will be generated for {len(instruments)} instrument(s).")
        if st.button("⚡ إنشاء التقرير | Generate PDF" if ui_lang == "ar" else "⚡ Generate PDF", use_container_width=True, key="ilm_generate_pdf"):
            with st.spinner("Generating evidence-first PDF…"):
                if report_kind.startswith("Instrument"):
                    pdf_bytes, ar_font = _instrument_pdf(selected, context, report_lang); safe_code = str(selected.get("instrument_code") or "instrument").replace("/", "-"); filename = f"{safe_code}_Lifecycle_Evidence_Report.pdf"
                else:
                    pdf_bytes, ar_font = _portfolio_pdf(instruments, context, report_lang); filename = "Instrument_Lifecycle_Portfolio_Snapshot.pdf"
                st.session_state["ilm_last_pdf"] = pdf_bytes; st.session_state["ilm_last_pdf_name"] = filename; st.session_state["ilm_last_pdf_ar_font"] = ar_font
            if report_lang == "ar" and not st.session_state.get("ilm_last_pdf_ar_font"):
                st.warning("Arabic PDF font support was not detected on this server. Visually check Arabic glyph rendering before use.")
            else: st.success("PDF ready.")
        pdf_bytes = st.session_state.get("ilm_last_pdf")
        if pdf_bytes:
            st.download_button("⬇️ تنزيل التقرير | Download PDF" if ui_lang == "ar" else "⬇️ Download PDF", data=pdf_bytes, file_name=st.session_state.get("ilm_last_pdf_name") or "Instrument_Lifecycle_Report.pdf", mime="application/pdf", use_container_width=True, key="ilm_download_pdf")
            st.caption("Recorded evidence stays recorded; missing evidence stays visible. The PDF does not silently complete missing lifecycle gates.")
