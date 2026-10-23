"""Temporal labels, denominators, selections and graph-only deliverables."""
import hashlib
import json
import shutil
from pathlib import Path
import sys

import numpy as np
import pandas as pd
import pytest
import pymupdf
from pptx import Presentation

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from build_temporal_graphs import build, label_topic, load_run_provenance, load_temporal, select_interpretable, topic_mix, YEARS

SOURCE = ROOT / 'artifacts/four_configuration_tuning/evidence/conservative'
OUTPUT = ROOT / 'artifacts/temporal_topics'
TITLE_CONFIG = json.loads((ROOT / 'configs/temporal_topic_titles_conservative.json').read_text())
OVERRIDES = json.loads((ROOT / 'configs/temporal_topic_titles.json').read_text())['overrides']


def test_labels_are_grounded_and_unsupported_override_fails():
    title, category, method, evidence = label_topic('semantic', 0, ['street', 'closure', 'traffic'], OVERRIDES)
    assert title == 'Temporary road closures and traffic control'
    assert category == 'policy' and set(evidence) <= {'street', 'closure', 'traffic'}
    with pytest.raises(ValueError, match='does not match'):
        label_topic('semantic', 0, ['school', 'education'], OVERRIDES)


def test_unclear_words_are_not_invented_policy_labels():
    _, category, _, evidence = label_topic('test', 99, ['ard', 'thb', 'gty', 'sectioii'], {})
    assert category == 'unclear'
    title, category, _, _ = label_topic('test', 99, ['unknownterm', 'mysteryword'], {})
    assert title.startswith('Unresolved keywords') and category == 'unclear'


def test_mixed_cluster_not_mislabeled_as_single_use_plastics():
    words = ['person', 'vehicle', 'dqr', 'singleuse', 'establishments', 'solo', 'plastic', 'public']
    title, category, _, _ = label_topic('semantic', 1, words, OVERRIDES)
    assert category == 'mixed' and 'Mixed' in title


def test_interpretable_selection_keeps_distinct_clusters_not_merges():
    catalog = pd.DataFrame({'topic': [1, 2, 3, 4], 'title': ['A', 'A', 'B', 'Noise'],
                            'category': ['policy', 'policy', 'governance', 'unclear']})
    chosen = select_interpretable(catalog, 8)
    assert chosen.topic.tolist() == [1, 3]


def test_zero_cells_and_other_topics_conserve_weight():
    matrix = pd.DataFrame([[.2]*10, [.3]*10, [.5]*10], index=[0, 1, -1], columns=YEARS)
    mix = topic_mix(matrix, [0])
    assert np.allclose(mix.sum(axis=1), 1)
    assert np.allclose(mix['Other assigned topics'], .3)
    assert np.allclose(mix['Outliers'], .5)


@pytest.mark.parametrize('model', ['lexical', 'semantic'])
def test_real_title_catalog_and_temporal_summary_match_source(model):
    catalog, matrix, weighted = load_temporal(SOURCE, model, TITLE_CONFIG['overrides'])
    saved = pd.read_csv(OUTPUT / 'tables' / f'{model}_topic_titles_and_temporal_summary.csv')
    assert catalog.topic.tolist() == saved.topic.tolist()
    assert catalog.title.tolist() == saved.title.tolist()
    assert (saved.label_status == 'draft_not_expert_validated').all()
    assert saved.configuration.eq('conservative').all() and saved.seed.eq(42).all()
    assert len(saved) == {'lexical': 107, 'semantic': 64}[model]
    labeled = pd.read_csv(OUTPUT / 'tables' / f'{model}_labeled_temporal_data.csv')
    assert labeled.configuration.eq('conservative').all() and labeled.seed.eq(42).all()
    assert labeled.model.eq(model).all()
    pd.testing.assert_frame_equal(labeled[weighted.columns], weighted)
    for row in catalog.itertuples():
        assert set(row.matched_keywords.split('; ')) <= set(row.clustered_words.split('; '))
        assert row.label_method != 'draft_keyword_excerpt_review'
    for row in saved.itertuples():
        assert np.isclose(row.peak_share_percent, matrix.loc[row.topic].max()*100)
        assert np.isclose(row.change_2016_to_2025_percentage_points,
                          (matrix.loc[row.topic,2025]-matrix.loc[row.topic,2016])*100)
    mix = pd.read_csv(OUTPUT / 'tables' / f'{model}_yearly_mix_percent.csv').set_index('year')
    assert np.allclose(mix.sum(axis=1), 100)
    selected = pd.read_csv(OUTPUT / 'tables' / f'{model}_interpretable_topic_selection.csv')
    assert selected.category.isin(['policy', 'governance']).all()
    assert selected.title.is_unique
    expected = select_interpretable(catalog, 8)
    assert expected.topic.tolist() == selected.topic.tolist()


def test_graph_only_exports_and_full_catalog():
    with pymupdf.open(OUTPUT / 'Temporal_Topic_Summaries.pdf') as pdf:
        assert len(pdf) == 8
        for page in pdf:
            text = page.get_text().lower()
            assert 'year' in text or 'time' in text or 'trajectories' in text
            assert 'c_v coherence' not in text
            assert 'conservative' in text and 'seed 42' in text
    deck = Presentation(str(OUTPUT / 'Temporal_Topic_Summaries.pptx'))
    assert len(deck.slides) == 8
    assert len(list((OUTPUT / 'figures').glob('*.png'))) == 8
    catalog = pd.read_csv(OUTPUT / 'tables/all_topic_titles.csv')
    assert len(catalog) == 171
    assert not catalog.duplicated(['model', 'topic']).any()
    manifest = json.loads((OUTPUT / 'manifest.json').read_text())
    assert manifest['models_rerun'] is False
    assert manifest['yearly_documents']['2025'] == 32
    assert manifest['configuration'] == 'conservative' and manifest['seed'] == 42
    assert manifest['parameters'] == {'neighbors': 30, 'min_dist': .1,
                                      'min_cluster_size': 30, 'min_samples': 10, 'umap_components': 5}
    assert manifest['topics_per_model'] == {'lexical': 107, 'semantic': 64}
    for name, expected in manifest['source_sha256'].items():
        assert hashlib.sha256((SOURCE / name).read_bytes()).hexdigest() == expected
    assert manifest['generator_sha256'] == hashlib.sha256((ROOT / 'scripts/build_temporal_graphs.py').read_bytes()).hexdigest()
    assert manifest['title_config_sha256'] == hashlib.sha256((ROOT / 'configs/temporal_topic_titles_conservative.json').read_bytes()).hexdigest()
    selected = pd.read_csv(OUTPUT / 'tables/selected_topic_temporal_summaries.csv')
    assert selected.configuration.eq('conservative').all() and selected.seed.eq(42).all()


def test_conservative_mixed_clusters_are_not_narrow_policy_labels():
    for model, topic in [('lexical', 18), ('semantic', 0), ('semantic', 24)]:
        catalog, _, _ = load_temporal(SOURCE, model, TITLE_CONFIG['overrides'])
        row = catalog.set_index('topic').loc[topic]
        assert row.category == 'mixed' and row.title.startswith('Mixed')
        assert row.label_method == 'draft_keyword_review'


def test_initial_package_is_preserved():
    archive = ROOT / 'artifacts/temporal_topics_initial'
    manifest = json.loads((archive / 'manifest.json').read_text())
    assert manifest['topic_titles'] == 361
    assert len(pd.read_csv(archive / 'tables/all_topic_titles.csv')) == 361
    for name, expected in manifest['source_sha256'].items():
        assert hashlib.sha256((ROOT / 'artifacts/clean_text_full/evidence' / name).read_bytes()).hexdigest() == expected


@pytest.mark.parametrize('field,value,message', [
    ('configuration', 'initial', 'scope'),
    ('seed', 43, 'scope'),
    ('keyword_sha256', {'lexical': 'incorrect', 'semantic': 'incorrect'}, 'fingerprint'),
])
def test_title_scope_and_keyword_fingerprint_are_enforced(field, value, message):
    with pytest.raises(ValueError, match=message):
        load_run_provenance(SOURCE, {**TITLE_CONFIG, field: value})


@pytest.fixture
def copied_evidence(tmp_path):
    root = tmp_path / 'report'
    source = root / 'evidence/conservative'
    shutil.copytree(SOURCE, source)
    shutil.copy2(SOURCE.parent / 'configuration.json', source.parent / 'configuration.json')
    shutil.copy2(SOURCE.parent.parent / 'report_manifest.json', root / 'report_manifest.json')
    return source


def test_changed_source_is_rejected_before_creating_outputs(copied_evidence, tmp_path):
    path = copied_evidence / 'lexical/document_weighted_prevalence.csv'
    path.write_bytes(path.read_bytes() + b'\n')
    output = tmp_path / 'figures'
    with pytest.raises(ValueError, match='hash mismatch'):
        build(copied_evidence, output, ROOT / 'configs/temporal_topic_titles_conservative.json')
    assert not output.exists()


def test_mixed_model_seeds_are_rejected(copied_evidence):
    path = copied_evidence / 'semantic/metrics.json'
    metrics = json.loads(path.read_text())
    metrics['seed'] = 43
    path.write_text(json.dumps(metrics))
    report_path = copied_evidence.parent.parent / 'report_manifest.json'
    report = json.loads(report_path.read_text())
    report['files_sha256'][path.relative_to(report_path.parent).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    report_path.write_text(json.dumps(report))
    with pytest.raises(ValueError, match='same configuration and seed'):
        load_run_provenance(copied_evidence, TITLE_CONFIG)


def test_existing_output_is_never_overwritten(tmp_path):
    with pytest.raises(ValueError, match='Output exists'):
        build(SOURCE, tmp_path, ROOT / 'configs/temporal_topic_titles_conservative.json')
