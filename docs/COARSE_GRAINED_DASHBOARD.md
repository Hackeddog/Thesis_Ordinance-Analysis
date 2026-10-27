# Active coarse-grained analysis and static dashboard

## Decision and scope

The research team requested a **fresh coarse-grained retraining** and chose
coarse-grained outputs for the active thesis dashboard. This replaces Conservative
as the active interface configuration, not as an erased historical experiment.
No new expert approval or universal superiority claim follows from that choice.

- Branch: `research/coarse-grained-dashboard`.
- Active configuration: `configs/coarse_grained_retrain.json`.
- Fresh full run (local, Git-ignored): `results/experiments/coarse_grained_retrain_fresh/`.
- Compact fresh evidence: `artifacts/coarse_grained_retrain/`.
- New temporal package: `artifacts/temporal_topics_coarse_grained/`.
- Plain HTML/CSS/JavaScript website: `dashboard/`.

`artifacts/temporal_topics/`, the four-configuration comparison, the original
selection record, and the Initial archive remain unchanged. Their historical
Conservative selection is not the current dashboard selection.
The previous expert-validation package refers to Conservative topics; review
packets must be rebuilt and the declared run updated before applying that
instrument to fresh coarse-grained topics. No completed expert responses exist.

## Exact protocol

| Parameter | Value |
|---|---|
| Models | A: lexical TF-IDF/SVD; B: frozen Legal-BERT |
| Corpus | Unchanged audited cleaned TXT input |
| Window | 2016–2025, using resolved years |
| Primary / sensitivity seeds | 42 / 43, 44 |
| UMAP neighbors / dimensions / min_dist | 30 / 5 / 0.1 |
| HDBSCAN min_cluster_size / min_samples | 60 / 15 |
| HDBSCAN metric / selection | Euclidean / EOM |
| Legal-BERT | `nlpaueb/legal-bert-base-uncased`, pinned checkpoint |
| Prior embedding-cache reuse | Disabled |
| Encoder fine-tuning | None |
| Fits | Six new fits: two models × three seeds |

Fresh retraining means reconstructing the lexical representation, recomputing
every Legal-BERT chunk embedding, and rerunning UMAP/HDBSCAN, keyword extraction,
metrics, temporal tables, and seed-alignment checks. Legal-BERT remains a frozen
representation as specified by the thesis method. A fresh run can legitimately
reproduce earlier measurements; unchanged output does not mean retraining was skipped.

The run checks source text, human overrides, preparation code and ordered-input
hashes. It saves environment versions, exact code snapshots, per-fit hashes and
measured timing. Code-snapshot hashes identify the executed source even if the
worktree contained uncommitted additions when execution began.

**Preserve `max_df: 1.0` as a floating-point fraction.** In scikit-learn,
integer `1` means at most one document, not 100% of documents. The new config
validator rejects that silent type change. An initial attempt hit the existing
empty-vocabulary safeguard before encoder inference or clustering; its failed
local directory is preserved separately. The corrected run uses the fresh output
directory above and its own complete provenance.

## Reproduce without overwriting

The checked-in configuration points to the completed run location. For another
experiment, copy it and change `output` to a fresh directory. Keep corpus,
preprocessing, parameter values and seeds unchanged for a replication.

```powershell
mise install
# Existing environment: .venv, with requirements-models.txt installed.
.\.venv\Scripts\python.exe scripts/run_four_configurations.py --config configs/coarse_grained_retrain.json
```

The runner supports `--resume` only with matching configuration, input, code and
Python packages. It never silently overwrites completed experiments. The publication
contract used here requires fresh uninterrupted encoder inference; a resumed
encoder checkpoint is valid research data but must be disclosed under a separately
adjusted publication policy, not mislabeled as uninterrupted fresh inference.

After all six fits succeed:

```powershell
.\.venv\Scripts\python.exe scripts/publish_coarse_grained.py --titles configs/temporal_topic_titles_coarse_grained.json
```

For a new publication, provide `--config`, `--report`, `--temporal`, and
`--dashboard` paths pointing to fresh destinations. Supply a newly reviewed, fingerprint-bound
`--titles` config for that run, or omit it to use only generic keyword rules with
no topic-ID overrides. The publisher checks completed
statuses, all model-artifact hashes, input identity, encoder provenance, parameters,
and original source integrity before exporting. It rejects existing output directories.

## What gets published

- Eight temporal PNGs: heatmap, leading trajectories, interpretable subset,
  and yearly composition for each model.
- Eight-page PDF and graph-only PowerPoint.
- Complete model-local topic catalogs and annual data, not only plotted topics.
- Run-scoped keyword titles with fingerprint checks. Broad or mixed clusters
  receive explicit descriptions rather than imported Conservative labels.
- Compact metric/seed evidence, source/config/code fingerprints, and environment.
- A small public JSON dataset and static downloads—no raw source excerpts,
  private reviewer records, encoder cache, or large assignment matrices.

The temporal manifest has `models_rerun: false` because the **rendering step**
does not train models. The separate retraining report records six fresh fits and
fresh encoder inference. These describe distinct steps, not contradictory claims.

## Interpretation

Annual shares give each source document total weight one across its assigned
topics and outliers. Every observed year sums to 100%. Ranking uses total
fractional-document weights, not an unweighted sum of yearly percentages.
The archive is uneven (only 32 source documents in 2025).

Metric coverage is the fraction of assigned **model units**. It is not the same
denominator as temporal document-weighted prevalence. Topic IDs are local to a
model/run; matching numbers or draft names do not establish topic alignment.

No legal accuracy, predictive performance, causal change, significance, or expert
rating is inferred. The active choice is a broad-theme research decision.

## Validate and preview

```powershell
.\.venv\Scripts\python.exe -m pytest tests -q
bun install --frozen-lockfile
bun run test
bunx playwright install chromium
bun run test:browser
bun run dev
```

See [dashboard/README.md](../dashboard/README.md) for VS Code F5 setup and online
hosting. GitHub Pages requires repository-owner setup; the contributor account's
push permission does not grant the authority to enable Pages.
