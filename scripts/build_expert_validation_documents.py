"""Export proposed expert-review documents; never generate responses or expert scores.

Uses stdlib OOXML for editable DOCX and the existing PyMuPDF installation for PDF.
No model inputs, tuning outputs, or original thesis PDFs are modified.
"""
from __future__ import annotations
import csv
from datetime import datetime, timezone
import hashlib
import html
import json
from pathlib import Path
import re
import zipfile
from xml.sax.saxutils import escape

import pymupdf

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "docs/expert_validation"
OUTPUT = ROOT / "artifacts/expert_validation"
TITLES = {
    "chapter3_revised": "Chapter 3 - Revised Model Evaluation and Expert Validation",
    "questionnaire": "Expert Evaluation Questionnaire",
    "administration_and_scoring": "Expert Review - Administration and Scoring Guide",
    "review_notes": "Thesis Review Notes and Integration Checklist",
}
DIMENSIONS = {
    "Legal Coherence": ["B1", "B4", "C1", "C2", "C3", "C4"],
    "Thematic Relevance": ["B3", "B5", "B6"],
    "Label Appropriateness": ["B2"],
    "Temporal Interpretation": ["D1", "D2", "D3", "D4"],
    "Overall Research Quality": ["E1", "E2"],
}


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def blocks(markdown):
    """Parse only the simple headings, paragraphs, tables and page breaks we author."""
    lines = markdown.splitlines()
    result, paragraph = [], []
    def flush():
        if paragraph:
            result.append(("paragraph", " ".join(paragraph)))
            paragraph.clear()
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            flush(); i += 1; continue
        if line == "<!-- pagebreak -->":
            flush(); result.append(("break", "")); i += 1; continue
        if line.startswith("```"):
            flush(); i += 1; code = []
            while i < len(lines) and not lines[i].startswith("```"):
                code.append(lines[i]); i += 1
            result.append(("code", "\n".join(code))); i += 1; continue
        heading = re.match(r"^(#{1,4})\s+(.*)$", line)
        if heading:
            flush(); result.append(("h"+str(len(heading[1])), heading[2])); i += 1; continue
        if line.startswith("|"):
            flush(); rows = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                cells = [x.strip() for x in lines[i].strip().strip("|").split("|")]
                if not all(re.fullmatch(r":?-{3,}:?", x) for x in cells):
                    rows.append(cells)
                i += 1
            result.append(("table", rows)); continue
        if line.startswith("- ") or re.match(r"^\d+\. ", line):
            flush(); result.append(("paragraph", "• "+line[2:] if line.startswith("- ") else line)); i += 1; continue
        if line.startswith("> "):
            line = line[2:]
        paragraph.append(line); i += 1
    flush()
    return result


def plain(value):
    value = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r"\1", value)
    value = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"\1", value)
    return value.replace("**", "").replace("`", "")


def inline_html(value):
    value = html.escape(value)
    value = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", value)
    value = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<em>\1</em>", value)
    value = re.sub(r"`([^`]+)`", r"<code>\1</code>", value)
    value = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r"\1", value)
    return value


def make_html(elements, title, questionnaire=False):
    body = []
    for kind, value in elements:
        if kind.startswith("h"):
            body.append(f"<{kind}>{inline_html(value)}</{kind}>")
        elif kind == "paragraph":
            body.append(f"<p>{inline_html(value)}</p>")
        elif kind == "break":
            body.append('<div style="page-break-before:always"></div>')
        elif kind == "code":
            body.append(f"<pre>{html.escape(value)}</pre>")
        elif kind == "table":
            rows = []
            for i, row in enumerate(value):
                tag = "th" if i == 0 else "td"
                rows.append("<tr>"+"".join(f"<{tag}>{inline_html(cell)}</{tag}>" for cell in row)+"</tr>")
            table_class = ' class="keep-table"' if len(rows) <= 8 else ''
            body.append("<table"+table_class+"><thead>"+rows[0]+"</thead><tbody>"+"".join(rows[1:])+"</tbody></table>")
    size = "10pt" if questionnaire else "11pt"
    css = f"""
    body {{ font-family: {'sans-serif' if questionnaire else 'serif'}; font-size:{size}; line-height:1.2; color:#18202a; }}
    h1 {{ font-size:16pt; margin:10pt 0 7pt; color:#183650; page-break-after:avoid; }}
    h2 {{ font-size:12pt; margin:{'8pt' if questionnaire else '10pt'} 0 5pt; color:#183650; page-break-after:avoid; }}
    h3,h4 {{ font-size:11pt; margin:8pt 0 4pt; page-break-after:avoid; }}
    p {{ margin:0 0 {'3pt' if questionnaire else '5pt'}; }}
    table {{ border-collapse:collapse; width:100%; margin:6pt 0; font-size:9pt; }}
    th,td {{ border:0.5pt solid #9ba8b5; padding:{'3pt' if questionnaire else '4pt'}; vertical-align:top; }}
    th {{ background-color:#eaf0f5; text-align:left; font-weight:bold; }}
    tr,table.keep-table {{ page-break-inside:avoid; }}
    pre,code {{ font-family:monospace; font-size:9pt; white-space:pre-wrap; }}
    @media print {{ body {{ margin:0; }} }}
    """
    document = '<!DOCTYPE html><html><head><meta charset="utf-8"><title>'+html.escape(title)+'</title><style>'+css+'</style></head><body>'+"\n".join(body)+'</body></html>'
    return document, css


def write_pdf(path, document, css, short_title):
    # A4 with consistent margins; final thesis typography will be applied in its source.
    mediabox = pymupdf.paper_rect("a4")
    content = pymupdf.Rect(42, 42, mediabox.width-42, mediabox.height-46)
    story = pymupdf.Story(html=document, user_css=css)
    temporary = path.with_suffix(".working.pdf")
    writer = pymupdf.DocumentWriter(str(temporary))
    story.write(writer, lambda rect_number, filled: (mediabox, content, None))
    writer.close()
    del writer  # Release the Windows file handle before reading/removing the temporary PDF.
    with pymupdf.open(temporary) as pdf:
        for i, page in enumerate(pdf):
            page.insert_text((42, mediabox.height-24), f"EV-1.0 | {short_title} | {i+1} / {len(pdf)}", fontsize=8, color=(.3,.3,.3))
        pdf.set_metadata({"title": short_title, "subject": "Proposed expert-review instrument; no completed expert ratings", "author": "Research team"})
        pdf.save(path, garbage=4, deflate=True)
        pages = len(pdf)
    temporary.unlink()
    return pages


def docx_paragraph(text, style="Normal", small=False):
    properties = f'<w:pPr><w:pStyle w:val="{style}"/></w:pPr>'
    runs = []
    # Preserve simple bold emphasis, but do not expose Markdown delimiters in Word.
    for i, part in enumerate(re.split(r"\*\*(.*?)\*\*", text)):
        if not part:
            continue
        rprops = ('<w:b/>' if i % 2 else '') + ('<w:sz w:val="19"/>' if small else '')
        runs.append('<w:r><w:rPr>'+rprops+'</w:rPr><w:t xml:space="preserve">'+escape(plain(part))+'</w:t></w:r>')
    return '<w:p>'+properties+''.join(runs)+'</w:p>'


def write_docx(path, elements, title, questionnaire=False):
    body = []
    for kind, value in elements:
        if kind.startswith("h"):
            body.append(docx_paragraph(value, "Heading"+kind[1:]))
        elif kind == "paragraph":
            body.append(docx_paragraph(value))
        elif kind == "break":
            body.append('<w:p><w:r><w:br w:type="page"/></w:r></w:p>')
        elif kind == "code":
            body.extend(docx_paragraph(line, "Code") for line in value.splitlines())
        elif kind == "table":
            borders = '<w:tblBorders>'+''.join(f'<w:{side} w:val="single" w:sz="4" w:color="9BA8B5"/>' for side in ['top','left','bottom','right','insideH','insideV'])+'</w:tblBorders>'
            rows = []
            for i, row in enumerate(value):
                rprops = '<w:trPr><w:tblHeader/></w:trPr>' if i == 0 else ''
                cells = []
                for cell in row:
                    props = '<w:tcPr><w:shd w:fill="EAF0F5"/></w:tcPr>' if i == 0 else '<w:tcPr/>'
                    cells.append('<w:tc>'+props+docx_paragraph('**'+cell+'**' if i == 0 else cell, 'TableText', True)+'</w:tc>')
                rows.append('<w:tr>'+rprops+''.join(cells)+'</w:tr>')
            body.append('<w:tbl><w:tblPr><w:tblW w:w="0" w:type="auto"/>'+borders+'</w:tblPr>'+''.join(rows)+'</w:tbl>')
            body.append(docx_paragraph(''))
    body.append('<w:sectPr><w:pgSz w:w="11906" w:h="16838"/><w:pgMar w:top="850" w:right="850" w:bottom="850" w:left="850" w:header="400" w:footer="400"/></w:sectPr>')
    namespace = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
    document = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:document xmlns:w="'+namespace+'"><w:body>'+''.join(body)+'</w:body></w:document>'
    font = 'Arial' if questionnaire else 'Times New Roman'
    size = '20' if questionnaire else '24'
    styles = f'<w:style w:type="paragraph" w:default="1" w:styleId="Normal"><w:name w:val="Normal"/><w:pPr><w:spacing w:after="90" w:line="276" w:lineRule="auto"/></w:pPr><w:rPr><w:rFonts w:ascii="{font}" w:hAnsi="{font}"/><w:sz w:val="{size}"/></w:rPr></w:style>'
    for i, pts in enumerate([32,26,24,22], 1):
        styles += f'<w:style w:type="paragraph" w:styleId="Heading{i}"><w:name w:val="heading {i}"/><w:basedOn w:val="Normal"/><w:pPr><w:keepNext/><w:spacing w:before="180" w:after="100"/><w:outlineLvl w:val="{i-1}"/></w:pPr><w:rPr><w:b/><w:color w:val="183650"/><w:sz w:val="{pts}"/></w:rPr></w:style>'
    styles += '<w:style w:type="paragraph" w:styleId="TableText"><w:name w:val="Table Text"/><w:basedOn w:val="Normal"/><w:pPr><w:spacing w:after="45" w:line="240" w:lineRule="auto"/></w:pPr><w:rPr><w:sz w:val="19"/></w:rPr></w:style>'
    styles += '<w:style w:type="paragraph" w:styleId="Code"><w:name w:val="Code"/><w:basedOn w:val="Normal"/><w:rPr><w:rFonts w:ascii="Consolas" w:hAnsi="Consolas"/><w:sz w:val="19"/></w:rPr></w:style>'
    styles = '<?xml version="1.0" encoding="UTF-8"?><w:styles xmlns:w="'+namespace+'">'+styles+'</w:styles>'
    types = '<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/><Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/></Types>'
    rels = '<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/></Relationships>'
    docrels = '<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rIdStyles" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/></Relationships>'
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, value in {'[Content_Types].xml':types, '_rels/.rels':rels, 'word/document.xml':document,
                            'word/styles.xml':styles, 'word/_rels/document.xml.rels':docrels}.items():
            archive.writestr(name, value.encode('utf-8'))


def write_csv(path, fields, rows=()):
    with path.open('w', encoding='utf-8-sig', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader(); writer.writerows(rows)


def build_templates():
    directory = SOURCE / 'templates'
    directory.mkdir(exist_ok=True)
    questionnaire = (SOURCE / 'questionnaire.md').read_text(encoding='utf-8')
    matched = re.findall(r'^\| ([BCDE]\d+) \| (.*?) \|', questionnaire, re.M)
    mapping = {item:dimension for dimension, items in DIMENSIONS.items() for item in items}
    if len(matched) != 16 or {item for item,_ in matched} != set(mapping):
        raise ValueError('The 16 questionnaire items must map exactly once to the five dimensions')
    bank = [{'form':'topic', 'section':item[0], 'item_id':item, 'question_type':'rating', 'prompt':prompt,
             'choices':'1 Strongly Disagree | 2 Disagree | 3 Neither Agree nor Disagree | 4 Agree | 5 Strongly Agree | NA Not Applicable / Unable to Assess',
             'dimension':mapping[item], 'repeat_scope':'each topic packet', 'required':'no'} for item,prompt in matched]
    extras = [
        ('profile','A1','checkbox','Relevant field or fields of expertise','Legal practice/research | Legislative drafting/research/administration | Public policy/planning/administration | Local ordinance work | Relevant academic work | Other'),
        ('profile','A2','short answer','Years of relevant experience','Numeric years or prefer not to state'),
        ('profile','A3','multiple choice','Familiarity with local ordinances or legislative documents','Limited | Occasional use | Regular use | Extensive use | Prefer not to state'),
        ('profile','A4','paragraph','Describe relevant work or subject areas; do not provide confidential examples',''),
        ('profile','A5','paragraph','Topic areas outside your expertise or circumstances affecting review',''),
        ('comparison','E3','multiple choice','Which systems have you reviewed?','Both X and Y | X only | Y only | Unable to complete either'),
        ('comparison','E4','multiple choice','Which supplied system was more understandable or substantively meaningful?','X | Y | Both equally useful | Neither useful | Insufficient information'),
        ('comparison','E5','paragraph','Main reason for the preference, with packet references',''),
        ('comparison','E6','paragraph','Major strengths and weaknesses of the supplied results',''),
        ('comparison','E7','paragraph','Topics to reconsider, rename, merge or separate; identify packet IDs',''),
        ('comparison','E8','paragraph','Incorrect/questionable assignments or temporal interpretations; cite source/example/year',''),
        ('comparison','E9','paragraph','Recommendations to improve usefulness, clarity or source support',''),
        ('comparison','E10','paragraph','Other limits on interpreting your judgments',''),
        ('topic','BCOM','paragraph','Comments on topic quality; identify item and example/comparison IDs',''),
        ('topic','CCOM','paragraph','Questionable grouping or source issue; describe correction and source/unit ID',''),
        ('topic','DCOM','paragraph','Years, claims, keyword changes or source examples needing clarification',''),
        ('topic','ECOM','paragraph','Suggested action: retain, rename, reconsider, merge, separate, recheck text, revise temporal interpretation, more evidence; explain',''),
        ('topic','NAREASON','paragraph','NA item IDs and reasons: insufficient materials, outside expertise, not applicable, unreadable source, missing context or other',''),
    ]
    bank.extend({'form':form,'section':item[0],'item_id':item,'question_type':kind,'prompt':prompt,'choices':choices,
                 'dimension':'not scored','repeat_scope':'each topic packet' if form=='topic' else 'once per reviewer','required':'no'}
                for form,item,kind,prompt,choices in extras)
    write_csv(directory/'forms_item_bank.csv', ['form','section','item_id','question_type','prompt','choices','dimension','repeat_scope','required'], bank)
    schemas = {
        'sampling_register.csv':['packet_id','packet_version','model','configuration','primary_seed','topic_id','sampling_role','sampling_seed','candidate_pool_reference','selection_value','source_manifest_hash','draft_label_version','selection_reason','deviation'],
        'excerpt_register.csv':['packet_id','example_id','selection_role','ordinance_id','section_id','unit_type','resolved_year','source_file','source_locator_verified','membership_strength','selection_seed','context_reference','shortening_or_OCR_notes'],
        'response_template.csv':['reviewer_code','session_id','packet_id','packet_version','system_code','item_id','rating','status','na_reason','comment','submitted_at'],
        'feedback_log.csv':['feedback_id','reviewer_code','packet_id','packet_version','item_id','source_or_unit_reference','concern_category','comment_summary','proposed_action','decision','rationale','affected_outputs','recalculation_required','new_version','rereview_status'],
        'model_key_template.csv':['system_code','model','configuration','seed','experiment_manifest_hash'],
        'analysis_summary_template.csv':['summary_level','model','packet_id','item_or_dimension','expected_responses','valid_responses','NA_responses','missing_responses','complete_reviewers','included_topics','count_1','count_2','count_3','count_4','count_5','mean','median','review_flag','notes'],
    }
    for name, fields in schemas.items():
        path = directory/name
        # Preserve any inadvertently filled templates rather than overwriting real data.
        if path.exists():
            with path.open(encoding='utf-8-sig', newline='') as handle:
                if list(csv.DictReader(handle)):
                    raise ValueError(f'Refusing to overwrite nonempty template: {path}')
        write_csv(path, fields)
    codebook = {'version':'EV-1.0','expert_review_status':'not_conducted','dimensions':DIMENSIONS,
                'rating_scale':{'1':'Strongly Disagree','2':'Disagree','3':'Neither Agree nor Disagree','4':'Agree','5':'Strongly Agree'},
                'NA':'Not Applicable / Unable to Assess; numeric rating empty',
                'missing':'Blank or unreturned response; numeric rating empty',
                'review_rule':{'threshold':3.0,'operator':'<','level':'topic-dimension mean','use_unrounded_value':True,
                               'origin':'Existing thesis, Table 6 and accompanying paragraph, PDF page 43; study-defined, not an empirical acceptance standard'},
                'aggregation':'Complete item set per reviewer-topic dimension; equal eligible-reviewer weights; equal sampled-topic weights; report all denominators.',
                'planned_topics_per_model':4,'planned_examples_per_topic':3,'sampling_seed':42,
                'actual_experts':None,'actual_responses':None,'actual_agreement_results':None}
    (directory/'scoring_codebook.json').write_text(json.dumps(codebook,indent=2),encoding='utf-8')


def main():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    build_templates()
    manifest = {'version':'EV-1.0','created_utc':datetime.now(timezone.utc).isoformat(),
                'reviewed_thesis':'CS_Undergraduate_Thesis_Template__Copy_-13.pdf',
                'reviewed_thesis_sha256':'4acb1916ef522c4dd15a36eb0cdccc5fafa60c37eddd829b0183a9214985d22e',
                'reviewed_thesis_pdf_pages':'41-43; research context also reviewed',
                'expert_validation_status':'proposed; no participants, responses, or results generated',
                'exporter_sha256':digest(__file__), 'documents':{}}
    for stem,title in TITLES.items():
        path = SOURCE/(stem+'.md')
        elements = blocks(path.read_text(encoding='utf-8'))
        document,css = make_html(elements,title,stem=='questionnaire')
        html_path=OUTPUT/(stem+'.html')
        html_path.write_text(document,encoding='utf-8')
        write_docx(OUTPUT/(stem+'.docx'),elements,title,stem=='questionnaire')
        pages=write_pdf(OUTPUT/(stem+'.pdf'),document,css,title)
        manifest['documents'][stem]={'source':path.relative_to(ROOT).as_posix(),'source_sha256':digest(path),'pdf_pages':pages,
                                    'exports_sha256':{ext:digest(OUTPUT/(stem+'.'+ext)) for ext in ['html','docx','pdf']}}
        print(stem, 'PDF pages:', pages)
    manifest['templates_sha256']={p.relative_to(SOURCE).as_posix():digest(p) for p in sorted((SOURCE/'templates').iterdir()) if p.is_file()}
    (OUTPUT/'export_manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    print('Exported proposed documents only; no expert data generated:',OUTPUT)


if __name__=='__main__':
    main()
