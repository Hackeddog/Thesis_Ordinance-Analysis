"""Publish only measured, complete four-configuration evidence and labeled figures."""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import shutil
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from tuning_evaluation import align_topics

NAMES = {"lexical": "Model A: Lexical", "semantic": "Model B: Legal-BERT"}
COLORS = {"lexical": "#146B85", "semantic": "#B8562C"}
TRIALS = ["initial", "conservative", "fine_grained", "coarse_grained"]
LABELS = ["Initial", "Conservative", "Fine-grained", "Coarse-grained"]
TRIAL_COLORS = ["#146B85", "#A14A76", "#3C8055", "#C58226"]


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def markdown(frame):
    def fmt(x):
        if x is None or (isinstance(x, float) and np.isnan(x)):
            return "N/A"
        return f"{x:.4f}" if isinstance(x, float) else str(x).replace("|", "/")
    return "| " + " | ".join(map(str, frame.columns)) + " |\n| " + " | ".join(["---"]*len(frame.columns)) + " |\n" + "\n".join("| " + " | ".join(fmt(v) for v in row) + " |" for row in frame.itertuples(index=False, name=None))


def save(fig, directory, name, caption):
    fig.text(.01, .012, caption, ha="left", va="bottom", fontsize=8, color="#444444", wrap=True)
    fig.tight_layout(rect=(0, .07, 1, .96))
    for extension in ["png", "pdf", "svg"]:
        fig.savefig(directory / f"{name}.{extension}", dpi=300, bbox_inches="tight")
    plt.close(fig)


def validate_completed(source, config):
    manifest = json.loads((source / "experiment.json").read_text())
    if manifest["status"] != "completed" or manifest.get("completed_runs") != 24:
        raise ValueError("A completed 24-fit experiment is required; never publish partial results as complete")
    if manifest["config"] != config:
        raise ValueError("Configuration does not match completed experiment")
    for file, expected in manifest["code_sha256"].items():
        if digest(source / "code_snapshot" / file) != expected:
            raise ValueError(f"Code snapshot changed: {file}")
    if digest(source / "input_units.csv") != manifest["input_units_sha256"]:
        raise ValueError("Ordered experimental input changed")
    for trial in config["trials"]:
        for seed in config["seeds"]:
            for model in NAMES:
                directory = source / trial["name"] / f"seed_{seed}" / model
                run = json.loads((directory / "run.json").read_text())
                if run["status"] != "completed":
                    raise ValueError("Incomplete seed fit")
                for name, expected in run["artifact_sha256"].items():
                    if digest(directory / name) != expected:
                        raise ValueError(f"Changed result artifact: {directory / name}")
    return manifest


def generate_figures(source, destination, summary, runs, temporal, primary):
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10,
                         "axes.spines.top": False, "axes.spines.right": False,
                         "axes.titleweight": "bold", "pdf.fonttype": 42, "ps.fonttype": 42})
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.6), sharey=True)
    for ax, model in zip(axes, NAMES):
        data = summary[summary.model.eq(model)].set_index("trial").loc[TRIALS]
        bars = ax.bar(LABELS, data.topics_excluding_outliers, color=COLORS[model], alpha=.85)
        for i, trial in enumerate(TRIALS):
            values = runs[(runs.model == model) & (runs.trial == trial)].topics_excluding_outliers
            ax.scatter(np.full(len(values), i), values, s=25, color="#222222", marker="_", zorder=4)
        ax.bar_label(bars, padding=4, fontsize=9)
        ax.set_title(NAMES[model]); ax.tick_params(axis="x", rotation=15)
        ax.set_ylabel("Topics excluding -1"); ax.margins(y=.18)
    fig.suptitle("Topic granularity across four configurations", fontsize=15)
    save(fig, destination, "01_topic_counts", "Bars: seed 42; black ticks: individual seeds 42, 43, 44. More topics is not necessarily better.")

    panels = [
        ("cv_coherence", "C_v coherence", True), ("topic_diversity", "Keyword diversity", True),
        ("topic_coverage", "Unit assignment coverage", True), ("outlier_fraction", "Outlier fraction", True),
        ("seed_aligned_weighted_jaccard_mean", "Aligned seed stability (weighted Jaccard)", False),
        ("fit_evaluation_seconds", "Fit + evaluation wall time (seconds)", True),
        ("cross_config_temporal_similarity_mean", "Temporal similarity to other configurations", False),
        ("largest_topic_fraction_all_units", "Largest topic / all units", True)]
    for model in NAMES:
        fig, axes = plt.subplots(2, 4, figsize=(17, 8))
        data = summary[summary.model.eq(model)].set_index("trial").loc[TRIALS]
        for ax, (metric, title, repeated) in zip(axes.flat, panels):
            values = data[metric+"_mean"] if repeated else data[metric]
            error = data[metric+"_sd"].fillna(0) if repeated else None
            ax.bar(LABELS, values, yerr=error, capsize=3, color=TRIAL_COLORS, alpha=.9)
            ax.set_title(title, fontsize=10, wrap=True); ax.tick_params(axis="x", rotation=35, labelsize=8)
            ax.set_ylim(bottom=0)
            if metric != "fit_evaluation_seconds":
                ax.set_ylim(0, 1.05)
            ax.grid(axis="y", alpha=.15)
        fig.suptitle(NAMES[model] + " — separate metric scales", fontsize=15)
        save(fig, destination, f"02_metrics_{model}", "Means ± sample SD over three seeds where repeated. Stability: three seed pairs. Temporal: seed-42 pairwise comparisons; sensitivity, not truth.\nCoverage and outlier fraction are complements. Runtime excludes shared representation construction. No normalized composite quality score.")

    metrics = [("cv_coherence_mean", "C_v (seed mean)"), ("topic_coverage_mean", "Coverage (seed mean)"),
               ("seed_aligned_weighted_jaccard_mean", "Aligned seed stability"), ("topics_excluding_outliers_mean", "Topics (seed mean)")]
    parameters = [("neighbors", "UMAP neighbors"), ("min_dist", "UMAP minimum distance"),
                  ("min_cluster_size", "HDBSCAN minimum cluster size"), ("min_samples", "HDBSCAN minimum samples")]
    markers = ["o", "s", "^", "D"]
    fig, axes = plt.subplots(4, 4, figsize=(16, 13))
    for i, (metric, title) in enumerate(metrics):
        for j, (parameter, parameter_name) in enumerate(parameters):
            ax = axes[i, j]
            for row in summary.itertuples():
                idx = TRIALS.index(row.trial)
                ax.scatter(getattr(row, parameter), getattr(row, metric), color=COLORS[row.model], marker=markers[idx], s=60, alpha=.8)
            if i == 3: ax.set_xlabel(parameter_name, fontsize=9)
            if j == 0: ax.set_ylabel(title)
            ax.grid(alpha=.15)
    from matplotlib.lines import Line2D
    handles = [Line2D([], [], color=COLORS[m], marker="o", linestyle="", label=NAMES[m]) for m in NAMES]
    handles += [Line2D([], [], color="#555555", marker=markers[i], linestyle="", label=label) for i, label in enumerate(LABELS)]
    fig.legend(handles=handles, loc="upper center", ncol=6, bbox_to_anchor=(.5, .953), fontsize=9)
    fig.suptitle("Parameter–performance associations (joint changes, not isolated effects)", fontsize=15)
    save(fig, destination, "03_parameters_performance", "Four predeclared settings per model. Several parameters co-vary; no regression, causal importance or independent parameter optimum is inferred.\nFine vs Initial fixes UMAP; Coarse vs Conservative fixes UMAP. Marker overlaps are possible.")

    fig, axes = plt.subplots(2, 3, figsize=(14, 8))
    side = [("cv_coherence_mean", "C_v"), ("topic_diversity_mean", "Diversity"), ("topic_coverage_mean", "Coverage"),
            ("seed_aligned_weighted_jaccard_mean", "Aligned seed stability"),
            ("cross_config_temporal_similarity_mean", "Cross-configuration temporal similarity"),
            ("fit_evaluation_seconds_mean", "Fit/evaluation seconds")]
    for ax, (metric, title) in zip(axes.flat, side):
        for i, model in enumerate(NAMES):
            data = summary[summary.model.eq(model)].set_index("trial").loc[TRIALS]
            ax.bar(np.arange(4)+(i-.5)*.36, data[metric], width=.36, color=COLORS[model], label=NAMES[model])
        ax.set_xticks(range(4), LABELS, rotation=20, fontsize=9); ax.set_title(title, fontsize=11)
        ax.set_ylim(bottom=0)
        if "seconds" not in metric: ax.set_ylim(0, 1.05)
    axes[0, 0].legend(fontsize=8)
    fig.suptitle("Comparable measurements on identical units and vocabulary", fontsize=15)
    save(fig, destination, "04_model_comparison", "Topic IDs are not shared between models. Cross-configuration sensitivity compares each model with itself, not identical semantic categories.\nSeed means except pairwise sensitivity measures. Intrinsic comparisons are not held-out accuracy or expert legal assessment.")

    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    for ax, model in zip(axes, NAMES):
        matrix = np.eye(4)
        for row in temporal[temporal.model.eq(model)].itertuples():
            i, j = TRIALS.index(row.left_trial), TRIALS.index(row.right_trial)
            matrix[i, j] = matrix[j, i] = row.temporal_similarity
        im = ax.imshow(matrix, vmin=0, vmax=1, cmap="YlGnBu")
        for i in range(4):
            for j in range(4):
                ax.text(j, i, f"{matrix[i,j]:.3f}", ha="center", va="center", color="white" if matrix[i,j] > .65 else "black")
        ax.set_xticks(range(4), LABELS, rotation=30, ha="right"); ax.set_yticks(range(4), LABELS)
        ax.set_title(NAMES[model]); fig.colorbar(im, ax=ax, fraction=.046, label="1 − mean annual JS divergence")
    fig.suptitle("Temporal sensitivity after one-to-one topic alignment", fontsize=15)
    save(fig, destination, "05_temporal_consistency", "Seed 42, document-weighted annual distributions; include unmatched-topic mass and noise. Equal year weights, base-2 divergence.\nMatching penalizes topic splits/merges; agreement can include shared outlier mass and does not establish historical validity.")

    fig, axes = plt.subplots(2, 3, figsize=(16, 8))
    for mi, model in enumerate(NAMES):
        baseline = source / "initial" / f"seed_{primary}" / model
        ltab = pd.read_csv(baseline / "document_weighted_prevalence.csv")
        ranking = ltab[ltab.topic.ne(-1)].groupby("topic").fractional_documents.sum().sort_values(ascending=False)
        keywords = pd.read_csv(baseline / "topic_keywords.csv")
        base_labels = pd.read_csv(baseline / "section_topics.csv", usecols=["topic"]).topic.to_numpy()
        for ci, topic in enumerate(ranking.head(3).index):
            ax = axes[mi, ci]
            words = keywords[keywords.topic.eq(topic)].sort_values("rank").term.head(3).tolist()
            for ti, trial in enumerate(TRIALS):
                directory = source / trial / f"seed_{primary}" / model
                labels = pd.read_csv(directory / "section_topics.csv", usecols=["topic"]).topic.to_numpy()
                pairs, _ = align_topics(base_labels, labels)
                match = pairs[pairs.left_topic.eq(topic)]
                if match.empty:
                    ax.plot([], [], color=TRIAL_COLORS[ti], label=LABELS[ti]+" (unmatched)")
                    continue
                matched = int(match.right_topic.iloc[0])
                table = pd.read_csv(directory / "document_weighted_prevalence.csv")
                series = table[table.topic.eq(matched)].set_index("year").share.reindex(range(2016, 2026), fill_value=0)
                ax.plot(series.index, series.values*100, marker="o", ms=3, color=TRIAL_COLORS[ti], label=LABELS[ti])
            ax.set_title(f"{NAMES[model]} · Initial topic {topic}\n"+", ".join(words), fontsize=10)
            ax.set_ylabel("Document-weighted annual share (%)")
            ax.set_xticks([2016, 2018, 2020, 2022, 2024, 2025]); ax.tick_params(axis="x", rotation=30)
            ax.set_ylim(bottom=0); ax.grid(alpha=.15); ax.legend(fontsize=7)
    fig.suptitle("Major-topic trajectories: fixed Initial reference, aligned across configurations", fontsize=14)
    save(fig, destination, "06_major_topic_trends", "Three largest Initial topics by fractional document mass per model; keyword captions are not expert titles. Independently scaled panels.\nOne-to-one membership alignment can match a broad cluster to only one narrow topic. Missing matches are omitted, never plotted as observed zero.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=ROOT / "configs/four_configuration_tuning.json")
    parser.add_argument("--output", type=Path, default=ROOT / "artifacts/four_configuration_tuning")
    args = parser.parse_args()
    config = json.loads(args.config.read_text(encoding="utf-8"))
    source = ROOT / config["output"]
    manifest = validate_completed(source, config)
    output = args.output.resolve()
    evidence, figures = output / "evidence", output / "figures"
    evidence.mkdir(parents=True, exist_ok=True); figures.mkdir(parents=True, exist_ok=True)
    primary = config["seeds"][0]
    summary = pd.read_csv(source / "tuning_results.csv")
    runs = pd.read_csv(source / "run_results.csv")
    temporal = pd.read_csv(source / "temporal_consistency.csv")
    if len(summary) != 8 or len(runs) != 24 or not runs.status.eq("completed").all() or not summary.completed_seeds.eq(3).all():
        raise ValueError("Incomplete or inconsistent evaluation tables")
    for filename in ["tuning_results.csv", "run_results.csv", "seed_stability.csv", "temporal_consistency.csv", "cross_model_agreement.csv",
                     "experiment.json", "configuration.json", "environment-freeze.txt", "embedding_reuse.json"]:
        if (source / filename).exists(): shutil.copy2(source / filename, evidence / filename)
    selection_path = ROOT / "configs/four_configuration_selection.json"
    if selection_path.exists():
        selection = json.loads(selection_path.read_text(encoding="utf-8"))
        if selection["source_sha256"] == manifest["source_sha256"] and selection["experiment_output"] == config["output"]:
            shutil.copy2(selection_path, evidence / "selection.json")
    shutil.copytree(source / "alignments", evidence / "alignments", dirs_exist_ok=True)
    shutil.copytree(source / "code_snapshot", evidence / "code_snapshot", dirs_exist_ok=True)
    shutil.copy2(ROOT / config["preparation"] / "yearly_corpus.csv", evidence / "yearly_corpus.csv")
    parameters = pd.DataFrame(config["trials"])
    parameters.to_csv(evidence / "parameters.csv", index=False)
    source_frame = pd.read_csv(source / "input_units.csv", keep_default_na=False)
    dictionary = set()
    for text in source_frame.text:
        dictionary.update(re.findall(r"[a-zA-Z]{2,}", text.lower()))
    audits, catalog = [], []
    for row in summary.itertuples():
        directory = source / row.trial / f"seed_{primary}" / row.model
        target = evidence / row.trial / row.model
        target.mkdir(parents=True, exist_ok=True)
        for file in ["topic_keywords.csv", "yearly_prevalence.csv", "document_weighted_prevalence.csv", "metrics.json", "model_metadata.json", "expert_review_template.csv"]:
            shutil.copy2(directory / file, target / file)
        keywords = pd.read_csv(directory / "topic_keywords.csv", keep_default_na=False)
        topic_lists = keywords[keywords.topic.ne(-1)].sort_values("rank").groupby("topic").term.apply(list)
        scored = sum(len([w for w in words[:10] if w in dictionary]) >= 2 for words in topic_lists)
        audits.append({"model": row.model, "trial": row.trial, "topics": len(topic_lists), "cv_topics_scored": scored,
                       "actual_keyword_slots": sum(len(words[:10]) for words in topic_lists),
                       "cv_terms_absent_from_dictionary": sum(w not in dictionary for words in topic_lists for w in words[:10])})
        counts = pd.read_csv(directory / "section_topics.csv", usecols=["topic"]).topic.value_counts()
        for topic, words in topic_lists.items():
            catalog.append({"model": row.model, "trial": row.trial, "topic": topic, "units": int(counts[topic]),
                            "unit_share": float(counts[topic]/len(source_frame)), "keywords": "; ".join(words),
                            "expert_validation": "pending; no inferred ratings"})
    pd.DataFrame(audits).to_csv(evidence / "coherence_audit.csv", index=False)
    pd.DataFrame(catalog).to_csv(evidence / "topic_catalog.csv", index=False)
    # Baseline is historical reference, never a substituted new experiment result.
    baseline = ROOT / config["baseline_experiment"] / "tuning_results.csv"
    if baseline.exists():
        previous = pd.read_csv(baseline)
        fields = ["topics_excluding_outliers", "cv_coherence", "topic_diversity", "topic_coverage", "stability_ari_mean"]
        comparison = previous[["model", "trial"]+fields].merge(summary[["model", "trial"]+fields], on=["model", "trial"], suffixes=("_previous", "_rerun"))
        for field in fields:
            comparison[field+"_delta"] = comparison[field+"_rerun"]-comparison[field+"_previous"]
        comparison.to_csv(evidence / "previous_baseline_check.csv", index=False)
    # Descriptive dominance only, not automatic selection or significance testing.
    criteria = ["cv_coherence_mean", "topic_diversity_mean", "topic_coverage_mean",
                "seed_aligned_weighted_jaccard_mean", "cross_config_temporal_similarity_mean"]
    pareto = []
    for model in NAMES:
        candidates = summary[summary.model.eq(model)]
        for _, row in candidates.iterrows():
            dominators = []
            for _, other in candidates.iterrows():
                if row.trial == other.trial:
                    continue
                if all(other[k] >= row[k] for k in criteria) and any(other[k] > row[k] for k in criteria):
                    dominators.append(other.trial)
            pareto.append({"model": model, "trial": row.trial, "dominated_by": "; ".join(dominators),
                           "nondominated_on_listed_metrics": not dominators,
                           "criteria": "; ".join(criteria), "note": "Descriptive only; excludes expert interpretation and granularity; three seeds do not establish significance."})
    pd.DataFrame(pareto).to_csv(evidence / "descriptive_pareto.csv", index=False)
    runs.groupby(["model", "trial"]).agg(completed_fits=("seed", "size"),
        total_fit_evaluation_seconds=("fit_evaluation_seconds", "sum"),
        mean_fit_evaluation_seconds=("fit_evaluation_seconds", "mean"),
        total_process_cpu_seconds=("process_cpu_seconds", "sum"),
        max_sampled_process_rss_mib=("sampled_peak_rss_mib", "max")).reset_index().to_csv(evidence / "computational_cost.csv", index=False)
    generate_figures(source, figures, summary, runs, temporal, primary)
    import pymupdf
    with pymupdf.open() as combined:
        for path in sorted(figures.glob("*.pdf")):
            with pymupdf.open(path) as document:
                combined.insert_pdf(document)
        combined.save(output / "Tuning_Comparison_Figures.pdf")
    columns = ["model", "trial", "topics_excluding_outliers", "cv_coherence", "topic_diversity", "assigned_units", "outlier_sections", "topic_coverage", "outlier_fraction"]
    stability_columns = ["model", "trial", "stability_ari_mean", "seed_aligned_macro_jaccard_mean", "seed_aligned_weighted_jaccard_mean", "cross_config_temporal_similarity_mean", "fit_evaluation_seconds_mean", "sampled_peak_rss_mib_mean"]
    seed_table = summary[["model", "trial"]].copy()
    for field in ["topics_excluding_outliers", "cv_coherence", "topic_diversity", "topic_coverage", "fit_evaluation_seconds"]:
        seed_table[field+" (mean ± SD)"] = [f"{m:.4f} ± {s:.4f}" for m,s in zip(summary[field+"_mean"], summary[field+"_sd"])]
    report = f"""# Four-configuration tuning — completed measured results

Generated {datetime.now(timezone.utc).isoformat()}. **24/24 full fits completed:**
four configurations × two models × seeds 42, 43, 44. All 7,832 eligible units from
2,118 source documents, 2016–2025; no sample or fabricated results. Source hash:
`{manifest['source_sha256']}`.

## Configurations

{markdown(parameters)}

## Primary seed 42 results

{markdown(summary[columns])}

## Stability, temporal sensitivity and computational cost

{markdown(summary[stability_columns])}

Original `stability_ari_mean` compares seed 42 to 43/44 with noise as a cluster.
Aligned scores use all three pairs and penalize unmatched topics. Temporal
similarity is 1 minus mean annual base-2 JS divergence to the other configurations,
not agreement with ground truth. Runtime means are single-seed fit/evaluation,
excluding shared representation construction; memory is sampled whole-process RSS.

## Seed sensitivity (not confidence intervals)

{markdown(seed_table)}

## Pairwise temporal comparisons

{markdown(temporal[['model','left_trial','right_trial','temporal_similarity','temporal_tv_mean','matched_intersection_fraction','unmatched_left_topics','unmatched_right_topics']])}

## Figures

[All seven figures as a vector PDF](Tuning_Comparison_Figures.pdf).

![Topic counts](figures/01_topic_counts.png)
![Model A metrics](figures/02_metrics_lexical.png)
![Model B metrics](figures/02_metrics_semantic.png)
![Parameter associations](figures/03_parameters_performance.png)
![Model comparison](figures/04_model_comparison.png)
![Temporal consistency](figures/05_temporal_consistency.png)
![Major-topic trends](figures/06_major_topic_trends.png)

## Reproducibility and limitations

- Full model outputs, code snapshots, configuration, environment and artifact hashes:
  `{config['output']}/`.
- Compact evidence and source-linked review templates: `evidence/`.
- All figures: 300-dpi PNG plus vector PDF/SVG in `figures/`.
- Shared lexical representation wall time: {manifest['lexical_representation_resources']['fit_evaluation_seconds']:.3f} seconds.
- Semantic cache/load or encoding wall time: {manifest['semantic_representation_resources']['fit_evaluation_seconds']:.3f} seconds;
  encoder cache used: **{manifest['semantic_encoder_metadata']['cache_used']}**.
- Original cached encoder session time: {manifest['semantic_encoder_metadata']['session_seconds']:.3f} seconds;
  this is historical provenance, **not fresh GPU encoding in these reruns**.
- Current complete session wall time: {manifest['session_wall_seconds']:.3f} seconds.
- The first lexical fit includes one-time import/Numba JIT overhead; fixed-order
  warmed timings are not an isolated algorithm-speed benchmark.
- SVD and Legal-BERT representations are fixed across seeds; seed stability concerns
  downstream clustering. Joint parameter changes do not isolate causal effects.
- C_v/diversity are intrinsic keyword diagnostics. Coverage and noise are complements.
  Different topic counts, noise and dominant clusters affect comparisons.
- The 597 fallback documents, 45 additional same-number text variants and 28 date
  flags remain part of the original audited methodology, not newly validated issues.
- Legal-expert ratings remain blank. Keyword examples and provisional recommendations
  must not be described as expert validation, predictive accuracy or causation.

See `docs/FOUR_CONFIGURATION_METHODS.md` for formulas and exact reproduction commands.
Research interpretation, provisional selection and a thesis-ready results section
are available in [the completed findings](../../docs/FOUR_CONFIGURATION_FINDINGS.md).
That section is written only after checking the completed experiments. The original
reference thesis PDF is not overwritten.
"""
    (output / "RESULTS.md").write_text(report, encoding="utf-8")
    provenance = {"status": "completed", "created_utc": datetime.now(timezone.utc).isoformat(),
                  "experiment_sha256": digest(source / "experiment.json"), "report_code_sha256": digest(__file__),
                  "files_sha256": {p.relative_to(output).as_posix(): digest(p) for p in sorted(output.rglob("*")) if p.is_file() and p.name != "report_manifest.json"}}
    (output / "report_manifest.json").write_text(json.dumps(provenance, indent=2), encoding="utf-8")
    print(f"Published measured report and figures: {output}")


if __name__ == "__main__":
    main()
