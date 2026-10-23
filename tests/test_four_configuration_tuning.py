"""Synthetic correctness checks, never research measurements."""
import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd
import pytest
ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "scripts")]
from tuning_evaluation import align_topics, temporal_comparison, document_prevalence, granularity, ResourceMonitor
from run_four_configurations import check_config, verify_sources, summarize


def frame():
    return pd.DataFrame({"year": [2016, 2016, 2016, 2017, 2017, 2017],
                         "ordinance_id": ["a", "a", "b", "c", "d", "d"],
                         "section_id": ["1", "2", "1", "1", "1", "2"]})


def test_label_permutation_is_perfect_and_noise_is_not_aligned():
    a = [0, 0, 1, 1, -1, -1]
    b = [7, 7, 3, 3, -1, -1]
    pairs, metrics = align_topics(a, b)
    assert metrics["aligned_macro_jaccard"] == 1
    assert metrics["aligned_weighted_jaccard"] == 1
    assert metrics["ari_all_units"] == 1
    assert -1 not in set(pairs.left_topic)
    annual, _, temporal = temporal_comparison(frame(), a, b, pairs)
    assert temporal["temporal_similarity"] == 1
    assert np.allclose(annual.total_variation, 0)


def test_splits_penalize_unmatched_topics_symmetrically():
    a, b = [0, 0, 0, 0], [4, 4, 5, 5]
    _, ab = align_topics(a, b)
    _, ba = align_topics(b, a)
    assert ab["aligned_macro_jaccard"] == pytest.approx(1/3)
    assert ab["aligned_weighted_jaccard"] == pytest.approx(.375)
    assert ab["aligned_macro_jaccard"] == ba["aligned_macro_jaccard"]
    assert ab["unmatched_right_topics"] == 1


def test_all_outliers_are_not_perfect_topic_stability():
    pairs, metrics = align_topics([-1]*6, [-1]*6)
    assert metrics["aligned_macro_jaccard"] is None
    assert metrics["aligned_weighted_jaccard"] is None
    # Noise-only annual agreement is possible; must not imply usable topics.
    _, _, temporal = temporal_comparison(frame(), [-1]*6, [-1]*6, pairs)
    assert temporal["temporal_similarity"] == 1
    assert metrics["ari_all_units"] == 1
    assert granularity([-1]*6)["effective_topics"] is None


def test_noise_to_topics_and_unmatched_mass_are_not_discarded():
    a, b = [-1]*6, [0]*6
    pairs, _ = align_topics(a, b)
    assert pairs.empty
    annual, _, metrics = temporal_comparison(frame(), a, b, pairs)
    assert metrics["temporal_js_mean"] == pytest.approx(1)
    assert np.allclose(annual.total_variation, 1)


def test_document_weighting_includes_zeroes_and_equal_document_mass():
    table = document_prevalence(frame(), [0, 0, 1, 0, -1, -1])
    assert np.allclose(table.groupby("year").share.sum(), 1)
    assert table.query("year == 2016 and topic == 0").share.iloc[0] == .5
    assert table.query("year == 2016 and topic == -1").share.iloc[0] == 0


def test_alignment_validates_inputs():
    with pytest.raises(ValueError):
        align_topics([], [])
    with pytest.raises(ValueError):
        align_topics([0], [0, 1])


def test_fixed_config_preserves_baselines():
    config = json.loads((ROOT / "configs/four_configuration_tuning.json").read_text())
    baseline = json.loads((ROOT / "configs/clean_text_full.json").read_text())
    check_config(config)
    for old in baseline["trials"]:
        new = next(t for t in config["trials"] if t["name"] == old["name"])
        assert all(new[k] == v for k, v in old.items())
    assert config["source"] == baseline["source"]
    assert config["years"] == baseline["years"]
    assert {k:v for k,v in config["common"].items() if k != "stability_runs"} == {k:v for k,v in baseline["common"].items() if k != "stability_runs"}
    assert config["seeds"] == [42, 43, 44]


def test_resource_monitor_returns_measured_time():
    with ResourceMonitor() as monitor:
        np.arange(100).sum()
    assert monitor.metrics["fit_evaluation_seconds"] > 0
    assert monitor.metrics["process_cpu_seconds"] >= 0


def test_aggregate_writes_all_eight_combinations(tmp_path):
    config = json.loads((ROOT / "configs/four_configuration_tuning.json").read_text())
    records = []
    data = frame()
    for trial in config["trials"]:
        for model in ["lexical", "semantic"]:
            for seed in config["seeds"]:
                directory = tmp_path / trial["name"] / f"seed_{seed}" / model
                directory.mkdir(parents=True)
                data.assign(topic=[0, 0, 1, 1, -1, -1]).to_csv(directory / "section_topics.csv", index=False)
                record = dict(trial=trial["name"], model=model, seed=seed, status="completed",
                              topics_excluding_outliers=2, cv_coherence=.5, topic_diversity=.5,
                              topic_coverage=4/6, outlier_fraction=2/6, fit_evaluation_seconds=1.,
                              sampled_peak_rss_mib=10., largest_topic_fraction_all_units=2/6, effective_topics=2.)
                records.append(record)
    summarize(tmp_path, config, data, records)
    results = pd.read_csv(tmp_path / "tuning_results.csv")
    assert len(results) == 8
    assert results.completed_seeds.eq(3).all()
    assert results.seed_aligned_macro_jaccard_mean.eq(1).all()
    assert results.cross_config_temporal_similarity_mean.eq(1).all()
    assert len(pd.read_csv(tmp_path / "temporal_consistency.csv")) == 12
    assert len(pd.read_csv(tmp_path / "seed_stability.csv")) == 24
