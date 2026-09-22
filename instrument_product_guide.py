from __future__ import annotations

from io import BytesIO
from pathlib import Path
from xml.sax.saxutils import escape as xml_escape

import streamlit as st

try:
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_RIGHT, TA_CENTER
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import mm
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
except Exception:
    colors = None

try:
    import arabic_reshaper
    from bidi.algorithm import get_display as bidi_get_display
except Exception:
    arabic_reshaper = None
    bidi_get_display = None


PRODUCT_NAME = "Yahia QC Instrument Intelligence™"
PRODUCT_TAGLINE = "From instrument data to evidence-based decisions."
PRODUCT_PROMISE = "ENTER LESS. DECIDE BETTER. KEEP THE INSTRUMENT STORY CONNECTED."
PRODUCT_CTA = "STOP MANAGING INSTRUMENT DATA. START MANAGING INSTRUMENT DECISIONS."


def _contains_arabic(text: str) -> bool:
    return any("\u0600" <= ch <= "\u06ff" or "\u0750" <= ch <= "\u077f" or "\u08a0" <= ch <= "\u08ff" for ch in str(text or ""))


def _shape_arabic(value) -> str:
    text = str(value or "")
    if not text or not _contains_arabic(text):
        return text
    if arabic_reshaper is None or bidi_get_display is None:
        return text
    try:
        return bidi_get_display(arabic_reshaper.reshape(text))
    except Exception:
        return text


def _font_paths():
    candidates = []
    try:
        import matplotlib
        root = Path(matplotlib.get_data_path()) / "fonts" / "ttf"
        candidates.append((root / "DejaVuSans.ttf", root / "DejaVuSans-Bold.ttf"))
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
            pass
    return None, None


def _register_fonts():
    if colors is None:
        return "Helvetica", "Helvetica-Bold", False
    regular, bold = _font_paths()
    if regular and bold:
        try:
            if "YQII" not in pdfmetrics.getRegisteredFontNames():
                pdfmetrics.registerFont(TTFont("YQII", regular))
            if "YQIIB" not in pdfmetrics.getRegisteredFontNames():
                pdfmetrics.registerFont(TTFont("YQIIB", bold))
            return "YQII", "YQIIB", True
        except Exception:
            pass
    return "Helvetica", "Helvetica-Bold", False


def _pdf_styles():
    regular, bold, arabic_ok = _register_fonts()
    base = getSampleStyleSheet()
    navy = colors.HexColor("#102A45")
    gold = colors.HexColor("#C6A15B")
    ink = colors.HexColor("#26384A")
    muted = colors.HexColor("#607286")
    styles = {
        "title": ParagraphStyle("title", parent=base["Title"], fontName=bold, fontSize=25, leading=30, textColor=navy, spaceAfter=8),
        "subtitle": ParagraphStyle("subtitle", parent=base["BodyText"], fontName=regular, fontSize=12, leading=18, textColor=muted, spaceAfter=10),
        "h1": ParagraphStyle("h1", parent=base["Heading1"], fontName=bold, fontSize=18, leading=22, textColor=navy, spaceBefore=5, spaceAfter=8),
        "h2": ParagraphStyle("h2", parent=base["Heading2"], fontName=bold, fontSize=11.5, leading=15, textColor=gold, spaceBefore=5, spaceAfter=5),
        "body": ParagraphStyle("body", parent=base["BodyText"], fontName=regular, fontSize=9.2, leading=14, textColor=ink, spaceAfter=7),
        "small": ParagraphStyle("small", parent=base["BodyText"], fontName=regular, fontSize=7.7, leading=11, textColor=muted, spaceAfter=5),
        "quote": ParagraphStyle("quote", parent=base["BodyText"], fontName=bold, fontSize=13, leading=18, textColor=navy, spaceBefore=7, spaceAfter=7),
        "ar": ParagraphStyle("ar", parent=base["BodyText"], fontName=regular, fontSize=9.4, leading=15, alignment=TA_RIGHT, textColor=ink, spaceAfter=8),
        "center": ParagraphStyle("center", parent=base["BodyText"], fontName=bold, fontSize=10, leading=14, alignment=TA_CENTER, textColor=navy),
    }
    return styles, arabic_ok


def _en(text: str, style):
    return Paragraph(xml_escape(str(text)).replace("\n", "<br/>"), style)


def _ar(text: str, style):
    return Paragraph(xml_escape(_shape_arabic(str(text))).replace("\n", "<br/>"), style)


def _bullet_table(items, styles, col_width=162*mm):
    rows = [[_en("• " + item, styles["body"])] for item in items]
    t = Table(rows, colWidths=[col_width])
    t.setStyle(TableStyle([
        ("LEFTPADDING", (0,0), (-1,-1), 4), ("RIGHTPADDING", (0,0), (-1,-1), 4),
        ("TOPPADDING", (0,0), (-1,-1), 2), ("BOTTOMPADDING", (0,0), (-1,-1), 2),
    ]))
    return t


def _section_page(story, styles, number, title, english, arabic=None, bullets=None, callout=None):
    story.append(_en(f"{number}. {title}", styles["h1"]))
    story.append(_en(english, styles["body"]))
    if bullets:
        story.append(_bullet_table(bullets, styles))
    if callout:
        box = Table([[_en(callout, styles["quote"])]], colWidths=[162*mm])
        box.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,-1), colors.HexColor("#F8F3E8")),
            ("BOX", (0,0), (-1,-1), 0.7, colors.HexColor("#C6A15B")),
            ("LEFTPADDING", (0,0), (-1,-1), 10), ("RIGHTPADDING", (0,0), (-1,-1), 10),
            ("TOPPADDING", (0,0), (-1,-1), 8), ("BOTTOMPADDING", (0,0), (-1,-1), 8),
        ]))
        story.extend([Spacer(1, 3*mm), box])
    if arabic:
        story.extend([Spacer(1, 3*mm), _ar(arabic, styles["ar"])])
    story.append(PageBreak())


@st.cache_data(show_spinner=False)
def build_product_user_guide_pdf() -> bytes:
    if colors is None:
        return b""
    styles, _ = _pdf_styles()
    out = BytesIO()
    doc = SimpleDocTemplate(
        out, pagesize=A4, leftMargin=16*mm, rightMargin=16*mm, topMargin=16*mm, bottomMargin=17*mm,
        title=f"{PRODUCT_NAME} - Product & User Guide", author="Yahia QC Instrument Intelligence",
        subject="Pharmaceutical QC instrument lifecycle, evidence, operations and management intelligence",
    )
    story = []

    story.extend([
        Spacer(1, 22*mm), _en("YAHIA QC", styles["h2"]), _en("INSTRUMENT INTELLIGENCE", styles["title"]),
        _en(PRODUCT_TAGLINE, styles["subtitle"]), Spacer(1, 7*mm), _en("PRODUCT • USER • MANAGEMENT GUIDE", styles["quote"]),
        Spacer(1, 10*mm), _en(PRODUCT_PROMISE, styles["quote"]), Spacer(1, 8*mm),
        _ar("من بيانات الأجهزة المتفرقة إلى دليل مترابط يساعد فريق الجودة على رؤية ما يحتاج الانتباه واتخاذ قرار أكثر انضباطًا.", styles["ar"]),
        Spacer(1, 18*mm), _en("DON'T GUESS. FOLLOW THE EVIDENCE.", styles["center"]), PageBreak(),
    ])

    _section_page(story, styles, "01", "The Executive Promise",
        "The platform is designed around one practical idea: an instrument should not have ten disconnected stories. Identity, acquisition, qualification, control, events, investigation, performance and evidence should remain connected around the same asset.",
        "الفكرة الأساسية: الجهاز لا ينبغي أن تكون له قصص منفصلة في ملفات مختلفة. هويته، شراؤه، تأهيله، معايرته، صيانته، أحداثه وتحقيقاته وأداؤه يجب أن تبقى مترابطة حول نفس الأصل.",
        ["Move from fragmented tracking to a connected instrument story.", "Move from passive records to attention and decision signals.", "Move from memory-driven troubleshooting to evidence-first investigation.", "Move from isolated personal tracking toward governed organization workspaces."],
        PRODUCT_CTA)

    _section_page(story, styles, "02", "The Problem We Are Solving",
        "Pharmaceutical QC laboratories often have enough data, but the data lives in different places. Excel trackers, calibration schedules, maintenance reports, qualification files, deviations, analyst notes and management summaries can describe the same instrument without forming one operational picture.",
        "المشكلة ليست دائمًا نقص البيانات؛ المشكلة أن البيانات متفرقة. عندما يحتاج الفريق قرارًا، يبدأ البحث في أكثر من ملف وأكثر من شخص بدل أن تبدأ القصة من جهاز واحد ودليل واحد مترابط.",
        ["Due dates can be visible without explaining operational risk.", "A repeated event can look new because previous evidence is hard to find.", "Management can see counts but still miss capacity, downtime and recurring burden.", "Investigations can start with assumptions because the historical context is fragmented."])

    story.append(_en("03. Before vs. After", styles["h1"]))
    data = [
        [_en("BEFORE", styles["center"]), _en("WITH QC INSTRUMENT INTELLIGENCE", styles["center"])],
        [_en("Multiple trackers", styles["body"]), _en("One connected instrument story", styles["body"])],
        [_en("Manual follow-up", styles["body"]), _en("Attention queues and due-control visibility", styles["body"])],
        [_en("Knowledge in individual memory", styles["body"]), _en("Traceable history around the asset", styles["body"])],
        [_en("Reactive troubleshooting", styles["body"]), _en("Observed / Inferred / Unknown discipline", styles["body"])],
        [_en("Operational data only", styles["body"]), _en("Performance and management intelligence", styles["body"])],
        [_en("User-by-user setup", styles["body"]), _en("Workspace, membership, role and admin foundation", styles["body"])],
    ]
    t = Table(data, colWidths=[81*mm, 81*mm], repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#102A45")), ("TEXTCOLOR", (0,0), (-1,0), colors.white),
        ("GRID", (0,0), (-1,-1), 0.4, colors.HexColor("#D8E0E8")),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, colors.HexColor("#F7F9FB")]),
        ("VALIGN", (0,0), (-1,-1), "TOP"), ("LEFTPADDING", (0,0), (-1,-1), 7),
        ("RIGHTPADDING", (0,0), (-1,-1), 7), ("TOPPADDING", (0,0), (-1,-1), 7), ("BOTTOMPADDING", (0,0), (-1,-1), 7),
    ]))
    story.extend([t, Spacer(1, 5*mm), _ar("القيمة ليست في إضافة شاشة جديدة؛ القيمة في تقليل المسافة بين الإشارة والدليل والقرار.", styles["ar"]), PageBreak()])

    _section_page(story, styles, "04", "How the Platform Thinks",
        "The operating loop is intentionally simple and repeatable. The product should help the team detect what matters, prioritize attention, investigate with evidence, act in a controlled way and preserve what was learned for the next event.",
        "المنصة مبنية على دورة قرار واضحة؛ كل خطوة يجب أن تقلل مساحة التخمين وتزيد وضوح الدليل.",
        callout="DETECT → PRIORITIZE → INVESTIGATE → DECIDE → ACT → VERIFY → DOCUMENT → LEARN")

    _section_page(story, styles, "05", "Instrument Passport",
        "Every instrument starts with a durable digital identity. Instrument ID, type, manufacturer, model, serial number, location, responsible team, operational status and key due dates form the anchor for every later lifecycle and investigation record.",
        "جواز الجهاز هو نقطة البداية. عندما تكون الهوية ثابتة، يصبح من الممكن ربط بقية التاريخ بنفس الأصل بدل أن تتوزع القصة بين أسماء وأكواد مختلفة.",
        ["Identity", "Operational status", "Responsible team", "Qualification / PM / calibration due dates", "Notes and traceability context"])

    _section_page(story, styles, "06", "Full Lifecycle Visibility",
        "The lifecycle view follows the instrument from the first laboratory need through acquisition, qualification, controlled release, routine use, performance review and retirement. Missing evidence remains visible instead of being silently assumed.",
        "دورة الحياة لا تبدأ عند تشغيل الجهاز. تبدأ من الاحتياج وتمتد حتى التكهين مع إبقاء الأدلة الناقصة ظاهرة بدل تحويلها إلى افتراضات.",
        ["Need / Initiation", "URS", "Quotation", "PR", "PO", "Receiving", "Installation", "IQ / OQ / PQ", "Release / Issuance", "First approved routine run", "Routine control", "Performance review", "Retirement"])

    _section_page(story, styles, "07", "Routine Control: Calibration, PM and Qualification",
        "Routine control records are kept around the same instrument so due work, maintenance context and qualification status can be reviewed without rebuilding the history from separate trackers.",
        "الهدف هو أن يصبح تاريخ التحكم الدوري جزءًا من ذاكرة الجهاز نفسها، وليس ملفًا منفصلًا يحتاج الفريق للبحث عنه كل مرة.",
        ["Calibration control", "Preventive maintenance", "Qualification / requalification", "Maintenance history", "Component context"])

    _section_page(story, styles, "08", "Events: Record the Fact Before the Theory",
        "An event starts with what was actually observed: date, type, severity, subsystem, status and objective facts. The system encourages users to avoid recording a suspected mechanism as if it were a confirmed failure.",
        "في بداية الحدث نسجل ما حدث فعليًا. مثال: Pressure fluctuation حقيقة مرصودة؛ Pump failure تفسير يحتاج دليلًا.",
        callout="Observed fact first. Interpretation second. Confirmation before conclusion.")

    _section_page(story, styles, "09", "Investigation Intelligence",
        "Investigation Intelligence organizes the problem into Expected, Actual/Observed, Changed, Unchanged and Objective Evidence. It separates Observed / Inferred / Unknown and supports choosing the next evidence action instead of jumping to a root cause.",
        "قوة التحقيق ليست في سرعة كتابة Root Cause؛ قوتها في تقليل الاحتمالات بخطوات تمييزية وتحويل المعلومة من Unknown إلى Evidence ثم إلى قرار يمكن الدفاع عنه.",
        ["Expected behavior and acceptance criteria", "Actual / observed behavior", "What changed recently", "What remained unchanged", "Objective evidence and instrument history", "Next controlled evidence action"],
        "A repeated pattern strengthens a hypothesis. It does not independently prove root cause.")

    _section_page(story, styles, "10", "Performance Intelligence",
        "Monthly performance connects scheduled service hours, planned downtime, unplanned downtime and productive run time. Availability and utilization are calculated with visible methodology so management can discuss capacity and burden using the same definitions.",
        "الأداء لا يختصر في رقم واحد. المنصة تربط وقت التشغيل المخطط والتوقف المخطط وغير المخطط والتشغيل المنتج لتوضيح أين توجد السعة وأين يوجد العبء.",
        ["Availability", "Utilization", "Planned vs. unplanned downtime", "Target comparison", "Portfolio-level weighted view", "Management commentary"])

    _section_page(story, styles, "11", "Management and Executive View",
        "The management layer is built to convert operational records into attention. It highlights what deserves review rather than asking managers to open every asset individually.",
        "الإدارة لا تحتاج مزيدًا من الجداول؛ تحتاج أن تعرف أين تنظر ولماذا. لذلك الهدف هو تحويل البيانات التشغيلية إلى أولويات يمكن مناقشتها واتخاذ قرار بشأنها.",
        ["Portfolio status", "Due-control attention", "Performance trend", "Downtime burden", "Capacity signals", "Executive PDF reporting"])

    _section_page(story, styles, "12", "Organization Workspace Foundation",
        "The platform now includes a multi-tenant workspace foundation: personal and organization workspaces, workspace memberships, job roles, access roles, admin status, permission matrices and access-audit records.",
        "تم بناء أساس Workspaces للمؤسسات مع العضويات والأدوار والصلاحيات وسجل تغييرات الوصول. هذا هو الأساس الذي يسمح بتحويل المنتج من استخدام فردي إلى تشغيل مؤسسي منظم.",
        ["Personal Workspace for individual use", "Organization Workspace foundation for customer deployment", "Workspace membership and account status", "Job role + access role separation", "Admin flag + permission matrix", "Access audit trail"],
        "Release boundary: workspace-wide business-table permission enforcement is being activated in phases. Existing conservative owner-level RLS remains in place until the cutover is complete.")

    _section_page(story, styles, "13", "Admin Control Center",
        "Organization administrators can manage members in the active workspace, assign job roles, activate/suspend accounts and configure module-level privileges such as View, Add, Edit, Delete and Approve. Changes require a reason and are written to the access audit trail.",
        "الـAdmin داخل المؤسسة لا يدير المحتوى فقط؛ يدير من يستطيع أن يرى أو يضيف أو يعدل أو يحذف أو يعتمد، مع تسجيل سبب التغيير في Audit Trail.",
        ["Add / invite users by email", "Role presets", "Privilege matrix", "Admin designation", "Account status", "Reason for change", "Access audit trail"])

    _section_page(story, styles, "14", "Secure Invitation Flow",
        "User invitation is handled through a server-side Supabase Edge Function. The function validates the signed-in caller, verifies workspace-admin authority and uses service-role capability only on the server side before adding or inviting the member.",
        "دعوة المستخدم لا تعتمد على زر مخفي فقط؛ يتم التحقق من صلاحية الـAdmin على الخادم قبل إضافة العضو أو إرسال الدعوة.",
        callout="Security is a backend responsibility, not a UI decoration.")

    _section_page(story, styles, "15", "Excel Migration Without Blind Mapping",
        "For teams moving from existing trackers, the application provides an exact Excel template. It recognizes only approved column names, previews recognized and ignored columns, checks required fields and duplicates, and supports create-only or update-and-create modes.",
        "الانتقال من Excel لا يجب أن يبدأ بتخمين الأعمدة. القالب دقيق، والحقول غير المعروفة لا يتم ربطها بصمت، والخلايا الفارغة لا تتحول إلى بيانات مخترعة.",
        ["Download exact template", "Validate headers", "Preview before import", "Detect duplicate IDs", "Create or update modes", "No silent mapping"])

    _section_page(story, styles, "16", "Camera-Assisted Instrument Entry",
        "New instrument entry supports camera/image capture to reduce transcription errors when recording instrument identity details such as manufacturer, model and serial number. Human review remains part of the workflow.",
        "استخدام الكاميرا هدفه تقليل أخطاء النقل في بيانات الهوية، وليس تحويل القراءة الآلية إلى حقيقة غير مراجعة.",
        callout="Capture faster. Review before saving.")

    _section_page(story, styles, "17", "One HPLC. One Complete Story.",
        "Imagine HPLC-001 shows a pressure fluctuation. The user does not start with a guess. The Passport confirms the asset. Routine Control shows recent PM and component context. Events records the pressure behavior as observed evidence. Investigation Intelligence compares what changed and what remained stable. The next controlled test is documented. The verified outcome remains attached to the instrument story and later contributes to performance and management review.",
        "في سيناريو HPLC حقيقي، القوة ليست في أن يقول النظام السبب بسرعة. القوة في أن الفريق لا يبدأ التحقيق من الصفر، وأن كل خطوة تترك أثرًا يمكن الرجوع إليه في الحدث القادم.",
        callout="Signal → History → Evidence → Controlled Test → Verification → Learning")

    _section_page(story, styles, "18", "Value by Role",
        "The same evidence should answer different questions for different responsibilities. Role-aware navigation keeps the product focused on the decision each user is expected to make.",
        "نفس البيانات يمكن أن تخدم المحلل والمشرف والمدير ومدير القطاع، لكن كل مستوى يحتاج سؤالًا مختلفًا وإشارة مختلفة.",
        ["QC Analyst: What needs action today?", "QC Supervisor: What is restricted, overdue or still open?", "QC Manager: Where are performance, capacity and compliance pressures?", "QC Director / Head: Where is business risk and asset burden increasing?", "Calibration / Maintenance: What control activity is due and what history matters?", "QA / Reviewer: Is the evidence traceable and is inference clearly separated from fact?"])

    _section_page(story, styles, "19", "GMP, Data Integrity and Evidence Boundary",
        "The product is decision-support software and is not currently presented as a validated GxP system of record. Official GMP records, raw data, deviations, CAPA, certificates and approvals remain in the organization's approved systems. The platform should never invent missing evidence or convert inference into fact.",
        "المنصة أداة لدعم القرار حاليًا وليست بديلًا عن السجلات الرسمية المعتمدة. إذا لم يوجد دليل، يجب أن تبقى المعلومة Unknown بدل أن تتحول إلى افتراض.",
        ["Official records stay in approved systems", "Missing evidence stays visible", "Inference is labeled", "Health / lifecycle signals do not equal release decisions", "Auditability is strengthened, not replaced"],
        "DON'T GUESS. FOLLOW THE EVIDENCE.")

    story.extend([
        _en("20. Why This Product Can Matter to a QC Organization", styles["h1"]),
        _en("A laboratory does not need another place to type data. It needs a practical operating layer that keeps the instrument story connected, makes missing evidence visible, reduces avoidable searching and helps every level see the decisions that require attention.", styles["body"]),
        Spacer(1, 7*mm), _en(PRODUCT_PROMISE, styles["quote"]), Spacer(1, 7*mm), _en(PRODUCT_CTA, styles["quote"]), Spacer(1, 10*mm),
        _ar("الهدف النهائي: أن يتحول تاريخ الجهاز من ملفات متفرقة إلى ذاكرة تشغيلية تساعد الفريق على اتخاذ قرار أكثر وضوحًا وقابلية للدفاع.", styles["ar"]),
        Spacer(1, 12*mm), _en("Yahia QC Instrument Intelligence™", styles["center"]),
        _en("Pharmaceutical QC instrument lifecycle, evidence and operations intelligence.", styles["small"]),
    ])

    def footer(canvas, doc_obj):
        canvas.saveState()
        navy = colors.HexColor("#102A45")
        gold = colors.HexColor("#C6A15B")
        canvas.setStrokeColor(gold); canvas.setLineWidth(0.6); canvas.line(16*mm, 12*mm, 194*mm, 12*mm)
        canvas.setFillColor(navy); canvas.setFont(_register_fonts()[0], 7)
        canvas.drawString(16*mm, 8*mm, "Yahia QC Instrument Intelligence - Product & User Guide")
        canvas.drawRightString(194*mm, 8*mm, f"Page {doc_obj.page}")
        canvas.restoreState()

    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    out.seek(0)
    return out.getvalue()


def render_product_guide_hub():
    st.markdown(
        """
<style>
.yqii-hero{border:1px solid #d9e1e9;border-radius:22px;padding:1.15rem 1.2rem;margin:.25rem 0 1rem;background:linear-gradient(135deg,#0b1d31 0%,#102a45 64%,#173b60 100%);box-shadow:0 12px 32px rgba(15,39,66,.16)}
.yqii-kicker{color:#d7bd7a;font-weight:800;font-size:.78rem;letter-spacing:.08em;text-transform:uppercase}.yqii-title{color:#fff;font-weight:900;font-size:1.52rem;line-height:1.2;margin:.25rem 0 .35rem}.yqii-sub{color:#dbe7f2;line-height:1.6;font-size:.95rem}.yqii-promise{margin-top:.85rem;padding:.7rem .8rem;border:1px solid rgba(215,189,122,.5);border-radius:14px;color:#fff;font-weight:800;background:rgba(255,255,255,.04)}
.yqii-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:.65rem;margin:.75rem 0}.yqii-card{border:1px solid #dce4ec;border-radius:15px;padding:.75rem;background:#fff;box-shadow:0 5px 16px rgba(15,39,66,.045)}.yqii-card b{color:#102a45}.yqii-card span{display:block;color:#64748b;font-size:.83rem;line-height:1.55;margin-top:.2rem}.yqii-flow{border:1px solid #eadfca;background:#fffaf0;border-radius:15px;padding:.78rem .85rem;font-weight:800;color:#102a45;line-height:1.75;margin:.65rem 0}.yqii-boundary{border-right:4px solid #c6a15b;background:#f8fafc;border-radius:12px;padding:.7rem .8rem;direction:rtl;text-align:right;line-height:1.75;color:#44566a}
@media(max-width:760px){.yqii-grid{grid-template-columns:1fr}.yqii-title{font-size:1.25rem}.yqii-hero{padding:.95rem}}
</style>
<div class="yqii-hero"><div class="yqii-kicker">Product • User • Management Guide</div><div class="yqii-title">Yahia QC Instrument Intelligence™</div><div class="yqii-sub">From Instrument Data to Evidence-Based Decisions.<br>منصة تربط قصة الجهاز من الهوية ودورة الحياة إلى التحقيق والأداء والإدارة — مع إبقاء الدليل منفصلًا عن الافتراض.</div><div class="yqii-promise">ENTER LESS. DECIDE BETTER. KEEP THE INSTRUMENT STORY CONNECTED.</div></div>
<div class="yqii-grid">
 <div class="yqii-card"><b>Connected Instrument Story</b><span>Passport + Lifecycle + Control + Events + Investigation + Performance + Evidence.</span></div>
 <div class="yqii-card"><b>Evidence-First Investigation</b><span>Observed / Inferred / Unknown + next controlled evidence action.</span></div>
 <div class="yqii-card"><b>Management Intelligence</b><span>Availability, utilization, downtime, due control, capacity and executive reporting.</span></div>
 <div class="yqii-card"><b>Organization Foundation</b><span>Workspaces, members, job roles, access roles, admin privileges and access audit.</span></div>
 <div class="yqii-card"><b>Controlled Migration</b><span>Exact Excel template, validation, preview, duplicate control and no blind mapping.</span></div>
 <div class="yqii-card"><b>Decision-Support Boundary</b><span>Missing evidence stays visible; inference is never silently promoted to fact.</span></div>
</div>
<div class="yqii-flow">DETECT → PRIORITIZE → INVESTIGATE → DECIDE → ACT → VERIFY → DOCUMENT → LEARN</div>
<div class="yqii-boundary"><b>حدود الإصدار الحالي:</b> بنية الـWorkspace والعضويات والصلاحيات والإدارة موجودة. تفعيل الصلاحيات على مستوى جميع جداول بيانات الأجهزة يتم على مراحل، ولذلك يستمر حاليًا نموذج RLS المحافظ على مستوى المالك إلى أن تكتمل عملية الانتقال.</div>
""", unsafe_allow_html=True)
    pdf_bytes = build_product_user_guide_pdf()
    c1, c2 = st.columns([1, 1])
    with c1:
        st.download_button("⬇️ Download Premium Product & User Guide (PDF)", data=pdf_bytes,
            file_name="Yahia_QC_Instrument_Intelligence_Product_User_Guide.pdf", mime="application/pdf",
            use_container_width=True, key="yqii_download_product_guide", disabled=not bool(pdf_bytes))
    with c2:
        st.info("21-page bilingual executive guide • No customer instrument data is embedded")
    with st.expander("💼 Why this matters to a QC organization", expanded=False):
        st.markdown("""
**Before:** scattered trackers, manual follow-up, repeated searching, knowledge held by individuals, investigations that can restart from zero.

**With the platform:** one connected instrument story, visible missing evidence, role-aware attention, controlled admin structure, performance intelligence and a reusable investigation history.

> **STOP MANAGING INSTRUMENT DATA. START MANAGING INSTRUMENT DECISIONS.**
""")
