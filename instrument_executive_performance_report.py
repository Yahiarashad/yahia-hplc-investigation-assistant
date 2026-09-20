# Executive Performance Intelligence Report
# Executed inside the authenticated Yahia QC Instrument Lifecycle app context.

from __future__ import annotations

from datetime import date, datetime, timezone
from io import BytesIO
from pathlib import Path
from xml.sax.saxutils import escape as xml_escape

import pandas as pd
import streamlit as st

try:
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import mm
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.platypus import KeepTogether, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
except Exception:
    colors = None

try:
    import arabic_reshaper
    from bidi.algorithm import get_display as bidi_get_display
except Exception:
    arabic_reshaper = None
    bidi_get_display = None


EXEC_INSTRUMENT_SELECT = (
    "id,instrument_code,instrument_name,instrument_type,operational_status,"
    "target_availability_pct,target_utilization_pct,performance_target_note,"
    "qualification_due,pm_due,calibration_due,created_at"
)
EXEC_PERF_SELECT = (
    "id,instrument_id,month_start,scheduled_hours,planned_downtime_hours,"
    "unplanned_downtime_hours,productive_run_hours,notes,created_at,updated_at"
)


EXEC_AR = {
    "Executive Performance Intelligence": "ذكاء الأداء التنفيذي",
    "Monthly management report": "تقرير الإدارة الشهري",
    "Report month": "شهر التقرير",
    "Generated": "تاريخ الإنشاء",
    "Portfolio overview": "نظرة عامة على المحفظة",
    "Monthly Availability": "الإتاحة الشهرية",
    "Monthly Utilization": "نسبة الاستخدام الشهرية",
    "Data coverage": "اكتمال بيانات الشهر",
    "Unplanned downtime": "التوقف غير المخطط",
    "Productive run hours": "ساعات التشغيل الإنتاجي",
    "Planned downtime": "التوقف المخطط",
    "Capacity risk": "مخاطر السعة",
    "Below Availability target": "أقل من هدف الإتاحة",
    "Below Utilization target": "أقل من هدف الاستخدام",
    "Open events": "الأحداث المفتوحة",
    "Open calibration OOC": "حالات OOC للمعايرة المفتوحة",
    "Management attention": "أولويات الإدارة",
    "Top Availability losses": "أعلى خسائر الإتاحة",
    "Highest unplanned downtime": "أعلى توقف غير مخطط",
    "Highest productive load": "أعلى حمل تشغيل إنتاجي",
    "Available spare capacity": "أعلى سعة متاحة غير مستغلة",
    "Instrument": "الجهاز",
    "Type": "النوع",
    "Availability %": "الإتاحة %",
    "Availability target %": "هدف الإتاحة %",
    "Availability gap pp": "فارق الإتاحة نقطة مئوية",
    "Utilization %": "الاستخدام %",
    "Utilization target %": "هدف الاستخدام %",
    "Utilization gap pp": "فارق الاستخدام نقطة مئوية",
    "Planned operating h": "ساعات التشغيل المخططة",
    "Unplanned downtime h": "التوقف غير المخطط ساعة",
    "Productive h": "الساعات الإنتاجية",
    "Idle available h": "الساعات المتاحة غير المستغلة",
    "Management signal": "إشارة الإدارة",
    "Management action": "إجراء إداري مقترح",
    "On target": "ضمن الهدف",
    "Capacity risk": "مخاطر سعة",
    "Capacity available": "سعة متاحة",
    "Reliability + demand review": "مراجعة الاعتمادية والطلب",
    "Availability below target": "الإتاحة أقل من الهدف",
    "Utilization below target": "الاستخدام أقل من الهدف",
    "Target met": "الهدف محقق",
    "No target": "لا يوجد هدف محدد",
    "Insufficient data": "بيانات غير كافية",
    "No monthly record": "لا يوجد سجل شهري",
    "Six-month portfolio trend": "اتجاه المحفظة لستة أشهر",
    "Month": "الشهر",
    "Coverage": "التغطية",
    "Evidence boundary": "حدود استخدام الدليل",
    "Methodology": "طريقة الحساب",
}


def _exec_ar_text(value: str) -> str:
    text = str(value or "")
    if not text or arabic_reshaper is None or bidi_get_display is None:
        return text
    try:
        return bidi_get_display(arabic_reshaper.reshape(text))
    except Exception:
        return text


def _exec_font_paths():
    candidates = [
        ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
        ("/usr/share/fonts/truetype/freefont/FreeSans.ttf", "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf"),
    ]
    for regular, bold in candidates:
        if Path(regular).exists() and Path(bold).exists():
            return regular, bold
    return None, None


def _exec_fonts():
    regular, bold = _exec_font_paths()
    if regular and bold:
        try:
            pdfmetrics.registerFont(TTFont("EXECREG", regular))
            pdfmetrics.registerFont(TTFont("EXECBOLD", bold))
            return "EXECREG", "EXECBOLD"
        except Exception:
            pass
    return "Helvetica", "Helvetica-Bold"


def _exec_styles(lang="en"):
    regular, bold = _exec_fonts()
    base = getSampleStyleSheet()
    rtl = lang == "ar"
    align = TA_RIGHT if rtl else TA_LEFT
    return {
        "regular": regular,
        "bold": bold,
        "title": ParagraphStyle("ExecTitle", parent=base["Title"], fontName=bold, fontSize=20, leading=24, textColor=colors.HexColor("#08233f"), alignment=align, spaceAfter=7),
        "h1": ParagraphStyle("ExecH1", parent=base["Heading1"], fontName=bold, fontSize=13, leading=17, textColor=colors.HexColor("#08233f"), alignment=align, spaceBefore=6, spaceAfter=5),
        "body": ParagraphStyle("ExecBody", parent=base["BodyText"], fontName=regular, fontSize=8.2, leading=11, textColor=colors.HexColor("#263445"), alignment=align),
        "small": ParagraphStyle("ExecSmall", parent=base["BodyText"], fontName=regular, fontSize=7.2, leading=9.2, textColor=colors.HexColor("#64748b"), alignment=align),
        "center": ParagraphStyle("ExecCenter", parent=base["BodyText"], fontName=bold, fontSize=9, leading=11, textColor=colors.HexColor("#0f2742"), alignment=TA_CENTER),
    }


def _exec_label(text, lang):
    return EXEC_AR.get(text, text) if lang == "ar" else text


def _exec_p(text, style, lang="en"):
    value = str(text or "")
    if lang == "ar":
        value = _exec_ar_text(value)
    return Paragraph(xml_escape(value).replace("\n", "<br/>"), style)


def _exec_month(value):
    try:
        return pd.to_datetime(value).date().replace(day=1)
    except Exception:
        return date.today().replace(day=1)


def _exec_target(value):
    try:
        if value is None or str(value).strip() == "":
            return None
        val = float(value)
        return val if 0 <= val <= 100 else None
    except Exception:
        return None


def _exec_calc(row):
    scheduled = float(row.get("scheduled_hours") or 0)
    planned = float(row.get("planned_downtime_hours") or 0)
    unplanned = float(row.get("unplanned_downtime_hours") or 0)
    productive = float(row.get("productive_run_hours") or 0)
    planned_operating = max(0.0, scheduled - planned)
    available = max(0.0, planned_operating - unplanned)
    availability = available / planned_operating * 100 if planned_operating > 0 else None
    utilization = productive / available * 100 if available > 0 else None
    idle_available = max(0.0, available - productive)
    return {
        "scheduled": scheduled,
        "planned": planned,
        "unplanned": unplanned,
        "productive": productive,
        "planned_operating": planned_operating,
        "available": available,
        "availability": availability,
        "utilization": utilization,
        "idle_available": idle_available,
    }


def _exec_signal(availability, utilization, ta, tu):
    ta = _exec_target(ta)
    tu = _exec_target(tu)
    if ta is None and tu is None:
        return "No target", "Set instrument-specific management targets before interpreting target gaps.", 4
    a_ok = None if availability is None or ta is None else availability >= ta
    u_ok = None if utilization is None or tu is None else utilization >= tu
    if a_ok is False and u_ok is True:
        return "Capacity risk", "Review unplanned downtime, reliability and workload concentration. If persistent, assess backup / replacement capacity.", 1
    if a_ok is False and u_ok is False:
        return "Reliability + demand review", "Availability and utilization are both below target. Review reliability, scheduling and demand before capacity decisions.", 2
    if a_ok is True and u_ok is False:
        return "Capacity available", "Instrument is available but underused versus target. Review scheduling, method allocation and real demand.", 3
    if a_ok is True and u_ok is True:
        return "On target", "Maintain current controls and trend performance month to month.", 5
    if a_ok is False:
        return "Availability below target", "Review unplanned downtime and reliability drivers.", 2
    if u_ok is False:
        return "Utilization below target", "Review scheduling, demand and capacity allocation.", 3
    if a_ok is True or u_ok is True:
        return "Target met", "Configured target is met for the available metric.", 5
    return "Insufficient data", "Complete monthly hours before interpreting performance.", 4


def _exec_dataset(instruments, perf_rows, month_start):
    inst_by_id = {str(i.get("id")): i for i in instruments}
    month_rows = [r for r in perf_rows if _exec_month(r.get("month_start")) == month_start]
    row_by_instrument = {str(r.get("instrument_id")): r for r in month_rows}
    out = []
    for inst in instruments:
        iid = str(inst.get("id"))
        row = row_by_instrument.get(iid)
        if not row:
            out.append({
                "iid": iid,
                "code": inst.get("instrument_code") or iid,
                "name": inst.get("instrument_name") or "",
                "type": inst.get("instrument_type") or "",
                "status": inst.get("operational_status") or "",
                "recorded": False,
                "ta": _exec_target(inst.get("target_availability_pct")),
                "tu": _exec_target(inst.get("target_utilization_pct")),
                "signal": "No monthly record",
                "action": "Record the selected month's scheduled, downtime and productive hours.",
                "rank": 0,
            })
            continue
        m = _exec_calc(row)
        ta = _exec_target(inst.get("target_availability_pct"))
        tu = _exec_target(inst.get("target_utilization_pct"))
        signal, action, rank = _exec_signal(m["availability"], m["utilization"], ta, tu)
        out.append({
            "iid": iid,
            "code": inst.get("instrument_code") or iid,
            "name": inst.get("instrument_name") or "",
            "type": inst.get("instrument_type") or "",
            "status": inst.get("operational_status") or "",
            "recorded": True,
            "ta": ta,
            "tu": tu,
            "availability": m["availability"],
            "utilization": m["utilization"],
            "availability_gap": (m["availability"] - ta) if m["availability"] is not None and ta is not None else None,
            "utilization_gap": (m["utilization"] - tu) if m["utilization"] is not None and tu is not None else None,
            "planned_operating": m["planned_operating"],
            "planned": m["planned"],
            "unplanned": m["unplanned"],
            "productive": m["productive"],
            "idle": m["idle_available"],
            "signal": signal,
            "action": action,
            "rank": rank,
            "notes": row.get("notes") or "",
        })
    return out


def _exec_portfolio(rows):
    recorded = [r for r in rows if r.get("recorded")]
    planned_operating = sum(float(r.get("planned_operating") or 0) for r in recorded)
    available = sum(max(0.0, float(r.get("planned_operating") or 0) - float(r.get("unplanned") or 0)) for r in recorded)
    productive = sum(float(r.get("productive") or 0) for r in recorded)
    availability = available / planned_operating * 100 if planned_operating > 0 else None
    utilization = productive / available * 100 if available > 0 else None
    return {
        "recorded": recorded,
        "coverage": len(recorded),
        "availability": availability,
        "utilization": utilization,
        "planned": sum(float(r.get("planned") or 0) for r in recorded),
        "unplanned": sum(float(r.get("unplanned") or 0) for r in recorded),
        "productive": productive,
        "idle": sum(float(r.get("idle") or 0) for r in recorded),
        "capacity_risk": sum(1 for r in recorded if r.get("signal") == "Capacity risk"),
        "below_avail": sum(1 for r in recorded if r.get("ta") is not None and r.get("availability") is not None and r.get("availability") < r.get("ta")),
        "below_util": sum(1 for r in recorded if r.get("tu") is not None and r.get("utilization") is not None and r.get("utilization") < r.get("tu")),
    }


def _exec_pct(value):
    return "—" if value is None else f"{float(value):.1f}%"


def _exec_num(value):
    try:
        return f"{float(value):.1f}"
    except Exception:
        return "—"


def _exec_gap(value):
    return "—" if value is None else f"{float(value):+.1f} pp"


def _exec_header(canvas, doc, styles, report_month, lang):
    canvas.saveState()
    w, h = doc.pagesize
    canvas.setFillColor(colors.HexColor("#07111f"))
    canvas.rect(0, h - 18 * mm, w, 18 * mm, fill=1, stroke=0)
    canvas.setFillColor(colors.HexColor("#d6b85f"))
    canvas.setFont(styles["bold"], 8)
    canvas.drawString(12 * mm, h - 11 * mm, "YAHIA QC · EXECUTIVE PERFORMANCE INTELLIGENCE")
    canvas.setFillColor(colors.HexColor("#7b8794"))
    canvas.setFont(styles["regular"], 7)
    canvas.drawRightString(w - 12 * mm, 7 * mm, f"{report_month:%Y-%m} · Page {doc.page}")
    canvas.restoreState()


def _exec_metric_table(items, styles, lang):
    cells = []
    for label, value, note in items:
        txt = f"<b>{xml_escape(str(value))}</b><br/><font size='7'>{xml_escape(_exec_label(label, lang))}</font><br/><font size='6' color='#77889a'>{xml_escape(str(note))}</font>"
        if lang == "ar":
            txt = f"<b>{xml_escape(str(value))}</b><br/><font size='7'>{xml_escape(_exec_ar_text(_exec_label(label, lang)))}</font><br/><font size='6' color='#77889a'>{xml_escape(_exec_ar_text(str(note)))}</font>"
        cells.append(Paragraph(txt, styles["center"]))
    table = Table([cells], colWidths=[63 * mm] * len(cells), rowHeights=[26 * mm])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f7fafc")),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#d9e3ec")),
        ("INNERGRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#d9e3ec")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
    ]))
    return table


def _exec_simple_table(headers, rows, styles, lang, widths=None):
    def cell(value, bold=False):
        style = styles["body"]
        text = str(value if value is not None else "—")
        if lang == "ar":
            text = _exec_ar_text(text)
        if bold:
            text = f"<b>{xml_escape(text)}</b>"
            return Paragraph(text, style)
        return Paragraph(xml_escape(text), style)

    hdrs = [_exec_label(h, lang) for h in headers]
    if lang == "ar":
        hdrs = [_exec_ar_text(h) for h in hdrs]
    data = [[Paragraph(f"<b>{xml_escape(str(h))}</b>", styles["small"]) for h in hdrs]]
    for row in rows:
        data.append([cell(v) for v in row])
    if widths is None:
        total = 270 * mm
        widths = [total / max(1, len(headers))] * len(headers)
    table = Table(data, colWidths=widths, repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0b2a46")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#dbe3ec")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
        ("LEFTPADDING", (0, 0), (-1, -1), 4), ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    return table


def _exec_trend(perf_rows, instruments, selected_month):
    inst_ids = {str(i.get("id")) for i in instruments}
    months = sorted({_exec_month(r.get("month_start")) for r in perf_rows if str(r.get("instrument_id")) in inst_ids and _exec_month(r.get("month_start")) <= selected_month})[-6:]
    output = []
    for month in months:
        rows = [r for r in perf_rows if str(r.get("instrument_id")) in inst_ids and _exec_month(r.get("month_start")) == month]
        planned = available = productive = 0.0
        covered = set()
        for r in rows:
            m = _exec_calc(r)
            planned += m["planned_operating"]
            available += m["available"]
            productive += m["productive"]
            covered.add(str(r.get("instrument_id")))
        av = available / planned * 100 if planned > 0 else None
        ut = productive / available * 100 if available > 0 else None
        output.append((month, len(covered), av, ut, sum(float(r.get("unplanned_downtime_hours") or 0) for r in rows)))
    return output


def _build_exec_pdf(instruments, perf_rows, events, calibrations, selected_month, lang="en"):
    if colors is None:
        raise RuntimeError("reportlab is not available")
    styles = _exec_styles(lang)
    rows = _exec_dataset(instruments, perf_rows, selected_month)
    p = _exec_portfolio(rows)
    missing = [r for r in rows if not r.get("recorded")]
    open_events = [e for e in events if str(e.get("event_status") or "") != "Closed"]
    open_ooc = [c for c in calibrations if str(c.get("result") or "").upper() == "OOC" and str(c.get("ooc_status") or "Open") not in {"Closed", "Resolved", "Not applicable"}]

    ranked = sorted([r for r in p["recorded"] if r.get("rank") <= 3], key=lambda x: (x.get("rank", 9), -(x.get("unplanned") or 0), x.get("code", "")))
    top_loss = sorted(p["recorded"], key=lambda r: (r.get("availability") if r.get("availability") is not None else 999))[:5]
    top_unplanned = sorted(p["recorded"], key=lambda r: r.get("unplanned") or 0, reverse=True)[:5]
    top_load = sorted(p["recorded"], key=lambda r: r.get("productive") or 0, reverse=True)[:5]
    top_idle = sorted(p["recorded"], key=lambda r: r.get("idle") or 0, reverse=True)[:5]

    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=landscape(A4), leftMargin=12*mm, rightMargin=12*mm, topMargin=23*mm, bottomMargin=13*mm, title="Executive Performance Intelligence", author="Yahia QC Instrument Lifecycle")
    story = []
    story.append(_exec_p(_exec_label("Executive Performance Intelligence", lang), styles["title"], lang))
    story.append(_exec_p(_exec_label("Monthly management report", lang), styles["h1"], lang))
    meta = f"{_exec_label('Report month', lang)}: {selected_month:%Y-%m}   ·   {_exec_label('Generated', lang)}: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}"
    story.append(_exec_p(meta, styles["small"], lang))
    story.append(Spacer(1, 4*mm))

    story.append(_exec_metric_table([
        ("Monthly Availability", _exec_pct(p["availability"]), "weighted by planned operating hours" if lang == "en" else "مرجحة بساعات التشغيل المخططة"),
        ("Monthly Utilization", _exec_pct(p["utilization"]), "weighted by available hours" if lang == "en" else "مرجحة بالساعات المتاحة"),
        ("Data coverage", f"{p['coverage']}/{len(instruments)}", "instruments with a monthly record" if lang == "en" else "أجهزة لديها سجل شهري"),
        ("Unplanned downtime", f"{p['unplanned']:.1f} h", "portfolio loss hours" if lang == "en" else "ساعات فقد على مستوى المحفظة"),
    ], styles, lang))
    story.append(Spacer(1, 5*mm))

    story.append(_exec_p(_exec_label("Management attention", lang), styles["h1"], lang))
    attention_rows = []
    for r in ranked[:10]:
        attention_rows.append([
            r.get("code"), r.get("type"), _exec_pct(r.get("availability")), _exec_pct(r.get("utilization")),
            _exec_label(r.get("signal"), lang), r.get("action"),
        ])
    if not attention_rows:
        attention_rows = [["—", "—", "—", "—", _exec_label("On target", lang), "No current target-based management signal detected." if lang == "en" else "لا توجد إشارة حالية تتطلب تصعيدًا إداريًا حسب الأهداف المسجلة."]]
    story.append(_exec_simple_table(
        ["Instrument", "Type", "Availability %", "Utilization %", "Management signal", "Management action"],
        attention_rows, styles, lang,
        widths=[28*mm, 22*mm, 26*mm, 26*mm, 40*mm, 128*mm],
    ))
    story.append(Spacer(1, 5*mm))

    story.append(_exec_p(_exec_label("Portfolio overview", lang), styles["h1"], lang))
    story.append(_exec_simple_table(
        ["Capacity risk", "Below Availability target", "Below Utilization target", "Open events", "Open calibration OOC", "Productive run hours", "Planned downtime"],
        [[p["capacity_risk"], p["below_avail"], p["below_util"], len(open_events), len(open_ooc), f"{p['productive']:.1f} h", f"{p['planned']:.1f} h"]],
        styles, lang,
    ))
    if missing:
        story.append(Spacer(1, 3*mm))
        story.append(_exec_p((f"Data completeness: {len(missing)} instrument(s) have no monthly performance record for {selected_month:%Y-%m}." if lang == "en" else f"اكتمال البيانات: عدد {len(missing)} جهاز بدون سجل أداء شهري لشهر {selected_month:%Y-%m}."), styles["small"], lang))

    story.append(PageBreak())
    story.append(_exec_p(_exec_label("Top Availability losses", lang), styles["title"], lang))
    story.append(_exec_simple_table(
        ["Instrument", "Type", "Availability %", "Availability target %", "Availability gap pp", "Unplanned downtime h", "Management signal"],
        [[r.get("code"), r.get("type"), _exec_pct(r.get("availability")), _exec_pct(r.get("ta")), _exec_gap(r.get("availability_gap")), _exec_num(r.get("unplanned")), _exec_label(r.get("signal"), lang)] for r in top_loss],
        styles, lang,
    ))
    story.append(Spacer(1, 5*mm))

    pair = []
    pair.append(KeepTogether([
        _exec_p(_exec_label("Highest unplanned downtime", lang), styles["h1"], lang),
        _exec_simple_table(["Instrument", "Unplanned downtime h", "Availability %", "Management signal"], [[r.get("code"), _exec_num(r.get("unplanned")), _exec_pct(r.get("availability")), _exec_label(r.get("signal"), lang)] for r in top_unplanned], styles, lang, widths=[45*mm, 45*mm, 38*mm, 68*mm]),
    ]))
    pair.append(KeepTogether([
        _exec_p(_exec_label("Highest productive load", lang), styles["h1"], lang),
        _exec_simple_table(["Instrument", "Productive h", "Utilization %", "Management signal"], [[r.get("code"), _exec_num(r.get("productive")), _exec_pct(r.get("utilization")), _exec_label(r.get("signal"), lang)] for r in top_load], styles, lang, widths=[45*mm, 45*mm, 38*mm, 68*mm]),
    ]))
    story.extend(pair)
    story.append(Spacer(1, 5*mm))
    story.append(_exec_p(_exec_label("Available spare capacity", lang), styles["h1"], lang))
    story.append(_exec_simple_table(["Instrument", "Idle available h", "Availability %", "Utilization %", "Management signal"], [[r.get("code"), _exec_num(r.get("idle")), _exec_pct(r.get("availability")), _exec_pct(r.get("utilization")), _exec_label(r.get("signal"), lang)] for r in top_idle], styles, lang))

    story.append(PageBreak())
    story.append(_exec_p(_exec_label("Six-month portfolio trend", lang), styles["title"], lang))
    trend = _exec_trend(perf_rows, instruments, selected_month)
    trend_rows = [[m.strftime("%Y-%m"), f"{coverage}/{len(instruments)}", _exec_pct(av), _exec_pct(ut), f"{unp:.1f} h"] for m, coverage, av, ut, unp in trend]
    story.append(_exec_simple_table(["Month", "Coverage", "Availability %", "Utilization %", "Unplanned downtime"], trend_rows or [[selected_month.strftime("%Y-%m"), "0", "—", "—", "—"]], styles, lang))
    story.append(Spacer(1, 5*mm))

    story.append(_exec_p(_exec_label("Portfolio overview", lang), styles["h1"], lang))
    portfolio_rows = []
    for r in sorted(rows, key=lambda x: (0 if x.get("recorded") else 1, x.get("rank", 9), x.get("code", ""))):
        portfolio_rows.append([
            r.get("code"), r.get("type"), _exec_pct(r.get("availability")), _exec_pct(r.get("ta")), _exec_gap(r.get("availability_gap")),
            _exec_pct(r.get("utilization")), _exec_pct(r.get("tu")), _exec_gap(r.get("utilization_gap")), _exec_label(r.get("signal"), lang),
        ])
    story.append(_exec_simple_table(
        ["Instrument", "Type", "Availability %", "Availability target %", "Availability gap pp", "Utilization %", "Utilization target %", "Utilization gap pp", "Management signal"],
        portfolio_rows, styles, lang,
        widths=[25*mm, 19*mm, 25*mm, 25*mm, 26*mm, 25*mm, 25*mm, 26*mm, 54*mm],
    ))

    story.append(PageBreak())
    story.append(_exec_p(_exec_label("Methodology", lang), styles["title"], lang))
    methodology_en = (
        "Planned Operating Time = Scheduled Service Hours − Planned Downtime.\n"
        "Available Time = Planned Operating Time − Unplanned Downtime.\n"
        "Availability % = Available Time ÷ Planned Operating Time × 100.\n"
        "Utilization % = Productive Run Hours ÷ Available Time × 100.\n"
        "Portfolio percentages are weighted by hours; the report does not average instrument percentages equally."
    )
    methodology_ar = (
        "وقت التشغيل المخطط = ساعات الخدمة المجدولة − التوقف المخطط.\n"
        "الوقت المتاح = وقت التشغيل المخطط − التوقف غير المخطط.\n"
        "الإتاحة % = الوقت المتاح ÷ وقت التشغيل المخطط × 100.\n"
        "الاستخدام % = ساعات التشغيل الإنتاجي ÷ الوقت المتاح × 100.\n"
        "نسب المحفظة محسوبة بطريقة مرجحة بالساعات، ولا يتم أخذ متوسط بسيط لنسب الأجهزة."
    )
    story.append(_exec_p(methodology_ar if lang == "ar" else methodology_en, styles["body"], lang))
    story.append(Spacer(1, 6*mm))
    story.append(_exec_p(_exec_label("Evidence boundary", lang), styles["h1"], lang))
    boundary_en = (
        "This report is decision-support intelligence, not a validated GxP record, release decision, root-cause conclusion or universal KPI specification. "
        "Targets are user-defined laboratory / management targets. A management signal identifies where evidence deserves attention; it does not prove why performance changed. "
        "Confirm decisions against approved SOPs, qualification/calibration status, raw evidence, QA requirements and the official system of record."
    )
    boundary_ar = (
        "هذا التقرير أداة لدعم القرار وليس سجلًا GxP معتمدًا، ولا قرار إفراج، ولا إثباتًا للسبب الجذري، ولا يفرض أهداف KPI عامة. "
        "الأهداف يحددها المعمل أو الإدارة. إشارة الإدارة تحدد أين يجب توجيه الانتباه إلى الأدلة لكنها لا تثبت سبب تغير الأداء. "
        "يجب تأكيد القرارات بالرجوع إلى الإجراءات المعتمدة وحالة التأهيل والمعايرة والبيانات الخام ومتطلبات الجودة والسجل الرسمي المعتمد."
    )
    story.append(_exec_p(boundary_ar if lang == "ar" else boundary_en, styles["body"], lang))

    doc.build(story, onFirstPage=lambda c, d: _exec_header(c, d, styles, selected_month, lang), onLaterPages=lambda c, d: _exec_header(c, d, styles, selected_month, lang))
    buf.seek(0)
    return buf.getvalue()


def render_executive_performance_report():
    st.divider()
    st.markdown("## 🔥 Executive Performance Intelligence")
    st.caption("Turn monthly instrument hours into management priorities, capacity signals and a decision-ready PDF.")

    instruments, inst_err, inst_ok = _db_list("instruments", EXEC_INSTRUMENT_SELECT, "instrument_code.asc")
    perf_rows, perf_err, perf_ok = _db_list("instrument_monthly_performance", EXEC_PERF_SELECT, "month_start.desc")
    events_exec, _, events_ok = _db_list("instrument_events", "id,instrument_id,event_status,severity,event_type,event_date", "event_date.desc")
    calibrations_exec, _, cal_ok = _db_list("calibration_records", "id,instrument_id,result,ooc_status,calibration_date", "calibration_date.desc")

    if not inst_ok or not perf_ok:
        st.warning("Executive Performance Intelligence needs the instrument and monthly-performance tables to be available.")
        st.caption(inst_err or perf_err or "Database access error")
        return
    if not instruments:
        st.info("Create or import Instrument Passports first.")
        return

    available_months = sorted({_exec_month(r.get("month_start")) for r in perf_rows}, reverse=True)
    default_month = available_months[0] if available_months else date.today().replace(day=1)
    chosen = st.date_input("Executive report month", value=default_month, key="exec_report_month")
    selected_month = _exec_month(chosen)

    rows = _exec_dataset(instruments, perf_rows, selected_month)
    p = _exec_portfolio(rows)
    missing = [r for r in rows if not r.get("recorded")]
    open_events = [e for e in events_exec if str(e.get("event_status") or "") != "Closed"] if events_ok else []
    open_ooc = [c for c in calibrations_exec if str(c.get("result") or "").upper() == "OOC" and str(c.get("ooc_status") or "Open") not in {"Closed", "Resolved", "Not applicable"}] if cal_ok else []

    if p["coverage"] == 0:
        st.info(f"No monthly performance records are available for {selected_month:%Y-%m}. Record or import monthly hours first; the report will not invent performance data.")
        return

    st.markdown(
        """
<style>
.exec-hero{border:1px solid #193b50;border-radius:20px;padding:1rem 1.05rem;background:linear-gradient(135deg,#071422,#0d2234);color:#dbeaf1;margin:.45rem 0 1rem}.exec-hero b{color:#fff}.exec-hero .gold{color:#e1c56d;font-weight:800}.exec-card-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:.6rem;margin:.6rem 0 1rem}.exec-card{border:1px solid #dce4ec;border-radius:16px;padding:.78rem;background:#fff}.exec-card span{display:block;color:#64748b;font-size:.74rem}.exec-card b{display:block;color:#0f2742;font-size:1.45rem;margin:.12rem 0}.exec-card.red{border-top:3px solid #d64545}.exec-card.gold{border-top:3px solid #d4a92e}.exec-card.green{border-top:3px solid #16a36f}.exec-card.blue{border-top:3px solid #2876a7}.exec-signal{border:1px solid #dce4ec;border-left:5px solid #d4a92e;border-radius:14px;padding:.7rem .8rem;margin:.4rem 0;background:#fff}.exec-signal.red{border-left-color:#d64545}.exec-signal.blue{border-left-color:#2876a7}.exec-signal b{color:#0f2742}.exec-signal span{display:block;color:#64748b;font-size:.82rem;margin-top:.1rem}@media(max-width:700px){.exec-card-grid{grid-template-columns:1fr 1fr}.exec-card b{font-size:1.25rem}}
</style>
<div class="exec-hero"><b>MONTHLY EXECUTIVE VIEW</b><br><span>Availability shows whether the instrument was ready. Utilization shows how intensively available capacity was used. The management signal combines both — without pretending to prove root cause.</span><br><span class="gold">DON'T GUESS. FOLLOW THE EVIDENCE.</span></div>
""",
        unsafe_allow_html=True,
    )

    cards = [
        ("Monthly Availability", _exec_pct(p["availability"]), "Weighted portfolio", "green" if p["availability"] is not None else "blue"),
        ("Monthly Utilization", _exec_pct(p["utilization"]), "Weighted portfolio", "blue"),
        ("Data coverage", f"{p['coverage']}/{len(instruments)}", f"Missing {len(missing)}", "gold" if missing else "green"),
        ("Unplanned downtime", f"{p['unplanned']:.1f} h", "Portfolio loss", "red" if p["unplanned"] > 0 else "green"),
        ("Capacity risk", p["capacity_risk"], "High demand + low availability", "red" if p["capacity_risk"] else "green"),
        ("Below Availability target", p["below_avail"], "Configured targets", "gold" if p["below_avail"] else "green"),
        ("Below Utilization target", p["below_util"], "Configured targets", "blue" if p["below_util"] else "green"),
        ("Open Event / OOC", f"{len(open_events)} / {len(open_ooc)}", "Quality context", "red" if open_ooc or open_events else "green"),
    ]
    st.markdown('<div class="exec-card-grid">' + ''.join(f'<div class="exec-card {tone}"><span>{xml_escape(str(label))}</span><b>{xml_escape(str(value))}</b><span>{xml_escape(str(note))}</span></div>' for label, value, note, tone in cards) + '</div>', unsafe_allow_html=True)

    st.markdown("### Management attention now")
    management_rows = sorted([r for r in p["recorded"] if r.get("rank") <= 3], key=lambda r: (r.get("rank", 9), -(r.get("unplanned") or 0)))
    if not management_rows:
        st.success("No current target-based capacity / reliability management signal in the selected month.")
    else:
        for r in management_rows[:8]:
            tone = "red" if r.get("signal") == "Capacity risk" else "blue" if r.get("signal") == "Capacity available" else ""
            st.markdown(f'<div class="exec-signal {tone}"><b>{xml_escape(str(r.get("code")))} · {xml_escape(str(r.get("signal")))}</b><span>Availability {_exec_pct(r.get("availability"))} · Utilization {_exec_pct(r.get("utilization"))} · Unplanned downtime {_exec_num(r.get("unplanned"))} h</span><span>{xml_escape(str(r.get("action")))}</span></div>', unsafe_allow_html=True)

    t1, t2 = st.columns(2)
    with t1:
        st.markdown("### 🔴 Highest unplanned downtime")
        top_unplanned = sorted(p["recorded"], key=lambda r: r.get("unplanned") or 0, reverse=True)[:5]
        st.dataframe(pd.DataFrame([{"Instrument": r.get("code"), "Unplanned h": round(r.get("unplanned") or 0, 1), "Availability %": None if r.get("availability") is None else round(r.get("availability"), 1), "Signal": r.get("signal")} for r in top_unplanned]), use_container_width=True, hide_index=True)
    with t2:
        st.markdown("### 🔵 Available spare capacity")
        top_idle = sorted(p["recorded"], key=lambda r: r.get("idle") or 0, reverse=True)[:5]
        st.dataframe(pd.DataFrame([{"Instrument": r.get("code"), "Idle available h": round(r.get("idle") or 0, 1), "Utilization %": None if r.get("utilization") is None else round(r.get("utilization"), 1), "Signal": r.get("signal")} for r in top_idle]), use_container_width=True, hide_index=True)

    st.markdown("### 📉 Six-month portfolio trend")
    trend = _exec_trend(perf_rows, instruments, selected_month)
    if trend:
        trend_df = pd.DataFrame([{"Month": m.strftime("%Y-%m"), "Coverage": coverage, "Availability %": None if av is None else round(av, 1), "Utilization %": None if ut is None else round(ut, 1), "Unplanned downtime h": round(unp, 1)} for m, coverage, av, ut, unp in trend]).set_index("Month")
        st.line_chart(trend_df[["Availability %", "Utilization %"]])
        st.dataframe(trend_df.reset_index(), use_container_width=True, hide_index=True)

    if missing:
        with st.expander(f"⚠ Data completeness · {len(missing)} instrument(s) missing this month"):
            st.write(" · ".join(str(r.get("code")) for r in missing[:50]))
            st.caption("The report shows the gap explicitly. It does not convert missing data into zero performance.")

    st.markdown("### 📄 Executive PDF")
    language = st.radio("Report language", ["English", "العربية"], horizontal=True, key="exec_pdf_language")
    lang = "ar" if language == "العربية" else "en"
    try:
        pdf_bytes = _build_exec_pdf(instruments, perf_rows, events_exec if events_ok else [], calibrations_exec if cal_ok else [], selected_month, lang)
        file_name = f"Yahia_QC_Executive_Performance_{selected_month:%Y_%m}_{lang}.pdf"
        st.download_button("⬇️ Generate / Download Executive Performance PDF", data=pdf_bytes, file_name=file_name, mime="application/pdf", use_container_width=True, key="exec_pdf_download")
        st.caption("The PDF contains executive KPIs, management attention, top losses, spare capacity, six-month trend, full portfolio target-gap table, formulas and evidence boundary.")
    except Exception as exc:
        st.error("Executive PDF could not be generated.")
        st.caption(f"Diagnostic: {type(exc).__name__}")
