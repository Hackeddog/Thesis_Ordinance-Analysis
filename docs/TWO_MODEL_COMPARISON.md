# Two-model comparison and initial-results presentation

## Start here

- Branch: `research/two-model-comparison`, based on `model_pipline_lamsin` (`36ae5bc`).
- Local worktree: `Desktop/Thesis/Thesis_Model_Comparison`. The original `Test-(Corpuz)` checkout is unchanged.
- Open `Thesis_Model_Comparison.code-workspace` in VS Code.
- Presentation: `artifacts/pilot/Ordinance_Two_Model_Initial_Results.pptx` (28 slides), with a matching `.pdf` exported through PowerPoint.
- PNG evidence: `artifacts/pilot/figures/`, including one paired comparison for each year, 2016–2025.
- Compact machine-readable evidence: `artifacts/pilot/evidence/`.

## Reference reconciliation

The earlier `Thesis_Corpuz, Lamsin, Nuril.pdf` describes LDA. The newer `Milestone-1_Corpus-Lamsin-Nuril.pdf` (methodology pp. 35–38) specifies section-level Legal-BERT, UMAP, HDBSCAN, c-TF-IDF, topics-over-time and expert assessment. The supplied `diagram.png` explicitly adds a lexical Model A comparison. This implementation follows the newer milestone and diagram, rather than presenting LDA as a completed second model.

The original PDFs are copied only into ignored `references/local/` and are not published. The supplied diagram is `docs/reference_diagram.png` and is used in the deck appendix.

**Methodological correction:** c-TF-IDF needs classes/topics before it can aggregate term counts. Model A therefore obtains initial assignments from TF-IDF → SVD → UMAP → HDBSCAN, then uses c-TF-IDF for keywords. Model B uses frozen Legal-BERT embeddings → UMAP → HDBSCAN → c-TF-IDF. This interpretation is documented rather than claiming class-based weighting can precede unknown classes.

## Corpus and evidence status

The source branch has 7,627 prepared sections from 1,501 ordinances spanning 2016–2025. Only 13 sections are marked verified; 7,614 are unverified. `temporal_status=valid` is not a substitute for human verification.

`configs/pilot.json` explicitly permits unverified input **only for an exploratory pilot**. It samples 20 sections per year, sorted by identifiers then seeded with 42. Both models receive the same 200 rows. There is no text-length exclusion or silent truncation; Legal-BERT pools all non-overlapping chunks. Repeated legal text remains present and is counted in the manifest.

This balanced sample must not be interpreted as the archive's natural yearly volume, full-corpus topic prevalence, or a final validation. Sections are not independent ordinances. The sample includes raw OCR errors and boilerplate.

The source branch also includes historical lexical-only metrics on 7,627 sections in `results/model_run_clean2/lexical/metrics.json`. Those figures were **not reproduced** here and must not be compared directly with this 200-section pilot or silently reused as newly measured BERT results.

## Initial measured snapshot

Both models use the same 200 sections from 184 ordinances; all 200 are marked unverified.

| Metric | Lexical | Legal-BERT |
|---|---:|---:|
| C_v coherence | 0.7075 | 0.6394 |
| Topic diversity | 0.8389 | 0.8214 |
| Assigned section share | 0.9550 | 0.9650 |
| Seed stability (ARI) | 0.8039 | 0.7484 |
| Topics excluding outliers | 18 | 14 |

These numbers describe the **initial** configuration, not the historical full-corpus lexical run. Full-precision values and the conservative trial are in `artifacts/pilot/evidence/tuning_results.csv`. The extra 1 percentage point of BERT coverage does not establish better legal topics; lexical coherence and stability are higher in this particular pilot. No winner is selected.

The first semantic attempt exposed a pre-existing fast-tokenizer `prepare_for_model` special-mask error. The pipeline now uses the compatible slow tokenizer API and has an offline regression test. The failed attempt is retained locally under ignored `results/experiments/pilot-failed-tokenizer`; only the subsequent completed run is presented.

## Setup (PowerShell, Windows)

Runtime versions are managed by mise; `.mise.toml` pins Python. The modeling environment is separate from your existing project environment.

```powershell
mise install
mise exec -- python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-models.txt
.\.venv\Scripts\python.exe -m pytest tests/test_models.py -q
.\.venv\Scripts\python.exe scripts/run_comparison.py --config configs/pilot.json
.\.venv\Scripts\python.exe scripts/build_presentation.py --experiment results/experiments/pilot --output artifacts/pilot
```

For Linux use `.venv/bin/python`. The first semantic run downloads the public Legal-BERT checkpoint into the normal Hugging Face cache. It requires network access and several hundred MB of disk. The supplied pilot uses CPU, even if a GPU exists; CUDA requires an appropriate PyTorch build. No secret/API key is required for the public model.

Outputs are immutable: choose a new `output` path in a copied config for a new experiment, and a new presentation output directory to regenerate the deck. Do not overwrite evidence from an earlier run. VS Code tasks are supplied for running, testing and rendering.

## What is recorded

- Source CSV, ordered sample and modeling/runner code SHA-256 hashes; base Git commit.
- Exact command lines, model revision, package versions, config and seed.
- Shared vocabulary, embeddings, vector-row → section/year metadata, topic assignments and keywords.
- Per-model coherence, diversity, coverage, outliers and seed stability.
- Parameter sensitivity table and yearly shares including outliers in the denominator.
- A real BERT vector excerpt and source-linked text snippets.
- Cross-model ARI (partition agreement, **not** accuracy or quality).

BERT is a frozen encoder, not a fine-tuned classifier. Learning rate, epochs and supervised accuracy/F1 therefore do not apply to this run. CPU time is recorded; later trials reuse hash-validated BERT vectors, so their timing is not an end-to-end runtime comparison.

## Metrics and tuning interpretation

- **C_v:** Gensim sliding-window coherence, top 10 words, shared texts. Pilot uses unigrams, so phrase terms are not silently discarded. General bigram runs disclose `cv_excluded_phrase_terms`; their c_v uses retained unigram terms only.
- **Topic diversity:** distinct top keywords divided by all actual top-keyword slots; excludes `-1`.
- **Coverage:** non-outlier sections / retained sections. Outlier rate is reported separately.
- **Seed stability:** mean adjusted Rand index between the initial partition and two additional UMAP seeds. It includes the outlier label as one cluster and can be inflated by dominant boilerplate/outlier groups. It is not bootstrap corpus stability.
- **Section NPMI:** supplementary whole-section co-occurrence diagnostic, not equivalent to sliding-window c_v.
- **Temporal share:** topic sections / all sampled sections in that year. Zero cells are explicit. Topic IDs are model-local; equal numbers do not align topics across models.
- **Perplexity:** not invented for BERTopic, which has no directly comparable generative document likelihood.
- **Expert validation:** pending, never fabricated. The review template is blank.

`initial` and `conservative` are two predeclared joint parameter configurations. They demonstrate sensitivity, not an exhaustive search, isolated ablation or a held-out winner. Neither configuration is selected solely because one metric is larger. No claim of superiority is justified by this pilot.

The evidence keeps the original source byte hash, plus `portable_source.json` with a CRLF-to-LF-normalized hash for Git checkouts on different operating systems. Normalized ordered text is separately checked against the semantic embedding fingerprint.

The PNG parameter/table images are genuine renderings of saved configs and measured outputs, **not screenshots of a training UI**. Source files for every figure remain in the evidence bundle.

## Full-corpus next stage

1. Correct OCR and section parsing against the PDFs, including very long sections and repeated legal boilerplate.
2. Resolve dates and ordinance provenance; update verification metadata only after review.
3. Copy the pilot config, change `source` to the curated CSV, `sections_per_year` to `null`, `allow_unverified` to `false`, and `output` to a new path. Preparation fails if a requested year has no verified data.
4. Predefine development/holdout splits grouped by ordinance (and, where appropriate, time), tune without looking at held-out performance, then fit and evaluate the final design.
5. Broaden seed/parameter and corpus-resampling sensitivity checks; compare against a sentence-embedding-oriented encoder if required by the milestone's methodological concerns.
6. Experts score legal coherence, relevance, label appropriateness, temporal interpretation and overall quality on 1–5/N/A. Flag means below 3.00 as specified by the milestone.

## PDF and visual verification

On Windows with PowerPoint installed:

```powershell
powershell -NoProfile -File scripts/export_presentation.ps1 -Previews
```

This exports the PDF and local slide PNG previews, without editing the source deck or closing other open presentations. Previews are ignored; the editable deck, PDF and evidence figures are tracked. On non-Windows CI, the generator creates the PPTX and figures; PDF export is optional/manual.

## Automation

- `.github/workflows/ci.yml`: model contracts, synthetic lexical integration, existing extraction/curation tests. No real-model download in tests; synthetic results are never put into the thesis deck.
- `.github/workflows/pilot.yml`: manually triggered real two-model pilot, presentation and artifacts. It is not scheduled and does not auto-run expensive experiments on every push. GitHub may require this workflow to reach the default branch before its manual-run button appears.
- Local unit/integration and pipeline tests should be run before publishing. A workflow definition alone is not evidence that GitHub Actions has passed.
