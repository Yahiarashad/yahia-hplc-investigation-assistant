from pathlib import Path

# --- In-app guide -----------------------------------------------------------
gp = Path('instrument_v03_user_guide.py')
g = gp.read_text(encoding='utf-8')

imp = 'from instrument_product_guide_pdf import build_product_user_guide_pdf\n'
if 'from instrument_guide_visuals import guide_visual_bytes\n' not in g:
    if imp not in g:
        raise SystemExit('Guide import anchor missing')
    g = g.replace(imp, imp + 'from instrument_guide_visuals import guide_visual_bytes\n', 1)

anchor = '            st.info("قاعدة الاستخدام: ENTER LESS. DECIDE BETTER. KEEP THE INSTRUMENT STORY CONNECTED.")'
visual_block = '''            st.markdown("### 📸 Visual walkthrough من التطبيق")\n            st.caption("لقطات Demo نظيفة توضح أين تقرأ الإشارة وكيف تنتقل من Overview إلى Attention. الصور للتدريب ولا تمثل سجل GMP رسمي.")\n            _shot_overview = guide_visual_bytes("instrument_360_overview")\n            if _shot_overview:\n                st.image(_shot_overview, caption="Step 4 · Instruments → Open Instrument 360: اقرأ Health Score وStatus وOpen Events وAvailability وUtilization أولًا.", width=260)\n            _shot_attention = guide_visual_bytes("instrument_360_attention")\n            if _shot_attention:\n                st.image(_shot_attention, caption="Management Attention: إشارة اتساق Evidence تحتاج مراجعة، وليست حكم Compliance أو Root Cause.", width=260)\n\n'''
if visual_block.strip() not in g:
    if anchor not in g:
        raise SystemExit('Workflow visual insertion anchor missing')
    g = g.replace(anchor, visual_block + anchor, 1)

gp.write_text(g, encoding='utf-8')

# --- Official PDF -----------------------------------------------------------
pp = Path('instrument_product_guide_pdf.py')
p = pp.read_text(encoding='utf-8')

old_import = 'from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Flowable\n'
new_import = 'from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Flowable, Image as RLImage\n'
if new_import not in p:
    if old_import not in p:
        raise SystemExit('PDF platypus import anchor missing')
    p = p.replace(old_import, new_import, 1)

shape_import = 'from bidi.algorithm import get_display\n'
if 'from instrument_guide_visuals import guide_visual_bytes\n' not in p:
    if shape_import not in p:
        raise SystemExit('PDF visual import anchor missing')
    p = p.replace(shape_import, shape_import + 'from instrument_guide_visuals import guide_visual_bytes\n', 1)

section_anchor = '''def _section(story, styles, number, title, arabic_title=None):\n    story.append(Paragraph(f'{number}. {title}', styles['h1']))\n    if arabic_title:\n        story.append(RTLBlock(arabic_title, size=13, leading=19, color=NAVY, bold=True, space_after=8))\n    story.append(GoldRule()); story.append(Spacer(1,4*mm))\n\n'''
helper = '''def _guide_screenshot(name: str, width=52*mm):\n    data = guide_visual_bytes(name)\n    if not data:\n        return Spacer(1, 0)\n    ratios = {\n        "instrument_360_overview": 367/200,\n        "instrument_360_attention": 370/200,\n    }\n    height = width * ratios.get(name, 1.82)\n    img = RLImage(BytesIO(data), width=width, height=height)\n    img.hAlign = 'CENTER'\n    return img\n\n\n'''
if helper.strip() not in p:
    if section_anchor not in p:
        raise SystemExit('PDF helper anchor missing')
    p = p.replace(section_anchor, section_anchor + helper, 1)

old_s5 = "    story.append(_table([['VIEW','WHAT IT CONNECTS'],['Identity','Instrument ID, manufacturer, model, serial, location and ownership'],['Lifecycle','Need, URS, acquisition, qualification, release, first run, retirement'],['Control','Calibration, qualification, PM, maintenance and components'],['Performance','Availability, utilization, available time and monthly trend'],['Events','Observed failures, status and active-event context'],['Evidence','Missing evidence, references, QR passport and traceability']],[45*mm,119*mm])); story.append(PageBreak())\n"
new_s5 = "    story.append(_table([['VIEW','WHAT IT CONNECTS'],['Identity','Instrument ID, manufacturer, model, serial, location and ownership'],['Lifecycle','Need, URS, acquisition, qualification, release, first run, retirement'],['Control','Calibration, qualification, PM, maintenance and components'],['Performance','Availability, utilization, available time and monthly trend'],['Events','Observed failures, status and active-event context'],['Evidence','Missing evidence, references, QR passport and traceability']],[45*mm,119*mm]))\n    story.append(Spacer(1,4*mm)); story.append(_guide_screenshot('instrument_360_overview'))\n    story.append(Paragraph('Actual app view - Instrument 360 overview using synthetic demonstration data.', styles['small']))\n    story.append(PageBreak())\n"
if "Actual app view - Instrument 360 overview" not in p:
    if old_s5 not in p:
        raise SystemExit('PDF section 5 visual anchor missing')
    p = p.replace(old_s5, new_s5, 1)

old_s13 = "    story.append(Paragraph('HPLC example: open Instrument 360 > review Control and Performance > create the event as pressure fluctuation, not pump failure > investigate expected vs actual and recent changes > choose one discriminating evidence action > confirm before root-cause disposition > carry the verified outcome into the asset history.',styles['body']))\n    story.append(PageBreak())\n"
new_s13 = "    story.append(Paragraph('HPLC example: open Instrument 360 > review Control and Performance > create the event as pressure fluctuation, not pump failure > investigate expected vs actual and recent changes > choose one discriminating evidence action > confirm before root-cause disposition > carry the verified outcome into the asset history.',styles['body']))\n    story.append(Spacer(1,4*mm)); story.append(_guide_screenshot('instrument_360_attention'))\n    story.append(Paragraph('Actual app view - explainable Health Score and Management Attention signal. Decision-support only.', styles['small']))\n    story.append(PageBreak())\n"
if "Actual app view - explainable Health Score" not in p:
    if old_s13 not in p:
        raise SystemExit('PDF section 13 visual anchor missing')
    p = p.replace(old_s13, new_s13, 1)

pp.write_text(p, encoding='utf-8')
print('Guide screenshots embedded in app guide and official PDF')
