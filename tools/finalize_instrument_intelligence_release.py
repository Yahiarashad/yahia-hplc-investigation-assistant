from pathlib import Path

# 1) Instrument 360 final UX polish
core = Path('instrument_supabase_app.py')
s = core.read_text(encoding='utf-8')

old_caption = '        st.caption("Instrument 360 summarizes connected evidence. Health and performance indicators prioritize attention; they do not determine GMP disposition or root cause.")\n'
new_caption = '        st.caption("Decision-support signal only — not a GMP disposition or root-cause conclusion.")\n'
if old_caption not in s:
    raise SystemExit('Instrument 360 caption anchor not found')
s = s.replace(old_caption, new_caption, 1)

old_control = '''            if reasons:\n                st.markdown("**Why the current Health Score needs attention**")\n                for reason in reasons:\n                    st.write(f"• {reason}")\n'''
new_control = '''            if reasons:\n                st.caption("Health Score drivers are shown above under ‘Why this score?’ so the Control view stays focused on current due-date and component control.")\n'''
if old_control not in s:
    raise SystemExit('Duplicate health reasons block not found')
s = s.replace(old_control, new_control, 1)
core.write_text(s, encoding='utf-8')

# 2) In-app practical guide: align terminology and navigation with current UX
guide = Path('instrument_v03_user_guide.py')
g = guide.read_text(encoding='utf-8')

replacements = {
'''<li><b><span dir="ltr">Lifecycle</span></b> — الرحلة الفعلية من <span dir="ltr">Need / URS</span> حتى <span dir="ltr">First Run</span> ثم <span dir="ltr">Performance Review / Retirement</span>.</li>\n<li><b><span dir="ltr">Passport</span></b> — الهوية الرقمية الثابتة للجهاز: ID، النوع، الشركة، الموديل، السيريال، المكان، المسؤول والحالة.</li>\n<li><b><span dir="ltr">Cal & PM</span></b> — <span dir="ltr">Calibration / Qualification / PM / Maintenance / Components</span> وتواريخ الاستحقاق.</li>\n<li><b><span dir="ltr">Events</span></b> — تسجيل العطل أو الحدث كما حدث فعلًا قبل كتابة أي تفسير.</li>\n<li><b><span dir="ltr">Investigation Intelligence</span></b> — ربط المشكلة بتاريخ الجهاز وفصل <span dir="ltr">Observed / Inferred / Unknown</span> وتحديد الخطوة التالية للحصول على دليل.</li>\n<li><b><span dir="ltr">Reports</span></b> — رؤية مجمعة للحالة الحالية والأولويات وتقارير قابلة للمشاركة.</li>\n<li><b><span dir="ltr">Guide / About</span></b> — مرجع للمبادئ، طريقة الاستخدام، وحدود النظام.</li>''':
'''<li><b><span dir="ltr">Instruments</span></b> — سجل الأجهزة، إضافة جهاز، استيراد/تصدير القائمة، ثم فتح <span dir="ltr">Instrument 360</span> لأي جهاز.</li>\n<li><b><span dir="ltr">Instrument 360</span></b> — القصة المتصلة للجهاز: <span dir="ltr">Identity → Lifecycle → Control → Performance → Events → Evidence</span> مع <span dir="ltr">Health Score</span> قابل للتفسير.</li>\n<li><b><span dir="ltr">Lifecycle</span></b> — الرحلة الفعلية من <span dir="ltr">Need / URS</span> حتى <span dir="ltr">First Run</span> ثم <span dir="ltr">Performance Review / Retirement</span>.</li>\n<li><b><span dir="ltr">Cal & PM</span></b> — <span dir="ltr">Calibration / Qualification / PM / Maintenance / Components</span> وتواريخ الاستحقاق.</li>\n<li><b><span dir="ltr">Events</span></b> — تسجيل العطل أو الحدث كما حدث فعلًا قبل كتابة أي تفسير.</li>\n<li><b><span dir="ltr">Investigation Intelligence</span></b> — ربط المشكلة بتاريخ الجهاز وفصل <span dir="ltr">Observed / Inferred / Unknown</span> وتحديد الخطوة التالية للحصول على دليل.</li>\n<li><b><span dir="ltr">Performance</span></b> — تسجيل وتحليل <span dir="ltr">Availability / Utilization</span> واتجاه الأداء الشهري.</li>\n<li><b><span dir="ltr">Reports / Cockpit / Alerts</span></b> — التقارير، الرؤية الإدارية، والإشارات التي تحتاج متابعة حسب الدور.</li>\n<li><b><span dir="ltr">Guide</span></b> — مرجع للمبادئ، طريقة الاستخدام، وحدود النظام.</li>''',

'''<div class="v03-guide-rule"><b>لإضافة عدة أجهزة دفعة واحدة:</b> استخدم <span dir="ltr">MY INSTRUMENTS → Instruments → Import Instrument List</span>. القالب والرفع والمراجعة موجودة هناك، وليس داخل الدليل.</div>''':
'''<div class="v03-guide-rule"><b>التنقل الحالي:</b><br><span dir="ltr">Desktop</span>: استخدم الـSidebar الثابتة واختر القسم.<br><span dir="ltr">Mobile</span>: اضغط <span dir="ltr">☰ Menu · [Current Page]</span> أعلى الشاشة ثم اختر القسم؛ القائمة تغلق ويُفتح القسم المحدد من أعلى الصفحة.<br><br><b>لإضافة عدة أجهزة:</b> استخدم <span dir="ltr">Instruments → Import Instrument List</span>. ويمكنك تنزيل السجل الحالي من <span dir="ltr">Current Instrument Registry</span> ثم تحديث الحقول المعتمدة وإعادة استيراده بعد المراجعة.</div>''',

'''<div class="v03-flow-step"><div class="v03-flow-num">1</div><div><div class="v03-flow-main">أنشئ <span dir="ltr">Passport</span></div><div class="v03-flow-sub">ثبّت هوية الجهاز وبياناته الأساسية أولًا.</div></div></div>''':
'''<div class="v03-flow-step"><div class="v03-flow-num">1</div><div><div class="v03-flow-main">افتح <span dir="ltr">Instruments</span> وأنشئ الجهاز أو استورد القائمة</div><div class="v03-flow-sub">ثبّت الهوية الأساسية أولًا، ثم افتح <span dir="ltr">Instrument 360</span> للجهاز.</div></div></div>''',

'''**بداية اليوم / بداية الشيفت**\n- افتح **Dashboard** أولًا.\n- راجع Calibration overdue، PM overdue، Qualification due، Open OOC، Open Events وPriority Attention Queue.\n- لا تبدأ بالبحث داخل كل جهاز؛ دع الـDashboard يحدد أين تحتاج أن تنظر أولًا.\n''':
'''**بداية اليوم / بداية الشيفت**\n- افتح **Dashboard** أولًا. على الهاتف: **☰ Menu → Dashboard**. على الكمبيوتر: اختر **Dashboard** من الـSidebar.\n- راجع Calibration overdue، PM overdue، Qualification due، Open OOC، Open Events وPriority Attention Queue.\n- لا تبدأ بالبحث داخل كل جهاز؛ دع الـDashboard يحدد أين تحتاج أن تنظر أولًا.\n\n**عند مراجعة جهاز محدد**\n- اذهب إلى **Instruments → Open Instrument 360** واختر الجهاز.\n- اقرأ أولًا **Health Score + Status + Open Events + Availability + Utilization**.\n- افتح **Why this score?** لفهم العوامل المؤثرة بدون تحويل الإشارة إلى حكم GMP.\n- راجع **Management Attention** إذا ظهر تعارض بين الحالة التشغيلية والدليل المرتبط داخل التطبيق.\n''',

'''**عند إغلاق المشكلة**\n- اربط Investigation reference / evidence والنتيجة النهائية.\n- حافظ على الفرق بين Confirmed Root Cause وProbable وNot Yet Identified.\n''':
'''**عند إغلاق المشكلة**\n- اربط Investigation reference / evidence والنتيجة النهائية.\n- حافظ على الفرق بين Confirmed Root Cause وProbable وNot Yet Identified.\n\n**عند تسجيل الأداء الشهري**\n- افتح **Performance**، اختر الجهاز والشهر، ثم أدخل: Scheduled Service Hours، Planned Downtime، Unplanned Downtime، Productive Run Hours.\n- التطبيق يحسب تلقائيًا Planned Operating Time، Available Time، Availability وUtilization.\n- يمكن مراجعة أحدث القيم والاتجاه من داخل **Instrument 360 → PERFORMANCE** لنفس الجهاز.\n''',
}
for old, new in replacements.items():
    if old not in g:
        raise SystemExit('Guide anchor not found:\n' + old[:160])
    g = g.replace(old, new, 1)
guide.write_text(g, encoding='utf-8')

# 3) Official PDF: keep 19-page structure, refresh current-product wording
pdf = Path('instrument_product_guide_pdf.py')
p = pdf.read_text(encoding='utf-8')

pdf_replacements = {
'''    story.append(Paragraph('IDENTITY | LIFECYCLE | CONTROL | PERFORMANCE | EVENTS | COMPONENTS | EVIDENCE',styles['quote']))\n    story.append(Paragraph('The Instrument Passport acts as the persistent identity layer: Instrument ID, type, manufacturer, model, serial number, location, responsible team, operational status and key due dates.',styles['body']))\n    story.append(RTLBlock('بدل أن تبدأ كل مشكلة بالبحث عن بيانات الجهاز الأساسية، يصبح للجهاز Passport رقمي ثابت يربط الهوية بالحالة التشغيلية والتواريخ الحرجة وباقي التاريخ.'))\n    story.append(_table([['VIEW','WHAT IT CONNECTS'],['Passport','Identity, ownership, status, due dates'],['Lifecycle','Need, URS, acquisition, qualification, release, first run, retirement'],['Control','Calibration, qualification, PM, maintenance, components'],['Events','Observed failures and operational signals'],['Investigation','Expected, observed, changed, unchanged, evidence and next action'],['Performance','Availability, utilization, downtime and historical trends']],[45*mm,119*mm])); story.append(PageBreak())''':
'''    story.append(Paragraph('IDENTITY | LIFECYCLE | CONTROL | PERFORMANCE | EVENTS | COMPONENTS | EVIDENCE',styles['quote']))\n    story.append(Paragraph('Open Instruments, choose an asset, then open Instrument 360. The first layer shows an explainable Health Score, operational status, open events, latest Availability and Utilization before the user drills into evidence.',styles['body']))\n    story.append(RTLBlock('بدل أن تبدأ كل مشكلة بالبحث عن بيانات الجهاز الأساسية، يفتح المستخدم Instrument 360 ليرى القصة المتصلة للجهاز وأهم إشارات القرار أولًا. الـHealth Score إشارة أولوية قابلة للتفسير وليست حكم امتثال أو قرار Release أو Root Cause.'))\n    story.append(_table([['VIEW','WHAT IT CONNECTS'],['Identity','Instrument ID, manufacturer, model, serial, location and ownership'],['Lifecycle','Need, URS, acquisition, qualification, release, first run, retirement'],['Control','Calibration, qualification, PM, maintenance and components'],['Performance','Availability, utilization, available time and monthly trend'],['Events','Observed failures, status and active-event context'],['Evidence','Missing evidence, references, QR passport and traceability']],[45*mm,119*mm])); story.append(PageBreak())''',

'''    story.append(Paragraph('Performance views connect Scheduled Service Hours, Planned Downtime, Unplanned Downtime and Productive Run Time.',styles['body']))''':
'''    story.append(Paragraph('Performance can be recorded from the Performance workspace and reviewed again inside the selected Instrument 360. The monthly record connects Scheduled Service Hours, Planned Downtime, Unplanned Downtime and Productive Run Time.',styles['body']))''',

'''    story.append(Paragraph('The Excel importer follows strict mapping: only recognized headers are imported. Unknown columns are shown and ignored rather than silently guessed. Users can preview recognized fields before import.',styles['body']))\n    story.append(RTLBlock('الفكرة ليست أن نجبر المعمل على إعادة إدخال كل شيء يدويًا. نبدأ من البيانات الموجودة، لكن بدون تخمين في معنى الأعمدة. إذا لم يكن الحقل واضحًا يظل Missing بدل أن نخترع Mapping غير موثوق.'))\n    story.append(Paragraph('Camera-assisted entry can reduce transcription errors for manufacturer, model and serial-number information during new instrument registration.',styles['body'])); story.append(PageBreak())''':
'''    story.append(Paragraph('The Instruments workspace supports three controlled paths: add one instrument, import an instrument list, or export the current registry using the same recognized headers for a reviewed round trip.',styles['body']))\n    story.append(RTLBlock('الفكرة ليست أن نجبر المعمل على إعادة إدخال كل شيء يدويًا. يمكن تنزيل Current Instrument Registry وتحديث الحقول المعتمدة ثم إعادة الاستيراد بعد Preview. الأعمدة غير المعروفة تظل ignored بدل تخمين معناها، والبيانات غير المتاحة تظل Missing Evidence.'))\n    story.append(Paragraph('Camera-assisted entry can reduce transcription errors for manufacturer, model and serial-number information during new instrument registration.',styles['body'])); story.append(PageBreak())''',

'''    steps=[['1','Open Passport','Confirm exact asset, status and responsibility.'],['2','Review Control','Check calibration, PM, maintenance and component history.'],['3','Create Event','Record pressure fluctuation as an observation - not pump failure.'],['4','Investigate','Compare expected vs actual, changed vs unchanged, and objective evidence.'],['5','Test','Choose one discriminating next evidence action.'],['6','Confirm','Separate pattern from confirmed root cause.'],['7','Learn','Carry the verified outcome into performance review and future investigations.']]''':
'''    steps=[['1','Open Instrument 360','Confirm the exact asset, Health Score, status and responsibility.'],['2','Review Control','Check calibration, PM, maintenance and component history.'],['3','Create Event','Record pressure fluctuation as an observation - not pump failure.'],['4','Investigate','Compare expected vs actual, changed vs unchanged, and objective evidence.'],['5','Test','Choose one discriminating next evidence action.'],['6','Confirm','Separate pattern from confirmed root cause.'],['7','Learn','Carry the verified outcome into performance review and future investigations.']]''',

'''    story.append(RTLBlock('اختلاف الواجهة حسب الدور هدفه ترتيب الأولويات وليس تغيير الحقائق. نفس الجهاز ونفس الدليل، لكن كل مستوى يرى القرارات التي تخص مسؤوليته أولًا.')); story.append(PageBreak())''':
'''    story.append(RTLBlock('اختلاف الواجهة حسب الدور هدفه ترتيب الأولويات وليس تغيير الحقائق. نفس الجهاز ونفس الدليل، لكن كل مستوى يرى القرارات التي تخص مسؤوليته أولًا.'))\n    story.append(Paragraph('NAVIGATION: Desktop uses the persistent sidebar. Mobile uses the compact top menu (Menu · Current Page); selecting a workspace closes the menu and opens the selected page from the top.',styles['small']))\n    story.append(RTLBlock('التنقل متجاوب مع الجهاز: على الكمبيوتر Sidebar ثابتة، وعلى الهاتف قائمة علوية مختصرة. تغيير Job Role يعيد ترتيب تجربة المستخدم ولا يساوي منح صلاحيات أمنية جديدة.',size=9.2,leading=14,space_after=5)); story.append(PageBreak())''',
}
for old, new in pdf_replacements.items():
    if old not in p:
        raise SystemExit('PDF guide anchor not found:\n' + old[:180])
    p = p.replace(old, new, 1)
pdf.write_text(p, encoding='utf-8')

print('Final release UX and guides updated')
