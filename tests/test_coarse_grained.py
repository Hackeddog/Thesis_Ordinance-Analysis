"""Fresh-run contracts and evidence checks; never synthesize research results."""
import copy
import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "scripts"), str(ROOT / "src")]
from run_four_configurations import check_config
from publish_coarse_grained import validate_completed, digest
from build_temporal_graphs import load_run_provenance, load_temporal
from tuning_evaluation import document_prevalence

CONFIG = json.loads((ROOT / "configs/coarse_grained_retrain.json").read_text())
SOURCE = ROOT / CONFIG["output"]
REPORT = ROOT / "artifacts/coarse_grained_retrain"
TEMPORAL = ROOT / "artifacts/temporal_topics_coarse_grained"


def test_coarse_grained_preserves_protocol_but_disables_old_embeddings():
    baseline = json.loads((ROOT / "configs/four_configuration_tuning.json").read_text())
    check_config(CONFIG)
    assert CONFIG["common"] == baseline["common"]
    assert type(CONFIG["common"]["max_df"]) is float
    assert type(CONFIG["common"]["min_df"]) is int
    assert CONFIG["trials"] == [t for t in baseline["trials"] if t["name"] == "coarse_grained"]
    assert CONFIG["embedding_cache_source"] is None
    assert CONFIG["seeds"] == [42, 43, 44]
    assert CONFIG["output"] != baseline["output"]
    assert CONFIG["source"] == baseline["source"]


@pytest.mark.parametrize("change", ["cache", "max_df", "trial", "seeds", "mode"])
def test_retrain_rejects_silent_protocol_changes(change):
    altered = copy.deepcopy(CONFIG)
    if change == "cache":
        altered["embedding_cache_source"] = "old-cache"
    elif change == "max_df":
        altered["common"]["max_df"] = 1  # int means one document, not 100%!
    elif change == "trial":
        altered["trials"][0]["min_cluster_size"] = 30
    elif change == "seeds":
        altered["seeds"] = [42]
    else:
        altered["experiment_kind"] = "unknown"
    with pytest.raises(ValueError):
        check_config(altered)


def test_exporter_rejects_incomplete_experiment(tmp_path):
    (tmp_path / "experiment.json").write_text(json.dumps({"status": "partial_failure", "completed_runs": 5}))
    with pytest.raises(ValueError, match="All fresh fits"):
        validate_completed(tmp_path, CONFIG)


@pytest.mark.skipif(not (SOURCE / "experiment.json").exists(), reason="Large local run not distributed in Git")
def test_six_fresh_fits_are_bound_to_unchanged_source():
    manifest = json.loads((SOURCE / "experiment.json").read_text())
    if manifest["status"] == "running":
        pytest.skip("Retraining still running")
    validated = validate_completed(SOURCE, CONFIG)
    assert validated["documents"] == 2118 and validated["units"] == 7832
    assert not validated["semantic_encoder_metadata"]["cache_used"]
    original = pd.read_csv(SOURCE / "input_units.csv", keep_default_na=False)
    rows = pd.read_csv(SOURCE / "run_results.csv")
    assert len(rows) == 6 and rows.status.eq("completed").all()
    for row in rows.itertuples():
        folder = SOURCE / "coarse_grained" / f"seed_{row.seed}" / row.model
        assignments = pd.read_csv(folder / "section_topics.csv", keep_default_na=False)
        assert assignments[original.columns].equals(original)
        assert assignments.topic.ne(-1).sum() == row.assigned_units
        assert assignments.topic.eq(-1).sum() == row.outlier_sections
        expected = document_prevalence(original, assignments.topic.to_numpy())
        actual = pd.read_csv(folder / "document_weighted_prevalence.csv")
        pd.testing.assert_frame_equal(expected, actual, check_dtype=False, atol=1e-12)
    assert len(pd.read_csv(SOURCE / "seed_stability.csv")) == 6


def test_compact_fresh_evidence_and_temporal_exports():
    if not (REPORT / "report_manifest.json").exists():
        pytest.skip("Fresh publication not generated yet")
    report = json.loads((REPORT / "report_manifest.json").read_text())
    assert report["models_retrained"] and report["fresh_encoder_inference"]
    assert not report["encoder_finetuned"] and report["completed_fits"] == 6
    for file, sha in report["files_sha256"].items():
        assert digest(REPORT / file) == sha
    titles = json.loads((REPORT / "title_config.json").read_text())
    source = REPORT / "evidence/coarse_grained"
    provenance = load_run_provenance(source, titles)
    assert provenance["configuration"] == "coarse_grained"
    assert provenance["seed"] == 42
    manifest = json.loads((TEMPORAL / "manifest.json").read_text())
    assert manifest["generator_sha256"] == digest(ROOT / "scripts/build_temporal_graphs.py")
    assert len(list((TEMPORAL / "figures").glob("*.png"))) == 8
    import pymupdf
    from pptx import Presentation
    with pymupdf.open(TEMPORAL / "Temporal_Topic_Summaries.pdf") as pdf:
        assert len(pdf) == 8
        assert all("coarse grained" in page.get_text().lower() for page in pdf)
    assert len(Presentation(str(TEMPORAL / "Temporal_Topic_Summaries.pptx")).slides) == 8
    for model in ["lexical", "semantic"]:
        catalog, matrix, weighted = load_temporal(source, model, titles["overrides"])
        assert len(catalog) == provenance["topics_per_model"][model]
        assert np.allclose(matrix.sum(axis=0), 1)
        saved = pd.read_csv(TEMPORAL / "tables" / f"{model}_labeled_temporal_data.csv")
        assert saved.configuration.eq("coarse_grained").all() and saved.seed.eq(42).all()
        pd.testing.assert_frame_equal(saved[weighted.columns], weighted)
        review = pd.read_csv(source / model / "expert_review_template.csv", keep_default_na=False)
        assert review[[c for c in review if c.endswith("_1_to_5")]].eq("").all().all()
