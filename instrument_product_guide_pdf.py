from __future__ import annotations

from io import BytesIO
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Flowable, Image as RLImage

import arabic_reshaper
from bidi.algorithm import get_display
from instrument_guide_visuals import guide_visual_bytes

NAVY = colors.HexColor('#0B1F33')
NAVY_2 = colors.HexColor('#12324F')
GOLD = colors.HexColor('#C9A54D')
SLATE = colors.HexColor('#5F6F80')
INK = colors.HexColor('#1D2E3F')
PALE = colors.HexColor('#F5F8FB')
LINE = colors.HexColor('#D9E2EA')
WHITE = colors.white


def _font_paths():
    candidates = [
        (Path('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'), Path('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf')),
        (Path('/usr/share/fonts/truetype/freefont/FreeSans.ttf'), Path('/usr/share/fonts/truetype/freefont/FreeSansBold.ttf')),
    ]
    try:
        import matplotlib
        root = Path(matplotlib.get_data_path()) / 'fonts' / 'ttf'
        candidates.insert(0, (root / 'DejaVuSans.ttf', root / 'DejaVuSans-Bold.ttf'))
    except Exception:
        pass
    for reg, bold in candidates:
        if reg.exists() and bold.exists():
            return str(reg), str(bold)
    return None, None


def _register_fonts():
    reg, bold = _font_paths()
    if reg and 'YQII_AR' not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(TTFont('YQII_AR', reg))
    if bold and 'YQII_ARB' not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(TTFont('YQII_ARB', bold))
    return ('YQII_AR' if reg else 'Helvetica', 'YQII_ARB' if bold else 'Helvetica-Bold')


AR_FONT, AR_BOLD = _register_fonts()


def _shape(text: str) -> str:
    return get_display(arabic_reshaper.reshape(str(text)))


class RTLBlock(Flowable):
    """Wrap Arabic logically first, then shape each line separately to avoid reversed wrapped lines."""
    def __init__(self, text, font=AR_FONT, size=10.9, leading=17.2, color=INK, bold=False, space_after=6):
        super().__init__()
        self.text = str(text)
        self.font = AR_BOLD if bold else font
        self.size = size
        self.leading = leading
        self.color = color
        self.space_after = space_after
        self.lines = []
        self._avail_width = 0

    def _wrap_logical(self, avail_width):
        words = self.text.split()
        lines, current = [], []
        for word in words:
            candidate = ' '.join(current + [word])
            visual = _shape(candidate)
            if current and pdfmetrics.stringWidth(visual, self.font, self.size) > avail_width:
                lines.append(' '.join(current))
                current = [word]
            else:
                current.append(word)
        if current:
            lines.append(' '.join(current))
        return lines or ['']

    def wrap(self, availWidth, availHeight):
        self._avail_width = availWidth
        self.lines = self._wrap_logical(availWidth)
        self.width = availWidth
        self.height = len(self.lines) * self.leading + self.space_after
        return self.width, self.height

    def draw(self):
        self.canv.setFillColor(self.color)
        self.canv.setFont(self.font, self.size)
        y = self.height - self.leading
        for logical in self.lines:
            self.canv.drawRightString(self._avail_width, y, _shape(logical))
            y -= self.leading


class GoldRule(Flowable):
    def __init__(self, width=170*mm, thickness=1.2):
        super().__init__(); self.w=width; self.t=thickness
    def wrap(self, aw, ah): self.width=min(aw,self.w); self.height=4; return self.width,self.height
    def draw(self):
        self.canv.setStrokeColor(GOLD); self.canv.setLineWidth(self.t); self.canv.line(0,2,self.width,2)


def _styles():
    s = getSampleStyleSheet()
    return {
        'h1': ParagraphStyle('h1x', parent=s['Heading1'], fontName=AR_BOLD, fontSize=19, leading=24, textColor=NAVY, spaceAfter=9),
        'h2': ParagraphStyle('h2x', parent=s['Heading2'], fontName=AR_BOLD, fontSize=12.2, leading=16.5, textColor=GOLD, spaceBefore=6, spaceAfter=5),
        'body': ParagraphStyle('bodyx', parent=s['BodyText'], fontName=AR_FONT, fontSize=10.3, leading=15.8, textColor=INK, spaceAfter=7),
        'small': ParagraphStyle('smallx', parent=s['BodyText'], fontName=AR_FONT, fontSize=8.4, leading=12.4, textColor=SLATE, spaceAfter=5),
        'quote': ParagraphStyle('quotex', parent=s['BodyText'], fontName=AR_BOLD, fontSize=13.4, leading=19, textColor=NAVY, spaceAfter=9),
        'center': ParagraphStyle('centerx', parent=s['BodyText'], fontName=AR_BOLD, fontSize=11, leading=16, textColor=NAVY, alignment=TA_CENTER),
    }


def _header_footer(canvas, doc):
    canvas.saveState(); w,h=A4
    if doc.page > 1:
        canvas.setStrokeColor(GOLD); canvas.setLineWidth(.7); canvas.line(15*mm, 13*mm, w-15*mm, 13*mm)
        canvas.setFont('Helvetica', 7.2); canvas.setFillColor(SLATE)
        canvas.drawString(15*mm, 8.5*mm, 'Yahia QC Instrument Intelligence - Official Guide v1.0')
        canvas.drawRightString(w-15*mm, 8.5*mm, f'Page {doc.page}')
    canvas.restoreState()


def _cover(canvas, doc):
    canvas.saveState(); w,h=A4
    canvas.setFillColor(NAVY); canvas.rect(0,0,w,h,stroke=0,fill=1)
    canvas.setFillColor(NAVY_2); canvas.circle(w*0.86,h*0.82,74*mm,stroke=0,fill=1)
    canvas.setStrokeColor(GOLD); canvas.setLineWidth(1.2)
    canvas.roundRect(16*mm,18*mm,w-32*mm,h-36*mm,8*mm,stroke=1,fill=0)
    canvas.setFont(AR_BOLD, 9.4); canvas.setFillColor(GOLD)
    canvas.drawString(22*mm,h-35*mm,'PHARMACEUTICAL QC · INSTRUMENT INTELLIGENCE')
    canvas.setFont(AR_BOLD, 25); canvas.setFillColor(WHITE)
    canvas.drawString(22*mm,h-58*mm,'YAHIA QC')
    canvas.drawString(22*mm,h-70*mm,'INSTRUMENT INTELLIGENCE™')
    canvas.setFont(AR_FONT, 11.6); canvas.setFillColor(colors.HexColor('#D8E1E9'))
    canvas.drawString(22*mm,h-87*mm,'From Instrument Data to Evidence-Based Decisions')
    canvas.setFillColor(GOLD); canvas.roundRect(22*mm,h-112*mm,132*mm,14*mm,4*mm,stroke=0,fill=1)
    canvas.setFillColor(NAVY); canvas.setFont(AR_BOLD, 9.8)
    canvas.drawCentredString(88*mm,h-107*mm,"DON'T GUESS. FOLLOW THE EVIDENCE.")
    canvas.setFillColor(WHITE); canvas.setFont(AR_BOLD, 13.4)
    canvas.drawString(22*mm,55*mm,'PRODUCT · USER · MANAGEMENT GUIDE')
    canvas.setFont(AR_FONT, 8.9); canvas.setFillColor(colors.HexColor('#C9D3DC'))
    canvas.drawString(22*mm,44*mm,'Lifecycle · Control · Investigation · Performance · Governance · Evidence')
    canvas.setFont(AR_FONT, 7.2); canvas.setFillColor(colors.HexColor('#92A4B5'))
    canvas.drawString(22*mm,28*mm,'Official Guide v1.0 · Decision-support platform. Official GxP records remain in approved company systems.')
    canvas.restoreState()


def _table(data, widths, header=True):
    # Use Paragraph cells so long workflow text wraps instead of clipping beyond
    # the printable area. This also keeps the same Unicode-capable font family
    # used by the rest of the guide.
    from xml.sax.saxutils import escape
    body_cell = ParagraphStyle(
        'table_body_cell', fontName=AR_FONT, fontSize=7.7, leading=9.9,
        textColor=INK, spaceAfter=0, spaceBefore=0,
    )
    head_cell = ParagraphStyle(
        'table_head_cell', fontName=AR_BOLD, fontSize=7.5, leading=9.7,
        textColor=WHITE, spaceAfter=0, spaceBefore=0,
    )
    wrapped=[]
    for r,row in enumerate(data):
        style=head_cell if header and r==0 else body_cell
        wrapped.append([Paragraph(escape(str(cell)), style) for cell in row])
    t=Table(wrapped,colWidths=widths,repeatRows=1 if header else 0,hAlign='LEFT',splitByRow=1)
    style=[
        ('VALIGN',(0,0),(-1,-1),'TOP'),('GRID',(0,0),(-1,-1),.35,LINE),
        ('LEFTPADDING',(0,0),(-1,-1),5.5),('RIGHTPADDING',(0,0),(-1,-1),5.5),
        ('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5),
    ]
    if header:
        style += [('BACKGROUND',(0,0),(-1,0),NAVY),('ROWBACKGROUNDS',(0,1),(-1,-1),[WHITE,PALE])]
    t.setStyle(TableStyle(style)); return t


def _section(story, styles, number, title, arabic_title=None):
    story.append(Paragraph(f'{number}. {title}', styles['h1']))
    if arabic_title:
        story.append(RTLBlock(arabic_title, size=13, leading=19, color=NAVY, bold=True, space_after=8))
    story.append(GoldRule()); story.append(Spacer(1,4*mm))

def _guide_screenshot(name: str, width=52*mm):
    data = guide_visual_bytes(name)
    if not data:
        return Spacer(1, 0)
    ratios = {
        "instrument_360_overview": 367/200,
        "instrument_360_attention": 370/200,
    }
    height = width * ratios.get(name, 1.82)
    img = RLImage(BytesIO(data), width=width, height=height)
    img.hAlign = 'CENTER'
    return img



def build_product_user_guide_pdf() -> bytes:
    styles=_styles(); out=BytesIO()
    doc=SimpleDocTemplate(out,pagesize=A4,rightMargin=16*mm,leftMargin=16*mm,topMargin=17*mm,bottomMargin=18*mm,title='Yahia QC Instrument Intelligence - Official Guide v1.0',author='Yahia Abdelhalim')
    story=[Spacer(1,245*mm), PageBreak()]

    _section(story,styles,1,'Why This Platform Exists','لماذا تم بناء هذه المنصة؟')
    story.append(Paragraph('Most QC laboratories do not suffer from a lack of data. They suffer from a fragmented instrument story: identity in one file, calibration in another, maintenance in a tracker, events in email, investigation evidence in separate folders, and critical knowledge in individual memory.',styles['body']))
    story.append(RTLBlock('معظم معامل الرقابة الدوائية لا تعاني من نقص البيانات بقدر ما تعاني من تشتت قصة الجهاز بين ملفات متعددة وأشخاص متعددين. الهدف هنا ليس إنشاء مكان جديد لإدخال البيانات، بل ربط الدليل بالقرار المطلوب الآن.'))
    story.append(Paragraph('DETECT → PRIORITIZE → INVESTIGATE → DECIDE → ACT → VERIFY → DOCUMENT → LEARN',styles['quote']))
    story.append(Paragraph('ENTER LESS. DECIDE BETTER. KEEP THE INSTRUMENT STORY CONNECTED.',styles['quote']))
    story.append(PageBreak())

    _section(story,styles,2,'Before vs. After','قبل المنصة وبعدها')
    story.append(_table([['BEFORE','WITH YAHIA QC INSTRUMENT INTELLIGENCE'],['Scattered Excel trackers','One connected instrument story'],['Dates without context','Lifecycle + control + performance context'],['Reactive troubleshooting','Evidence-first investigation workflow'],['Knowledge depends on individuals','Role-aware shared workspace'],['Manual follow-up','Attention signals and management visibility'],['History is hard to reuse','Evidence supports the next decision']],[77*mm,87*mm]))
    story.append(Spacer(1,6*mm)); story.append(RTLBlock('القيمة الحقيقية ليست استبدال Excel بواجهة أجمل. القيمة هي أن تتحول البيانات المتفرقة إلى سياق تشغيلي يساعد المحلل والمشرف والمدير على اتخاذ قرار أفضل وأسرع وبأقل تخمين.')); story.append(PageBreak())

    _section(story,styles,3,'Built for Organizations','مبني للمؤسسات وليس لمستخدم منفرد فقط')
    story.append(Paragraph('Platform Owner → Organizations → Workspaces → Admins → Team Members → Roles → Privileges → Shared QC Data → Audit Trail',styles['quote']))
    story.append(RTLBlock('كل عميل مؤسسي يعمل داخل Workspace مستقل. مدير المؤسسة يدير المستخدمين والأدوار والصلاحيات داخل بيئته، بينما تظل حوكمة المنصة منفصلة عن الإدارة اليومية لبيانات العميل.'))
    story.append(_table([['LAYER','RESPONSIBILITY'],['Platform Owner','Provision organizations, platform governance, controlled support.'],['Organization Owner / Admin','Manage team membership, status, roles and permissions.'],['Team Members','Use the shared QC evidence according to assigned responsibilities.'],['Audit Trail','Record access and administrative changes for accountability.']],[52*mm,112*mm])); story.append(PageBreak())

    _section(story,styles,4,'Role-Aware Workspace','كل مستخدم يرى ما يهم قراره')
    story.append(_table([['ROLE','PRIMARY DECISION VALUE'],['QC Analyst','Due work, events, investigation evidence and next controlled action.'],['QC Supervisor','Restrictions, overdue tasks, open investigations and team workload.'],['QC Manager','Availability, utilization, downtime, compliance, capacity and attention.'],['QC Director / Head','Risk, capacity, asset burden, escalation and investment evidence.'],['QA / Reviewer','Evidence readiness, traceability and quality-signal visibility.'],['Calibration / Maintenance','Due control work, maintenance history and component context.'],['Organization Admin','Users, roles, privileges, status and access audit.']],[44*mm,120*mm]))
    story.append(RTLBlock('اختلاف الواجهة حسب الدور هدفه ترتيب الأولويات وليس تغيير الحقائق. نفس الجهاز ونفس الدليل، لكن كل مستوى يرى القرارات التي تخص مسؤوليته أولًا.'))
    story.append(Paragraph('NAVIGATION: Desktop uses the persistent sidebar. Mobile uses the compact top menu (Menu · Current Page); selecting a workspace closes the menu and opens the selected page from the top.',styles['small']))
    story.append(RTLBlock('التنقل متجاوب مع الجهاز: على الكمبيوتر Sidebar ثابتة، وعلى الهاتف قائمة علوية مختصرة. تغيير Job Role يعيد ترتيب تجربة المستخدم ولا يساوي منح صلاحيات أمنية جديدة.',size=9.2,leading=14,space_after=5)); story.append(PageBreak())

    _section(story,styles,5,'Instrument 360','قصة الجهاز في مكان واحد')
    story.append(Paragraph('IDENTITY | LIFECYCLE | CONTROL | PERFORMANCE | EVENTS | COMPONENTS | EVIDENCE',styles['quote']))
    story.append(Paragraph('Open Instruments, choose an asset, then open Instrument 360. The first layer shows an explainable Health Score, operational status, open events, latest Availability and Utilization before the user drills into evidence.',styles['body']))
    story.append(RTLBlock('بدل أن تبدأ كل مشكلة بالبحث عن بيانات الجهاز الأساسية، يفتح المستخدم Instrument 360 ليرى القصة المتصلة للجهاز وأهم إشارات القرار أولًا. الـHealth Score إشارة أولوية قابلة للتفسير وليست حكم امتثال أو قرار Release أو Root Cause.'))
    story.append(_table([['VIEW','WHAT IT CONNECTS'],['Identity','Instrument ID, manufacturer, model, serial, location and ownership'],['Lifecycle','Need, URS, acquisition, qualification, release, first run, retirement'],['Control','Calibration, qualification, PM, maintenance and components'],['Performance','Availability, utilization, available time and monthly trend'],['Events','Observed failures, status and active-event context'],['Evidence','Missing evidence, references, QR passport and traceability']],[45*mm,119*mm]))
    story.append(Spacer(1,4*mm)); story.append(_guide_screenshot('instrument_360_overview'))
    story.append(Paragraph('Actual app view - Instrument 360 overview using synthetic demonstration data.', styles['small']))
    story.append(PageBreak())

    _section(story,styles,6,'Lifecycle Intelligence','من الحاجة إلى التكهين')
    story.append(Paragraph('Need → URS → Quotation → PR → PO → Receiving → Installation → IQ → OQ → PQ → Release / Issuance → First Approved Routine Run → Routine Control → Performance Review → Retirement',styles['quote']))
    story.append(RTLBlock('الهدف ليس مجرد حفظ تواريخ. الهدف أن يظل تسلسل القرارات والدليل واضحًا من لحظة ظهور الحاجة للجهاز وحتى خروجه من الخدمة.'))
    story.append(Paragraph('When an event occurs years later, lifecycle context can explain what changed, which components are aging, what qualification history exists, and which evidence is still missing.',styles['body'])); story.append(PageBreak())

    _section(story,styles,7,'Calibration, PM & Maintenance Control','التحكم الدوري بدون جزر منفصلة')
    story.append(Paragraph('Calibration, qualification, preventive maintenance, corrective maintenance and component replacement remain connected to the same asset instead of separate trackers.',styles['body']))
    story.append(RTLBlock('التطبيق لا يحول موعد Calibration أو PM إلى مجرد Reminder. هو يربط الموعد بسياق الجهاز وتاريخه والأحداث والتحقيقات، بحيث يصبح التأخير أو التكرار إشارة قابلة للفهم وليس رقمًا منفصلًا.'))
    story.append(Paragraph('Planning signal ≠ GMP disposition.',styles['quote'])); story.append(PageBreak())

    _section(story,styles,8,'Events & Investigation Intelligence','التحقيق يبدأ بما حدث فعلًا')
    story.append(Paragraph('The evidence model deliberately separates OBSERVED / REPORTED from INFERRED and UNKNOWN.',styles['quote']))
    story.append(_table([['EVIDENCE STATE','MEANING'],['OBSERVED / REPORTED','What is actually known or directly reported.'],['INFERRED','A supported interpretation, not yet confirmed fact.'],['UNKNOWN','Information still required before a controlled conclusion.']],[48*mm,116*mm]))
    story.append(Spacer(1,5*mm)); story.append(RTLBlock('تكرار نفس النمط يقوّي الفرضية لكنه لا يثبت Root Cause بمفرده. المنصة مصممة لتدفع المستخدم نحو الخطوة التالية التي تميز بين الفرضيات بدل القفز إلى التشخيص.'))
    story.append(Paragraph('Expected → Actual → Changed → Unchanged → Objective Evidence → Next Evidence Action',styles['quote'])); story.append(PageBreak())

    _section(story,styles,9,'Performance Intelligence','من وقت الجهاز إلى قرار الإدارة')
    story.append(Paragraph('Performance can be recorded from the Performance workspace and reviewed again inside the selected Instrument 360. The monthly record connects Scheduled Service Hours, Planned Downtime, Unplanned Downtime and Productive Run Time.',styles['body']))
    story.append(_table([['KPI','FORMULA / PURPOSE'],['Planned Operating','Scheduled Service Hours - Planned Downtime'],['Available Time','Planned Operating - Unplanned Downtime'],['Availability','Available Time / Planned Operating × 100'],['Utilization','Productive Run / Available Time × 100']],[48*mm,116*mm]))
    story.append(RTLBlock('الإدارة لا تحتاج رقم Availability فقط. تحتاج أن تعرف لماذا انخفض، هل المشكلة Planned أم Unplanned، وهل هناك سعة غير مستغلة أو جهاز أصبح عبئًا تشغيليًا.')); story.append(PageBreak())

    _section(story,styles,10,'Management & Executive Intelligence','من متابعة الأجهزة إلى إدارة الأصول')
    story.append(Paragraph('Management views are designed to surface what deserves attention: overdue control work, restricted instruments, critical events, repeat patterns, downtime burden, capacity gaps and evidence supporting repair-or-replace discussions.',styles['body']))
    story.append(RTLBlock('الهدف ليس أن يتخذ النظام قرار شراء أو استبدال الجهاز نيابة عن الإدارة. الهدف أن يجمع الأدلة التي تجعل القرار قابلًا للدفاع عنه: العمر، الاعتمادية، التوقف، الاستغلال، تكلفة الصيانة، أهمية الجهاز والسعة المتاحة.'))
    story.append(Paragraph('DATA → EVIDENCE → DECISION → ACTION',styles['quote'])); story.append(PageBreak())

    _section(story,styles,11,'Admin, Users & Privileges','إدارة الفريق والصلاحيات')
    story.append(Paragraph('Organization Admins can add or invite users, assign job roles, control account status and configure module-level privileges such as View, Add, Edit, Delete and Approve.',styles['body']))
    story.append(RTLBlock('الفكرة الأساسية هي الفصل بين Job Role الذي يرتب تجربة المستخدم وبين Access Privileges التي يجب أن تحكم ما يستطيع المستخدم فعله فعليًا. تغييرات الوصول يجب أن تكون قابلة للتتبع.'))
    story.append(Paragraph('Secure invitation is enforced server-side: the signed-in caller is validated, workspace-admin authority is checked, and service-role capability remains on the server. Access changes require an accountable reason and are written to the access audit trail.',styles['small']))
    story.append(RTLBlock('الأمان ليس مجرد زر مخفي في الواجهة: دعوة المستخدم والتحقق من صلاحية مدير الـWorkspace تتم على الخادم، وتغييرات الوصول يجب أن تترك أثرًا واضحًا في Audit Trail.',size=9.2,leading=14,space_after=5))
    story.append(_table([['ACTION','EXAMPLE'],['View','See instrument or report data'],['Add','Create a new record'],['Edit','Modify an existing record'],['Delete / Archive','Remove or retire according to governance'],['Approve','Perform a controlled approval action when implemented']],[48*mm,116*mm])); story.append(PageBreak())

    _section(story,styles,12,'Excel Migration & Data Entry','ابدأ من بياناتك الحالية بدون تخمين')
    story.append(Paragraph('The Instruments workspace supports three controlled paths: add one instrument, import an instrument list, or export the current registry using the same recognized headers for a reviewed round trip.',styles['body']))
    story.append(RTLBlock('الفكرة ليست أن نجبر المعمل على إعادة إدخال كل شيء يدويًا. يمكن تنزيل Current Instrument Registry وتحديث الحقول المعتمدة ثم إعادة الاستيراد بعد Preview. الأعمدة غير المعروفة تظل ignored بدل تخمين معناها، والبيانات غير المتاحة تظل Missing Evidence.'))
    story.append(Paragraph('Camera-assisted entry can reduce transcription errors for manufacturer, model and serial-number information during new instrument registration.',styles['body'])); story.append(PageBreak())

    _section(story,styles,13,'Practical App Workflows','خطوات العمل الفعلية داخل التطبيق')
    workflow_rows=[
        ['TASK','WHERE TO GO','WHAT TO DO'],
        ['Start the shift','Dashboard','Review priority signals, overdue controls, restrictions, open events and role-relevant attention.'],
        ['Add one instrument','Instruments > Add one instrument','Enter identity, status and due-date evidence; save, then open Instrument 360.'],
        ['Bulk import / update','Instruments > Import Instrument List','Download template or current registry, keep exact headers, upload, preview recognized fields, confirm import.'],
        ['Review one asset','Instruments > Open Instrument 360','Read Health Score, Status, Open Events, Availability and Utilization; drill into Identity, Lifecycle, Control, Performance, Events and Evidence.'],
        ['Control work','Cal & PM','Record calibration, qualification, PM, maintenance or component work with approved reference and next due.'],
        ['Create an event','Events','Record observed facts, severity, subsystem and status before interpreting cause.'],
        ['Investigate','Investigate','Expected > Observed > Changed > Unchanged > Objective Evidence > Next Evidence Action.'],
        ['Monthly performance','Performance','Enter Scheduled, Planned Downtime, Unplanned Downtime and Productive Run hours; review calculated KPIs and trend.'],
        ['Management output','Reports / Cockpit / Alerts','Generate evidence packs, review operational/capacity signals and follow attention according to role.'],
        ['Account actions','ACCOUNT','Change role for UX priorities or Log out to end the authenticated session.'],
    ]
    story.append(_table(workflow_rows,[38*mm,48*mm,78*mm])); story.append(Spacer(1,5*mm))
    story.append(RTLBlock('المسار العملي ثابت: افتح القسم الصحيح، سجل فقط ما لديك كدليل، راجع ما تغيّر في Instrument 360، ثم انتقل من الإشارة إلى القرار التالي. لا تستخدم الفراغات كدعوة للتخمين.'))
    story.append(Paragraph('HPLC example: open Instrument 360 > review Control and Performance > create the event as pressure fluctuation, not pump failure > investigate expected vs actual and recent changes > choose one discriminating evidence action > confirm before root-cause disposition > carry the verified outcome into the asset history.',styles['body']))
    story.append(PageBreak())

    _section(story,styles,14,'Inspection Readiness & Evidence Packs','الاستعداد للمراجعة بدون رحلة بحث')
    story.append(Paragraph('The platform can organize evidence views across calibration, qualification, PM, events, investigations, missing evidence, lifecycle status and traceability.',styles['body']))
    story.append(RTLBlock('بدل أن يبدأ الاستعداد للمراجعة بجمع معلومات من عدة ملفات، يمكن استخدام المنصة كطبقة تنظيم وقرار توضح أين يوجد الدليل وأين توجد الفجوة. السجلات الرسمية نفسها تظل في الأنظمة المعتمدة للمؤسسة.')); story.append(PageBreak())

    _section(story,styles,15,'GMP, Data Integrity & Evidence Boundary','حدود النظام ومصداقيته')
    story.append(Paragraph('This product is decision-support software and is not currently presented as a validated GxP system of record.',styles['quote']))
    story.append(RTLBlock('السجلات الرسمية المعتمدة، Raw Data، الانحرافات، CAPA، الشهادات، الموافقات والنماذج الخاضعة لإجراءات الشركة يجب أن تظل داخل الأنظمة المعتمدة. المنصة تساعد على الرؤية والقرار ولا تستبدل متطلبات التحقق والحوكمة الخاصة بالمؤسسة.'))
    story.append(Paragraph('Missing Evidence remains visible. Inference is never promoted to fact automatically.',styles['quote'])); story.append(PageBreak())

    _section(story,styles,16,'Current Product Boundary','ما الذي نبيعه اليوم فعلًا؟')
    story.append(Paragraph('The guide intentionally distinguishes implemented capability from the target enterprise architecture. Organization workspaces, admin membership, role-aware UX and privilege-management foundations are implemented. Workspace-wide RLS and privilege enforcement across every business action continue to be hardened in phases and should not be represented as complete until verified end-to-end.',styles['body']))
    story.append(RTLBlock('البيع القوي لا يحتاج مبالغة. نعرض ما تم تنفيذه فعلًا، ونوضح ما يتم تقويته قبل اعتباره Security Authority كاملة. هذا يزيد الثقة بدل أن يقلل قيمة المنتج.')); story.append(PageBreak())

    _section(story,styles,17,'Business Value by Stakeholder','القيمة التي يراها كل مستوى')
    story.append(_table([['STAKEHOLDER','VALUE'],['Analyst','Less searching, clearer evidence path, better handover.'],['Supervisor','Faster exception visibility and team control.'],['Manager','Operational, compliance and capacity intelligence.'],['Director / Head','Risk, asset burden and investment evidence.'],['QA / Reviewer','Traceability and visible evidence gaps.'],['Organization','Less dependence on memory and disconnected trackers.']],[48*mm,116*mm]))
    story.append(Spacer(1,6*mm)); story.append(RTLBlock('كلما زادت خبرة الفريق لا يجب أن تزيد المعلومات المحبوسة في رؤوس الأفراد. المنصة تحول المعرفة التشغيلية إلى قصة يمكن للفريق كله الاستفادة منها.')); story.append(PageBreak())

    _section(story,styles,18,'The Product Promise','الوعد الذي تقدمه المنصة')
    story.append(Spacer(1,12*mm)); story.append(Paragraph('ENTER LESS. DECIDE BETTER.<br/>KEEP THE INSTRUMENT STORY CONNECTED.',styles['quote']))
    story.append(Spacer(1,7*mm)); story.append(Paragraph('STOP MANAGING INSTRUMENT DATA.<br/>START MANAGING INSTRUMENT DECISIONS.',styles['quote']))
    story.append(Spacer(1,9*mm)); story.append(RTLBlock('ليست الفكرة أن تمتلك Dashboard أكثر. الفكرة أن تعرف ما الذي يحتاج انتباهك الآن، ما الدليل الذي ينقصك، وما القرار التالي الذي تستطيع الدفاع عنه.',size=12,leading=19,bold=True))
    story.append(Spacer(1,12*mm)); story.append(Paragraph('Yahia QC Instrument Intelligence™',styles['center']))
    story.append(Paragraph('Pharmaceutical QC instrument lifecycle, evidence and operations intelligence.',styles['small']))

    doc.build(story,onFirstPage=_cover,onLaterPages=_header_footer)
    out.seek(0)
    return out.getvalue()
