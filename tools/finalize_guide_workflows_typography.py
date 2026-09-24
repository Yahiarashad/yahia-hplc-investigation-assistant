from pathlib import Path

# -----------------------------------------------------------------------------
# In-app guide: clearer typography + actual step-by-step workflows
# -----------------------------------------------------------------------------
guide_path = Path('instrument_v03_user_guide.py')
g = guide_path.read_text(encoding='utf-8')

# Typography: use modern system fonts, larger body text and clearer hierarchy.
g = g.replace(
    '.v03-guide-banner{\n  direction:rtl;text-align:right;',
    '.v03-guide-banner{\n  direction:rtl;text-align:right;\n  font-family:Inter,"Segoe UI","Noto Sans Arabic",Tahoma,Arial,sans-serif;',
    1,
)
g = g.replace(
    '.v03-guide-banner b{color:#0f2742;font-size:1.02rem}.v03-guide-banner span{display:block;color:#64748b;font-size:.86rem;margin-top:.18rem}\n.v03-guide-rtl{direction:rtl;text-align:right;line-height:1.9;unicode-bidi:plaintext}',
    '.v03-guide-banner b{color:#0f2742;font-size:1.08rem}.v03-guide-banner span{display:block;color:#64748b;font-size:.94rem;margin-top:.22rem;line-height:1.7}\n.v03-guide-rtl{direction:rtl;text-align:right;line-height:1.95;unicode-bidi:plaintext;font-size:1.02rem;font-family:Inter,"Segoe UI","Noto Sans Arabic",Tahoma,Arial,sans-serif}\n.v03-guide-rtl h3{font-size:1.30rem;line-height:1.5;margin:.9rem 0 .45rem;font-weight:850}\n.v03-guide-rtl h4{font-size:1.12rem;line-height:1.55;margin:.8rem 0 .35rem;font-weight:800}',
    1,
)
g = g.replace(
    '.v03-guide-rule{direction:rtl;text-align:right;border-right:4px solid #d4af37;border-left:0;background:#fffaf0;border-radius:12px;padding:.75rem .85rem;margin:.6rem 0;line-height:1.85}',
    '.v03-guide-rule{direction:rtl;text-align:right;border-right:4px solid #d4af37;border-left:0;background:#fffaf0;border-radius:14px;padding:.9rem 1rem;margin:.7rem 0;line-height:1.95;font-size:1rem;font-family:Inter,"Segoe UI","Noto Sans Arabic",Tahoma,Arial,sans-serif}',
    1,
)
g = g.replace(
    '.v03-flow-main{font-weight:850;color:#102a45;font-size:.98rem;line-height:1.45}\n.v03-flow-sub{color:#66778a;font-size:.81rem;margin-top:.12rem;line-height:1.45}',
    '.v03-flow-main{font-weight:850;color:#102a45;font-size:1.04rem;line-height:1.55}\n.v03-flow-sub{color:#66778a;font-size:.91rem;margin-top:.16rem;line-height:1.6}',
    1,
)
g = g.replace(
    '.v03-guide-banner-brand{direction:ltr;text-align:left;color:#0f2742;font-weight:900;font-size:1rem;unicode-bidi:isolate}\n.v03-guide-banner-title{direction:rtl;text-align:right;color:#0f2742;font-weight:900;font-size:1.06rem;margin-top:.35rem}',
    '.v03-guide-banner-brand{direction:ltr;text-align:left;color:#0f2742;font-weight:900;font-size:1.08rem;unicode-bidi:isolate}\n.v03-guide-banner-title{direction:rtl;text-align:right;color:#0f2742;font-weight:900;font-size:1.22rem;margin-top:.42rem}',
    1,
)

# Add workflow card styles before mobile CSS.
workflow_css = '''\n.v03-workflow-card{\n  direction:rtl;text-align:right;border:1px solid rgba(128,128,128,.30);border-radius:16px;\n  padding:.9rem 1rem;margin:.65rem 0;background:var(--secondary-background-color);\n  color:var(--text-color);font-family:Inter,"Segoe UI","Noto Sans Arabic",Tahoma,Arial,sans-serif;line-height:1.9\n}\n.v03-workflow-card b{font-size:1.03rem}\n.v03-workflow-route{display:inline-block;direction:ltr;unicode-bidi:isolate;font-weight:800;color:#c9a54d;margin:.2rem 0}\n.v03-workflow-outcome{margin-top:.45rem;padding:.55rem .7rem;border-radius:10px;background:rgba(201,165,77,.10);border:1px solid rgba(201,165,77,.28)}\n'''
anchor = '\n@media(max-width:700px){\n'
if workflow_css.strip() not in g:
    if anchor not in g:
        raise SystemExit('Guide CSS mobile anchor missing')
    g = g.replace(anchor, workflow_css + anchor, 1)

# Mobile font tuning.
g = g.replace(
    '  .v03-guide-banner{padding:.78rem .82rem}.v03-guide-banner span{font-size:.82rem}.v03-guide-rtl{line-height:1.78}',
    '  .v03-guide-banner{padding:.82rem .88rem}.v03-guide-banner span{font-size:.90rem}.v03-guide-rtl{line-height:1.9;font-size:1rem}',
    1,
)
g = g.replace(
    '  .v03-flow-main{font-size:.94rem}.v03-flow-sub{font-size:.79rem}',
    '  .v03-flow-main{font-size:1rem}.v03-flow-sub{font-size:.88rem}',
    1,
)

# Add a dedicated actual-workflow tab without disturbing existing tab indexes.
old_tabs = '''        guide_tabs = st.tabs([\n            "🎯 ابدأ من هنا",\n            "↻ دورة الحياة",\n            "🧾 الاستخدام اليومي",\n            "🔎 التحقيق",\n            "🔐 الحوكمة والخصوصية",\n        ])'''
new_tabs = '''        guide_tabs = st.tabs([\n            "🎯 ابدأ من هنا",\n            "↻ دورة الحياة",\n            "🧾 الاستخدام اليومي",\n            "🔎 التحقيق",\n            "🔐 الحوكمة والخصوصية",\n            "🧭 خطوات العمل الفعلية",\n        ])'''
if old_tabs not in g:
    raise SystemExit('Guide tabs anchor missing')
g = g.replace(old_tabs, new_tabs, 1)

# Make security wording accurate for the current product boundary.
g = g.replace(
    '- كل حساب يرى بياناته فقط؛ **Supabase Row Level Security** هو طبقة العزل الأساسية.\n- Excel import يكتب البيانات من خلال جلسة المستخدم الحالية، لذلك تظل الصفوف خاضعة لنفس RLS.',
    '- البيانات منظمة داخل **Workspaces** منفصلة، و**Supabase Row Level Security** هو أساس طبقة العزل. التطبيق يواصل تقوية enforcement على مستوى كل business action قبل اعتباره Security Authority مكتملة.\n- Excel import يكتب من خلال جلسة المستخدم الحالية وداخل الـWorkspace النشط؛ لا تستخدم الاستيراد كبديل عن مراجعة الصلاحيات والحوكمة.',
    1,
)

# Append the practical workflow tab after governance tab. The file currently ends
# with the governance rule, so use that exact final line as a safe insertion anchor.
end_anchor = '''            st.markdown("<div class='v03-guide-rule'><b>DON'T GUESS. FOLLOW THE EVIDENCE.</b><br>لو لم يوجد دليل، سجّل أن المعلومة Unknown بدل أن تستنتجها.</div>", unsafe_allow_html=True)'''
workflow_block = '''\n\n        with guide_tabs[5]:\n            st.markdown("### 🧭 خطوات العمل الفعلية داخل التطبيق")\n            st.caption("اتبع المسار كما هو ظاهر في التطبيق. Desktop: Sidebar. Mobile: ☰ Menu · Current Page.")\n\n            st.markdown("""\n<div class="v03-workflow-card"><b>1) بداية اليوم / بداية الشيفت</b><br><span class="v03-workflow-route">Dashboard</span><br>\nراجع الإشارات ذات الأولوية: overdue controls، open events، OOC، restrictions، والـattention queue المتاحة لدورك.\n<div class="v03-workflow-outcome"><b>النتيجة:</b> تعرف أين تبدأ قبل أن تدخل إلى تفاصيل أي جهاز.</div></div>\n\n<div class="v03-workflow-card"><b>2) إضافة جهاز واحد</b><br><span class="v03-workflow-route">Instruments → Add one instrument</span><br>\nأدخل Instrument ID، الاسم، النوع، الشركة، الموديل، Serial Number، Location، Responsible Team والحالة التشغيلية. استخدم Camera Assist عند الحاجة لتقليل أخطاء النقل. احفظ السجل ثم افتح الجهاز من <span dir="ltr">Open Instrument 360</span>.\n<div class="v03-workflow-outcome"><b>النتيجة:</b> يصبح للجهاز Digital Identity ثابتة يمكن ربط كل التاريخ بها.</div></div>\n\n<div class="v03-workflow-card"><b>3) استيراد أو تحديث قائمة أجهزة</b><br><span class="v03-workflow-route">Instruments → Import Instrument List</span><br>\nحمّل القالب أو نزّل Current Instrument Registry، لا تغيّر أسماء الأعمدة، املأ فقط البيانات المعروفة، ارفع الملف، راجع Recognized / Ignored Columns ثم اختر Create أو Update وبعدها Confirm Import.\n<div class="v03-workflow-outcome"><b>النتيجة:</b> انتقال منظم من Excel بدون تخمين في Mapping أو ملء Evidence غير موجود.</div></div>\n\n<div class="v03-workflow-card"><b>4) مراجعة جهاز محدد</b><br><span class="v03-workflow-route">Instruments → Open Instrument 360</span><br>\nابدأ بـ Health Score، Status، Open Events، Availability وUtilization. بعد ذلك افتح: Identity → Lifecycle → Control → Performance → Events → Evidence. افتح <span dir="ltr">Why XX/100?</span> لفهم عوامل السكور.\n<div class="v03-workflow-outcome"><b>النتيجة:</b> ترى قصة الجهاز المتصلة قبل اتخاذ أي قرار أو بدء تحقيق.</div></div>\n\n<div class="v03-workflow-card"><b>5) تسجيل Calibration / Qualification / PM / Maintenance</b><br><span class="v03-workflow-route">Cal & PM</span><br>\nاختر الجهاز، سجل نوع العمل وتاريخ التنفيذ ومرجع Certificate / Protocol / Work Order / Service Report، ثم أدخل Next Due المعتمد. عند تغيير Component سجل Part / Serial / Installed Date / Review or Replacement Due إن توفرت.\n<div class="v03-workflow-outcome"><b>النتيجة:</b> Control history يظل مرتبطًا بنفس الجهاز ويظهر أثره في Dashboard وInstrument 360.</div></div>\n\n<div class="v03-workflow-card"><b>6) تسجيل عطل أو Quality Event</b><br><span class="v03-workflow-route">Events</span><br>\nاختر الجهاز وسجل التاريخ، Event Type، Severity، Subsystem، الحالة وObserved Facts. اكتب ما حدث فعلًا؛ لا تحول Pressure fluctuation إلى Pump failure بدون Evidence.\n<div class="v03-workflow-outcome"><b>النتيجة:</b> تبدأ التحقيق من Observation موثق وليس من تشخيص مسبق.</div></div>\n\n<div class="v03-workflow-card"><b>7) تشغيل Investigation Intelligence</b><br><span class="v03-workflow-route">Investigate</span><br>\nرتب الحالة: Expected → Actual / Observed → Changed → Unchanged → Objective Evidence → Next Evidence Action. اختبر متغيرًا discriminating واحدًا عندما يكون ذلك مناسبًا، ثم Confirm قبل رفع الفرضية إلى Root Cause.\n<div class="v03-workflow-outcome"><b>النتيجة:</b> تقل مساحة التخمين وتبقى Unknowns واضحة بدل دفنها داخل narrative.</div></div>\n\n<div class="v03-workflow-card"><b>8) تسجيل Availability & Utilization</b><br><span class="v03-workflow-route">Performance</span><br>\nاختر الجهاز والشهر وأدخل 4 قيم: Scheduled Service Hours، Planned Downtime، Unplanned Downtime، Productive Run Hours. التطبيق يحسب Planned Operating، Available Time، Availability وUtilization ثم يعرض الاتجاه الشهري.\n<div class="v03-workflow-outcome"><b>النتيجة:</b> أحدث القيم تظهر أيضًا داخل Instrument 360 وتدعم capacity / reliability review.</div></div>\n\n<div class="v03-workflow-card"><b>9) التقارير والرؤية الإدارية</b><br><span class="v03-workflow-route">Reports / Cockpit / Alerts</span><br>\nاستخدم Reports عندما تحتاج Evidence Pack أو مخرجًا قابلًا للمشاركة، Cockpit للرؤية الإدارية والمخاطر والسعة، وAlerts لمتابعة الإشارات التي تحتاج action حسب الدور.\n<div class="v03-workflow-outcome"><b>النتيجة:</b> تتحول البيانات إلى Attention → Decision → Action بدل قائمة تواريخ فقط.</div></div>\n\n<div class="v03-workflow-card"><b>10) تغيير الدور أو تسجيل الخروج</b><br><span class="v03-workflow-route">Mobile: ☰ Menu → ACCOUNT · Desktop: Sidebar → ACCOUNT</span><br>\nاستخدم Change role لتغيير ترتيب الواجهة والأولويات، واستخدم Log out لإنهاء جلسة Supabase ومسح تسجيل الدخول المستمر. Job Role يخص تجربة الاستخدام؛ الصلاحيات الأمنية الفعلية تُدار بشكل منفصل.\n<div class="v03-workflow-outcome"><b>النتيجة:</b> واجهة مناسبة للمسؤولية بدون الخلط بين Role وPrivilege.</div></div>\n""", unsafe_allow_html=True)\n\n            st.info("قاعدة الاستخدام: ENTER LESS. DECIDE BETTER. KEEP THE INSTRUMENT STORY CONNECTED.")'''
if end_anchor not in g:
    raise SystemExit('Guide end anchor missing')
if 'with guide_tabs[5]:' not in g:
    g = g.replace(end_anchor, end_anchor + workflow_block, 1)

guide_path.write_text(g, encoding='utf-8')

# -----------------------------------------------------------------------------
# Official PDF: clearer typography + practical workflow playbook
# -----------------------------------------------------------------------------
pdf_path = Path('instrument_product_guide_pdf.py')
p = pdf_path.read_text(encoding='utf-8')

# Use the same Unicode-capable registered font for English and Arabic for a cleaner,
# more consistent visual voice across the whole document.
old_styles = '''        'h1': ParagraphStyle('h1x', parent=s['Heading1'], fontName='Helvetica-Bold', fontSize=18, leading=22, textColor=NAVY, spaceAfter=8),\n        'h2': ParagraphStyle('h2x', parent=s['Heading2'], fontName='Helvetica-Bold', fontSize=11.5, leading=15, textColor=GOLD, spaceBefore=5, spaceAfter=4),\n        'body': ParagraphStyle('bodyx', parent=s['BodyText'], fontName='Helvetica', fontSize=9.5, leading=14.5, textColor=INK, spaceAfter=6),\n        'small': ParagraphStyle('smallx', parent=s['BodyText'], fontName='Helvetica', fontSize=7.8, leading=11, textColor=SLATE, spaceAfter=4),\n        'quote': ParagraphStyle('quotex', parent=s['BodyText'], fontName='Helvetica-Bold', fontSize=13, leading=18, textColor=NAVY, spaceAfter=8),\n        'center': ParagraphStyle('centerx', parent=s['BodyText'], fontName='Helvetica-Bold', fontSize=10.5, leading=15, textColor=NAVY, alignment=TA_CENTER),'''
new_styles = '''        'h1': ParagraphStyle('h1x', parent=s['Heading1'], fontName=AR_BOLD, fontSize=19, leading=24, textColor=NAVY, spaceAfter=9),\n        'h2': ParagraphStyle('h2x', parent=s['Heading2'], fontName=AR_BOLD, fontSize=12.2, leading=16.5, textColor=GOLD, spaceBefore=6, spaceAfter=5),\n        'body': ParagraphStyle('bodyx', parent=s['BodyText'], fontName=AR_FONT, fontSize=10.3, leading=15.8, textColor=INK, spaceAfter=7),\n        'small': ParagraphStyle('smallx', parent=s['BodyText'], fontName=AR_FONT, fontSize=8.4, leading=12.4, textColor=SLATE, spaceAfter=5),\n        'quote': ParagraphStyle('quotex', parent=s['BodyText'], fontName=AR_BOLD, fontSize=13.4, leading=19, textColor=NAVY, spaceAfter=9),\n        'center': ParagraphStyle('centerx', parent=s['BodyText'], fontName=AR_BOLD, fontSize=11, leading=16, textColor=NAVY, alignment=TA_CENTER),'''
if old_styles not in p:
    raise SystemExit('PDF styles anchor missing')
p = p.replace(old_styles, new_styles, 1)

p = p.replace(
    "def __init__(self, text, font=AR_FONT, size=10.4, leading=16, color=INK, bold=False, space_after=5):",
    "def __init__(self, text, font=AR_FONT, size=10.9, leading=17.2, color=INK, bold=False, space_after=6):",
    1,
)

# Cover typography consistency.
p = p.replace("canvas.setFont('Helvetica-Bold', 9)", "canvas.setFont(AR_BOLD, 9.4)", 1)
p = p.replace("canvas.setFont('Helvetica-Bold', 26)", "canvas.setFont(AR_BOLD, 25)", 1)
p = p.replace("canvas.setFont('Helvetica', 12)", "canvas.setFont(AR_FONT, 11.6)", 1)
p = p.replace("canvas.setFillColor(NAVY); canvas.setFont('Helvetica-Bold', 10)", "canvas.setFillColor(NAVY); canvas.setFont(AR_BOLD, 9.8)", 1)
p = p.replace("canvas.setFillColor(WHITE); canvas.setFont('Helvetica-Bold', 14)", "canvas.setFillColor(WHITE); canvas.setFont(AR_BOLD, 13.4)", 1)
p = p.replace("canvas.setFont('Helvetica', 9.2)", "canvas.setFont(AR_FONT, 8.9)", 1)
p = p.replace("canvas.setFont('Helvetica', 7.4)", "canvas.setFont(AR_FONT, 7.2)", 1)

# Role-aware navigation section: explicitly document desktop/mobile routes.
role_anchor = "    story.append(RTLBlock('اختلاف الواجهة حسب الدور هدفه ترتيب الأولويات وليس تغيير الحقائق. نفس الجهاز ونفس الدليل، لكن كل مستوى يرى القرارات التي تخص مسؤوليته أولًا.')); story.append(PageBreak())"
role_new = "    story.append(RTLBlock('اختلاف الواجهة حسب الدور هدفه ترتيب الأولويات وليس تغيير الحقائق. نفس الجهاز ونفس الدليل، لكن كل مستوى يرى القرارات التي تخص مسؤوليته أولًا.'))\n    story.append(Paragraph('Navigation: Desktop uses the persistent Sidebar. Mobile uses the top \\u2630 Menu - Current Page control; selecting a route closes the menu and opens the chosen workspace from the top.',styles['body']))\n    story.append(PageBreak())"
if role_anchor not in p:
    raise SystemExit('Role navigation PDF anchor missing')
p = p.replace(role_anchor, role_new, 1)

# Replace section 13 with a practical, real-app workflow playbook while retaining
# the HPLC evidence-first scenario as the final workflow.
start = "    _section(story,styles,13,'One HPLC - One Complete Story','سيناريو عملي لجهاز HPLC')"
end = "    _section(story,styles,14,'Inspection Readiness & Evidence Packs','الاستعداد للمراجعة بدون رحلة بحث')"
if start not in p or end not in p:
    raise SystemExit('Section 13 PDF anchors missing')
pre, rest = p.split(start, 1)
old13, post = rest.split(end, 1)
new13 = '''    _section(story,styles,13,'Practical App Workflows','خطوات العمل الفعلية داخل التطبيق')\n    workflow_rows=[\n        ['TASK','WHERE TO GO','WHAT TO DO'],\n        ['Start the shift','Dashboard','Review priority signals, overdue controls, restrictions, open events and role-relevant attention.'],\n        ['Add one instrument','Instruments > Add one instrument','Enter identity, status and due-date evidence; save, then open Instrument 360.'],\n        ['Bulk import / update','Instruments > Import Instrument List','Download template or current registry, keep exact headers, upload, preview recognized fields, confirm import.'],\n        ['Review one asset','Instruments > Open Instrument 360','Read Health Score, Status, Open Events, Availability and Utilization; drill into Identity, Lifecycle, Control, Performance, Events and Evidence.'],\n        ['Control work','Cal & PM','Record calibration, qualification, PM, maintenance or component work with approved reference and next due.'],\n        ['Create an event','Events','Record observed facts, severity, subsystem and status before interpreting cause.'],\n        ['Investigate','Investigate','Expected > Observed > Changed > Unchanged > Objective Evidence > Next Evidence Action.'],\n        ['Monthly performance','Performance','Enter Scheduled, Planned Downtime, Unplanned Downtime and Productive Run hours; review calculated KPIs and trend.'],\n        ['Management output','Reports / Cockpit / Alerts','Generate evidence packs, review operational/capacity signals and follow attention according to role.'],\n        ['Account actions','ACCOUNT','Change role for UX priorities or Log out to end the authenticated session.'],\n    ]\n    story.append(_table(workflow_rows,[38*mm,48*mm,78*mm])); story.append(Spacer(1,5*mm))\n    story.append(RTLBlock('المسار العملي ثابت: افتح القسم الصحيح، سجل فقط ما لديك كدليل، راجع ما تغيّر في Instrument 360، ثم انتقل من الإشارة إلى القرار التالي. لا تستخدم الفراغات كدعوة للتخمين.'))\n    story.append(Paragraph('HPLC example: open Instrument 360 > review Control and Performance > create the event as pressure fluctuation, not pump failure > investigate expected vs actual and recent changes > choose one discriminating evidence action > confirm before root-cause disposition > carry the verified outcome into the asset history.',styles['body']))\n    story.append(PageBreak())\n\n'''
p = pre + new13 + end + post

# Refine current product boundary wording so guide and app remain honest.
p = p.replace(
    "Organization workspaces, admin membership and privilege-management foundations are implemented. Full workspace-wide RLS enforcement across every business action is being hardened in phases and should not be represented as complete until verified end-to-end.",
    "Organization workspaces, admin membership, role-aware UX and privilege-management foundations are implemented. Workspace-wide RLS and privilege enforcement across every business action continue to be hardened in phases and should not be represented as complete until verified end-to-end.",
    1,
)

pdf_path.write_text(p, encoding='utf-8')
print('Guide workflows and typography finalized')
