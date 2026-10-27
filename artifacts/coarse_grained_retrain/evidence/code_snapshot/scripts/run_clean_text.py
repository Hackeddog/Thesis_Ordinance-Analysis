"""Run two comparable topic models on the full prepared clean-TXT corpus."""
import argparse
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
import logging
from pathlib import Path
import sys
import time

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from clean_encoder import encode
from clean_model import build_vocabulary, lexical_vectors, fit_branch, json_write


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def validate(frame):
    required = {"ordinance_id", "section_id", "year", "text", "source_file", "verification_status"}
    if required - set(frame):
        raise ValueError(f"Missing columns: {required - set(frame)}")
    if frame.empty or frame.duplicated(["ordinance_id", "section_id"]).any():
        raise ValueError("Empty corpus or duplicate unit IDs")
    years = pd.to_numeric(frame.year, errors="raise")
    if (years % 1 != 0).any() or not years.between(2016, 2025).all():
        raise ValueError("Invalid study-window years")
    if frame.groupby("ordinance_id").year.nunique().gt(1).any():
        raise ValueError("Conflicting years for a document")
    if not frame.verification_status.eq("verified").all():
        raise ValueError("This run requires user-verified cleaned inputs")
    if frame.text.str.strip().eq("").any():
        raise ValueError("Empty unit text")


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--config", type=Path, default=ROOT / "configs/clean_text_full.json")
    p.add_argument("--resume", action="store_true", help="Resume this exact config/input; preserves the embedding checkpoint")
    args = p.parse_args()
    logging.basicConfig(level=logging.WARNING)
    config = json.loads(args.config.read_text(encoding="utf-8"))
    source, output = ROOT / config["source"], ROOT / config["output"]
    fingerprint = {"config": config, "source_sha256": digest(source),
                   "code_sha256": {f: digest(ROOT / f) for f in ["scripts/run_clean_text.py", "src/clean_model.py", "src/clean_encoder.py"]}}
    if output.exists():
        if not args.resume:
            raise ValueError("Output exists; use a new config/output or explicitly --resume")
        prior = json.loads((output / "experiment.json").read_text())
        if any(prior.get(k) != v for k, v in fingerprint.items()):
            raise ValueError("Cannot resume changed input/config/code")
        if prior["status"] == "completed":
            print("Experiment already completed; nothing overwritten")
            return
    else:
        output.mkdir(parents=True)
    frame = pd.read_csv(source, keep_default_na=False)
    validate(frame)
    settings = argparse.Namespace(**config["common"])
    # Apply a common, explicit eligibility mask before either representation is computed.
    from sklearn.feature_extraction.text import CountVectorizer
    analyzer = CountVectorizer(lowercase=True, strip_accents="unicode", stop_words=settings.stopwords,
                               token_pattern=r"(?u)\b[a-zA-Z][a-zA-Z]+\b").build_analyzer()
    usable = frame.text.map(lambda text: bool(analyzer(text)))
    frame.loc[~usable].assign(exclusion_reason="no tokens after shared vocabulary preprocessing").to_csv(output / "vocabulary_exclusions.csv", index=False)
    frame = frame.loc[usable].reset_index(drop=True)
    if set(frame.year) != set(config["years"]):
        raise ValueError("A requested study year has no eligible units")
    counts, terms, frozen = build_vocabulary(frame.text.tolist(), settings)
    frame.to_csv(output / "input_units.csv", index=False)
    pd.DataFrame({"term": terms}).to_csv(output / "shared_vocabulary.csv", index=False)
    manifest = {**fingerprint, "created_utc": datetime.now(timezone.utc).isoformat(), "status": "running",
                "documents": int(frame.ordinance_id.nunique()), "units": len(frame),
                "unique_ordinance_numbers": int(frame.ordinance_number.nunique()),
                "vocabulary_exclusions": int((~usable).sum()), "vocabulary_terms": len(terms),
                "unit_types": frame.unit_type.value_counts().to_dict(), "packages": {}}
    for package in ["torch", "transformers", "bertopic", "hdbscan", "umap-learn", "numpy", "pandas", "scikit-learn", "gensim"]:
        manifest["packages"][package] = importlib.metadata.version(package)
    json_write(output / "experiment.json", manifest)
    results = []
    try:
        print(f"Full corpus: {len(frame)} units, {frame.ordinance_id.nunique()} documents; no sampling", flush=True)
        embeddings, encoder_metadata = encode(frame.text.tolist(), config["common"], output / "embedding_cache")
        for trial in config["trials"]:
            args_model = argparse.Namespace(**(config["common"] | {k: v for k, v in trial.items() if k != "name"}),
                                            output=output / trial["name"])
            trial_metrics, labels_by_model = [], {}
            for name in ["lexical", "semantic"]:
                print(f"Fitting {trial['name']} / {name}", flush=True)
                started = time.perf_counter()
                if name == "lexical":
                    vectors, metadata = lexical_vectors(counts, args_model)
                else:
                    vectors, metadata = embeddings, encoder_metadata
                labels, metrics = fit_branch(name, vectors, frame, counts, terms, frozen, args_model, metadata)
                metrics.update({"trial": trial["name"], "fit_evaluation_seconds": time.perf_counter()-started,
                                **{k: trial[k] for k in ["neighbors", "min_dist", "min_cluster_size", "min_samples"]}})
                json_write(args_model.output / name / "metrics.json", metrics)
                trial_metrics.append(metrics)
                results.append(metrics)
                labels_by_model[name] = labels
                pd.DataFrame(results).to_csv(output / "tuning_results.csv", index=False)
                # Document-weighted view reduces unequal section-count contributions.
                assignments = frame.assign(topic=labels)
                per_doc = assignments.groupby(["year", "ordinance_id", "topic"]).size().rename("units").reset_index()
                per_doc["document_share"] = per_doc.units / per_doc.groupby("ordinance_id").units.transform("sum")
                doc_prevalence = per_doc.groupby(["year", "topic"]).document_share.sum().rename("fractional_documents").reset_index()
                doc_prevalence["documents_in_year"] = doc_prevalence.year.map(frame.groupby("year").ordinance_id.nunique())
                doc_prevalence["share"] = doc_prevalence.fractional_documents / doc_prevalence.documents_in_year
                doc_prevalence.to_csv(args_model.output / name / "document_weighted_prevalence.csv", index=False)
            pd.DataFrame(trial_metrics).to_csv(args_model.output / "comparison_metrics.csv", index=False)
            from sklearn.metrics import adjusted_rand_score
            a, b = labels_by_model["lexical"], labels_by_model["semantic"]
            both = (a != -1) & (b != -1)
            json_write(args_model.output / "cross_model_agreement.json", {
                "ari_all_units": float(adjusted_rand_score(a, b)), "jointly_assigned_units": int(both.sum()),
                "ari_jointly_assigned": float(adjusted_rand_score(a[both], b[both])) if both.sum() > 1 else None,
                "note": "Partition agreement, not accuracy. Topic IDs are model-local."})
        manifest["status"] = "completed"
    except BaseException as exc:
        manifest.update(status="failed", error=str(exc))
        raise
    finally:
        json_write(output / "experiment.json", manifest)
    print("Completed full clean-text experiment", flush=True)


if __name__ == "__main__":
    main()
