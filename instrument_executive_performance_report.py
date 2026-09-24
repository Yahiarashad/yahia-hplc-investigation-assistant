# Executive Performance Intelligence v2
# Evidence-first monthly management intelligence for Yahia QC Instrument Lifecycle.

from __future__ import annotations

from datetime import date, datetime, timezone
from io import BytesIO
from pathlib import Path
from xml.sax.saxutils import escape as xml_escape

import pandas as pd
import streamlit as st
from instrument_i18n import current_language as _current_language

try:
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    from reportlab.lib.pagesizes import landscape, A4
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import mm
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.platypus import (
        PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle,
        KeepTogether,
    )
    from reportlab.graphics.shapes import Drawing, String
    from reportlab.graphics.charts.linecharts import HorizontalLineChart
    from reportlab.graphics.charts.barcharts import VerticalBarChart
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

UI = {
    "en": {
        "title": "Executive Performance Intelligence",
        "subtitle": "Turn monthly instrument hours into management priorities, capacity signals and a decision-ready report.",
        "month": "Executive report month",
        "view": "MONTHLY EXECUTIVE VIEW",
        "view_desc": "Availability shows whether capacity was ready. Utilization shows how intensively available capacity was used. Signals prioritize evidence — they do not prove root cause.",
        "availability": "Monthly Availability",
        "utilization": "Monthly Utilization",
        "coverage": "Data coverage",
        "unplanned": "Unplanned downtime",
        "capacity_risk": "Capacity risk",
        "below_avail": "Below Availability target",
        "below_util": "Below Utilization target",
        "quality": "Open Event / OOC",
        "commentary": "Executive commentary",
        "attention": "Top management attention",
        "downtime": "Highest unplanned downtime",
        "spare": "Available spare capacity",
        "trend": "Six-month portfolio trend",
        "missing": "Data completeness",
        "pdf": "Executive PDF v2",
        "download": "Generate / Download Executive Intelligence PDF",
        "language": "Language",
        "no_data": "No monthly performance records are available for this month. Record or import monthly hours first; the application will not invent performance data.",
        "no_signal": "No current high-priority management signal was detected for the selected month.",
        "signal_note": "A management signal identifies where evidence deserves attention. It is not a root-cause conclusion.",
    },
    "ar": {
        "title": "ذكاء الأداء التنفيذي",
        "subtitle": "حوّل ساعات تشغيل الأجهزة الشهرية إلى أولويات إدارية وإشارات سعة وتقرير جاهز لاتخاذ القرار.",
        "month": "شهر التقرير التنفيذي",
        "view": "الرؤية التنفيذية الشهرية",
        "view_desc": "الإتاحة توضح هل السعة كانت جاهزة للعمل، والاستخدام يوضح مدى استغلال السعة المتاحة. الإشارات ترتب الأدلة حسب الأولوية ولا تثبت السبب الجذري.",
        "availability": "الإتاحة الشهرية",
        "utilization": "الاستخدام الشهري",
        "coverage": "اكتمال البيانات",
        "unplanned": "التوقف غير المخطط",
        "capacity_risk": "مخاطر السعة",
        "below_avail": "أقل من هدف الإتاحة",
        "below_util": "أقل من هدف الاستخدام",
        "quality": "حدث مفتوح / OOC",
        "commentary": "الملخص التنفيذي",
        "attention": "أعلى أولويات الإدارة",
        "downtime": "أعلى توقف غير مخطط",
        "spare": "السعة المتاحة غير المستغلة",
        "trend": "اتجاه المحفظة خلال 6 أشهر",
        "missing": "اكتمال البيانات",
        "pdf": "التقرير التنفيذي PDF v2",
        "download": "إنشاء / تحميل تقرير الذكاء التنفيذي",
        "language": "اللغة",
        "no_data": "لا توجد سجلات أداء شهرية لهذا الشهر. سجّل أو استورد الساعات أولًا؛ التطبيق لن يفترض بيانات غير موجودة.",
        "no_signal": "لا توجد إشارة إدارية عالية الأولوية حاليًا للشهر المحدد.",
        "signal_note": "الإشارة الإدارية تحدد أين تحتاج الأدلة إلى انتباه. وهي ليست إثباتًا للسبب الجذري.",
    },
}

AR_LABELS = {
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
    "Out of Service": "خارج الخدمة",
    "Under Maintenance": "تحت الصيانة",
    "Restricted": "مقيد الاستخدام",
    "Critical event": "حدث حرج",
    "High-severity event": "حدث عالي الخطورة",
    "Open OOC": "OOC مفتوح",
    "Availability below target": "الإتاحة أقل من الهدف",
    "Utilization below target": "الاستخدام أقل من الهدف",
    "Unplanned downtime": "توقف غير مخطط",
    "Missing monthly performance": "بيانات الأداء الشهرية مفقودة",
}


def _t(key: str, lang: str) -> str:
    return UI.get(lang, UI["en"]).get(key, key)


def _ar(value: str) -> str:
    text = str(value or "")
    if not text or arabic_reshaper is None or bidi_get_display is None:
        return text
    try:
        return bidi_get_display(arabic_reshaper.reshape(text))
    except Exception:
        return text


def _pdf_text(value, lang):
    text = str(value or "")
    return _ar(text) if lang == "ar" else text


def _month(value):
    try:
        return pd.to_datetime(value).date().replace(day=1)
    except Exception:
        return date.today().replace(day=1)


def _prev_month(month_start: date) -> date:
    if month_start.month == 1:
        return date(month_start.year - 1, 12, 1)
    return date(month_start.year, month_start.month - 1, 1)


def _target(value):
    try:
        if value is None or str(value).strip() == "":
            return None
        val = float(value)
        return val if 0 <= val <= 100 else None
    except Exception:
        return None


def _calc(row):
    scheduled = float(row.get("scheduled_hours") or 0)
    planned = float(row.get("planned_downtime_hours") or 0)
    unplanned = float(row.get("unplanned_downtime_hours") or 0)
    productive = float(row.get("productive_run_hours") or 0)
    planned_operating = max(0.0, scheduled - planned)
    available = max(0.0, planned_operating - unplanned)
    availability = available / planned_operating * 100 if planned_operating > 0 else None
    utilization = productive / available * 100 if available > 0 else None
    idle = max(0.0, available - productive)
    return {
        "scheduled": scheduled,
        "planned": planned,
        "unplanned": unplanned,
        "productive": productive,
        "planned_operating": planned_operating,
        "available": available,
        "availability": availability,
        "utilization": utilization,
        "idle": idle,
    }


def _signal(availability, utilization, ta, tu):
    ta = _target(ta)
    tu = _target(tu)
    if ta is None and tu is None:
        return "No target", "Set instrument-specific management targets before interpreting target gaps.", 4
    a_ok = None if availability is None or ta is None else availability >= ta
    u_ok = None if utilization is None or tu is None else utilization >= tu
    if a_ok is False and u_ok is True:
        return "Capacity risk", "Review reliability, unplanned downtime and workload concentration. If persistent, assess backup or replacement capacity.", 1
    if a_ok is False and u_ok is False:
        return "Reliability + demand review", "Availability and utilization are both below target. Review reliability, scheduling and demand before a capacity decision.", 2
    if a_ok is True and u_ok is False:
        return "Capacity available", "The instrument is available but underused versus target. Review scheduling, method allocation and real demand.", 3
    if a_ok is True and u_ok is True:
        return "On target", "Maintain current controls and continue monthly trending.", 5
    if a_ok is False:
        return "Availability below target", "Review unplanned downtime and reliability drivers.", 2
    if u_ok is False:
        return "Utilization below target", "Review scheduling, demand and capacity allocation.", 3
    if a_ok is True or u_ok is True:
        return "Target met", "The configured target is met for the available metric.", 5
    return "Insufficient data", "Complete monthly hours before interpreting performance.", 4


def _dataset(instruments, perf_rows, selected_month):
    month_rows = [r for r in perf_rows if _month(r.get("month_start")) == selected_month]
    row_by_instrument = {str(r.get("instrument_id")): r for r in month_rows}
    out = []
    for inst in instruments:
        iid = str(inst.get("id"))
        row = row_by_instrument.get(iid)
        base = {
            "iid": iid,
            "code": inst.get("instrument_code") or iid,
            "name": inst.get("instrument_name") or "",
            "type": inst.get("instrument_type") or "",
            "status": inst.get("operational_status") or "",
            "ta": _target(inst.get("target_availability_pct")),
            "tu": _target(inst.get("target_utilization_pct")),
        }
        if not row:
            base.update({
                "recorded": False,
                "signal": "No monthly record",
                "action": "Record the selected month's scheduled, downtime and productive hours.",
                "rank": 0,
                "availability": None,
                "utilization": None,
                "unplanned": 0.0,
                "productive": 0.0,
                "idle": 0.0,
                "planned_operating": 0.0,
                "planned": 0.0,
                "availability_gap": None,
                "utilization_gap": None,
            })
            out.append(base)
            continue
        m = _calc(row)
        sig, action, rank = _signal(m["availability"], m["utilization"], base["ta"], base["tu"])
        base.update({
            "recorded": True,
            **m,
            "signal": sig,
            "action": action,
            "rank": rank,
            "availability_gap": m["availability"] - base["ta"] if m["availability"] is not None and base["ta"] is not None else None,
            "utilization_gap": m["utilization"] - base["tu"] if m["utilization"] is not None and base["tu"] is not None else None,
            "notes": row.get("notes") or "",
        })
        out.append(base)
    return out


def _portfolio(rows):
    recorded = [r for r in rows if r.get("recorded")]
    planned_operating = sum(float(r.get("planned_operating") or 0) for r in recorded)
    available = sum(float(r.get("available") or 0) for r in recorded)
    productive = sum(float(r.get("productive") or 0) for r in recorded)
    return {
        "recorded": recorded,
        "coverage": len(recorded),
        "availability": available / planned_operating * 100 if planned_operating > 0 else None,
        "utilization": productive / available * 100 if available > 0 else None,
        "planned": sum(float(r.get("planned") or 0) for r in recorded),
        "unplanned": sum(float(r.get("unplanned") or 0) for r in recorded),
        "productive": productive,
        "idle": sum(float(r.get("idle") or 0) for r in recorded),
        "capacity_risk": sum(1 for r in recorded if r.get("signal") == "Capacity risk"),
        "below_avail": sum(1 for r in recorded if r.get("ta") is not None and r.get("availability") is not None and r.get("availability") < r.get("ta")),
        "below_util": sum(1 for r in recorded if r.get("tu") is not None and r.get("utilization") is not None and r.get("utilization") < r.get("tu")),
    }


def _pct(value):
    return "—" if value is None else f"{float(value):.1f}%"


def _num(value):
    try:
        return f"{float(value):.1f}"
    except Exception:
        return "—"


def _gap(value):
    return "—" if value is None else f"{float(value):+.1f} pp"


def _sev(value):
    return str(value or "").strip().lower()


def _open_quality_context(events, calibrations):
    open_events = [e for e in events if str(e.get("event_status") or "").strip().lower() != "closed"]
    open_ooc = [c for c in calibrations if str(c.get("result") or "").upper() == "OOC" and str(c.get("ooc_status") or "Open").strip().lower() not in {"closed", "resolved", "not applicable"}]
    ev_by = {}
    for e in open_events:
        ev_by.setdefault(str(e.get("instrument_id")), []).append(e)
    ooc_by = {}
    for c in open_ooc:
        ooc_by.setdefault(str(c.get("instrument_id")), []).append(c)
    return open_events, open_ooc, ev_by, ooc_by


def _attention(rows, events, calibrations):
    _, _, ev_by, ooc_by = _open_quality_context(events, calibrations)
    output = []
    for r in rows:
        reasons = []
        score = 0
        iid = str(r.get("iid"))
        status = str(r.get("status") or "")
        if status == "Out of Service":
            score += 9; reasons.append("Out of Service")
        elif status == "Restricted":
            score += 6; reasons.append("Restricted")
        elif status == "Under Maintenance":
            score += 4; reasons.append("Under Maintenance")
        if ooc_by.get(iid):
            score += 10; reasons.append("Open OOC")
        for event in ev_by.get(iid, []):
            sev = _sev(event.get("severity"))
            if sev in {"critical", "very high"}:
                score += 8; reasons.append("Critical event")
                break
            if sev == "high":
                score += 5; reasons.append("High-severity event")
                break
            score += 2
        if r.get("signal") == "Capacity risk":
            score += 7; reasons.append("Capacity risk")
        elif r.get("signal") == "Reliability + demand review":
            score += 5; reasons.append("Reliability + demand review")
        elif r.get("signal") == "Capacity available":
            score += 2; reasons.append("Capacity available")
        if r.get("availability_gap") is not None and r.get("availability_gap") < 0:
            score += min(6, 2 + int(abs(float(r.get("availability_gap"))) // 5))
            reasons.append("Availability below target")
        if r.get("utilization_gap") is not None and r.get("utilization_gap") < 0:
            score += 2
            reasons.append("Utilization below target")
        unplanned = float(r.get("unplanned") or 0)
        if unplanned > 0:
            score += min(5, max(1, int(unplanned // 8) + 1))
            reasons.append("Unplanned downtime")
        if not r.get("recorded"):
            score += 2
            reasons.append("Missing monthly performance")
        # Deduplicate while preserving order.
        reasons = list(dict.fromkeys(reasons))
        output.append({**r, "attention_score": score, "attention_reasons": reasons, "open_event_count": len(ev_by.get(iid, [])), "open_ooc_count": len(ooc_by.get(iid, []))})
    return sorted(output, key=lambda x: (-x.get("attention_score", 0), -(x.get("unplanned") or 0), str(x.get("code") or "")))


def _trend(perf_rows, instruments, selected_month):
    months = []
    cur = selected_month
    for _ in range(6):
        months.append(cur)
        cur = _prev_month(cur)
    months.reverse()
    out = []
    for m in months:
        rows = _dataset(instruments, perf_rows, m)
        p = _portfolio(rows)
        out.append((m, p["coverage"], p["availability"], p["utilization"], p["unplanned"]))
    return out


def _delta(current, previous):
    if current is None or previous is None:
        return None
    return float(current) - float(previous)


def _commentary(rows, p, prev_p, attention_rows, total_instruments, selected_month, lang):
    lines = []
    coverage_pct = (p["coverage"] / total_instruments * 100) if total_instruments else 0
    if lang == "ar":
        lines.append(f"تم تسجيل بيانات الأداء الشهري لعدد {p['coverage']} من {total_instruments} جهاز ({coverage_pct:.0f}%).")
    else:
        lines.append(f"Monthly performance is recorded for {p['coverage']} of {total_instruments} instruments ({coverage_pct:.0f}% coverage).")

    av_delta = _delta(p.get("availability"), prev_p.get("availability") if prev_p else None)
    ut_delta = _delta(p.get("utilization"), prev_p.get("utilization") if prev_p else None)
    dt_delta = _delta(p.get("unplanned"), prev_p.get("unplanned") if prev_p else None)

    if av_delta is not None:
        direction = "ارتفعت" if av_delta > 0 else "انخفضت" if av_delta < 0 else "لم تتغير"
        if lang == "ar":
            lines.append(f"الإتاحة الشهرية {direction} بمقدار {abs(av_delta):.1f} نقطة مئوية مقارنة بالشهر السابق، لتصل إلى {_pct(p.get('availability'))}.")
        else:
            word = "improved" if av_delta > 0 else "declined" if av_delta < 0 else "was unchanged"
            lines.append(f"Portfolio Availability {word} by {abs(av_delta):.1f} percentage points versus the previous month, reaching {_pct(p.get('availability'))}.")
    if ut_delta is not None:
        if lang == "ar":
            direction = "ارتفع" if ut_delta > 0 else "انخفض" if ut_delta < 0 else "لم يتغير"
            lines.append(f"الاستخدام الشهري {direction} بمقدار {abs(ut_delta):.1f} نقطة مئوية، ليصل إلى {_pct(p.get('utilization'))}.")
        else:
            word = "increased" if ut_delta > 0 else "decreased" if ut_delta < 0 else "was unchanged"
            lines.append(f"Portfolio Utilization {word} by {abs(ut_delta):.1f} percentage points to {_pct(p.get('utilization'))}.")
    if dt_delta is not None:
        if lang == "ar":
            direction = "زاد" if dt_delta > 0 else "انخفض" if dt_delta < 0 else "لم يتغير"
            lines.append(f"إجمالي التوقف غير المخطط {direction} بمقدار {abs(dt_delta):.1f} ساعة عن الشهر السابق، والقيمة الحالية {p['unplanned']:.1f} ساعة.")
        else:
            word = "increased" if dt_delta > 0 else "decreased" if dt_delta < 0 else "was unchanged"
            lines.append(f"Unplanned downtime {word} by {abs(dt_delta):.1f} hours versus the previous month; current total is {p['unplanned']:.1f} hours.")

    if p.get("capacity_risk"):
        if lang == "ar":
            lines.append(f"يوجد {p['capacity_risk']} جهاز بإشارة Capacity Risk: استخدام مرتفع مع إتاحة أقل من الهدف، ما يستدعي مراجعة الاعتمادية والسعة البديلة قبل أي قرار توسع أو استبدال.")
        else:
            lines.append(f"{p['capacity_risk']} instrument(s) show Capacity Risk: high use with Availability below target. Review reliability and backup capacity before expansion or replacement decisions.")
    if p.get("below_avail"):
        if lang == "ar":
            lines.append(f"عدد {p['below_avail']} جهاز أقل من هدف الإتاحة المحدد له.")
        else:
            lines.append(f"{p['below_avail']} instrument(s) are below their configured Availability target.")

    critical = [r for r in attention_rows if r.get("attention_score", 0) >= 8]
    if critical:
        top = ", ".join(str(r.get("code")) for r in critical[:3])
        if lang == "ar":
            lines.append(f"أعلى الأجهزة احتياجًا للمراجعة الآن: {top}. الأولوية مبنية على تجميع إشارات الحالة، OOC/Events، فجوات الأهداف والتوقف غير المخطط.")
        else:
            lines.append(f"Highest current attention priority: {top}. Ranking combines status, OOC/events, target gaps and unplanned downtime signals.")

    spare = sorted([r for r in p["recorded"] if (r.get("idle") or 0) > 0], key=lambda x: x.get("idle") or 0, reverse=True)
    if spare and float(spare[0].get("idle") or 0) >= 8:
        r = spare[0]
        if lang == "ar":
            lines.append(f"أكبر سعة متاحة غير مستغلة حاليًا لدى {r.get('code')} بحوالي {r.get('idle'):.1f} ساعة؛ راجع توزيع طرق التحليل والجدولة قبل طلب سعة إضافية.")
        else:
            lines.append(f"Largest currently available spare capacity is {r.get('code')} at about {r.get('idle'):.1f} idle-available hours; review scheduling and method allocation before adding capacity.")
    return lines[:7]


# ------------------------------ PDF helpers ---------------------------------
def _font_paths():
    candidates = [
        ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
        ("/usr/share/fonts/truetype/freefont/FreeSans.ttf", "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf"),
    ]
    for regular, bold in candidates:
        if Path(regular).exists() and Path(bold).exists():
            return regular, bold
    return None, None


def _fonts():
    regular, bold = _font_paths()
    if regular and bold:
        try:
            pdfmetrics.registerFont(TTFont("EXECV2REG", regular))
            pdfmetrics.registerFont(TTFont("EXECV2BOLD", bold))
            return "EXECV2REG", "EXECV2BOLD"
        except Exception:
            pass
    return "Helvetica", "Helvetica-Bold"


def _styles(lang):
    reg, bold = _fonts()
    base = getSampleStyleSheet()
    align = TA_RIGHT if lang == "ar" else TA_LEFT
    return {
        "reg": reg,
        "bold": bold,
        "title": ParagraphStyle("V2Title", parent=base["Title"], fontName=bold, fontSize=21, leading=25, textColor=colors.HexColor("#0b2946"), alignment=align, spaceAfter=7),
        "h1": ParagraphStyle("V2H1", parent=base["Heading1"], fontName=bold, fontSize=13, leading=17, textColor=colors.HexColor("#0b2946"), alignment=align, spaceBefore=5, spaceAfter=5),
        "body": ParagraphStyle("V2Body", parent=base["BodyText"], fontName=reg, fontSize=8.4, leading=12, textColor=colors.HexColor("#263445"), alignment=align),
        "small": ParagraphStyle("V2Small", parent=base["BodyText"], fontName=reg, fontSize=7, leading=9.2, textColor=colors.HexColor("#66778a"), alignment=align),
        "center": ParagraphStyle("V2Center", parent=base["BodyText"], fontName=bold, fontSize=9.2, leading=11, textColor=colors.HexColor("#0b2946"), alignment=TA_CENTER),
        "card_label": ParagraphStyle("V2CardLabel", parent=base["BodyText"], fontName=reg, fontSize=6.8, leading=8.5, textColor=colors.HexColor("#64748b"), alignment=TA_CENTER),
        "card_value": ParagraphStyle("V2CardValue", parent=base["BodyText"], fontName=bold, fontSize=16, leading=18, textColor=colors.HexColor("#0b2946"), alignment=TA_CENTER),
    }


def _p(text, style, lang):
    val = _pdf_text(text, lang)
    return Paragraph(xml_escape(str(val)).replace("\n", "<br/>"), style)


def _header(canvas, doc, styles, selected_month, lang):
    canvas.saveState()
    w, h = landscape(A4)
    canvas.setFillColor(colors.HexColor("#071422"))
    canvas.rect(0, h - 18*mm, w, 18*mm, fill=1, stroke=0)
    canvas.setFillColor(colors.HexColor("#e1c56d"))
    canvas.setFont(styles["bold"], 8.5)
    brand = "YAHIA QC INSTRUMENT LIFECYCLE · EVIDENCE FIRST"
    canvas.drawString(14*mm, h - 11*mm, brand)
    canvas.setFillColor(colors.HexColor("#94a3b8"))
    canvas.setFont(styles["reg"], 6.5)
    canvas.drawRightString(w - 14*mm, 9*mm, f"{selected_month:%Y-%m} · Page {doc.page}")
    canvas.restoreState()


def _simple_table(headers, rows, styles, lang, widths=None, traffic_col=None):
    if not rows:
        rows = [["—" for _ in headers]]
    data = [[_p(h if lang == "en" else AR_LABELS.get(h, h), styles["small"], lang) for h in headers]]
    for row in rows:
        data.append([_p(v, styles["small"], lang) for v in row])
    table = Table(data, colWidths=widths, repeatRows=1, hAlign="RIGHT" if lang == "ar" else "LEFT")
    style = [
        ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#0b2946")),
        ("TEXTCOLOR", (0,0), (-1,0), colors.white),
        ("GRID", (0,0), (-1,-1), 0.3, colors.HexColor("#dbe3ea")),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ("BACKGROUND", (0,1), (-1,-1), colors.white),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, colors.HexColor("#f8fafc")]),
        ("TOPPADDING", (0,0), (-1,-1), 4),
        ("BOTTOMPADDING", (0,0), (-1,-1), 4),
        ("LEFTPADDING", (0,0), (-1,-1), 5),
        ("RIGHTPADDING", (0,0), (-1,-1), 5),
    ]
    if traffic_col is not None:
        for idx, row in enumerate(rows, start=1):
            val = str(row[traffic_col] if traffic_col < len(row) else "").lower()
            if "critical" in val or "risk" in val or "ooc" in val or "خطر" in val:
                style.append(("BACKGROUND", (traffic_col, idx), (traffic_col, idx), colors.HexColor("#fde8e8")))
            elif "review" in val or "below" in val or "مراجعة" in val or "أقل" in val:
                style.append(("BACKGROUND", (traffic_col, idx), (traffic_col, idx), colors.HexColor("#fff4d8")))
            elif "target" in val or "ضمن" in val:
                style.append(("BACKGROUND", (traffic_col, idx), (traffic_col, idx), colors.HexColor("#e8f7ef")))
    table.setStyle(TableStyle(style))
    return table


def _metric_cards(items, styles, lang):
    cells = []
    tones = []
    for label, value, tone in items:
        cells.append(Table([
            [_p(label, styles["card_label"], lang)],
            [_p(value, styles["card_value"], lang)],
        ], colWidths=[61*mm], rowHeights=[8*mm, 12*mm]))
        tones.append(tone)
    tbl = Table([cells], colWidths=[63*mm]*len(cells), hAlign="LEFT")
    ts = [("VALIGN", (0,0), (-1,-1), "MIDDLE"), ("LEFTPADDING", (0,0), (-1,-1), 2), ("RIGHTPADDING", (0,0), (-1,-1), 2)]
    tone_map = {"green":"#e9f8f1", "blue":"#e9f4fb", "gold":"#fff5dc", "red":"#fdeaea"}
    for i, tone in enumerate(tones):
        ts.append(("BACKGROUND", (i,0), (i,0), colors.HexColor(tone_map.get(tone, "#f8fafc"))))
        ts.append(("BOX", (i,0), (i,0), 0.8, colors.HexColor("#dbe3ea")))
    tbl.setStyle(TableStyle(ts))
    return tbl


def _trend_chart(trend, lang):
    valid = [(m,av,ut) for m,_,av,ut,_ in trend if av is not None or ut is not None]
    if not valid:
        return Spacer(1, 1)
    labels = [m.strftime("%m/%y") for m,_,_ in valid]
    av = [float(a or 0) for _,a,_ in valid]
    ut = [float(u or 0) for _,_,u in valid]
    drawing = Drawing(245*mm, 72*mm)
    chart = HorizontalLineChart()
    chart.x = 18*mm; chart.y = 14*mm; chart.width = 210*mm; chart.height = 46*mm
    chart.data = [av, ut]
    chart.categoryAxis.categoryNames = labels
    chart.categoryAxis.labels.fontSize = 7
    chart.valueAxis.valueMin = 0; chart.valueAxis.valueMax = 100; chart.valueAxis.valueStep = 20
    chart.valueAxis.labels.fontSize = 7
    chart.lines[0].strokeColor = colors.HexColor("#1e9e6f"); chart.lines[0].strokeWidth = 2
    chart.lines[1].strokeColor = colors.HexColor("#2876a7"); chart.lines[1].strokeWidth = 2
    drawing.add(chart)
    drawing.add(String(18*mm, 64*mm, "Availability", fontSize=7, fillColor=colors.HexColor("#1e9e6f")))
    drawing.add(String(55*mm, 64*mm, "Utilization", fontSize=7, fillColor=colors.HexColor("#2876a7")))
    return drawing


def _downtime_chart(rows):
    data = sorted([r for r in rows if r.get("recorded")], key=lambda x: x.get("unplanned") or 0, reverse=True)[:5]
    if not data or max(float(r.get("unplanned") or 0) for r in data) <= 0:
        return Spacer(1, 1)
    drawing = Drawing(245*mm, 68*mm)
    chart = VerticalBarChart()
    chart.x = 20*mm; chart.y = 15*mm; chart.width = 205*mm; chart.height = 42*mm
    chart.data = [[float(r.get("unplanned") or 0) for r in data]]
    chart.categoryAxis.categoryNames = [str(r.get("code"))[:14] for r in data]
    chart.categoryAxis.labels.fontSize = 6.5
    chart.valueAxis.labels.fontSize = 7
    chart.bars[0].fillColor = colors.HexColor("#d84a4a")
    drawing.add(chart)
    return drawing


def _build_pdf(instruments, perf_rows, events, calibrations, selected_month, lang):
    if colors is None:
        raise RuntimeError("reportlab is unavailable")
    rows = _dataset(instruments, perf_rows, selected_month)
    p = _portfolio(rows)
    prev_rows = _dataset(instruments, perf_rows, _prev_month(selected_month))
    prev_p = _portfolio(prev_rows)
    attention_rows = _attention(rows, events, calibrations)
    open_events, open_ooc, _, _ = _open_quality_context(events, calibrations)
    commentary = _commentary(rows, p, prev_p if prev_p.get("coverage") else None, attention_rows, len(instruments), selected_month, lang)
    trend = _trend(perf_rows, instruments, selected_month)

    styles = _styles(lang)
    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=landscape(A4),
        rightMargin=14*mm, leftMargin=14*mm, topMargin=24*mm, bottomMargin=15*mm,
        title="Yahia QC Executive Performance Intelligence",
        author="Yahia Abdelhalim",
    )
    story = []
    story.append(_p(_t("title", lang), styles["title"], lang))
    story.append(_p((f"{selected_month:%B %Y} · Generated {datetime.now(timezone.utc):%Y-%m-%d %H:%M UTC}" if lang == "en" else f"{selected_month:%Y-%m} · تم الإنشاء {datetime.now(timezone.utc):%Y-%m-%d %H:%M UTC}"), styles["small"], lang))
    story.append(Spacer(1, 4*mm))

    metrics = [
        (_t("availability", lang), _pct(p.get("availability")), "green" if p.get("availability") is not None else "blue"),
        (_t("utilization", lang), _pct(p.get("utilization")), "blue"),
        (_t("coverage", lang), f"{p['coverage']}/{len(instruments)}", "gold" if p["coverage"] < len(instruments) else "green"),
        (_t("unplanned", lang), f"{p['unplanned']:.1f} h", "red" if p["unplanned"] > 0 else "green"),
    ]
    story.append(_metric_cards(metrics, styles, lang))
    story.append(Spacer(1, 5*mm))

    story.append(_p(_t("commentary", lang), styles["h1"], lang))
    comment_rows = [[f"{i+1}", line] for i, line in enumerate(commentary)]
    story.append(_simple_table(["#", _t("commentary", lang)], comment_rows, styles, lang, widths=[10*mm, 245*mm]))
    story.append(Spacer(1, 5*mm))

    story.append(_p(_t("attention", lang), styles["h1"], lang))
    top = [r for r in attention_rows if r.get("attention_score", 0) > 0][:10]
    attention_table = []
    for r in top:
        reasons = ", ".join(AR_LABELS.get(x, x) if lang == "ar" else x for x in r.get("attention_reasons", [])[:4])
        attention_table.append([
            r.get("code"), r.get("status"), r.get("attention_score"),
            _pct(r.get("availability")), _pct(r.get("utilization")), _num(r.get("unplanned")), reasons,
        ])
    story.append(_simple_table(
        ["Instrument", "Status", "Priority score", "Availability %", "Utilization %", "Unplanned h", "Evidence signals"],
        attention_table, styles, lang,
        widths=[28*mm, 33*mm, 23*mm, 28*mm, 28*mm, 27*mm, 95*mm],
        traffic_col=6,
    ))

    story.append(PageBreak())
    story.append(_p(_t("trend", lang), styles["title"], lang))
    story.append(_trend_chart(trend, lang))
    story.append(Spacer(1, 3*mm))
    trend_rows = [[m.strftime("%Y-%m"), f"{cov}/{len(instruments)}", _pct(av), _pct(ut), f"{unp:.1f} h"] for m,cov,av,ut,unp in trend]
    story.append(_simple_table(["Month", "Coverage", "Availability %", "Utilization %", "Unplanned downtime"], trend_rows, styles, lang))
    story.append(Spacer(1, 5*mm))
    story.append(_p(_t("downtime", lang), styles["h1"], lang))
    story.append(_downtime_chart(rows))

    story.append(PageBreak())
    story.append(_p("Portfolio target-gap table" if lang == "en" else "جدول فجوات الأهداف للمحفظة", styles["title"], lang))
    portfolio_rows = []
    for r in sorted(rows, key=lambda x: (0 if x.get("recorded") else 1, x.get("rank", 9), str(x.get("code") or ""))):
        portfolio_rows.append([
            r.get("code"), r.get("type"), r.get("status"), _pct(r.get("availability")), _pct(r.get("ta")), _gap(r.get("availability_gap")),
            _pct(r.get("utilization")), _pct(r.get("tu")), _gap(r.get("utilization_gap")), AR_LABELS.get(r.get("signal"), r.get("signal")) if lang == "ar" else r.get("signal"),
        ])
    story.append(_simple_table(
        ["Instrument", "Type", "Status", "Availability %", "Avail target %", "Avail gap", "Utilization %", "Util target %", "Util gap", "Signal"],
        portfolio_rows, styles, lang,
        widths=[23*mm, 18*mm, 28*mm, 23*mm, 23*mm, 22*mm, 23*mm, 23*mm, 22*mm, 52*mm],
        traffic_col=9,
    ))

    story.append(PageBreak())
    story.append(_p("Methodology & Evidence Boundary" if lang == "en" else "طريقة الحساب وحدود استخدام الدليل", styles["title"], lang))
    methodology_en = (
        "Planned Operating Time = Scheduled Service Hours − Planned Downtime.\n"
        "Available Time = Planned Operating Time − Unplanned Downtime.\n"
        "Availability % = Available Time ÷ Planned Operating Time × 100.\n"
        "Utilization % = Productive Run Hours ÷ Available Time × 100.\n"
        "Portfolio percentages are weighted by hours; instrument percentages are not averaged equally."
    )
    methodology_ar = (
        "وقت التشغيل المخطط = ساعات الخدمة المجدولة − التوقف المخطط.\n"
        "الوقت المتاح = وقت التشغيل المخطط − التوقف غير المخطط.\n"
        "الإتاحة % = الوقت المتاح ÷ وقت التشغيل المخطط × 100.\n"
        "الاستخدام % = ساعات التشغيل الإنتاجي ÷ الوقت المتاح × 100.\n"
        "نسب المحفظة مرجحة بالساعات ولا يتم أخذ متوسط بسيط لنسب الأجهزة."
    )
    story.append(_p(methodology_ar if lang == "ar" else methodology_en, styles["body"], lang))
    story.append(Spacer(1, 5*mm))
    boundary_en = (
        "This report is decision-support intelligence, not a validated GxP record, release decision, root-cause conclusion or universal KPI specification. "
        "Targets are user-defined. Priority scores combine evidence signals only to rank review; they do not prove why performance changed. "
        "Confirm decisions against approved SOPs, qualification/calibration status, raw evidence, QA requirements and the official system of record."
    )
    boundary_ar = (
        "هذا التقرير أداة لدعم القرار وليس سجلًا GxP معتمدًا ولا قرار إفراج ولا إثباتًا للسبب الجذري ولا يفرض أهداف KPI عامة. "
        "الأهداف يحددها المستخدم، ودرجة الأولوية تجمع إشارات الأدلة فقط لترتيب المراجعة ولا تثبت سبب تغير الأداء. "
        "يجب تأكيد القرارات بالرجوع إلى الإجراءات المعتمدة وحالة التأهيل والمعايرة والبيانات الخام ومتطلبات الجودة والسجل الرسمي المعتمد."
    )
    story.append(_p(boundary_ar if lang == "ar" else boundary_en, styles["body"], lang))
    story.append(Spacer(1, 5*mm))
    story.append(_p("DON'T GUESS. FOLLOW THE EVIDENCE.", styles["h1"], "en"))

    doc.build(story, onFirstPage=lambda c,d: _header(c,d,styles,selected_month,lang), onLaterPages=lambda c,d: _header(c,d,styles,selected_month,lang))
    buf.seek(0)
    return buf.getvalue()


# ------------------------------ Streamlit UI ---------------------------------
def render_executive_performance_report():
    st.divider()

    lang = _current_language()
    direction = "rtl" if lang == "ar" else "ltr"
    align = "right" if lang == "ar" else "left"

    st.markdown(
        f"""
<style>
.exec-v2-wrap{{direction:{direction};text-align:{align}}}
.exec-v2-hero{{border:1px solid #214458;border-radius:22px;padding:1rem 1.05rem;background:linear-gradient(135deg,#06121f,#0b2438);color:#dce9f0;margin:.45rem 0 1rem;box-shadow:0 10px 26px rgba(0,0,0,.10)}}
.exec-v2-hero b{{font-size:1.02rem;color:#fff}} .exec-v2-hero .gold{{color:#e1c56d;font-weight:850}}
.exec-v2-grid{{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:.6rem;margin:.6rem 0 1rem}}
.exec-v2-card{{border:1px solid #dce4ec;border-radius:17px;padding:.78rem;background:#fff;min-height:104px}}
.exec-v2-card span{{display:block;color:#64748b;font-size:.73rem}} .exec-v2-card b{{display:block;color:#0f2742;font-size:1.42rem;margin:.12rem 0}}
.exec-v2-card.red{{border-top:4px solid #d64545}} .exec-v2-card.gold{{border-top:4px solid #d4a92e}} .exec-v2-card.green{{border-top:4px solid #16a36f}} .exec-v2-card.blue{{border-top:4px solid #2876a7}}
.exec-comment{{border:1px solid #294b61;background:linear-gradient(135deg,#071522,#10293d);color:#e8f0f5;border-radius:18px;padding:.8rem 1rem;margin:.45rem 0}}
.exec-comment-title{{font-weight:850;color:#e1c56d;margin-bottom:.4rem}} .exec-comment ul{{margin:.25rem 0;padding-{ 'right' if lang == 'ar' else 'left' }:1.2rem}} .exec-comment li{{margin:.36rem 0;line-height:1.55}}
.exec-attn{{border:1px solid #dce4ec;border-{ 'right' if lang == 'ar' else 'left' }:5px solid #d4a92e;border-radius:15px;padding:.72rem .82rem;margin:.42rem 0;background:#fff}}
.exec-attn.red{{border-{ 'right' if lang == 'ar' else 'left' }-color:#d64545}} .exec-attn.blue{{border-{ 'right' if lang == 'ar' else 'left' }-color:#2876a7}}
.exec-attn b{{color:#0f2742}} .exec-attn span{{display:block;color:#64748b;font-size:.82rem;margin-top:.12rem;line-height:1.45}}
.exec-score{{display:inline-block;padding:.12rem .45rem;border-radius:999px;background:#eef2f7;color:#0f2742;font-size:.72rem;font-weight:800;margin-{ 'left' if lang == 'ar' else 'right' }:.35rem}}
@media(max-width:700px){{.exec-v2-grid{{grid-template-columns:1fr 1fr}}.exec-v2-card b{{font-size:1.22rem}}.exec-v2-card{{min-height:96px}}}}
</style>
<div class="exec-v2-wrap"><h2>🔥 {_t('title',lang)}</h2><div style="color:#7b8b9c;margin-top:-.35rem;margin-bottom:.75rem">{_t('subtitle',lang)}</div></div>
""",
        unsafe_allow_html=True,
    )

    instruments, inst_err, inst_ok = _db_list("instruments", EXEC_INSTRUMENT_SELECT, "instrument_code.asc")
    perf_rows, perf_err, perf_ok = _db_list("instrument_monthly_performance", EXEC_PERF_SELECT, "month_start.desc")
    events, _, events_ok = _db_list("instrument_events", "id,instrument_id,event_status,severity,event_type,event_date", "event_date.desc")
    calibrations, _, cal_ok = _db_list("calibration_records", "id,instrument_id,result,ooc_status,calibration_date", "calibration_date.desc")

    if not inst_ok or not perf_ok:
        st.warning("Executive Performance Intelligence needs the instrument and monthly-performance tables to be available.")
        st.caption(inst_err or perf_err or "Database access error")
        return
    if not instruments:
        st.info("Create or import Instrument Passports first.")
        return

    available_months = sorted({_month(r.get("month_start")) for r in perf_rows}, reverse=True)
    default_month = available_months[0] if available_months else date.today().replace(day=1)
    chosen = st.date_input(_t("month", lang), value=default_month, key="exec_v2_report_month")
    selected_month = _month(chosen)

    rows = _dataset(instruments, perf_rows, selected_month)
    p = _portfolio(rows)
    prev_rows = _dataset(instruments, perf_rows, _prev_month(selected_month))
    prev_p = _portfolio(prev_rows)
    open_events, open_ooc, _, _ = _open_quality_context(events if events_ok else [], calibrations if cal_ok else [])
    attention_rows = _attention(rows, events if events_ok else [], calibrations if cal_ok else [])
    missing = [r for r in rows if not r.get("recorded")]

    if p["coverage"] == 0:
        st.info(_t("no_data", lang))
        return

    st.markdown(
        f'<div class="exec-v2-hero exec-v2-wrap"><b>{_t("view",lang)}</b><br><span>{_t("view_desc",lang)}</span><br><span class="gold">DON\'T GUESS. FOLLOW THE EVIDENCE.</span></div>',
        unsafe_allow_html=True,
    )

    cards = [
        (_t("availability",lang), _pct(p["availability"]), "Weighted" if lang == "en" else "مرجحة بالساعات", "green" if p["availability"] is not None else "blue"),
        (_t("utilization",lang), _pct(p["utilization"]), "Weighted" if lang == "en" else "مرجحة بالساعات", "blue"),
        (_t("coverage",lang), f"{p['coverage']}/{len(instruments)}", f"Missing {len(missing)}" if lang == "en" else f"ناقص {len(missing)}", "gold" if missing else "green"),
        (_t("unplanned",lang), f"{p['unplanned']:.1f} h", "Portfolio loss" if lang == "en" else "فقد على مستوى المحفظة", "red" if p["unplanned"] > 0 else "green"),
        (_t("capacity_risk",lang), p["capacity_risk"], "High use + low availability" if lang == "en" else "استخدام مرتفع + إتاحة منخفضة", "red" if p["capacity_risk"] else "green"),
        (_t("below_avail",lang), p["below_avail"], "Targets" if lang == "en" else "الأهداف", "gold" if p["below_avail"] else "green"),
        (_t("below_util",lang), p["below_util"], "Targets" if lang == "en" else "الأهداف", "blue" if p["below_util"] else "green"),
        (_t("quality",lang), f"{len(open_events)} / {len(open_ooc)}", "Quality context" if lang == "en" else "سياق الجودة", "red" if open_events or open_ooc else "green"),
    ]
    html_cards = ''.join(f'<div class="exec-v2-card {tone}"><span>{xml_escape(str(label))}</span><b>{xml_escape(str(value))}</b><span>{xml_escape(str(note))}</span></div>' for label,value,note,tone in cards)
    st.markdown(f'<div class="exec-v2-grid exec-v2-wrap">{html_cards}</div>', unsafe_allow_html=True)

    commentary = _commentary(rows, p, prev_p if prev_p.get("coverage") else None, attention_rows, len(instruments), selected_month, lang)
    li = ''.join(f'<li>{xml_escape(x)}</li>' for x in commentary)
    st.markdown(f'<div class="exec-comment exec-v2-wrap"><div class="exec-comment-title">{_t("commentary",lang)}</div><ul>{li}</ul></div>', unsafe_allow_html=True)

    st.markdown(f'<div class="exec-v2-wrap"><h3>{_t("attention",lang)}</h3></div>', unsafe_allow_html=True)
    top_attention = [r for r in attention_rows if r.get("attention_score",0) > 0][:10]
    if not top_attention:
        st.success(_t("no_signal", lang))
    else:
        for r in top_attention:
            tone = "red" if r.get("attention_score",0) >= 8 else "blue" if r.get("signal") == "Capacity available" else ""
            reasons = " · ".join(AR_LABELS.get(x,x) if lang == "ar" else x for x in r.get("attention_reasons",[])[:5])
            st.markdown(
                f'<div class="exec-attn {tone} exec-v2-wrap"><b><span class="exec-score">{r.get("attention_score",0)}</span>{xml_escape(str(r.get("code")))} · {xml_escape(AR_LABELS.get(r.get("signal"),r.get("signal")) if lang=="ar" else str(r.get("signal")))}</b><span>{xml_escape(reasons)}</span><span>{_t("availability",lang)} {_pct(r.get("availability"))} · {_t("utilization",lang)} {_pct(r.get("utilization"))} · {_t("unplanned",lang)} {_num(r.get("unplanned"))} h</span></div>',
                unsafe_allow_html=True,
            )
    st.caption(_t("signal_note", lang))

    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"### 🔴 {_t('downtime',lang)}")
        top_unplanned = sorted(p["recorded"], key=lambda r: r.get("unplanned") or 0, reverse=True)[:5]
        st.dataframe(pd.DataFrame([{
            "Instrument": r.get("code"),
            ("Unplanned h" if lang=="en" else "توقف غير مخطط h"): round(r.get("unplanned") or 0,1),
            ("Availability %" if lang=="en" else "الإتاحة %"): None if r.get("availability") is None else round(r.get("availability"),1),
        } for r in top_unplanned]), use_container_width=True, hide_index=True)
    with c2:
        st.markdown(f"### 🔵 {_t('spare',lang)}")
        top_idle = sorted(p["recorded"], key=lambda r: r.get("idle") or 0, reverse=True)[:5]
        st.dataframe(pd.DataFrame([{
            "Instrument": r.get("code"),
            ("Idle available h" if lang=="en" else "ساعات متاحة غير مستغلة"): round(r.get("idle") or 0,1),
            ("Utilization %" if lang=="en" else "الاستخدام %"): None if r.get("utilization") is None else round(r.get("utilization"),1),
        } for r in top_idle]), use_container_width=True, hide_index=True)

    st.markdown(f"### 📉 {_t('trend',lang)}")
    trend = _trend(perf_rows, instruments, selected_month)
    trend_df = pd.DataFrame([{
        "Month": m.strftime("%Y-%m"),
        "Coverage": cov,
        "Availability %": None if av is None else round(av,1),
        "Utilization %": None if ut is None else round(ut,1),
        "Unplanned downtime h": round(unp,1),
    } for m,cov,av,ut,unp in trend]).set_index("Month")
    if not trend_df.empty:
        st.line_chart(trend_df[["Availability %","Utilization %"]])
        st.dataframe(trend_df.reset_index(), use_container_width=True, hide_index=True)

    if missing:
        with st.expander(f"⚠ {_t('missing',lang)} · {len(missing)}"):
            st.write(" · ".join(str(r.get("code")) for r in missing[:100]))
            st.caption("Missing data is shown as missing — never converted into zero performance." if lang=="en" else "البيانات المفقودة تظهر كمفقودة ولا يتم تحويلها إلى أداء صفري.")

    st.markdown(f"### 📄 {_t('pdf',lang)}")
    try:
        pdf_bytes = _build_pdf(instruments, perf_rows, events if events_ok else [], calibrations if cal_ok else [], selected_month, lang)
        file_name = f"Yahia_QC_Executive_Intelligence_{selected_month:%Y_%m}_{lang}.pdf"
        st.download_button(f"⬇️ {_t('download',lang)}", data=pdf_bytes, file_name=file_name, mime="application/pdf", use_container_width=True, key=f"exec_v2_pdf_{lang}")
        st.caption("Includes executive commentary, traffic-light attention ranking, KPI cards, six-month trend, downtime chart, target-gap portfolio table, methodology and evidence boundary." if lang=="en" else "يتضمن ملخصًا تنفيذيًا، وترتيب الأولويات، وبطاقات KPI، واتجاه 6 أشهر، ورسم التوقف، وجدول فجوات الأهداف، وطريقة الحساب وحدود استخدام الدليل.")
    except Exception as exc:
        st.error("Executive PDF could not be generated." if lang=="en" else "تعذر إنشاء التقرير التنفيذي PDF.")
        st.caption(f"Diagnostic: {type(exc).__name__}")
