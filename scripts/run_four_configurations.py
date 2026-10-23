"""Actual full-corpus four-configuration reruns, with durable per-seed evidence."""
from __future__ import annotations
# Fixed thread settings must precede NumPy/Numba imports. No PATH modification.
import os
for variable in ["OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS", "NUMBA_NUM_THREADS"]:
    os.environ[variable] = "4"
os.environ["TOKENIZERS_PARALLELISM"] = "false"

import argparse
from datetime import datetime, timezone
import gc
import hashlib
import importlib.metadata
import itertools
import json
from pathlib import Path
import platform
import random
import shutil
import subprocess
import sys
import time
import traceback

import numpy as np
import pandas as pd
ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "scripts")]
from clean_encoder import encode
from clean_model import build_vocabulary, lexical_vectors, fit_branch, json_write
from run_clean_text import validate
from tuning_evaluation import align_topics, temporal_comparison, document_prevalence, granularity, ResourceMonitor

CODE_FILES = ["scripts/run_four_configurations.py", "scripts/run_clean_text.py", "scripts/prepare_clean_text.py",
              "src/clean_model.py", "src/clean_encoder.py", "src/tuning_evaluation.py"]


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def verify_sources(config):
    preparation = ROOT / config["preparation"]
    manifest = json.loads((preparation / "preparation.json").read_text())
    if digest(ROOT / config["source"]) != manifest["sections_sha256"]:
        raise ValueError("Prepared input changed since the original preparation")
    if digest(ROOT / "scripts/prepare_clean_text.py") != manifest["preparation_code_sha256"]:
        raise ValueError("Preprocessing code differs from the original")
    sources = ROOT / "data/processed/clean_text"
    hashes = sorted((p.relative_to(sources).as_posix(), digest(p)) for p in sources.rglob("*.txt"))
    actual = hashlib.sha256(json.dumps(hashes).encode()).hexdigest()
    if actual != manifest["source_manifest_sha256"]:
        raise ValueError("Cleaned source files differ from the original audit")
    for name, expected in manifest["override_files"].items():
        if digest(ROOT / "data" / name) != expected:
            raise ValueError(f"Temporal override changed: {name}")
    current_overrides = {p.name for p in (ROOT / "data").glob("manual_year_overrides_*.csv")}
    if current_overrides != set(manifest["override_files"]):
        raise ValueError("Temporal override file set changed")
    return manifest


def check_config(config):
    seeds = config["seeds"]
    names = [t["name"] for t in config["trials"]]
    if len(names) != 4 or len(set(names)) != 4 or len(seeds) < 3 or len(set(seeds)) != len(seeds):
        raise ValueError("Require four unique trials and at least three distinct seeds")
    if seeds[0] != config["common"]["seed"] or config["common"]["stability_runs"] != 1:
        raise ValueError("Primary seed must match fixed representation seed; repeats are orchestrated externally")
    if config["common"]["ngram_max"] != 1:
        raise ValueError("Preserve the shared unigram C_v methodology")
    for trial in config["trials"]:
        if not trial["name"].replace("_", "").isalnum():
            raise ValueError("Unsafe trial name")
        if trial["neighbors"] < 2 or trial["min_cluster_size"] < 2 or trial["min_samples"] < 1 or not 0 <= trial["min_dist"] <= 1:
            raise ValueError("Invalid clustering parameters")


def reuse_embeddings(config, output):
    """Copy, never modify, an optional completed encoder cache; encode validates identity."""
    source = config.get("embedding_cache_source")
    destination = output / "embedding_cache"
    if not source or destination.exists():
        return
    source = ROOT / source
    if not source.exists():
        print("Prior cache unavailable; encoding the full corpus afresh", flush=True)
        return
    old = json.loads((ROOT / config["baseline_experiment"] / "experiment.json").read_text())
    if old["code_sha256"]["src/clean_encoder.py"] != digest(ROOT / "src/clean_encoder.py"):
        raise ValueError("Encoder implementation changed; do not reuse the old embeddings")
    files = ["identity.json", "metadata.json", "vectors.npy"]
    if not all((source / f).exists() for f in files):
        raise ValueError("Prior embedding cache is incomplete")
    destination.mkdir()
    for f in files:
        shutil.copy2(source / f, destination / f)
    json_write(output / "embedding_reuse.json", {"source": str(source), "source_files_sha256": {f: digest(source / f) for f in files},
               "note": "Frozen representation cache only; all clustering and evaluation are rerun. Historic encoder time is not charged as current inference."})


def summarize(output, config, frame, records):
    table = pd.DataFrame(records)
    table.to_csv(output / "run_results.csv", index=False)
    successes = table[table.status.eq("completed")]
    labels = {}
    for row in successes.itertuples():
        # Index correspondence is checked, not inferred from row count alone.
        assignments = pd.read_csv(output / row.trial / f"seed_{row.seed}" / row.model / "section_topics.csv", keep_default_na=False,
                                  dtype={"ordinance_id": str, "section_id": str})
        if not assignments[["ordinance_id", "section_id", "year"]].equals(frame[["ordinance_id", "section_id", "year"]]):
            raise ValueError("Saved assignments do not match ordered input identity")
        labels[row.trial, row.model, row.seed] = assignments.topic.to_numpy()
    pairs_dir = output / "alignments"
    pairs_dir.mkdir(exist_ok=True)
    stability, temporal, cross = [], [], []
    def compare(kind, name, akey, bkey):
        a, b = labels[akey], labels[bkey]
        alignment, stats = align_topics(a, b)
        annual, trajectory, tstats = temporal_comparison(frame, a, b, alignment)
        alignment.to_csv(pairs_dir / f"{name}_alignment.csv", index=False)
        annual.to_csv(pairs_dir / f"{name}_annual.csv", index=False)
        trajectory.to_csv(pairs_dir / f"{name}_trajectories.csv", index=False)
        return {"kind": kind, "comparison": name, **stats, **tstats}
    primary = config["seeds"][0]
    for model in ["lexical", "semantic"]:
        for trial in config["trials"]:
            name = trial["name"]
            for a, b in itertools.combinations(config["seeds"], 2):
                keys = [(name, model, s) for s in [a, b]]
                if all(k in labels for k in keys):
                    stability.append({"trial": name, "model": model, "seed_left": a, "seed_right": b,
                                      **compare("seed", f"{model}_{name}_{a}_{b}", *keys)})
        for a, b in itertools.combinations([t["name"] for t in config["trials"]], 2):
            keys = [(t, model, primary) for t in [a, b]]
            if all(k in labels for k in keys):
                temporal.append({"model": model, "left_trial": a, "right_trial": b,
                                 **compare("configuration", f"{model}_{a}_vs_{b}", *keys)})
    for trial in config["trials"]:
        keys = [(trial["name"], m, primary) for m in ["lexical", "semantic"]]
        if all(k in labels for k in keys):
            _, stats = align_topics(*(labels[k] for k in keys))
            cross.append({"trial": trial["name"], **stats})
    stable = pd.DataFrame(stability)
    temp = pd.DataFrame(temporal)
    stable.to_csv(output / "seed_stability.csv", index=False)
    temp.to_csv(output / "temporal_consistency.csv", index=False)
    pd.DataFrame(cross).to_csv(output / "cross_model_agreement.csv", index=False)
    rows = []
    aggregate = ["topics_excluding_outliers", "cv_coherence", "topic_diversity", "topic_coverage", "outlier_fraction",
                 "fit_evaluation_seconds", "sampled_peak_rss_mib", "largest_topic_fraction_all_units", "effective_topics"]
    for (trial, model), group in successes.groupby(["trial", "model"], sort=False):
        first = group[group.seed.eq(primary)]
        row = first.iloc[0].to_dict() if len(first) else {"trial": trial, "model": model}
        row["completed_seeds"] = len(group)
        for metric in aggregate:
            values = pd.to_numeric(group[metric], errors="coerce").dropna()
            row[metric+"_mean"] = float(values.mean()) if len(values) else None
            row[metric+"_sd"] = float(values.std(ddof=1)) if len(values) > 1 else None
        s = stable[(stable.trial == trial) & (stable.model == model)] if len(stable) else pd.DataFrame()
        if len(s):
            for metric in ["ari_all_units", "ari_jointly_assigned", "aligned_macro_jaccard", "aligned_weighted_jaccard", "temporal_similarity"]:
                row["seed_"+metric+"_mean"] = float(s[metric].mean()) if s[metric].notna().any() else None
            row["stability_ari_mean"] = float(s.loc[s.seed_left.eq(primary), "ari_all_units"].mean())
        t = temp[(temp.model == model) & ((temp.left_trial == trial) | (temp.right_trial == trial))] if len(temp) else pd.DataFrame()
        row["cross_config_temporal_similarity_mean"] = float(t.temporal_similarity.mean()) if len(t) else None
        row["cross_config_temporal_tv_mean"] = float(t.temporal_tv_mean.mean()) if len(t) else None
        rows.append(row)
    pd.DataFrame(rows).to_csv(output / "tuning_results.csv", index=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=ROOT / "configs/four_configuration_tuning.json")
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    config = json.loads(args.config.read_text(encoding="utf-8"))
    check_config(config)
    preparation = verify_sources(config)
    output = ROOT / config["output"]
    fingerprint = {"config": config, "source_sha256": digest(ROOT / config["source"]),
                   "preparation_sha256": digest(ROOT / config["preparation"] / "preparation.json"),
                   "code_sha256": {f: digest(ROOT / f) for f in CODE_FILES}}
    packages = {d.metadata["Name"]: d.version for d in importlib.metadata.distributions() if d.metadata["Name"]}
    fingerprint["packages"] = dict(sorted(packages.items()))
    if output.exists():
        if not args.resume:
            raise ValueError("Choose a new output or --resume; never overwrite a previous experiment")
        old = json.loads((output / "experiment.json").read_text())
        if any(old.get(k) != v for k, v in fingerprint.items()):
            raise ValueError("Resume rejected: changed configuration, input, code or packages")
        if old["status"] == "completed":
            print("Already completed; nothing overwritten")
            return
    else:
        output.mkdir(parents=True)
    manifest = {**fingerprint, "status": "running", "created_utc": datetime.now(timezone.utc).isoformat(),
                "python": sys.version, "platform": platform.platform(), "processor": platform.processor(),
                "logical_cpus": os.cpu_count(), "preparation": preparation,
                "threads": {k: os.environ[k] for k in ["OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS", "NUMBA_NUM_THREADS"]},
                "runtime_scope": "Per-seed fit/evaluation includes UMAP, HDBSCAN, keywords, coherence and saving artifacts; excludes shared representation construction and pairwise postprocessing. RSS is whole-process sampled resident memory, not incremental model allocation or VRAM."}
    try:
        manifest["git_head"] = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
        manifest["git_branch"] = subprocess.check_output(["git", "branch", "--show-current"], cwd=ROOT, text=True).strip()
    except subprocess.CalledProcessError:
        pass
    json_write(output / "experiment.json", manifest)
    json_write(output / "configuration.json", config)
    (output / "environment-freeze.txt").write_text(subprocess.check_output([sys.executable, "-m", "pip", "freeze"], text=True), encoding="utf-8")
    for f in CODE_FILES:
        target = output / "code_snapshot" / f
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / f, target)
    records = []
    began = time.perf_counter()
    try:
        frame = pd.read_csv(ROOT / config["source"], keep_default_na=False)
        validate(frame)
        from sklearn.feature_extraction.text import CountVectorizer
        common = argparse.Namespace(**config["common"])
        analyzer = CountVectorizer(lowercase=True, strip_accents="unicode", stop_words=common.stopwords,
                                   token_pattern=r"(?u)\b[a-zA-Z][a-zA-Z]+\b").build_analyzer()
        usable = frame.text.map(lambda text: bool(analyzer(text)))
        frame.loc[~usable].to_csv(output / "vocabulary_exclusions.csv", index=False)
        frame = frame.loc[usable].reset_index(drop=True)
        if set(frame.year) != set(config["years"]):
            raise ValueError("Study years differ from the fixed experiment")
        frame.to_csv(output / "input_units.csv", index=False)
        with ResourceMonitor() as monitor:
            counts, terms, frozen = build_vocabulary(frame.text.tolist(), common)
        manifest["shared_vocabulary_resources"] = monitor.metrics
        pd.DataFrame({"term": terms}).to_csv(output / "shared_vocabulary.csv", index=False)
        with ResourceMonitor() as monitor:
            lexical, lexical_meta = lexical_vectors(counts, common)
        manifest["lexical_representation_resources"] = monitor.metrics
        reuse_embeddings(config, output)
        with ResourceMonitor() as monitor:
            semantic, semantic_meta = encode(frame.text.tolist(), config["common"], output / "embedding_cache")
        manifest["semantic_representation_resources"] = monitor.metrics
        manifest["semantic_encoder_metadata"] = semantic_meta
        import torch
        manifest["gpu"] = torch.cuda.get_device_name(0) if torch.cuda.is_available() else None
        manifest.update(units=len(frame), documents=int(frame.ordinance_id.nunique()), vocabulary_terms=len(terms),
                        input_units_sha256=digest(output / "input_units.csv"), shared_vocabulary_sha256=digest(output / "shared_vocabulary.csv"))
        print(f"ACTUAL EXPERIMENT: {len(frame)} units / {frame.ordinance_id.nunique()} documents; 4 configurations x 2 models x {len(config['seeds'])} seeds", flush=True)
        json_write(output / "experiment.json", manifest)
        for trial in config["trials"]:
            params = {k: trial[k] for k in ["neighbors", "min_dist", "min_cluster_size", "min_samples"]}
            for seed in config["seeds"]:
                for model, vectors, meta in [("lexical", lexical, lexical_meta), ("semantic", semantic, semantic_meta)]:
                    directory = output / trial["name"] / f"seed_{seed}" / model
                    run_record = directory / "run.json"
                    if args.resume and run_record.exists():
                        saved = json.loads(run_record.read_text())
                        if saved["status"] == "completed" and all((directory / f).exists() and digest(directory / f) == sha for f, sha in saved["artifact_sha256"].items()):
                            records.append(saved["metrics"])
                            continue
                    directory.mkdir(parents=True, exist_ok=True)
                    identity = {"model": model, "trial": trial["name"], "seed": seed, **params}
                    json_write(run_record, {**identity, "status": "running"})
                    print(f"START {trial['name']} / {model} / seed {seed}", flush=True)
                    random.seed(seed)
                    np.random.seed(seed)
                    options = argparse.Namespace(**(config["common"] | params | {"seed": seed}), output=directory.parent)
                    try:
                        with ResourceMonitor() as monitor:
                            labels, metrics = fit_branch(model, vectors, frame, counts, terms, frozen, options, meta)
                            document_prevalence(frame, labels).to_csv(directory / "document_weighted_prevalence.csv", index=False)
                        metrics.update(identity | monitor.metrics | granularity(labels) | {
                            "status": "completed", "assigned_units": int((labels != -1).sum()),
                            "documents_with_any_assignment": int(frame.loc[labels != -1, "ordinance_id"].nunique()),
                            "documents_with_all_units_assigned": int(frame.assign(assigned=labels != -1).groupby("ordinance_id").assigned.all().sum())})
                        json_write(directory / "metrics.json", metrics)
                        artifacts = {p.name: digest(p) for p in directory.iterdir() if p.is_file() and p.name != "run.json"}
                        json_write(run_record, {**identity, "status": "completed", "metrics": metrics, "artifact_sha256": artifacts})
                        records.append(metrics)
                        print(f"DONE {trial['name']} / {model} / {seed}: topics={metrics['topics_excluding_outliers']} coverage={metrics['topic_coverage']:.4f}, seconds={metrics['fit_evaluation_seconds']:.1f}", flush=True)
                    except Exception as exc:
                        failure = {**identity, "status": "failed", "error": repr(exc)}
                        json_write(run_record, failure)
                        (directory / "failure.txt").write_text(traceback.format_exc(), encoding="utf-8")
                        records.append(failure)
                        print(f"FAILED {identity}: {exc}", flush=True)
                    pd.DataFrame(records).to_csv(output / "run_results.csv", index=False)
                    gc.collect()
        summarize(output, config, frame, records)
        expected = len(config["trials"]) * 2 * len(config["seeds"])
        complete = sum(r["status"] == "completed" for r in records)
        manifest.update(status="completed" if complete == expected else "partial_failure", completed_runs=complete, expected_runs=expected)
    except BaseException as exc:
        manifest.update(status="failed", error=repr(exc))
        raise
    finally:
        manifest.update(finished_utc=datetime.now(timezone.utc).isoformat(), session_wall_seconds=time.perf_counter()-began)
        json_write(output / "experiment.json", manifest)
    print(f"Experiment status: {manifest['status']}", flush=True)
    if manifest["status"] != "completed":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
