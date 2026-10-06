import argparse
import json
from pathlib import Path
import sys
import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "scripts")]
from prepare_clean_text import identity, segment, enacted_year, overrides, prepare
from run_clean_text import validate
from clean_model import yearly_prevalence, keyword_metrics, build_vocabulary, lexical_vectors, fit_branch
from clean_encoder import encode


def test_identity_normalizes_leading_zeroes_not_years():
    assert identity('Ordinance No. 0134-16 (2).txt') == '134-16'
    assert identity('Ordinance No. 134-17.txt') != '134-16'


def test_section_extraction_trims_signatures_and_flags_boilerplate():
    text = 'City header\nBe it ordained\nSECTION 1. Public health\nProvide community medical services.\nSECTION 2. Effectivity.\nThis shall take effect upon approval.\nENACTED, 2016'
    units, audit = segment(text)
    assert len(units) == 1 and units[0]['unit_type'] == 'legal_section'
    assert audit['boilerplate_units_omitted'] == 1
    assert 'ENACTED' not in units[0]['text']


def test_no_heading_preserves_document_instead_of_dropping_it():
    units, _ = segment('Establish a public health facility and community medical assistance program.')
    assert len(units) == 1 and units[0]['unit_type'] == 'document_fallback'


def test_repeated_heading_numbers_are_not_duplicate_ids():
    units, audit = segment('SECTION 1. Provide health services.\nSECTION 1. Provide transport assistance.')
    assert audit['repeated_heading_numbers']
    assert units[0]['unit_type'] == 'document_fallback'


def test_enactment_does_not_use_cited_years():
    assert enacted_year('Amending the 1998 ordinance.\nENACTED, March 5, 2020\nApproved.') == 2020
    assert enacted_year('The 2018 and 2019 policies are cited.') is None


def test_manual_year_overrides_are_preserved(tmp_path):
    path = tmp_path / 'corrections.csv'
    path.write_text('filename,correct_year,verified_by,evidence\nOrdinance No. 0134-16.pdf,2017,Lamsin,reviewed date\n')
    assert overrides([path])['134-16'][0]['year'] == 2017


def test_duplicate_files_contribute_once_and_sources_are_untouched(tmp_path):
    root = tmp_path / 'texts'
    content = 'SECTION 1. Community health facilities and hospital patient services.\nENACTED, March 5, 2016'
    for year in [2016, 2017]:
        folder = root / str(year)
        folder.mkdir(parents=True)
        (folder / 'Ordinance No. 99999-16.txt').write_text(content)
    frame, manifest = prepare(root, tmp_path / 'prepared')
    assert manifest['duplicate_copies'] == 1
    assert frame.ordinance_id.nunique() == 1
    assert frame.year.tolist() == [2016]
    assert len(list(root.rglob('*.txt'))) == 2
    audit = pd.read_csv(tmp_path / 'prepared/file_audit.csv')
    assert set(audit.status) == {'included', 'duplicate_copy'}


def test_validation_rejects_duplicate_unit_ids():
    row = dict(ordinance_id='x', section_id='s', year=2016, text='health services', source_file='x.txt', verification_status='verified')
    with pytest.raises(ValueError, match='duplicate'):
        validate(pd.DataFrame([row, row]))


def test_yearly_share_includes_outliers_and_zero_cells():
    table = yearly_prevalence(pd.DataFrame({'year': [2016, 2016, 2017]}), [0, -1, 1])
    assert len(table) == 6
    assert np.allclose(table.groupby('year').section_share.sum(), 1)


def test_all_outliers_have_null_quality_scores():
    from scipy.sparse import csr_matrix
    result = keyword_metrics({-1: ['health']}, csr_matrix([[1]]), ['health'], 10)
    assert result['topic_diversity'] is None and result['section_npmi'] is None


def test_batched_encoder_uses_all_chunks_and_cache_identity(tmp_path):
    from transformers import BertConfig, BertModel, BertTokenizerFast
    checkpoint = tmp_path / 'tiny'
    checkpoint.mkdir()
    vocab = checkpoint / 'vocab.txt'
    vocab.write_text('[PAD]\n[UNK]\n[CLS]\n[SEP]\n[MASK]\npublic\nhealth\nservices\n')
    BertTokenizerFast(vocab_file=str(vocab)).save_pretrained(checkpoint)
    BertModel(BertConfig(vocab_size=8, hidden_size=8, num_hidden_layers=1, num_attention_heads=2,
                        intermediate_size=16, max_position_embeddings=16)).save_pretrained(checkpoint)
    config = dict(encoder=str(checkpoint), encoder_revision='main', max_tokens=8, seed=42, batch_size=2, device='cpu')
    docs = ['public health services ' * 8, 'public health']
    vectors, metadata = encode(docs, config, tmp_path / 'cache')
    assert vectors.shape == (2, 8) and np.allclose(np.linalg.norm(vectors, axis=1), 1)
    assert metadata['total_chunks'] == 5 and metadata['multi_chunk_units'] == 1
    cached, cached_meta = encode(docs, config, tmp_path / 'cache')
    assert np.array_equal(vectors, cached) and cached_meta['cache_used']
    with pytest.raises(ValueError, match='identity mismatch'):
        encode(docs[::-1], config, tmp_path / 'cache')


def test_lexical_fit_on_synthetic_data(tmp_path):
    docs = ['health clinic doctor medicine', 'road traffic vehicle parking', 'waste recycling garbage environment'] * 10
    frame = pd.DataFrame({'text': docs, 'ordinance_id': [f'synthetic-{i}' for i in range(30)],
                          'section_id': 'section_1', 'year': [2016 + i % 2 for i in range(30)]})
    args = argparse.Namespace(stopwords='english', extra_stopwords=None, ngram_max=1, min_df=1,
                              max_df=1., max_features=5000, svd_components=8, seed=42, neighbors=3,
                              umap_components=3, min_dist=0., min_cluster_size=3, min_samples=1,
                              top_words=3, stability_runs=1, skip_html=True, output=tmp_path)
    counts, terms, frozen = build_vocabulary(docs, args)
    vectors, metadata = lexical_vectors(counts, args)
    labels, metrics = fit_branch('lexical', vectors, frame, counts, terms, frozen, args, metadata)
    assert len(labels) == 30 and 0 <= metrics['topic_coverage'] <= 1
    assert (tmp_path / 'lexical/metrics.json').exists()
