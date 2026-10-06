"""Generate a clean-TXT-only presentation and compact evidence from a completed run."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import textwrap

import numpy as np
import pandas as pd
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.util import Inches
from presentation_style import plt, pretty, save_table, add_text, picture, NAVY, TEAL, ORANGE, INK, GRAY

ROOT = Path(__file__).resolve().parents[1]
COLORS = {"lexical": "#" + TEAL, "semantic": "#" + ORANGE}
NAMES = {"lexical": "Model A · Lexical", "semantic": "Model B · Legal-BERT"}


def build(run, output):
    run, output = Path(run), Path(output)
    experiment = json.loads((run / "experiment.json").read_text())
    if experiment["status"] != "completed":
        raise ValueError("Only completed measured runs can be presented")
    if output.exists():
        raise ValueError("Output exists; choose a new path to preserve previous evidence")
    config = experiment["config"]
    preparation = ROOT / config["preparation"]
    prep = json.loads((preparation / "preparation.json").read_text())
    doc_audit = pd.read_csv(preparation / "document_audit.csv", keep_default_na=False)
    out_of_scope = int(doc_audit.reason.eq("outside 2016-2025 after human date correction").sum())
    unusable = int(doc_audit.reason.eq("no usable text after deterministic extraction").sum())
    if hashlib.sha256((ROOT / config["source"]).read_bytes()).hexdigest() != experiment["source_sha256"]:
        raise ValueError("Preparation source changed since execution")
    evidence, figures = output / "evidence", output / "figures"
    evidence.mkdir(parents=True)
    figures.mkdir()
    for filename in ["experiment.json", "tuning_results.csv", "vocabulary_exclusions.csv"]:
        shutil.copy2(run / filename, evidence / filename)
    for filename in ["preparation.json", "file_audit.csv", "document_audit.csv", "yearly_corpus.csv"]:
        shutil.copy2(preparation / filename, evidence / filename)
    shutil.copy2(run / "embedding_cache/metadata.json", evidence / "encoder_metadata.json")
    metadata = json.loads((run / "embedding_cache/metadata.json").read_text())
    tuning = pd.read_csv(run / "tuning_results.csv")
    initial = run / config["trials"][0]["name"]
    units = pd.read_csv(run / "input_units.csv", keep_default_na=False)
    yearly = units.groupby("year").agg(units=("text", "size"), documents=("ordinance_id", "nunique"))
    yearly.to_csv(evidence / "modeled_yearly_counts.csv")
    models = ["lexical", "semantic"]
    assignments, keywords = {}, {}
    for name in models:
        dest = evidence / name
        dest.mkdir()
        for filename in ["metrics.json", "topic_keywords.csv", "yearly_prevalence.csv", "document_weighted_prevalence.csv", "expert_review_template.csv"]:
            shutil.copy2(initial / name / filename, dest / filename)
        assignments[name] = pd.read_csv(initial / name / "section_topics.csv", keep_default_na=False)
        keywords[name] = pd.read_csv(initial / name / "topic_keywords.csv")
    (evidence / "render_provenance.json").write_text(json.dumps({
        "generator_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "style_sha256": hashlib.sha256((ROOT / "scripts/presentation_style.py").read_bytes()).hexdigest(),
        "input_source": "data/processed/clean_text TXT files, with explicit human year-override CSV metadata",
        "no_sampling": True, "source_verification": prep["verification_basis"],
        "note": "Figures are rendered measured artifacts, not screenshots of a training UI. Review scores remain blank."
    }, indent=2), encoding="utf-8")
    def topic_label(name, topic):
        if topic == -1:
            return "Outliers (-1)"
        top = keywords[name].query("topic == @topic").sort_values("rank").term.head(3)
        return f"T{topic}: " + ", ".join(top)

    # A completely new architecture image, sourced only from the executed text workflow.
    fig, axes = plt.subplots(3, 1, figsize=(14, 6))
    stages = [
        ["Clean TXT files", "Content-hash\ndeduplication", "Human year\noverrides / folders", "Sections + fallback\nboilerplate policy", "Shared model units"],
        ["Shared units", "TF-IDF", "SVD + L2 norm", "UMAP → HDBSCAN", "c-TF-IDF keywords"],
        ["Shared units", "Frozen Legal-BERT", "All-chunk pooling", "UMAP → HDBSCAN", "c-TF-IDF keywords"]]
    for ax, labels, title, color in zip(axes, stages, ["Shared preparation", NAMES["lexical"], NAMES["semantic"]], ["#" + NAVY, COLORS["lexical"], COLORS["semantic"]]):
        ax.axis("off")
        ax.text(0, .95, title, fontsize=14, weight="bold", color=color)
        for i, label in enumerate(labels):
            x = .025 + i * .198
            ax.text(x+.075, .42, label, ha="center", va="center", fontsize=11,
                    bbox=dict(boxstyle="round,pad=.6", facecolor="#F1F6F8", edgecolor=color))
            if i < 4:
                ax.annotate("", xy=(x+.19, .42), xytext=(x+.163, .42), arrowprops=dict(arrowstyle="->", color=color))
    fig.tight_layout()
    fig.savefig(figures / "clean_text_pipelines.png", dpi=170, bbox_inches="tight")
    plt.close(fig)

    params = pd.DataFrame(config["trials"])[["name", "neighbors", "min_dist", "min_cluster_size", "min_samples"]]
    params.columns = ["Trial", "UMAP neighbors", "Min distance", "Cluster min size", "Min samples"]
    save_table(params, figures / "executed_parameters.png", "Executed parameter configurations",
               f"Shared: seed 42 | UMAP 5 dimensions | top 10 unigram words | 3 seed runs | no encoder fine-tuning")
    comparison = tuning[["trial", "model", "topics_excluding_outliers", "cv_coherence", "topic_diversity", "topic_coverage", "stability_ari_mean"]].copy()
    for col in comparison.columns[3:]:
        comparison[col] = comparison[col].map(pretty)
    comparison.columns = ["Trial", "Model", "Topics", "C_v", "Diversity", "Coverage", "Seed ARI"]
    save_table(comparison, figures / "tuning_results.png", "Measured parameter sensitivity · full eligible corpus",
               "Joint configuration changes, not isolated ablations. No held-out winner is selected.")
    scores = tuning[tuning.trial.eq(config["trials"][0]["name"])].set_index("model")
    metric_keys = ["cv_coherence", "topic_diversity", "topic_coverage", "outlier_fraction", "stability_ari_mean", "topics_excluding_outliers"]
    table = pd.DataFrame({"Metric": ["C_v coherence", "Top-10 diversity", "Assigned unit share", "Outlier share", "Seed stability (ARI)", "Topics (excluding outliers)"],
        **{NAMES[n]: [pretty(scores.loc[n, k]) if k != metric_keys[-1] else str(int(scores.loc[n, k])) for k in metric_keys] for n in models}})
    save_table(table, figures / "initial_metrics.png", "Initial full-corpus configuration",
               f"Identical {len(units):,} text units for both paths; quality scores are intrinsic and in-sample.")
    count_table = yearly.reset_index().astype(int)
    count_table.columns = ["Study year", "Modeled text units", "Source documents"]
    save_table(count_table, figures / "corpus_by_year.png", "Actual corpus coverage · no year-balanced sampling")

    vectors = np.load(run / "embedding_cache/vectors.npy", allow_pickle=False)
    row = assignments["semantic"].iloc[0]
    trace = {"source_file": row.source_file, "ordinance_number": row.ordinance_number,
             "unit": row.section_id, "unit_type": row.unit_type, "year": int(row.year), "topic": int(row.topic),
             "text_excerpt": row.text[:450], "embedding_shape": list(vectors.shape),
             "first_8_values": vectors[0, :8].tolist(), "l2_norm": float(np.linalg.norm(vectors[0])),
             "model_revision": metadata["resolved_model_revision"]}
    (evidence / "bert_output_snippet.json").write_text(json.dumps(trace, indent=2), encoding="utf-8")
    fig, ax = plt.subplots(figsize=(14, 5))
    fig.set_facecolor("#" + NAVY)
    ax.axis("off")
    text = (f"ENCODER  {metadata['encoder']}\nDEVICE   {metadata['device']} | {metadata['torch_version']}\n"
            f"SOURCE   {row.source_file} / {row.section_id}\n"
            f"OUTPUT   {vectors.shape[0]:,} units x {vectors.shape[1]} dimensions | {metadata['total_chunks']:,} chunks\n"
            f"VECTOR   {np.array2string(vectors[0, :8], precision=5)} ...\n"
            f"NORM     {np.linalg.norm(vectors[0]):.6f} | TOPIC {row.topic}\n\n" + textwrap.fill(row.text[:290], 100))
    ax.text(.015, .96, text, va="top", color="#EDF4FA", fontfamily="DejaVu Sans Mono", fontsize=12, linespacing=1.7)
    fig.savefig(figures / "bert_output_snippet.png", dpi=170, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(13, 4.8))
    for name in models:
        coverage = assignments[name].assign(assigned=lambda x: x.topic.ne(-1)).groupby("year").assigned.mean()
        ax.plot(coverage.index, coverage * 100, "o-", color=COLORS[name], label=NAMES[name])
    ax.set(ylim=(0, 105), ylabel="Assigned / all modeled units in year (%)", xlabel="Resolved study year")
    ax.set_xticks(config["years"])
    ax.grid(axis="y", alpha=.2)
    ax.legend()
    fig.tight_layout()
    fig.savefig(figures / "yearly_coverage.png", dpi=170)
    plt.close(fig)
    for name in models:
        frame = assignments[name]
        top = frame.loc[frame.topic.ne(-1), "topic"].value_counts().head(8).index.tolist() or [-1]
        prevalence = pd.read_csv(initial / name / "document_weighted_prevalence.csv")
        matrix = prevalence.pivot(index="topic", columns="year", values="share").reindex(index=top, columns=config["years"]).fillna(0)
        fig, ax = plt.subplots(figsize=(14, 5.5))
        image = ax.imshow(matrix.to_numpy()*100, cmap="Blues" if name == "lexical" else "Oranges", aspect="auto", vmin=0, vmax=100)
        ax.set_yticks(range(len(top)), [topic_label(name, t) for t in top], fontsize=10)
        ax.set_xticks(range(10), config["years"])
        for i in range(len(top)):
            for j in range(10):
                ax.text(j, i, f"{matrix.iloc[i,j]*100:.1f}", ha="center", va="center", fontsize=9,
                        color="white" if matrix.iloc[i,j] > .5 else "#"+INK)
        fig.colorbar(image, ax=ax, label="Document-weighted topic share (%)")
        fig.tight_layout()
        fig.savefig(figures / f"{name}_yearly_heatmap.png", dpi=170)
        plt.close(fig)
    for year in config["years"]:
        fig, axes = plt.subplots(1, 2, figsize=(14, 5.3))
        for ax, name in zip(axes, models):
            frame = assignments[name].query("year == @year")
            counts = frame.topic.value_counts()
            top = counts[counts.index != -1].head(3)
            labels, values = [topic_label(name, t) for t in top.index], top.tolist()
            labels += ["Other assigned topics", "Outliers (-1)"]
            values += [int(counts[counts.index != -1].sum()-top.sum()), int(counts.get(-1, 0))]
            ax.barh(range(len(values)), np.array(values)/len(frame)*100, color=COLORS[name], alpha=.85)
            ax.set_yticks(range(len(values)), [textwrap.fill(label, 27) for label in labels], fontsize=10)
            ax.invert_yaxis()
            ax.set(xlim=(0, 108), xlabel="Share of modeled units (%)")
            ax.set_title(f"{NAMES[name]}\n{len(frame):,} units / {frame.ordinance_id.nunique()} source documents", fontsize=13, weight="bold")
            for i, v in enumerate(values):
                ax.text(v/len(frame)*100+1, i, f"{v}/{len(frame)}", va="center", fontsize=9)
        fig.suptitle(f"{year} · full eligible clean-text corpus", x=.02, ha="left", fontsize=19, weight="bold")
        fig.tight_layout(rect=[0, 0, 1, .91], w_pad=3)
        fig.savefig(figures / f"year_{year}_comparison.png", dpi=170)
        plt.close(fig)

    prs = Presentation()
    prs.core_properties.title = "Clean-text full-corpus initial results"
    prs.core_properties.author = "Corpuz; Lamsin; Nuril"
    prs.core_properties.subject = "Davao ordinance topic modeling: lexical vs Legal-BERT"
    prs.slide_width, prs.slide_height = Inches(13.333), Inches(7.5)
    def slide(title, section="INITIAL RESULTS"):
        s = prs.slides.add_slide(prs.slide_layouts[6])
        add_text(s, section, .65, .24, 12, .35, 11, TEAL, True)
        add_text(s, title, .65, .75, 12.1, .75, 30, INK, True)
        bar = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(.7), Inches(1.48), Inches(.75), Inches(.045))
        bar.fill.solid(); bar.fill.fore_color.rgb = RGBColor.from_string(TEAL); bar.line.fill.background()
        add_text(s, "CORPUZ · LAMSIN · NURIL   /   CLEAN-TEXT FULL-CORPUS RUN · INITIAL INTRINSIC RESULTS", .65, 7.03, 11.8, .23, 9, GRAY)
        add_text(s, f"{len(prs.slides):02}", 12.15, 7, .55, .3, 10, GRAY)
        return s
    def image_slide(title, filename, note="", section="INITIAL RESULTS"):
        s = slide(title, section)
        picture(s, figures / filename, h=4.6 if note else 5)
        if note:
            add_text(s, note, .8, 6.4, 11.7, .5, 14, GRAY)
        return s
    def body_slide(title, text, section="METHOD"):
        s = slide(title, section)
        add_text(s, text, .8, 1.85, 11.7, 4.95, 19)
        return s

    s = prs.slides.add_slide(prs.slide_layouts[6])
    s.background.fill.solid(); s.background.fill.fore_color.rgb = RGBColor.from_string(NAVY)
    add_text(s, "DAVAO CITY MUNICIPAL ORDINANCES", .85, .8, 11.5, .5, 15, "63D5D0", True)
    add_text(s, "Clean text. Full corpus.\nTwo comparable model paths.", .85, 1.8, 11.6, 2, 39, "FFFFFF", True)
    add_text(s, "Lexical TF-IDF + c-TF-IDF  vs  Legal-BERT + BERTopic", .85, 4.1, 11.5, .65, 21, "DBE8F2")
    add_text(s, f"{experiment['documents']:,} source documents · {experiment['units']:,} modeled units\n2016–2025 · Corpuz · Lamsin · Nuril", .85, 5.2, 11.5, 1, 19, "DBE8F2")
    add_text(s, "USER-VERIFIED TXT SOURCE / AUDITED PREPARATION / EXPERT MODEL VALIDATION PENDING", .85, 6.9, 11.5, .3, 11, "F9BF88", True)

    body_slide("What changed in this rerun", "Only data/processed/clean_text/*.txt supplies model text.\nThe full eligible corpus replaces the previous 200-unit sample.\nContent hashes remove duplicate copies without deleting sources.\nHuman year overrides take priority; every decision is auditable.\nSpecified boilerplate sections and signature blocks are excluded.\nGPU batching and checkpointed embeddings support reproducible full runs.\nBoth models use identical units, years, vocabulary and evaluation inputs.", "IMPROVEMENTS")
    body_slide("Exactly which data reached the models?", f"Input: {prep['source_files']:,} TXT files → {prep['content_groups']:,} distinct contents.\n{prep['duplicate_copies']} duplicate copies removed from modeling, not from disk.\n{out_of_scope} content groups excluded by existing human out-of-scope year corrections.\n{unusable} content groups had no usable text after deterministic extraction.\n\nModeled: {experiment['documents']:,} source documents / {experiment['unique_ordinance_numbers']:,} distinct normalized ordinance numbers.\n{experiment['units']:,} units; all eligible years included with their natural corpus sizes.\nVerification is based on the researcher's confirmation of the cleaned source—not a new independent PDF audit.", "DATA ACCOUNTING")
    image_slide("Year-by-year corpus coverage", "corpus_by_year.png", section="DATA ACCOUNTING")
    body_slide("Source verification and extraction are different", f"{prep['unit_types']['legal_section']:,} automatically detected numbered sections.\n{prep['unit_types']['document_fallback']:,} whole-document fallback units for missing or repeated section headings.\n{prep['boilerplate_units_omitted']} effectivity/separability/repealing-clause units removed.\nExplicit signature blocks are trimmed; source TXT files remain unchanged.\n\n{prep['distinct_versions_same_number']} additional text versions share ordinance numbers and are flagged, not silently merged.\n{prep['remaining_date_disagreements']} extracted enactment-year candidates disagree with assigned study years. Human overrides / user-verified folders remain authoritative.\nThese flags and mixed unit lengths remain interpretation limitations.", "EXTRACTION AUDIT")
    image_slide("A clean-text-only architecture", "clean_text_pipelines.png", "c-TF-IDF requires classes: lexical TF-IDF/SVD supplies initial assignments; both paths apply c-TF-IDF after clustering.", "MODEL PIPELINES")
    body_slide("Legal-BERT: what actually ran", f"Encoder: nlpaueb/legal-bert-base-uncased; pinned revision.\n{metadata['total_chunks']:,} non-overlapping chunks, maximum 512 tokens including specials.\nContent-token weighted pooling excludes padding and special tokens; every chunk is included.\nL2-normalized {vectors.shape[1]}-dimensional vectors retain source file / unit / year associations.\nDevice: {metadata['device']} · GPU inference uses unchanged pretrained weights.\n\nNo classifier training, learning rate or fine-tuning epochs are claimed. Encoder suitability still requires empirical and legal-expert assessment.", "SEMANTIC PIPELINE")
    image_slide("Actual tuning parameters", "executed_parameters.png", "Rendered configuration evidence—not a training-interface screenshot. Three stability runs means one primary fit plus two extra seeds.", "PARAMETER EVIDENCE")
    image_slide("Initial full-corpus metrics", "initial_metrics.png", "These are in-sample intrinsic scores, not accuracy/F1 or proof of legal validity.")
    a, b = scores.loc['lexical'], scores.loc['semantic']
    body_slide("Read the comparison as trade-offs", f"Coherence C_v: lexical {a.cv_coherence:.3f} vs Legal-BERT {b.cv_coherence:.3f}.\nKeyword diversity: lexical {a.topic_diversity:.3f} vs Legal-BERT {b.topic_diversity:.3f}.\nCoverage: lexical {a.topic_coverage:.1%} vs Legal-BERT {b.topic_coverage:.1%}.\nSeed stability ARI: lexical {a.stability_ari_mean:.3f} vs Legal-BERT {b.stability_ari_mean:.3f}.\n\nThe stronger model can differ by criterion. More coverage or fewer topics alone does not establish better policy themes.\nDo not attribute differences from the old sample solely to the text-input change: corpus size, extraction and parameter settings also changed.", "COMPARATIVE READING")
    image_slide("Sensitivity to a second configuration", "tuning_results.png", "Both configurations are evaluated on the same units. This is not held-out tuning or a final model selection.")
    image_slide("A real BERT output snippet", "bert_output_snippet.png", section="EXECUTION EVIDENCE")

    s = slide("Representative outputs retain TXT provenance", "INTERPRETATION")
    excerpts = []
    for i, name in enumerate(models):
        frame = assignments[name]
        assigned = frame[frame.topic.ne(-1)]
        if assigned.empty:
            add_text(s, f"{NAMES[name]}\nAll units are outliers.", .8+i*6.2, 1.85, 5.55, 4.8, 18)
            continue
        topic = assigned.topic.value_counts().index[0]
        row = assigned[assigned.topic.eq(topic)].iloc[0]
        text = f"{NAMES[name]}\n{topic_label(name, topic)}\n\n{row.source_file}\n{row.section_id} / study year {row.year}\n\n{row.text[:300]}"
        add_text(s, text, .8+i*6.2, 1.85, 5.55, 4.9, 16)
        excerpts.append({"model": name, "topic": int(topic), "source_file": row.source_file,
                         "unit": row.section_id, "year": int(row.year), "text_excerpt": row.text[:300]})
    (evidence / "representative_excerpts.json").write_text(json.dumps(excerpts, indent=2), encoding="utf-8")
    add_text(s, "Machine-generated keyword sets are not expert-approved policy labels.", .8, 6.45, 11.7, .45, 14, GRAY)
    image_slide("Yearly assignment coverage", "yearly_coverage.png", "Each year's denominator includes all modeled units, including outliers; corpus sizes differ across years.", "TEMPORAL COMPARISON")
    for name in models:
        image_slide(f"{NAMES[name]} · document-weighted trends", f"{name}_yearly_heatmap.png", "Each source document contributes total weight 1, distributed across its unit topics. Top eight topics only; columns need not sum to 100%.", "TEMPORAL COMPARISON")
    body_slide("Evaluation contract and remaining limitations", "C_v: shared unigram keywords and the same model-input texts.\nDiversity: unique top keywords / actual keyword slots, excluding outliers.\nCoverage: assigned units / all units. Seed ARI includes outliers as one cluster.\nYearly unit shares and document-weighted shares answer different questions.\n\nNo artificial BERTopic perplexity, supervised accuracy or fabricated expert scores.\nRemaining work: inspect extraction/date/version flags, review topic labels with experts, and predefine ordinance-grouped holdouts before final tuning.\nSource verification does not itself validate clusters or temporal policy interpretations.", "RESEARCH STATUS")
    for year in config['years']:
        image_slide(f"{year} · both models, full eligible texts", f"year_{year}_comparison.png", "Topic numbers are model-local: A/T0 does not mean B/T0. Bars include top three topics, other assigned topics and outliers.", "YEAR-BY-YEAR RESULTS")
    prs.save(output / "Clean_Text_Full_Corpus_Initial_Results.pptx")
    summary = "# Clean-text full-corpus initial results\n\n" + config['interpretation'] + "\n\n```csv\n" + tuning.to_csv(index=False, lineterminator='\n') + "```\n\nNo source TXT files were modified. See evidence/ for hashes, per-file audit and source-linked excerpts.\n"
    (output / "RESULTS.md").write_text(summary, encoding="utf-8", newline="\n")
    print(f"Created {len(prs.slides)} slides and {len(list(figures.glob('*.png')))} figures in {output}")


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--experiment', type=Path, default=ROOT / 'results/experiments/clean_text_full')
    p.add_argument('--output', type=Path, default=ROOT / 'artifacts/clean_text_full')
    args = p.parse_args()
    build(args.experiment, args.output)
