"""Document/schema QA only; these checks are not human or psychometric validation."""
import csv
import hashlib
import json
from pathlib import Path
import sys
import unicodedata
import xml.etree.ElementTree as ET
import zipfile

import pymupdf
import pytest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'docs/expert_validation'
OUTPUT = ROOT / 'artifacts/expert_validation'
sys.path.insert(0, str(ROOT / 'scripts'))
import build_expert_validation_documents as exporter


def test_item_bank_preserves_five_dimensions_and_six_response_options():
    with (SOURCE/'templates/forms_item_bank.csv').open(encoding='utf-8-sig', newline='') as handle:
        rows = list(csv.DictReader(handle))
    ratings = [r for r in rows if r['question_type']=='rating']
    assert len(ratings)==16 and len({r['item_id'] for r in ratings})==16
    assert {r['dimension'] for r in ratings}==set(exporter.DIMENSIONS)
    for row in ratings:
        assert row['item_id'] in exporter.DIMENSIONS[row['dimension']]
        assert len(row['choices'].split(' | '))==6
        assert '3 Neither Agree nor Disagree' in row['choices']
        assert 'NA Not Applicable / Unable to Assess' in row['choices']
        assert row['required']=='no'
    assert all(r['dimension']=='not scored' for r in rows if r['question_type']!='rating')


def test_response_registers_are_empty_and_no_expert_results_are_claimed():
    for name in ['sampling_register.csv','excerpt_register.csv','response_template.csv',
                 'feedback_log.csv','model_key_template.csv','analysis_summary_template.csv']:
        with (SOURCE/'templates'/name).open(encoding='utf-8-sig', newline='') as handle:
            assert list(csv.DictReader(handle))==[]
    book = json.loads((SOURCE/'templates/scoring_codebook.json').read_text())
    assert book['expert_review_status']=='not_conducted'
    assert all(book[key] is None for key in ['actual_experts','actual_responses','actual_agreement_results'])
    assert book['review_rule']['threshold']==3.0 and book['review_rule']['operator']=='<'
    assert book['review_rule']['use_unrounded_value']
    assert book['planned_topics_per_model']==4 and book['planned_examples_per_topic']==3


def test_export_files_and_sources_match_manifest_and_docx_is_well_formed():
    manifest = json.loads((OUTPUT/'export_manifest.json').read_text())
    assert manifest['reviewed_thesis_sha256']=='4acb1916ef522c4dd15a36eb0cdccc5fafa60c37eddd829b0183a9214985d22e'
    assert manifest['exporter_sha256']==exporter.digest(exporter.__file__)
    assert set(manifest['documents'])==set(exporter.TITLES)
    for stem, record in manifest['documents'].items():
        assert exporter.digest(ROOT/record['source'])==record['source_sha256']
        for extension, expected in record['exports_sha256'].items():
            assert exporter.digest(OUTPUT/f'{stem}.{extension}')==expected
        with pymupdf.open(OUTPUT/f'{stem}.pdf') as pdf:
            assert len(pdf)==record['pdf_pages']
            assert all(len(page.get_text().strip())>100 for page in pdf)
        with zipfile.ZipFile(OUTPUT/f'{stem}.docx') as archive:
            assert archive.testzip() is None
            for name in archive.namelist():
                if name.endswith(('.xml','.rels')):
                    ET.fromstring(archive.read(name))
            document = ET.fromstring(archive.read('word/document.xml'))
            assert document.tag.endswith('document')
    for relative, expected in manifest['templates_sha256'].items():
        assert exporter.digest(SOURCE/relative)==expected


def test_questionnaire_print_layout_and_items_are_complete():
    with pymupdf.open(OUTPUT/'questionnaire.pdf') as pdf:
        assert len(pdf)==4, 'Keep profile + two reusable topic pages + final comparison; avoid orphan pages'
        pages = [unicodedata.normalize('NFKC', p.get_text()) for p in pdf]
    assert 'Section A' in pages[0]
    assert 'Section B' in pages[1] and 'Section C' in pages[1]
    assert 'Section D' in pages[2] and 'Section E' in pages[2]
    assert 'Final Comparison' in pages[3] and 'E10.' in pages[3]
    all_text='\n'.join(pages)
    for items in exporter.DIMENSIONS.values():
        for item in items:
            assert item in all_text
    assert 'Not Applicable / Unable to Assess' in all_text
    assert 'predetermined' in all_text and 'denominator' in all_text


def test_template_regeneration_refuses_to_overwrite_existing_records(tmp_path, monkeypatch):
    monkeypatch.setattr(exporter, 'SOURCE', tmp_path)
    (tmp_path/'questionnaire.md').write_text((SOURCE/'questionnaire.md').read_text(encoding='utf-8'),encoding='utf-8')
    folder=tmp_path/'templates'; folder.mkdir()
    protected=folder/'sampling_register.csv'
    protected.write_text('packet_id\nDO_NOT_OVERWRITE_TEST_DATA\n',encoding='utf-8')
    with pytest.raises(ValueError, match='nonempty template'):
        exporter.build_templates()
    assert 'DO_NOT_OVERWRITE_TEST_DATA' in protected.read_text()


def test_original_thesis_is_unchanged_when_available():
    path=Path.home()/'Downloads/CS_Undergraduate_Thesis_Template__Copy_-13.pdf'
    if not path.exists():
        pytest.skip('Researcher-provided local reference is not distributed')
    assert hashlib.sha256(path.read_bytes()).hexdigest()=='4acb1916ef522c4dd15a36eb0cdccc5fafa60c37eddd829b0183a9214985d22e'
