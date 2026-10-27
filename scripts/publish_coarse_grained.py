"""Validate fresh retraining and export compact evidence, temporal figures, and static data.

Never overwrites an existing publication. No raw source text or personal review
records are exported to the public dashboard. Run after all six fits complete.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import sys

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "scripts")]
from run_four_configurations import check_config, verify_sources
from build_temporal_graphs import build, load_temporal

MODELS = ("lexical", "semantic")
COMPACT = ("metrics.json", "topic_keywords.csv", "document_weighted_prevalence.csv",
           "yearly_prevalence.csv", "model_metadata.json", "expert_review_template.csv")


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_json(path, data):
    Path(path).write_text(json.dumps(data, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")


def validate_completed(source, config):
    check_config(config)
    if config.get("experiment_kind") != "coarse_grained_retrain":
        raise ValueError("Only an explicit coarse-grained retraining can be published here")
    manifest = read_json(source / "experiment.json")
    expected = len(config["seeds"]) * 2
    if manifest.get("status") != "completed" or manifest.get("completed_runs") != expected or manifest.get("expected_runs") != expected:
        raise ValueError("All fresh fits must complete before publication")
    if manifest["config"] != config or read_json(source / "configuration.json") != config:
        raise ValueError("Configuration differs from completed experiment")
    encoder = manifest["semantic_encoder_metadata"]
    if encoder["cache_used"] or encoder["resume_start_chunk"] != 0 or (source / "embedding_reuse.json").exists():
        raise ValueError("This publication requires fresh, uninterrupted encoder inference")
    for file, sha in manifest["code_sha256"].items():
        if digest(source / "code_snapshot" / file) != sha:
            raise ValueError(f"Code snapshot hash mismatch: {file}")
    if digest(source / "input_units.csv") != manifest["input_units_sha256"]:
        raise ValueError("Ordered input hash mismatch")
    if digest(ROOT / config["source"]) != manifest["source_sha256"]:
        raise ValueError("Prepared source hash mismatch")
    verify_sources(config)
    for seed in config["seeds"]:
        for model in MODELS:
            directory = source / "coarse_grained" / f"seed_{seed}" / model
            run = read_json(directory / "run.json")
            if run.get("status") != "completed" or (run["trial"], run["seed"], run["model"]) != ("coarse_grained", seed, model):
                raise ValueError("Incomplete or incorrect run identity")
            if not set(COMPACT).issubset(run["artifact_sha256"]):
                raise ValueError("Run is missing required artifact fingerprints")
            for file, sha in run["artifact_sha256"].items():
                if digest(directory / file) != sha:
                    raise ValueError(f"Result hash mismatch: {model}/{file}")
            if read_json(directory / "metrics.json") != run["metrics"]:
                raise ValueError("Run metrics disagree with saved evidence")
    return manifest


def title_config(source, seed):
    """Rules start without inherited topic-ID overrides; hashes bind this fresh run."""
    return {
        "status": "Draft descriptive labels, not expert-validated legal categories",
        "scope": "Fresh coarse-grained retraining, primary seed; keyword-only descriptions, not expert review",
        "configuration": "coarse_grained", "seed": seed,
        "keyword_sha256": {model: digest(source / model / "topic_keywords.csv") for model in MODELS},
        "overrides": {},
    }


def dashboard_data(evidence, temporal, manifest, summary):
    figures = read_json(temporal / "manifest.json")
    years = figures["years"]
    result = {
        "schema_version": 1, "configuration": "coarse_grained", "seed": figures["seed"],
        "sensitivity_seeds": manifest["config"]["seeds"][1:],
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "run_started_utc": manifest["created_utc"], "run_finished_utc": manifest["finished_utc"],
        "documents": manifest["documents"], "units": manifest["units"],
        "parameters": figures["parameters"], "years": years,
        "yearly_documents": [figures["yearly_documents"][str(y)] for y in years],
        "source_sha256": manifest["source_sha256"],
        "input_units_sha256": manifest["input_units_sha256"],
        "experiment_config_sha256": figures["experiment_config_sha256"],
        "temporal_manifest_sha256": digest(temporal / "manifest.json"),
        "fresh_encoder_inference": not manifest["semantic_encoder_metadata"]["cache_used"],
        "encoder": manifest["config"]["common"]["encoder"],
        "encoder_revision": manifest["config"]["common"]["encoder_revision"],
        "fit_count": manifest["completed_runs"], "session_wall_seconds": manifest["session_wall_seconds"],
        "label_status": figures["label_status"],
        "selection_reason": manifest["config"]["selection_policy"],
        "models": {},
    }
    for model in MODELS:
        catalog = pd.read_csv(temporal / "tables" / "all_topic_titles.csv", keep_default_na=False)
        catalog = catalog[catalog.model.eq(model)]
        _, matrix, weighted = load_temporal(evidence / "coarse_grained", model, read_json(temporal / "title_rules_overrides.json")["overrides"])
        rows = []
        for row in catalog.to_dict("records"):
            rows.append({"id": int(row["topic"]), "title": row["title"], "category": row["category"],
                         "label_method": row["label_method"], "keywords": row["clustered_words"].split("; "),
                         "matched_keywords": row["matched_keywords"].split("; ") if row["matched_keywords"] else [],
                         "fractional_documents": float(row["fractional_documents_total"]),
                         "shares": matrix.loc[row["topic"], years].tolist()})
        outliers = matrix.loc[-1, years].tolist() if -1 in matrix.index else [0.] * len(years)
        shares = np.array([t["shares"] for t in rows])
        if not np.allclose(shares.sum(axis=0) + outliers, 1):
            raise ValueError("Dashboard data lost document weight")
        if not np.array_equal(weighted.groupby("year").documents_in_year.first().to_numpy(), result["yearly_documents"]):
            raise ValueError("Dashboard yearly denominators disagree")
        metrics = read_json(evidence / "coarse_grained" / model / "metrics.json")
        if len(rows) != metrics["topics_excluding_outliers"]:
            raise ValueError("Dashboard topic count disagrees with measured metrics")
        stability = summary[summary.model.eq(model)].iloc[0]
        result["models"][model] = {"name": "Lexical" if model == "lexical" else "Legal-BERT",
            "pipeline": "TF-IDF → SVD → UMAP → HDBSCAN → c-TF-IDF" if model == "lexical" else "Frozen Legal-BERT → all-chunk pooling → UMAP → HDBSCAN → c-TF-IDF",
            "metrics": metrics,
            "aligned_seed_stability": float(stability["seed_aligned_weighted_jaccard_mean"]),
            "topics": rows, "outlier_shares": outliers}
    return result


def publish(config_path, report, temporal, dashboard, titles_path=None):
    config = read_json(config_path)
    source = ROOT / config["output"]
    if report.exists() or temporal.exists() or (dashboard / "data").exists() or (dashboard / "downloads").exists():
        raise ValueError("Publication output exists; choose fresh destinations, never overwrite")
    manifest = validate_completed(source, config)
    seed = config["seeds"][0]
    evidence = report / "evidence"
    evidence.mkdir(parents=True)
    for name in ("configuration.json", "experiment.json", "run_results.csv", "tuning_results.csv", "seed_stability.csv", "cross_model_agreement.csv", "environment-freeze.txt"):
        shutil.copy2(source / name, evidence / name)
    shutil.copytree(source / "code_snapshot", evidence / "code_snapshot")
    for script in (Path(__file__), ROOT / "scripts/build_temporal_graphs.py"):
        shutil.copy2(script, evidence / "code_snapshot/scripts" / script.name)
    shutil.copytree(source / "alignments", evidence / "alignments")
    for model in MODELS:
        original = source / "coarse_grained" / f"seed_{seed}" / model
        target = evidence / "coarse_grained" / model
        target.mkdir(parents=True)
        for file in COMPACT:
            shutil.copy2(original / file, target / file)
    titles = read_json(titles_path) if titles_path else title_config(evidence / "coarse_grained", seed)
    write_json(report / "title_config.json", titles)
    report_manifest = {"status": "completed", "models_retrained": True,
        "encoder_finetuned": False, "fresh_encoder_inference": True,
        "completed_fits": manifest["completed_runs"], "primary_seed": seed,
        "selection": "Research-team choice for broad-theme analysis, not expert validation or a new superiority claim",
        "source_experiment": config["output"],
        "exporter_sha256": digest(Path(__file__)),
        "files_sha256": {p.relative_to(report).as_posix(): digest(p) for p in sorted(report.rglob("*")) if p.is_file()}}
    write_json(report / "report_manifest.json", report_manifest)
    build(evidence / "coarse_grained", temporal, report / "title_config.json")
    summary = pd.read_csv(source / "tuning_results.csv")
    data = dashboard_data(evidence, temporal, manifest, summary)
    data_dir = dashboard / "data"
    data_dir.mkdir(parents=True)
    write_json(data_dir / "results.json", data)
    downloads = dashboard / "downloads"
    downloads.mkdir()
    for name in ("Temporal_Topic_Summaries.pdf", "Temporal_Topic_Summaries.pptx", "manifest.json", "title_rules_overrides.json"):
        shutil.copy2(temporal / name, downloads / name)
    for name in ("all_topic_titles.csv", "lexical_labeled_temporal_data.csv", "semantic_labeled_temporal_data.csv"):
        shutil.copy2(temporal / "tables" / name, downloads / name)
    for name in ("configuration.json", "tuning_results.csv", "seed_stability.csv"):
        shutil.copy2(evidence / name, downloads / name)
    shutil.copy2(report / "report_manifest.json", downloads / "retraining_manifest.json")
    shutil.copytree(temporal / "figures", downloads / "figures")
    write_json(downloads / "checksums.json", {p.relative_to(dashboard).as_posix(): digest(p)
        for p in sorted(dashboard.rglob("*")) if p.is_file() and (data_dir in p.parents or downloads in p.parents)})
    lines = ["# Fresh coarse-grained retraining", "",
        f"Completed {manifest['completed_runs']} fresh fits; seeds {config['seeds']}; primary seed {seed}.",
        f"Unchanged corpus: {manifest['documents']:,} source documents / {manifest['units']:,} model units.",
        "Fresh lexical representation and frozen Legal-BERT inference; no prior embedding cache reused. Legal-BERT was not fine-tuned.",
        "", "| Model | Topics | C_v | Unit coverage | Mean aligned seed stability |",
        "|---|---:|---:|---:|---:|"]
    for model, value in data["models"].items():
        m = value["metrics"]
        lines.append(f"| {value['name']} | {m['topics_excluding_outliers']} | {m['cv_coherence']:.4f} | {m['topic_coverage']:.2%} | {value['aligned_seed_stability']:.4f} |")
    lines.extend(["", config["selection_policy"], "",
        "Temporal titles are keyword-derived drafts, not expert-approved categories. Procedural, mixed and OCR-heavy topics remain visible.",
        "Annual shares are document-weighted, include outliers, and describe the eligible archive, not all city legislation. Only 32 documents represent 2025.",
        "", "The temporal renderer records `models_rerun: false` because rendering does not train models. This report records the separate fresh retraining and binds its evidence by SHA-256.",
        "Historical Conservative artifacts are preserved unchanged. Their labels and expert-review scope do not validate the new coarse-grained outputs.",
        "", f"Measured total run wall time: {manifest['session_wall_seconds']:.2f} seconds.",
        "No expert scores, predictive accuracy, causal trend claims, or external validation are inferred.", ""])
    (report / "RESULTS.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"Published verified fresh evidence: {report}")
    print(f"Dashboard: {dashboard}; {sum(len(m['topics']) for m in data['models'].values())} topics")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=ROOT / "configs/coarse_grained_retrain.json")
    parser.add_argument("--report", type=Path, default=ROOT / "artifacts/coarse_grained_retrain")
    parser.add_argument("--temporal", type=Path, default=ROOT / "artifacts/temporal_topics_coarse_grained")
    parser.add_argument("--dashboard", type=Path, default=ROOT / "dashboard")
    parser.add_argument("--titles", type=Path, help="Optional reviewed, run-scoped keyword-title config")
    args = parser.parse_args()
    publish(args.config, args.report, args.temporal, args.dashboard, args.titles)
