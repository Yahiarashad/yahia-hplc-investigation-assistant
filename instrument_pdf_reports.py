from __future__ import annotations

from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path
from xml.sax.saxutils import escape as xml_escape

import streamlit as st

try:
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_LEFT, TA_RIGHT
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import mm
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
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
    ("Need", "need_identified_date"),
    ("URS", "urs_approval_date"),
    ("Quotation", "quotation_date"),
    ("PR", "pr_approval_date"),
    ("PO", "po_approval_date"),
    ("Receiving", "receiving_date"),
    ("Installation", "installation_date"),
    ("IQ", "iq_date"),
    ("OQ", "oq_date"),
    ("PQ", "pq_date"),
    ("Release / Issuance", "issuance_date"),
    ("First Run", "first_run_date"),
]

AR_LABELS = {
    "Instrument Lifecycle Evidence Report": "تقرير أدلة دورة حياة الجهاز",
    "Portfolio Management Snapshot": "ملخص محفظة الأجهزة للإدارة",
    "Management summary": "الملخص الإداري",
    "Instrument identity": "هوية الجهاز",
    "Lifecycle readiness": "جاهزية دورة الحياة",
    "Acquisition & qualification": "الشراء والتأهيل",
    "Routine control": "التحكم أثناء التشغيل",
    "Events & investigation": "الأحداث والتحقيق",
    "Components": "المكونات",
    "Current stage": "المرحلة الحالية",
    "Completion": "نسبة الاكتمال",
    "Next controlled action": "الخطوة التالية المنضبطة",
    "Missing evidence": "الأدلة الناقصة",
    "Health score": "درجة صحة الجهاز",
    "Open events": "الأحداث المفتوحة",
    "Operational status": "حالة التشغيل",
    "Instrument ID": "كود الجهاز",
    "Instrument name": "اسم الجهاز",
    "Type": "النوع",
    "Manufacturer": "الشركة المصنعة",
    "Model": "الموديل",
    "Serial number": "الرقم التسلسلي",
    "Location": "الموقع",
    "Responsible team": "الفريق المسؤول",
    "Qualification due": "موعد إعادة التأهيل",
    "PM due": "موعد الصيانة الوقائية",
    "Calibration due": "موعد المعايرة",
    "Generated": "تاريخ الإنشاء",
    "Decision-support copy": "نسخة لدعم القرار وليست سجل GMP معتمدًا",
    "Evidence note": "ملاحظة الدليل",
    "Recorded": "عدد السجلات",
    "Need identified": "تاريخ تحديد الاحتياج",
    "URS reference": "مرجع URS",
    "URS approval date": "تاريخ اعتماد URS",
    "Quotation reference": "مرجع عرض السعر",
    "Quotation date": "تاريخ عرض السعر",
    "PR number": "رقم PR",
    "PR approval date": "تاريخ اعتماد PR",
    "PO number": "رقم PO",
    "PO approval / issue date": "تاريخ اعتماد / إصدار PO",
    "Expected receiving date": "تاريخ الاستلام المتوقع",
    "Actual receiving date": "تاريخ الاستلام الفعلي",
    "Installation date": "تاريخ التركيب",
    "IQ completion date": "تاريخ اكتمال IQ",
    "OQ completion date": "تاريخ اكتمال OQ",
    "PQ completion date": "تاريخ اكتمال PQ",
    "Release / issuance date": "تاريخ الإصدار / الإتاحة للاستخدام",
    "First approved routine run": "أول تشغيل روتيني معتمد",
    "Maintenance records": "سجلات الصيانة",
    "Calibration / qualification records": "سجلات المعايرة / التأهيل",
    "Date": "التاريخ",
    "Event": "الحدث",
    "Severity": "الخطورة",
    "Status": "الحالة",
    "Observed facts": "الحقائق المرصودة",
    "Evidence boundary": "حدود استخدام التقرير",
}

AR_STAGE = {
    "Need": "الاحتياج",
    "URS": "URS",
    "Quotation": "عرض السعر",
    "PR": "PR",
    "PO": "PO",
    "Receiving": "الاستلام",
    "Installation": "التركيب",
    "IQ": "IQ",
    "OQ": "OQ",
    "PQ": "PQ",
    "Release / Issuance": "الإصدار / الإتاحة للاستخدام",
    "First Run": "أول تشغيل معتمد",
    "Routine Operation": "التشغيل الروتيني",
}

AR_NEXT_ACTION = {
    "Need": "سجّل احتياج المعمل ومبرره والاستخدام المقصود ودرجة الأهمية.",
    "URS": "اعتمد وسجّل مواصفات متطلبات المستخدم URS.",
    "Quotation": "سجّل عرض السعر المختار أو الذي تم تقييمه وتاريخه.",
    "PR": "سجّل اعتماد طلب الشراء PR.",
    "PO": "سجّل إصدار أو اعتماد أمر الشراء PO.",
    "Receiving": "سجّل الاستلام الفعلي وقارنه بتاريخ الاستلام المتوقع.",
    "Installation": "وثّق التركيب وجاهزية الموقع والمرافق المطلوبة.",
    "IQ": "أكمل ووثّق تأهيل التركيب IQ.",
    "OQ": "أكمل ووثّق التأهيل التشغيلي OQ.",
    "PQ": "أكمل ووثّق تأهيل الأداء PQ.",
    "Release / Issuance": "أصدر الجهاز المؤهل للاستخدام المعملي المنضبط وسجّل تاريخ الإتاحة.",
    "First Run": "سجّل أول تشغيل تحليلي روتيني معتمد.",
    "Routine Operation": "حافظ على المعايرة والصيانة الوقائية وإعادة التأهيل والأحداث والمكونات والمراجعة الدورية محدثة.",
}

AR_VALUES = {
    "Active": "نشط",
    "Restricted": "مقيد الاستخدام",
    "Under Maintenance": "تحت الصيانة",
    "Out of Service": "خارج الخدمة",
    "Retired": "مكهّن / خارج الخدمة نهائيًا",
    "None": "لا يوجد",
    "Not available": "غير متاح",
    "Low": "منخفض",
    "Medium": "متوسط",
    "High": "مرتفع",
    "Critical": "حرج",
    "Open": "مفتوح",
    "Closed": "مغلق",
    "Yes": "نعم",
    "No": "لا",
}


def _contains_arabic(text: str) -> bool:
    return any(
        "\u0600" <= ch <= "\u06ff" or "\u0750" <= ch <= "\u077f" or "\u08a0" <= ch <= "\u08ff"
        for ch in str(text or "")
    )


def _shape_arabic_for_pdf(value) -> str:
    """ReportLab needs shaping/BiDi. Browsers do NOT; never use this for Streamlit UI."""
    text = str(value or "")
    if not text or not _contains_arabic(text):
        return text
    if arabic_reshaper is None or bidi_get_display is None:
        return text
    try:
        return bidi_get_display(arabic_reshaper.reshape(text))
    except Exception:
        return text


def _find_arabic_font():
    candidates = []
    try:
        import matplotlib
        mpl_fonts = Path(matplotlib.get_data_path()) / "fonts" / "ttf"
        candidates.append((mpl_fonts / "DejaVuSans.ttf", mpl_fonts / "DejaVuSans-Bold.ttf"))
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


def _register_fonts():
    regular, bold = _find_arabic_font()
    if regular and bold:
        try:
            if "ILM" not in pdfmetrics.getRegisteredFontNames():
                pdfmetrics.registerFont(TTFont("ILM", regular))
            if "ILMB" not in pdfmetrics.getRegisteredFontNames():
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


def _label(label, lang):
    return AR_LABELS.get(label, label) if lang == "ar" else label


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


def _raw_stage(value, lang="en"):
    return AR_STAGE.get(str(value), str(value)) if lang == "ar" else str(value)


def _raw_next_action(current, next_action, lang="en"):
    return AR_NEXT_ACTION.get(current, next_action) if lang == "ar" else next_action


def _raw_missing(missing, lang="en"):
    if not missing:
        return "لا يوجد" if lang == "ar" else "None"
    if lang == "ar":
        return "، ".join(AR_STAGE.get(x, x) for x in missing)
    return ", ".join(missing)


def _raw_display_value(value, lang="en"):
    text = _v(value)
    return AR_VALUES.get(text, text) if lang == "ar" else text


def _build_styles(lang="en"):
    font, bold, ar_font = _register_fonts()
    right = lang == "ar"
    base = getSampleStyleSheet()
    return {
        "font": font,
        "bold": bold,
        "arabic_font": ar_font,
        "title": ParagraphStyle(
            "ILMTitle", parent=base["Title"], fontName=bold, fontSize=20, leading=25,
            textColor=colors.HexColor("#08233f"), alignment=TA_RIGHT if right else TA_LEFT, spaceAfter=8,
        ),
        "h1": ParagraphStyle(
            "ILMH1", parent=base["Heading1"], fontName=bold, fontSize=13, leading=18,
            textColor=colors.HexColor("#08233f"), alignment=TA_RIGHT if right else TA_LEFT,
            spaceBefore=8, spaceAfter=6,
        ),
        "body": ParagraphStyle(
            "ILMBody", parent=base["BodyText"], fontName=font, fontSize=8.8, leading=12,
            textColor=colors.HexColor("#263445"), alignment=TA_RIGHT if right else TA_LEFT,
        ),
        "body_bold": ParagraphStyle(
            "ILMBodyBold", parent=base["BodyText"], fontName=bold, fontSize=8.8, leading=12,
            textColor=colors.HexColor("#08233f"), alignment=TA_RIGHT if right else TA_LEFT,
        ),
        "small": ParagraphStyle(
            "ILMSmall", parent=base["BodyText"], fontName=font, fontSize=7.4, leading=10,
            textColor=colors.HexColor("#65758b"), alignment=TA_RIGHT if right else TA_LEFT,
        ),
        "metric": ParagraphStyle(
            "ILMMetric", parent=base["BodyText"], fontName=bold, fontSize=15, leading=18,
            textColor=colors.HexColor("#08233f"), alignment=TA_RIGHT if right else TA_LEFT,
        ),
    }


def _pdf_para(text, style, lang="en"):
    value = _shape_arabic_for_pdf(text) if lang == "ar" else str(text or "")
    return Paragraph(xml_escape(str(value)).replace("\n", "<br/>"), style)


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


def _kv_table(rows, styles, lang="en"):
    data = []
    for key, value in rows:
        label_p = _pdf_para(_label(key, lang), styles["body_bold"], lang)
        value_p = _pdf_para(_raw_display_value(value, lang), styles["body"], lang)
        data.append([value_p, label_p] if lang == "ar" else [label_p, value_p])
    widths = [118 * mm, 47 * mm] if lang == "ar" else [47 * mm, 118 * mm]
    label_col = 1 if lang == "ar" else 0
    table = Table(data, colWidths=widths, hAlign="RIGHT" if lang == "ar" else "LEFT")
    table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BACKGROUND", (label_col, 0), (label_col, -1), colors.HexColor("#f4f7fa")),
        ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#dce4ec")),
        ("ALIGN", (0, 0), (-1, -1), "RIGHT" if lang == "ar" else "LEFT"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    return table


def _section(story, title, rows, styles, lang="en"):
    story.append(_pdf_para(_label(title, lang), styles["h1"], lang))
    story.append(_kv_table(rows, styles, lang))
    story.append(Spacer(1, 4 * mm))


def _summary_cards(completion, current, score, open_events, styles, lang="en"):
    labels = ["Completion", "Current stage", "Health score", "Open events"]
    values = [
        f"{completion}%",
        _raw_stage(current, lang),
        f"{score}/100" if score is not None else _raw_display_value("Not available", lang),
        str(open_events),
    ]
    cells = []
    for label, value in zip(labels, values):
        cells.append([
            _pdf_para(value, styles["metric"], lang),
            _pdf_para(_label(label, lang), styles["small"], lang),
        ])
    if lang == "ar":
        cells.reverse()
    table = Table([cells], colWidths=[41.25 * mm] * 4)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#dce4ec")),
        ("INNERGRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#dce4ec")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (0, 0), (-1, -1), "RIGHT" if lang == "ar" else "LEFT"),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
        ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ]))
    return table


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
    open_events = [e for e in inst_events if str(e.get("event_status") or "").strip().lower() != "closed"]
    completion, current, missing, next_action = _stage_summary(inst)

    score = None
    try:
        score, _ = context["health_score_v2"](inst, events, components)
    except Exception:
        pass

    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4, rightMargin=14 * mm, leftMargin=14 * mm,
        topMargin=23 * mm, bottomMargin=15 * mm,
        title="Instrument Lifecycle Evidence Report", author="Yahia QC Instrument Lifecycle",
    )
    story = []
    story.append(_pdf_para(_label("Instrument Lifecycle Evidence Report", lang), styles["title"], lang))
    # Keep IDs/names as a technical LTR line even in Arabic reports.
    story.append(_pdf_para(f"{_v(inst.get('instrument_code'))} · {_v(inst.get('instrument_name'))}", styles["h1"], "en"))
    generated = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    story.append(_pdf_para(f"{_label('Generated', lang)}: {generated}", styles["small"], lang))
    story.append(_pdf_para(_label("Decision-support copy", lang), styles["small"], lang))
    story.append(Spacer(1, 4 * mm))

    story.append(_pdf_para(_label("Management summary", lang), styles["h1"], lang))
    story.append(_summary_cards(completion, current, score, len(open_events), styles, lang))
    story.append(Spacer(1, 3 * mm))

    next_display = _raw_next_action(current, next_action, lang)
    missing_display = _raw_missing(missing, lang)
    story.append(_kv_table([
        ("Next controlled action", next_display),
        ("Missing evidence", missing_display),
    ], styles, lang))
    story.append(Spacer(1, 4 * mm))

    _section(story, "Instrument identity", [
        ("Instrument ID", inst.get("instrument_code")),
        ("Instrument name", inst.get("instrument_name")),
        ("Type", inst.get("instrument_type")),
        ("Manufacturer", inst.get("manufacturer")),
        ("Model", inst.get("model")),
        ("Serial number", inst.get("serial_number")),
        ("Location", inst.get("location")),
        ("Responsible team", inst.get("responsible_team")),
        ("Operational status", inst.get("operational_status")),
    ], styles, lang)

    _section(story, "Lifecycle readiness", [
        ("Completion", f"{completion}%"),
        ("Current stage", _raw_stage(current, lang)),
        ("Next controlled action", next_display),
        ("Missing evidence", missing_display),
        ("Health score", f"{score}/100" if score is not None else "Not available"),
        ("Open events", len(open_events)),
    ], styles, lang)

    _section(story, "Acquisition & qualification", [
        ("Need identified", inst.get("need_identified_date")),
        ("URS reference", inst.get("urs_reference")),
        ("URS approval date", inst.get("urs_approval_date")),
        ("Quotation reference", inst.get("quotation_reference")),
        ("Quotation date", inst.get("quotation_date")),
        ("PR number", inst.get("pr_number")),
        ("PR approval date", inst.get("pr_approval_date")),
        ("PO number", inst.get("po_number")),
        ("PO approval / issue date", inst.get("po_approval_date")),
        ("Expected receiving date", inst.get("expected_receiving_date")),
        ("Actual receiving date", inst.get("receiving_date")),
        ("Installation date", inst.get("installation_date")),
        ("IQ completion date", inst.get("iq_date")),
        ("OQ completion date", inst.get("oq_date")),
        ("PQ completion date", inst.get("pq_date")),
        ("Release / issuance date", inst.get("issuance_date")),
        ("First approved routine run", inst.get("first_run_date")),
    ], styles, lang)

    _section(story, "Routine control", [
        ("Qualification due", inst.get("qualification_due")),
        ("PM due", inst.get("pm_due")),
        ("Calibration due", inst.get("calibration_due")),
        ("Maintenance records", len(inst_maintenance)),
        ("Calibration / qualification records", len(inst_lifecycle)),
    ], styles, lang)

    if inst_events:
        story.append(_pdf_para(_label("Events & investigation", lang), styles["h1"], lang))
        headers = ["Date", "Event", "Severity", "Status", "Observed facts"]
        values_rows = []
        for e in inst_events[:15]:
            values_rows.append([
                e.get("event_date"), e.get("event_type"), e.get("severity"), e.get("event_status"), e.get("observed_facts")
            ])
        if lang == "ar":
            headers.reverse()
            values_rows = [list(reversed(r)) for r in values_rows]
        event_data = [[_pdf_para(_label(h, lang), styles["small"], lang) for h in headers]]
        for row in values_rows:
            event_data.append([_pdf_para(_raw_display_value(v, lang), styles["small"], lang) for v in row])
        widths = [67 * mm, 24 * mm, 22 * mm, 30 * mm, 22 * mm] if lang == "ar" else [22 * mm, 30 * mm, 22 * mm, 24 * mm, 67 * mm]
        table = Table(event_data, colWidths=widths, repeatRows=1)
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#08233f")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#dce4ec")),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("ALIGN", (0, 0), (-1, -1), "RIGHT" if lang == "ar" else "LEFT"),
        ]))
        story.append(table)
        story.append(Spacer(1, 4 * mm))

    if inst_components:
        component_note = "; ".join(f"{_v(c.get('component_name'))}: {_v(c.get('status'))}" for c in inst_components[:10])
        _section(story, "Components", [("Recorded", len(inst_components)), ("Evidence note", component_note)], styles, lang)

    boundary_en = (
        "This PDF is generated from the current application dataset as decision-support evidence. "
        "It is not a validated GxP record and does not replace approved certificates, qualification protocols, "
        "deviations, CAPA, raw data, or SOP-controlled records."
    )
    boundary_ar = (
        "هذا التقرير مولّد من بيانات التطبيق الحالية كأداة لدعم القرار. لا يعد سجل GxP معتمدًا، "
        "ولا يستبدل الشهادات أو بروتوكولات التأهيل أو الانحرافات أو CAPA أو البيانات الخام "
        "أو السجلات الخاضعة لإجراءات العمل المعتمدة."
    )
    story.append(_pdf_para(_label("Evidence boundary", lang), styles["h1"], lang))
    story.append(_pdf_para(boundary_ar if lang == "ar" else boundary_en, styles["body"], lang))

    doc.build(
        story,
        onFirstPage=lambda c, d: _page_header(c, d, styles),
        onLaterPages=lambda c, d: _page_header(c, d, styles),
    )
    return buf.getvalue(), styles["arabic_font"]


def _portfolio_pdf(instruments, context, report_lang="en"):
    styles = _build_styles(report_lang)
    lang = report_lang
    events = context.get("events") or []
    components = context.get("components") or []
    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=landscape(A4), rightMargin=12 * mm, leftMargin=12 * mm,
        topMargin=23 * mm, bottomMargin=14 * mm,
        title="Portfolio Management Snapshot", author="Yahia QC Instrument Lifecycle",
    )
    story = [_pdf_para(_label("Portfolio Management Snapshot", lang), styles["title"], lang)]
    generated = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    story.append(_pdf_para(f"{_label('Generated', lang)}: {generated}", styles["small"], lang))
    story.append(Spacer(1, 4 * mm))

    headers = ["Instrument ID", "Instrument name", "Operational status", "Current stage", "Completion", "Health score", "Open events", "Calibration due", "PM due"]
    if lang == "ar":
        headers.reverse()
    data = [[_pdf_para(_label(h, lang), styles["small"], lang) for h in headers]]

    for inst in instruments:
        completion, current, _, _ = _stage_summary(inst)
        iid = str(inst.get("id") or "")
        open_events = sum(
            1 for e in events
            if str(e.get("instrument_id")) == iid and str(e.get("event_status") or "").strip().lower() != "closed"
        )
        try:
            score, _ = context["health_score_v2"](inst, events, components)
        except Exception:
            score = "—"
        values = [
            inst.get("instrument_code"), inst.get("instrument_name"), inst.get("operational_status"),
            _raw_stage(current, lang), f"{completion}%", score, open_events,
            inst.get("calibration_due"), inst.get("pm_due"),
        ]
        if lang == "ar":
            values.reverse()
        data.append([_pdf_para(_raw_display_value(v, lang), styles["small"], lang) for v in values])

    widths = [27 * mm, 27 * mm, 20 * mm, 21 * mm, 21 * mm, 30 * mm, 30 * mm, 42 * mm, 24 * mm] if lang == "ar" else [24 * mm, 42 * mm, 30 * mm, 30 * mm, 21 * mm, 21 * mm, 20 * mm, 27 * mm, 27 * mm]
    table = Table(data, colWidths=widths, repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#08233f")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#dce4ec")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f7f9fb")]),
        ("ALIGN", (0, 0), (-1, -1), "RIGHT" if lang == "ar" else "LEFT"),
    ]))
    story.append(table)
    story.append(Spacer(1, 4 * mm))
    boundary = (
        "Decision-support portfolio snapshot. Official GMP records remain in approved company systems."
        if lang == "en"
        else "ملخص لدعم القرار فقط. تظل السجلات الرسمية الخاصة بـ GMP داخل الأنظمة المعتمدة بالشركة."
    )
    story.append(_pdf_para(boundary, styles["small"], lang))
    doc.build(
        story,
        onFirstPage=lambda c, d: _page_header(c, d, styles),
        onLaterPages=lambda c, d: _page_header(c, d, styles),
    )
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
    intro = (
        "حوّل بيانات الجهاز الحالية إلى تقرير Evidence-first منظم للمراجعة والمتابعة الإدارية، مع بقاء السجلات الرسمية داخل الأنظمة المعتمدة."
        if ui_lang == "ar"
        else "Turn the current instrument dataset into an evidence-first review or management PDF while keeping official GMP records in approved systems."
    )

    with st.expander(title, expanded=False):
        st.markdown(f"**{intro}**")
        st.caption("Generated on demand · No PDF is stored automatically · Decision-support / uncontrolled copy")
        instruments, err, ok = _load_full_instruments(context)
        if not ok:
            st.error("تعذر تحميل بيانات دورة الحياة الكاملة للتقرير." if ui_lang == "ar" else "Could not load the full lifecycle dataset for reporting.")
            if err:
                st.caption(f"Diagnostic: {err}")
            return
        if not instruments:
            st.info("أنشئ Passport لجهاز أولًا ثم ارجع إلى مركز التقارير." if ui_lang == "ar" else "Create an Instrument Passport first, then return here to generate reports.")
            return

        c1, c2 = st.columns(2)
        report_kind = c1.selectbox(
            "نوع التقرير | Report type" if ui_lang == "ar" else "Report type",
            ["Instrument Lifecycle Evidence Report", "Portfolio Management Snapshot"],
            key="ilm_pdf_report_kind",
        )
        report_lang_label = c2.selectbox(
            "لغة التقرير | Report language" if ui_lang == "ar" else "Report language",
            ["English", "العربية"],
            index=1 if ui_lang == "ar" else 0,
            key="ilm_pdf_report_language",
        )
        report_lang = "ar" if report_lang_label == "العربية" else "en"

        selected = None
        if report_kind.startswith("Instrument"):
            options = {
                f"{i.get('instrument_code')} · {i.get('instrument_name') or 'Unnamed'}": i
                for i in instruments
            }
            label = st.selectbox(
                "الجهاز | Instrument" if ui_lang == "ar" else "Instrument",
                list(options.keys()),
                key="ilm_pdf_instrument",
            )
            selected = options[label]
            completion, current, missing, next_action = _stage_summary(selected)
            iid = str(selected.get("id") or "")
            open_evt = sum(
                1 for e in (context.get("events") or [])
                if str(e.get("instrument_id")) == iid and str(e.get("event_status") or "").strip().lower() != "closed"
            )

            # Browser Arabic must stay logical Unicode. Do NOT use ReportLab shaping here.
            a, b, c = st.columns(3)
            a.metric("اكتمال دورة الحياة" if ui_lang == "ar" else "Lifecycle", f"{completion}%")
            b.metric("الأدلة الناقصة" if ui_lang == "ar" else "Missing evidence", len(missing))
            c.metric("الأحداث المفتوحة" if ui_lang == "ar" else "Open events", open_evt)
            stage_ui = _raw_stage(current, ui_lang)
            next_ui = _raw_next_action(current, next_action, ui_lang)
            if ui_lang == "ar":
                st.markdown(
                    f"<div dir='rtl' style='text-align:right;padding:.75rem 1rem;border:1px solid rgba(128,128,128,.25);border-radius:12px;margin:.25rem 0 .65rem;'>"
                    f"<strong>المرحلة الحالية:</strong> {stage_ui}</div>",
                    unsafe_allow_html=True,
                )
                st.info("الخطوة التالية المنضبطة: " + next_ui)
            else:
                st.markdown(f"**Current stage:** {stage_ui}")
                st.info("Next controlled action: " + next_ui)
        else:
            st.info(
                f"سيتم إنشاء ملخص إداري لـ {len(instruments)} جهاز/أجهزة."
                if ui_lang == "ar"
                else f"A management snapshot will be generated for {len(instruments)} instrument(s)."
            )

        if st.button(
            "⚡ إنشاء التقرير | Generate PDF" if ui_lang == "ar" else "⚡ Generate PDF",
            use_container_width=True,
            key="ilm_generate_pdf",
        ):
            with st.spinner("Generating evidence-first PDF…"):
                if report_kind.startswith("Instrument"):
                    pdf_bytes, ar_font = _instrument_pdf(selected, context, report_lang)
                    safe_code = str(selected.get("instrument_code") or "instrument").replace("/", "-")
                    filename = f"{safe_code}_Lifecycle_Evidence_Report.pdf"
                else:
                    pdf_bytes, ar_font = _portfolio_pdf(instruments, context, report_lang)
                    filename = "Instrument_Lifecycle_Portfolio_Snapshot.pdf"
                st.session_state["ilm_last_pdf"] = pdf_bytes
                st.session_state["ilm_last_pdf_name"] = filename
                st.session_state["ilm_last_pdf_ar_font"] = ar_font

            if report_lang == "ar" and not ar_font:
                st.warning("لم يتم العثور على خط عربي مضمّن على الخادم. لا تستخدم التقرير العربي قبل مراجعة شكل الحروف.")
            elif report_lang == "ar" and (arabic_reshaper is None or bidi_get_display is None):
                st.warning("Arabic shaping dependency is missing. Rebuild the app before using Arabic PDF output.")
            else:
                st.success("PDF ready · التقرير جاهز.")

        pdf_bytes = st.session_state.get("ilm_last_pdf")
        if pdf_bytes:
            st.download_button(
                "⬇️ تنزيل التقرير | Download PDF" if ui_lang == "ar" else "⬇️ Download PDF",
                data=pdf_bytes,
                file_name=st.session_state.get("ilm_last_pdf_name") or "Instrument_Lifecycle_Report.pdf",
                mime="application/pdf",
                use_container_width=True,
                key="ilm_download_pdf",
            )
            st.caption("Recorded evidence stays recorded; missing evidence stays visible. The PDF does not silently complete missing lifecycle gates.")
