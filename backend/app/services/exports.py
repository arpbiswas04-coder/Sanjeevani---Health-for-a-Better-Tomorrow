import csv
import io
import json
from xml.sax.saxutils import escape
from fastapi.encoders import jsonable_encoder


def cell(value):
    if isinstance(value,(dict,list)):
        value=json.dumps(value,ensure_ascii=True)
    if value is None:
        return ''
    if isinstance(value,str) and value.lstrip().startswith(('=','+','-','@','\t','\r','\n')):
        return "'"+value
    return value


def export(rows,format):
    rows=jsonable_encoder(rows)
    headers=list(rows[0]) if rows else ['No records']
    values=[[cell(row.get(k)) for k in headers] for row in rows]
    if format=='csv':
        stream=io.StringIO(newline='')
        writer=csv.writer(stream)
        writer.writerow(headers)
        writer.writerows(values)
        return stream.getvalue().encode('utf-8-sig'),'text/csv; charset=utf-8'
    if format=='xlsx':
        from openpyxl import Workbook
        stream=io.BytesIO()
        workbook=Workbook(write_only=True)
        sheet=workbook.create_sheet('Report')
        sheet.append(headers)
        for row in values:
            sheet.append(row)
        workbook.save(stream)
        return stream.getvalue(),'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,KeepTogether
    stream=io.BytesIO()
    styles=getSampleStyleSheet()
    story=[Paragraph('Sanjeevani operational report',styles['Title'])]
    # Record layout wraps long identifiers; JSON escapes preserve non-Latin values
    # without silently substituting unsupported glyphs in standard PDF fonts.
    for index,row in enumerate(rows,1):
        story.append(Paragraph(f'Record {index}',styles['Heading3']))
        for key,value in row.items():
            text=json.dumps(value,ensure_ascii=True) if value is not None else ''
            story.append(Paragraph(escape(key)+': '+escape(text),styles['BodyText']))
        story.append(Spacer(1,8))
    if not rows:
        story.append(Paragraph('No records matched the filters.',styles['BodyText']))
    SimpleDocTemplate(stream,pagesize=A4).build(story)
    return stream.getvalue(),'application/pdf'
