"""Validate completed research outputs when present; no synthetic research results."""
import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd
import pytest
ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "scripts")]
from report_four_configurations import validate_completed, digest
from tuning_evaluation import align_topics, document_prevalence

SOURCE = ROOT / "results/experiments/four_configuration_tuning"
CONFIG = json.loads((ROOT / "configs/four_configuration_tuning.json").read_text())
READY = (SOURCE / "experiment.json").exists() and json.loads((SOURCE / "experiment.json").read_text()).get("status") == "completed"


def test_report_rejects_partial_experiment(tmp_path):
    (tmp_path / "experiment.json").write_text(json.dumps({"status": "partial_failure", "completed_runs": 23}))
    with pytest.raises(ValueError, match="completed 24-fit"):
        validate_completed(tmp_path, CONFIG)


@pytest.mark.skipif(not READY, reason="Real full-corpus experiment not yet complete")
def test_all_completed_artifacts_match_recorded_hashes():
    manifest = validate_completed(SOURCE, CONFIG)
    assert manifest["units"] == 7832 and manifest["documents"] == 2118


@pytest.mark.skipif(not READY, reason="Real full-corpus experiment not yet complete")
def test_all_24_fits_have_identical_input_and_measured_counts():
    original = pd.read_csv(SOURCE / "input_units.csv", keep_default_na=False)
    rows = pd.read_csv(SOURCE / "run_results.csv")
    assert len(rows) == 24 and rows.status.eq("completed").all()
    assert not rows.duplicated(["model", "trial", "seed"]).any()
    assert set(rows.seed) == {42, 43, 44}
    for row in rows.itertuples():
        path = SOURCE / row.trial / f"seed_{row.seed}" / row.model
        data = pd.read_csv(path / "section_topics.csv", keep_default_na=False)
        assert data[original.columns].equals(original)
        assert row.topics_excluding_outliers == data.loc[data.topic.ne(-1), "topic"].nunique()
        assert row.assigned_units == data.topic.ne(-1).sum()
        assert row.outlier_sections == data.topic.eq(-1).sum()
        assert row.assigned_units + row.outlier_sections == len(original)
        assert row.topic_coverage + row.outlier_fraction == pytest.approx(1)
        assert np.isfinite(row.cv_coherence) and 0 <= row.topic_diversity <= 1
        assert row.fit_evaluation_seconds > 0 and row.process_cpu_seconds >= 0
        yearly = pd.read_csv(path / "yearly_prevalence.csv")
        assert np.allclose(yearly.groupby("year").section_share.sum(), 1)
        weighted = pd.read_csv(path / "document_weighted_prevalence.csv")
        expected = document_prevalence(original, data.topic.to_numpy())
        pd.testing.assert_frame_equal(weighted, expected, check_dtype=False, atol=1e-12)
        words = pd.read_csv(path / "topic_keywords.csv", keep_default_na=False).query("topic != -1").term
        assert row.topic_diversity == pytest.approx(words.nunique()/len(words))


@pytest.mark.skipif(not READY, reason="Real full-corpus experiment not yet complete")
def test_alignment_and_temporal_outputs_are_complete_and_bounded():
    stable = pd.read_csv(SOURCE / "seed_stability.csv")
    temporal = pd.read_csv(SOURCE / "temporal_consistency.csv")
    results = pd.read_csv(SOURCE / "tuning_results.csv")
    assert len(stable) == 24 and len(temporal) == 12 and len(results) == 8
    assert results.completed_seeds.eq(3).all()
    for table in [stable, temporal]:
        for field in ["aligned_macro_jaccard", "aligned_weighted_jaccard", "matched_intersection_fraction", "temporal_js_mean", "temporal_tv_mean", "temporal_similarity"]:
            assert table[field].dropna().between(-1e-12, 1+1e-12).all()
        assert np.allclose(table.temporal_similarity, 1-table.temporal_js_mean)
    for row in stable.itertuples():
        left = pd.read_csv(SOURCE / row.trial / f"seed_{row.seed_left}" / row.model / "section_topics.csv", usecols=["topic"]).topic
        right = pd.read_csv(SOURCE / row.trial / f"seed_{row.seed_right}" / row.model / "section_topics.csv", usecols=["topic"]).topic
        _, measured = align_topics(left, right)
        assert row.aligned_weighted_jaccard == pytest.approx(measured["aligned_weighted_jaccard"])


@pytest.mark.skipif(not READY, reason="Real full-corpus experiment not yet complete")
def test_original_input_and_baseline_configuration_are_preserved():
    manifest = json.loads((SOURCE / "experiment.json").read_text())
    baseline = json.loads((ROOT / "results/experiments/clean_text_full/experiment.json").read_text())
    assert manifest["source_sha256"] == baseline["source_sha256"]
    for file in ["src/clean_model.py", "src/clean_encoder.py", "scripts/run_clean_text.py"]:
        assert manifest["code_sha256"][file] == baseline["code_sha256"][file]


def test_compact_report_is_complete_and_untampered():
    import pymupdf
    output = ROOT / "artifacts/four_configuration_tuning"
    if not (output / "report_manifest.json").exists():
        pytest.skip("Compact report not generated")
    report = json.loads((output / "report_manifest.json").read_text())
    assert report["status"] == "completed"
    for file, expected in report["files_sha256"].items():
        assert digest(output / file) == expected
    results = pd.read_csv(output / "evidence/tuning_results.csv")
    assert len(results) == 8 and results.completed_seeds.eq(3).all()
    assert len(list((output / "figures").glob("*.png"))) == 7
    assert len(list((output / "figures").glob("*.svg"))) == 7
    assert len(list((output / "figures").glob("*.pdf"))) == 7
    with pymupdf.open(output / "Tuning_Comparison_Figures.pdf") as pdf:
        assert len(pdf) == 7
        assert all(page.get_text().strip() for page in pdf)
    coherence = pd.read_csv(output / "evidence/coherence_audit.csv")
    assert coherence.topics.eq(coherence.cv_topics_scored).all()
    assert coherence.cv_terms_absent_from_dictionary.eq(0).all()


def test_selection_is_provisional_and_expert_scores_stay_blank():
    output = ROOT / "artifacts/four_configuration_tuning"
    if not (output / "report_manifest.json").exists():
        pytest.skip("Compact report not generated")
    selection = json.loads((ROOT / "configs/four_configuration_selection.json").read_text())
    assert selection["completed_fits"] == 24 and selection["selected_after_completion"]
    assert "pending" in selection["expert_validation"]
    assert selection["primary_seed"] == 42 and selection["sensitivity_seeds"] == [43, 44]
    for trial in CONFIG["trials"]:
        for model in ["lexical", "semantic"]:
            table = pd.read_csv(output / "evidence" / trial["name"] / model / "expert_review_template.csv", keep_default_na=False)
            scores = [c for c in table if c.endswith("_1_to_5")]
            assert len(scores) == 5 and table[scores].eq("").all().all()
