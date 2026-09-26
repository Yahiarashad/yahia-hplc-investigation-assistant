import hashlib
import html
import json
import re
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

try:
    import arabic_reshaper
    from bidi.algorithm import get_display
except Exception:  # PDF still works for English if optional shaping is unavailable.
    arabic_reshaper = None
    get_display = None


NAVY = colors.HexColor("#071A2E")
NAVY_2 = colors.HexColor("#0B3154")
GOLD = colors.HexColor("#C9A54C")
PALE_GOLD = colors.HexColor("#FBF6E8")
PALE_BLUE = colors.HexColor("#F3F7FB")
TEXT = colors.HexColor("#182433")
MUTED = colors.HexColor("#5D6B7A")
BORDER = colors.HexColor("#D9E2EA")

_MACHINE_LINE_RE = re.compile(
    r"(?im)^\s*(?:INVESTIGATION_STATUS|EVIDENCE_STAGE)\s*:\s*[^\n]+\s*$"
)
_CONTRACT_LINE_RE = re.compile(r"(?im)^\s*(?:WHAT_NEXT|YOUR_TURN)\s*:\s*[^\n]*\s*$")
_EXPLANATION_HEADER_RE = re.compile(r"(?im)^\s*EXPLANATION\s*:\s*$")
_ARABIC_RE = re.compile(r"[\u0600-\u06FF]")


def _register_font():
    candidates = [
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
        Path("/usr/share/fonts/dejavu/DejaVuSansCondensed.ttf"),
        Path("/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf"),
    ]
    for path in candidates:
        if path.exists():
            try:
                pdfmetrics.registerFont(TTFont("YahiaUnicode", str(path)))
                return "YahiaUnicode"
            except Exception:
                continue
    return "Helvetica"


FONT_NAME = _register_font()


def _shape(text):
    value = str(text or "").replace("\x00", " ").strip()
    if not value:
        return ""
    if _ARABIC_RE.search(value) and arabic_reshaper and get_display and FONT_NAME != "Helvetica":
        try:
            return get_display(arabic_reshaper.reshape(value))
        except Exception:
            return value
    return value


def _paragraph(text, style):
    value = _shape(text)
    value = html.escape(value).replace("\n", "<br/>")
    return Paragraph(value or "—", style)


def _clean_assistant_text(text):
    value = text or ""
    value = _MACHINE_LINE_RE.sub("", value)
    value = _CONTRACT_LINE_RE.sub("", value)
    value = _EXPLANATION_HEADER_RE.sub("", value)
    return re.sub(r"\n{3,}", "\n\n", value).strip()


def _extract_machine_value(text, key, default=""):
    match = re.search(rf"(?im)^\s*{re.escape(key)}\s*:\s*([^\n]+)", text or "")
    return match.group(1).strip() if match else default


def _canonical_payload(case_id, app_version, category, messages, status, evidence_stage):
    return {
        "case_id": case_id,
        "app_version": app_version,
        "category": category,
        "status": status,
        "evidence_stage": evidence_stage,
        "messages": [
            {"role": m.get("role", ""), "content": m.get("content", "")}
            for m in messages
        ],
    }


def report_fingerprint(case_id, app_version, category, messages, status, evidence_stage):
    payload = _canonical_payload(case_id, app_version, category, messages, status, evidence_stage)
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest().upper()


def build_investigation_pdf(
    *,
    case_id,
    app_version,
    category,
    messages,
    status,
    evidence_stage,
):
    """Return (pdf_bytes, report_id, report_status).

    The PDF is a documentation-ready decision-support record, not a substitute for
    the laboratory's validated GMP investigation system, approved SOP, or QA record.
    """
    fingerprint = report_fingerprint(case_id, app_version, category, messages, status, evidence_stage)
    report_id = f"HPLC-{fingerprint[:10]}"
    report_status = "FINAL" if status in {"PROBABLE", "CONFIRMED"} else "INTERIM / DRAFT"
    generated = datetime.now(timezone.utc).strftime("%d-%b-%Y %H:%M UTC")

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "YahiaTitle", parent=styles["Title"], fontName=FONT_NAME, fontSize=18,
        leading=22, textColor=colors.white, alignment=TA_LEFT, spaceAfter=4,
    )
    subtitle_style = ParagraphStyle(
        "YahiaSubtitle", parent=styles["Normal"], fontName=FONT_NAME, fontSize=8.5,
        leading=11, textColor=colors.HexColor("#D9E6F2"), alignment=TA_LEFT,
    )
    h1 = ParagraphStyle(
        "YahiaH1", parent=styles["Heading1"], fontName=FONT_NAME, fontSize=12.5,
        leading=15, textColor=NAVY, spaceBefore=9, spaceAfter=6,
    )
    body = ParagraphStyle(
        "YahiaBody", parent=styles["BodyText"], fontName=FONT_NAME, fontSize=9.3,
        leading=13.2, textColor=TEXT, spaceAfter=5,
    )
    body_right = ParagraphStyle(
        "YahiaBodyRight", parent=body, alignment=TA_RIGHT,
    )
    small = ParagraphStyle(
        "YahiaSmall", parent=body, fontSize=7.6, leading=10.2, textColor=MUTED,
    )
    label = ParagraphStyle(
        "YahiaLabel", parent=body, fontSize=8.2, leading=10.5, textColor=MUTED,
    )

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=16 * mm,
        rightMargin=16 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
        title=f"Yahia QC HPLC Investigation Report {case_id}",
        author="Yahia QC",
        subject="Evidence-first HPLC investigation decision-support record",
    )

    def _footer(canvas, document):
        canvas.saveState()
        width, _ = A4
        canvas.setStrokeColor(BORDER)
        canvas.setLineWidth(0.4)
        canvas.line(16 * mm, 12 * mm, width - 16 * mm, 12 * mm)
        canvas.setFont(FONT_NAME, 7)
        canvas.setFillColor(MUTED)
        canvas.drawString(16 * mm, 7.5 * mm, f"Case {case_id}  |  {report_status}  |  {report_id}")
        page_label = f"Page {canvas.getPageNumber()}"
        canvas.drawRightString(width - 16 * mm, 7.5 * mm, page_label)
        canvas.restoreState()

    story = []

    header = Table(
        [[
            Paragraph("YAHIA QC", title_style),
            Paragraph("HPLC INVESTIGATION REPORT<br/><font size='8'>DON'T GUESS. FOLLOW THE EVIDENCE.</font>", title_style),
        ]],
        colWidths=[45 * mm, 118 * mm],
    )
    header.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), NAVY),
        ("BOX", (0, 0), (-1, -1), 0.6, GOLD),
        ("INNERGRID", (0, 0), (-1, -1), 0, NAVY),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 9),
        ("RIGHTPADDING", (0, 0), (-1, -1), 9),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
    ]))
    story.extend([header, Spacer(1, 8)])

    metadata = [
        ["Case ID", case_id, "Report", report_status],
        ["Category", category or "Auto-detected / Unclassified", "App version", app_version],
        ["Investigation status", status or "INVESTIGATING", "Evidence stage", evidence_stage or "OBSERVED"],
        ["Generated", generated, "Report ID", report_id],
    ]
    meta_table = Table(
        [[_paragraph(cell, label if c % 2 == 0 else body) for c, cell in enumerate(row)] for row in metadata],
        colWidths=[31 * mm, 52 * mm, 31 * mm, 52 * mm],
    )
    meta_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), PALE_BLUE),
        ("BOX", (0, 0), (-1, -1), 0.5, BORDER),
        ("INNERGRID", (0, 0), (-1, -1), 0.35, BORDER),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.extend([meta_table, Spacer(1, 8)])

    first_user = next((m.get("content", "") for m in messages if m.get("role") == "user"), "")
    last_assistant_raw = next((m.get("content", "") for m in reversed(messages) if m.get("role") == "assistant"), "")
    last_assistant = _clean_assistant_text(last_assistant_raw)
    what_next = _extract_machine_value(last_assistant_raw, "WHAT_NEXT", "")
    your_turn = _extract_machine_value(last_assistant_raw, "YOUR_TURN", "")

    story.append(_paragraph("Initial case statement", h1))
    story.append(_paragraph(first_user or "No initial user statement was available.", body_right if _ARABIC_RE.search(first_user or "") else body))

    story.append(_paragraph("Current investigation snapshot", h1))
    snapshot_rows = [
        ["Evidence stage", evidence_stage or "OBSERVED"],
        ["What next", what_next or "No explicit next action recorded."],
        ["User action requested", your_turn or "None recorded."],
    ]
    snapshot = Table(
        [[_paragraph(r[0], label), _paragraph(r[1], body_right if _ARABIC_RE.search(r[1]) else body)] for r in snapshot_rows],
        colWidths=[42 * mm, 124 * mm],
    )
    snapshot.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), PALE_GOLD),
        ("BOX", (0, 0), (-1, -1), 0.6, GOLD),
        ("INNERGRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#E7D9A9")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.extend([snapshot, Spacer(1, 4)])

    story.append(_paragraph("Current conclusion / explanation", h1))
    story.append(_paragraph(last_assistant or "No assistant conclusion has been recorded yet.", body_right if _ARABIC_RE.search(last_assistant or "") else body))

    story.append(PageBreak())
    story.append(_paragraph("Investigation timeline", h1))
    story.append(_paragraph(
        "This timeline preserves the submitted observations and the assistant's documented decision-support responses in sequence. User-entered facts remain distinct from assistant interpretation.",
        small,
    ))

    for idx, message in enumerate(messages, start=1):
        role = (message.get("role") or "unknown").upper()
        raw = message.get("content", "")
        content = _clean_assistant_text(raw) if role == "ASSISTANT" else raw
        if not content.strip():
            continue
        role_label = "USER / REPORTED EVIDENCE" if role == "USER" else "ASSISTANT / INVESTIGATION DECISION SUPPORT"
        block = [
            _paragraph(f"Step {idx} · {role_label}", label),
            _paragraph(content, body_right if _ARABIC_RE.search(content) else body),
        ]
        story.append(KeepTogether(block))
        story.append(Spacer(1, 5))

    story.extend([
        Spacer(1, 6),
        _paragraph("Record integrity", h1),
        _paragraph(f"SHA-256 fingerprint: {fingerprint}", small),
        _paragraph(
            "Any change to the case content, status, evidence stage, application version, or recorded messages will produce a different fingerprint.",
            small,
        ),
        Spacer(1, 6),
        _paragraph("Documentation notice", h1),
        _paragraph(
            "This PDF is a decision-support record generated from information entered during the investigation. It does not by itself constitute a validated GMP electronic record, QA approval, electronic signature, or replacement for the laboratory's approved SOPs and formal quality system.",
            small,
        ),
    ])

    doc.build(story, onFirstPage=_footer, onLaterPages=_footer)
    return buffer.getvalue(), report_id, report_status
