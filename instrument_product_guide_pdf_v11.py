from __future__ import annotations
from io import BytesIO
from pathlib import Path
from xml.sax.saxutils import escape
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Flowable, Image as RLImage
try:
    import arabic_reshaper
    from bidi.algorithm import get_display
except Exception:
    arabic_reshaper = None; get_display = None

NAVY=colors.HexColor('#0B1F33'); NAVY2=colors.HexColor('#12324F'); GOLD=colors.HexColor('#C9A54D')
SLATE=colors.HexColor('#5F6F80'); INK=colors.HexColor('#1D2E3F'); PALE=colors.HexColor('#F5F8FB')
LINE=colors.HexColor('#D9E2EA'); WHITE=colors.white; BLUE=colors.HexColor('#EEF5FB'); GREEN=colors.HexColor('#EDF8F1'); CREAM=colors.HexColor('#FFF9E6')
ASSET_DIR=Path(__file__).resolve().parent/'guide_assets'/'screenshots'

def _fonts():
    pairs=[('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf','/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'),('/usr/share/fonts/truetype/freefont/FreeSans.ttf','/usr/share/fonts/truetype/freefont/FreeSansBold.ttf')]
    for r,b in pairs:
        if Path(r).exists() and Path(b).exists():
            if 'YQII_AR' not in pdfmetrics.getRegisteredFontNames(): pdfmetrics.registerFont(TTFont('YQII_AR',r))
            if 'YQII_ARB' not in pdfmetrics.getRegisteredFontNames(): pdfmetrics.registerFont(TTFont('YQII_ARB',b))
            return 'YQII_AR','YQII_ARB'
    return 'Helvetica','Helvetica-Bold'
REG,BOLD=_fonts()
def _shape(s):
    s=str(s)
    return get_display(arabic_reshaper.reshape(s)) if arabic_reshaper and get_display else s

class RTL(Flowable):
    def __init__(self,text,size=11,leading=17,bold=False,color=INK): super().__init__(); self.text=str(text); self.size=size; self.leading=leading; self.font=BOLD if bold else REG; self.color=color
    def wrap(self,w,h):
        words=self.text.split(); self.lines=[]; cur=[]
        for word in words:
            c=' '.join(cur+[word])
            if cur and pdfmetrics.stringWidth(_shape(c),self.font,self.size)>w: self.lines.append(' '.join(cur)); cur=[word]
            else: cur.append(word)
        if cur: self.lines.append(' '.join(cur))
        self.w=w; self.width=w; self.height=max(1,len(self.lines))*self.leading; return self.width,self.height
    def draw(self):
        self.canv.setFont(self.font,self.size); self.canv.setFillColor(self.color); y=self.height-self.leading
        for line in self.lines: self.canv.drawRightString(self.w,y,_shape(line)); y-=self.leading

def styles():
    s=getSampleStyleSheet()
    return {'h1':ParagraphStyle('h1v11',parent=s['Heading1'],fontName=BOLD,fontSize=18.5,leading=23,textColor=NAVY,spaceAfter=5),'body':ParagraphStyle('bodyv11',parent=s['BodyText'],fontName=REG,fontSize=9.2,leading=13.7,textColor=INK,spaceAfter=5),'small':ParagraphStyle('smallv11',parent=s['BodyText'],fontName=REG,fontSize=7.5,leading=10.5,textColor=SLATE),'quote':ParagraphStyle('quotev11',parent=s['BodyText'],fontName=BOLD,fontSize=11.7,leading=16.5,textColor=NAVY),'label':ParagraphStyle('labelv11',parent=s['BodyText'],fontName=BOLD,fontSize=7.2,leading=9.5,textColor=GOLD),'card':ParagraphStyle('cardv11',parent=s['BodyText'],fontName=REG,fontSize=8.3,leading=12,textColor=INK),'center':ParagraphStyle('centerv11',parent=s['BodyText'],fontName=BOLD,fontSize=10.5,leading=15,textColor=NAVY,alignment=TA_CENTER)}

def header(canvas,doc):
    canvas.saveState(); w,h=A4
    if doc.page>1:
        canvas.setStrokeColor(GOLD); canvas.line(15*mm,13*mm,w-15*mm,13*mm); canvas.setFillColor(SLATE); canvas.setFont(REG,7)
        canvas.drawString(15*mm,8.5*mm,'Yahia QC Instrument Intelligence - Official Guide v1.1'); canvas.drawRightString(w-15*mm,8.5*mm,f'Page {doc.page}')
    canvas.restoreState()

def cover(canvas,doc):
    canvas.saveState(); w,h=A4; canvas.setFillColor(NAVY); canvas.rect(0,0,w,h,0,1); canvas.setFillColor(NAVY2); canvas.circle(w*.86,h*.82,74*mm,0,1)
    canvas.setStrokeColor(GOLD); canvas.roundRect(16*mm,18*mm,w-32*mm,h-36*mm,8*mm,1,0); canvas.setFillColor(GOLD); canvas.setFont(BOLD,9.4); canvas.drawString(22*mm,h-35*mm,'PHARMACEUTICAL QC - INSTRUMENT INTELLIGENCE')
    canvas.setFillColor(WHITE); canvas.setFont(BOLD,25); canvas.drawString(22*mm,h-58*mm,'YAHIA QC'); canvas.drawString(22*mm,h-70*mm,'INSTRUMENT INTELLIGENCE')
    canvas.setFont(REG,11.4); canvas.setFillColor(colors.HexColor('#D8E1E9')); canvas.drawString(22*mm,h-87*mm,'User Manual - Training Guide - Product Demo')
    canvas.setFillColor(GOLD); canvas.roundRect(22*mm,h-112*mm,132*mm,14*mm,4*mm,0,1); canvas.setFillColor(NAVY); canvas.setFont(BOLD,9.7); canvas.drawCentredString(88*mm,h-107*mm,"DON'T GUESS. FOLLOW THE EVIDENCE.")
    canvas.setFillColor(WHITE); canvas.setFont(BOLD,13.2); canvas.drawString(22*mm,55*mm,'OFFICIAL GUIDE v1.1'); canvas.setFont(REG,7.2); canvas.setFillColor(colors.HexColor('#92A4B5')); canvas.drawString(22*mm,28*mm,'Decision-support prototype. Not a validated GxP system of record.'); canvas.restoreState()

def section(st,sty,n,title,ar): st += [Paragraph(f'{n}. {escape(title)}',sty['h1']),RTL(ar,size=12.2,leading=18,bold=True,color=NAVY),Spacer(1,1*mm)]
def table(rows,widths,sty):
    body=ParagraphStyle('tbv11',fontName=REG,fontSize=7.4,leading=9.5,textColor=INK); head=ParagraphStyle('thv11',fontName=BOLD,fontSize=7.2,leading=9.3,textColor=WHITE)
    r=[[Paragraph(escape(str(c)),head if i==0 else body) for c in row] for i,row in enumerate(rows)]; t=Table(r,colWidths=widths,repeatRows=1,hAlign='LEFT')
    t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),NAVY),('ROWBACKGROUNDS',(0,1),(-1,-1),[WHITE,PALE]),('GRID',(0,0),(-1,-1),.35,LINE),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),5),('RIGHTPADDING',(0,0),(-1,-1),5),('TOPPADDING',(0,0),(-1,-1),4),('BOTTOMPADDING',(0,0),(-1,-1),4)])); return t

def shot(name,max_w=160*mm,max_h=105*mm):
    p=ASSET_DIR/name; iw,ih=ImageReader(str(p)).getSize(); k=min(float(max_w)/iw,float(max_h)/ih); im=RLImage(str(p),width=iw*k,height=ih*k); im.hAlign='CENTER'; return im

def cards(sty,goal,where,steps,see,value):
    out=[]
    for label,text,bg in [('GOAL',goal,PALE),('WHERE TO GO',where,BLUE),('STEPS',steps,WHITE),('WHAT YOU SHOULD SEE',see,GREEN),('DECISION VALUE',value,CREAM)]:
        c=Table([[Paragraph(label,sty['label'])],[Paragraph(escape(text),sty['card'])]],colWidths=[160*mm]); c.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),bg),('BOX',(0,0),(-1,-1),.35,LINE),('LEFTPADDING',(0,0),(-1,-1),7),('RIGHTPADDING',(0,0),(-1,-1),7),('TOPPADDING',(0,0),(-1,-1),4),('BOTTOMPADDING',(0,0),(-1,-1),4)])); out.append([c])
    t=Table(out,colWidths=[164*mm]); t.setStyle(TableStyle([('TOPPADDING',(0,0),(-1,-1),1.4),('BOTTOMPADDING',(0,0),(-1,-1),1.4)])); return t

WORKFLOWS=[
('Navigation: Mobile and Desktop','التنقل داخل التطبيق','Move between major workspaces without losing context.','Mobile: Menu - Current Page. Desktop: persistent sidebar.','Choose the workspace, continue from the top of that page, and use ACCOUNT for role change or logout.','A stable role-aware page structure on mobile and desktop.','Navigation changes priorities, not underlying evidence.','dashboard_context.jpg'),
('Start from the Dashboard','ابدأ الشيفت من لوحة البداية','Start the session with the product purpose and workspace context.','Dashboard / landing page.','Sign in, confirm context, then move to the operational page needed for the shift.','A welcome card describing lifecycle, maintenance, failures, components and investigations.','The dashboard frames the product as an evidence-first workspace.','dashboard_context.jpg'),
('Go to Instruments and Open Instrument 360','الوصول إلى الجهاز وفتح Instrument 360','Open the main instrument workspace and select one asset.','Instruments.','Add one instrument, import/update a list, or review the current registry, then select an asset under Open Instrument 360.','Registry controls plus the selected asset card.','The registry bridges raw instrument data and structured review.','registry_open_360.jpg'),
('Instrument 360: Connected Asset Story','قصة الجهاز في مكان واحد','Review the selected asset as one connected story.','Instrument 360.','Move through Identity, Lifecycle, Control, Performance, Events and Evidence.','Connected evidence layers for the same asset.','One view reduces fragmented searching and supports better handover.','instrument_story.jpg'),
('Understand the Health Score','فهم Health Score','See which instrument may need attention first.','Instrument 360 - top summary.','Read the score, operational status, open events, availability and utilization before drilling down.','Example: 53/100 Critical, Out of Service, with no current performance values.','The score is an explainable prioritization signal, not a compliance verdict.','why_management.jpg'),
('Why the Score and Management Attention','لماذا ظهرت الدرجة وإشارة الإدارة؟','Understand exactly what is driving attention.','Instrument 360 - Why score / Management Attention.','Open Why XX/100, review drivers, then open Why am I seeing this? when a management signal appears.','Example drivers: Out of Service and qualification overdue; attention: no active linked event.','Management Attention is an evidence-consistency signal only.','why_management.jpg'),
('Review Identity','مراجعة هوية الجهاز','Confirm the correct asset is being reviewed.','Instrument 360 - IDENTITY.','Check Instrument ID, name, type, manufacturer, model, serial, location and responsible team.','Structured identity evidence for the selected instrument.','Correct identity is the foundation for traceability.','instrument_story.jpg'),
('Review Lifecycle','مراجعة دورة حياة الجهاز','Review lifecycle history or identify missing lifecycle entry.','Instrument 360 - LIFECYCLE.','Open Lifecycle and review qualification / maintenance / calibration history and lifecycle context.','Recorded history, or a clear no-history-yet message.','The user can distinguish missing app data from documented evidence.','instrument_story.jpg'),
('Review Control','مراجعة حالة التحكم الحالية','See current due-date pressure and control status.','Instrument 360 - CONTROL.','Review qualification, PM and calibration due dates and any current score explanation.','Due dates with overdue or remaining-time status.','Control data helps prioritize follow-up without making GMP disposition.','instrument_story.jpg'),
('Review Performance','مراجعة Availability و Utilization','Check whether current monthly performance context exists.','Instrument 360 - PERFORMANCE / Performance workspace.','Review the latest month; if absent, record Scheduled, Planned Downtime, Unplanned Downtime and Productive Run hours.','Availability / Utilization context or a prompt to record the first month.','Performance connects asset status with real operating capacity.','instrument_story.jpg'),
('Review Events','مراجعة الأعطال والإشارات','Check whether failures or instrument events are linked.','Instrument 360 - EVENTS.','Review current linkage, then open Event / Failure Log when an event needs to be created or reviewed.','Event history or a clear no-events-yet state.','Event context prevents interpretation without checking known failures.','instrument_story.jpg'),
('Review Evidence and QR Digital Passport','مراجعة الدليل والتتبع','Review traceability evidence and reopen the same asset securely.','Instrument 360 - EVIDENCE.','Review reference status and missing evidence; use the QR Digital Passport after authentication.','Evidence summary, reference status and QR access point.','Evidence keeps the asset story traceable while access remains controlled.','instrument_story.jpg'),
('Edit an Instrument','تحديث بيانات الجهاز','Keep the instrument record current.','Instrument 360 - Edit instrument.','Update identity, status, team, due dates and notes, then Save changes.','A structured editable form.','Current data improves every downstream decision-support view.','edit_delete.jpg'),
('Retire or Delete an Instrument','التكهين أو الحذف بعناية','Prevent accidental destructive actions.','Instrument 360 - Retire / delete instrument.','Read the warning, export first if needed, type the Instrument ID to confirm, and proceed only according to governance.','A destructive-action warning and explicit confirmation field.','Deletion may cascade to linked history; retention must follow approved governance.','edit_delete.jpg')]

def build_product_user_guide_pdf():
    sty=styles(); out=BytesIO(); doc=SimpleDocTemplate(out,pagesize=A4,leftMargin=16*mm,rightMargin=16*mm,topMargin=16*mm,bottomMargin=18*mm,title='Yahia QC Instrument Intelligence - Official Guide v1.1',author='Yahia Abdelhalim'); st=[Spacer(1,245*mm),PageBreak()]
    section(st,sty,1,'What This Application Is','ما هي هذه المنصة؟'); st += [Paragraph('Yahia QC Instrument Intelligence connects instrument identity, lifecycle, control status, performance context, events and traceability evidence into one evidence-first workspace.',sty['body']),RTL('المنصة تجمع قصة الجهاز في مكان واحد لتساعد فريق QC على رؤية الحالة والفجوات والأدلة التي تحتاج متابعة قبل القرار التالي.'),Paragraph('IDENTITY > LIFECYCLE > CONTROL > PERFORMANCE > EVENTS > EVIDENCE',sty['quote']),PageBreak()]
    section(st,sty,2,'Why This Platform Exists','لماذا تم بناء هذه المنصة؟'); st += [Paragraph('Most laboratories already have data. The real problem is that the instrument story is fragmented across trackers, records, emails, folders and individual memory.',sty['body']),table([['BEFORE','WITH THE PLATFORM'],['Scattered trackers','One connected asset story'],['Dates without context','Lifecycle + control + performance context'],['Reactive follow-up','Visible attention signals'],['Knowledge in memory','Shared role-aware workspace'],['Hard-to-reuse history','Evidence supports the next decision']],[77*mm,87*mm],sty),RTL('القيمة ليست استبدال Excel بواجهة أجمل، بل تحويل البيانات المتفرقة إلى سياق تشغيلي يساعد على اتخاذ قرار أسرع وأوضح وبأقل تخمين.'),PageBreak()]
    section(st,sty,3,'Important Scope and Intended Use','حدود الاستخدام المقصود'); st += [Paragraph('This product is decision-support software and is not currently presented as a validated GxP system of record.',sty['quote']),table([['THE APP MAY SUPPORT','THE APP DOES NOT CLAIM'],['Prioritization and visibility','Automatic GMP disposition'],['Evidence follow-up','Automatic root-cause determination'],['Lifecycle context','Proof of compliance on its own'],['Operational intelligence','Replacement of approved quality records'],['Traceability support','Release decision authority']],[82*mm,82*mm],sty),RTL('السجلات الرسمية وRaw Data والانحرافات وCAPA والشهادات والموافقات تظل في الأنظمة المعتمدة للمؤسسة.'),PageBreak()]
    n=4
    for title,ar,goal,where,steps,see,value,img in WORKFLOWS:
        section(st,sty,n,title,ar); st += [cards(sty,goal,where,steps,see,value),Spacer(1,3*mm),shot(img,max_w=164*mm,max_h=88*mm),PageBreak()]; n+=1
    section(st,sty,n,'Events and Investigation Intelligence','التحقيق يبدأ بما حدث فعلًا'); st += [Paragraph('The investigation model deliberately separates evidence states before asking for conclusions.',sty['body']),table([['EVIDENCE STATE','MEANING'],['OBSERVED / REPORTED','What is actually known or directly reported.'],['INFERRED','A supported interpretation, not yet confirmed fact.'],['UNKNOWN','Information still required before a controlled conclusion.']],[48*mm,116*mm],sty),Paragraph('Expected > Observed > Changed > Unchanged > Objective Evidence > Next Evidence Action',sty['quote']),RTL('تكرار نفس النمط يقوي الفرضية لكنه لا يثبت Root Cause بمفرده. المطلوب Evidence يميز بين الفرضيات ثم تأكيد النتيجة قبل أي disposition رسمي.'),PageBreak()]; n+=1
    section(st,sty,n,'Daily Working Flow','مسار العمل اليومي'); st += [table([['STEP','ACTION'],['1','Start from Dashboard and review role-relevant attention.'],['2','Open Instruments and select the asset.'],['3','Read Health Score and Why score before drilling down.'],['4','Review Identity > Lifecycle > Control > Performance > Events > Evidence.'],['5','Update only what is supported by evidence.'],['6','Create / review events and investigate with evidence-state separation.'],['7','Use Reports / Cockpit / Alerts for management follow-up.'],['8','ACCOUNT > Logout to end the session.']],[24*mm,140*mm],sty),RTL('المسار العملي ثابت: سجل فقط ما لديك كدليل، راجع ما تغير، ثم انتقل من الإشارة إلى القرار التالي. لا تستخدم الفراغات كدعوة للتخمين.'),PageBreak()]; n+=1
    section(st,sty,n,'Product Boundary and Decision Value','القيمة وحدود الادعاء'); st += [table([['THE PRODUCT SUPPORTS','THE PRODUCT DOES NOT REPLACE'],['Priority visibility','Validated GxP system of record'],['Connected instrument context','Approved deviations / CAPA / quality records'],['Explainable attention signals','GMP disposition authority'],['Evidence gaps and traceability','Root-cause confirmation without evidence'],['Operational / capacity intelligence','Human review and governance']],[82*mm,82*mm],sty),Spacer(1,7*mm),Paragraph('ENTER LESS. DECIDE BETTER. KEEP THE INSTRUMENT STORY CONNECTED.',sty['quote']),RTL('الفكرة ليست أن تمتلك Dashboard أكثر. الفكرة أن تعرف ما الذي يحتاج انتباهك الآن، ما الدليل الذي ينقصك، وما القرار التالي الذي تستطيع الدفاع عنه.',size=11.4,leading=18,bold=True),Spacer(1,10*mm),Paragraph('Yahia QC Instrument Intelligence',sty['center'])]
    doc.build(st,onFirstPage=cover,onLaterPages=header); out.seek(0); return out.getvalue()
