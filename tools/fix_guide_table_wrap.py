from pathlib import Path

p=Path('instrument_product_guide_pdf.py')
s=p.read_text(encoding='utf-8')

old="""def _table(data, widths, header=True):
    t=Table(data,colWidths=widths,repeatRows=1 if header else 0,hAlign='LEFT')
    style=[('VALIGN',(0,0),(-1,-1),'TOP'),('GRID',(0,0),(-1,-1),.35,LINE),('FONTSIZE',(0,0),(-1,-1),8.1),('LEADING',(0,0),(-1,-1),11),('LEFTPADDING',(0,0),(-1,-1),6),('RIGHTPADDING',(0,0),(-1,-1),6),('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6)]
    if header:
        style += [('BACKGROUND',(0,0),(-1,0),NAVY),('TEXTCOLOR',(0,0),(-1,0),WHITE),('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),('ROWBACKGROUNDS',(0,1),(-1,-1),[WHITE,PALE])]
    t.setStyle(TableStyle(style)); return t
"""
new="""def _table(data, widths, header=True):
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
"""
if old not in s:
    raise SystemExit('table function anchor missing')
s=s.replace(old,new,1)
p.write_text(s,encoding='utf-8')
print('Guide PDF tables now wrap long text')
