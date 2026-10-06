"""Temporal labels, denominators, selections and graph-only deliverables."""
import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd
import pytest
import pymupdf
from pptx import Presentation

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from build_temporal_graphs import label_topic, load_temporal, select_interpretable, topic_mix, YEARS

SOURCE = ROOT / 'artifacts/clean_text_full/evidence'
OUTPUT = ROOT / 'artifacts/temporal_topics'
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
    catalog, matrix, weighted = load_temporal(SOURCE, model, OVERRIDES)
    saved = pd.read_csv(OUTPUT / 'tables' / f'{model}_topic_titles_and_temporal_summary.csv')
    assert catalog.topic.tolist() == saved.topic.tolist()
    assert catalog.title.tolist() == saved.title.tolist()
    assert (saved.label_status == 'draft_not_expert_validated').all()
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
    deck = Presentation(str(OUTPUT / 'Temporal_Topic_Summaries.pptx'))
    assert len(deck.slides) == 8
    assert len(list((OUTPUT / 'figures').glob('*.png'))) == 8
    catalog = pd.read_csv(OUTPUT / 'tables/all_topic_titles.csv')
    assert len(catalog) == 361
    assert not catalog.duplicated(['model', 'topic']).any()
    manifest = json.loads((OUTPUT / 'manifest.json').read_text())
    assert manifest['models_rerun'] is False
    assert manifest['yearly_documents']['2025'] == 32
