# Davao ordinance analysis — cleaned TXT, full corpus

**Model text comes exclusively from `data/processed/clean_text/**/*.txt`.**
Human year-override CSVs provide temporal metadata; no PDF re-extraction, external
archive application, or previously prepared note-derived dataset is used.

## Latest: completed four-configuration tuning

**24/24 fits completed** on the unchanged full corpus: Initial, Conservative,
Fine-grained and Coarse-grained for both models, seeds 42/43/44.
**Provisional selection: Conservative for both models** (107 lexical topics,
64 semantic topics at seed 42), subject to legal-expert review—not simply the
highest-coherence or highest-coverage setting.

- [Research findings and thesis-ready results section](docs/FOUR_CONFIGURATION_FINDINGS.md)
- [Eight-combination tables and seven figure sets](artifacts/four_configuration_tuning/RESULTS.md)
- [Combined vector PDF](artifacts/four_configuration_tuning/Tuning_Comparison_Figures.pdf)
- [Protocol, formulas, caveats and reproduction](docs/FOUR_CONFIGURATION_METHODS.md)
- [Configurations](configs/four_configuration_tuning.json) · [Selection record](configs/four_configuration_selection.json)

## Selected-run temporal topics

[Temporal tables and figures](artifacts/temporal_topics/) now use **Conservative,
seed 42, for both models**: 107 lexical and 64 semantic topics. The package contains
8 labeled PNGs, PDF/PPTX exports and complete temporal tables for all 171 topics.
It reuses verified completed runs; no models were retrained during rendering.
The previous Initial package is preserved at [temporal_topics_initial](artifacts/temporal_topics_initial/).
See [the temporal graph guide](docs/TEMPORAL_TOPIC_GRAPHS.md) for parameters and provenance.

The earlier presentation below is preserved as historical two-configuration
research evidence; it is not the updated four-configuration report.

## Expert validation — proposed protocol and questionnaire

The [EV-1.0 revision package](docs/expert_validation/README.md) reviews the actual
Chapter 3 in `CS_Undergraduate_Thesis_Template__Copy_-13.pdf`. It includes a
thesis-ready replacement subsection, a 16-item questionnaire, and practical
sampling/scoring procedures. [Editable DOCX and printable PDFs](artifacts/expert_validation/)
are provided. Expert recruitment, packet preparation, and survey administration
remain future activities; no expert responses or validation results are invented.
The original thesis PDF and completed model outputs are unchanged.

## Earlier deliverables

- [Original full-corpus presentation](artifacts/clean_text_full/Clean_Text_Full_Corpus_Initial_Results.pptx)
- [PDF](artifacts/clean_text_full/Clean_Text_Full_Corpus_Initial_Results.pdf)
- [Measured metrics and audit evidence](artifacts/clean_text_full/evidence/)
- [Pipeline, parameter and yearly PNG figures](artifacts/clean_text_full/figures/)
- [Methodology and reproducibility](docs/CLEAN_TEXT_RUNBOOK.md)
- [Archived Initial temporal-topic graphs](artifacts/temporal_topics_initial/) — original 8 PNGs, PDF/PPTX, and draft-title catalog for 361 model-local topics; not the current Conservative outputs.

Temporal figures use document-weighted annual shares. Topic titles are keyword-based
descriptions, not expert-validated categories. See [the temporal graph guide](docs/TEMPORAL_TOPIC_GRAPHS.md).

The earlier experiment remains on the separate `research/two-model-comparison`
branch. This branch replaces its legacy archive workflow rather than mixing the
old sample's results into the new full-corpus comparison.

## What the new pipeline does

1. Reads cleaned TXT files without modifying them.
2. Hashes all sources and groups whitespace-equivalent duplicates.
3. Applies existing human year corrections; records all duplicate and date decisions.
4. Extracts numbered sections, with document fallback for missing/repeated headings.
5. Removes explicitly defined boilerplate sections and signature blocks, with an audit.
6. Runs the same full eligible input through two representations:
   - **Model A:** TF-IDF → SVD → UMAP → HDBSCAN → c-TF-IDF.
   - **Model B:** frozen Legal-BERT → all-chunk mean pooling → UMAP → HDBSCAN → c-TF-IDF.
7. Evaluates coherence, diversity, coverage, outliers and seed stability. The original
   run used two configurations; the latest extension uses four, saves all three
   seeds' full fits, and adds explicit topic alignment and temporal sensitivity.
8. Generates a new editable presentation entirely from completed measurements.

## Data accounting

The available files are researcher-confirmed verified cleaned text. The additional
machine audit found 2,283 TXT files, 150 duplicate copies and 2,133 distinct contents.
Existing human year corrections exclude 13 content groups outside 2016–2025;
2 further groups have no usable extracted content. The preparation contains
**2,118 source documents and 7,832 model units**.

Verification of source text is different from validation of automated section
extraction or discovered topics. Of these units, 7,235 are detected sections and
597 are document fallbacks. There are 45 additional text variants sharing ordinance
numbers and 28 extracted-date disagreement flags. These remain visible in the audit;
they are not silently resolved or treated as proof that the source review was wrong.

## Run locally (PowerShell)

```powershell
mise install
mise exec -- python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-models.txt
# Optional, for a compatible NVIDIA GPU; the measured local run uses CUDA 12.6:
.\.venv\Scripts\python.exe -m pip install torch==2.8.0+cu126 --index-url https://download.pytorch.org/whl/cu126

.\.venv\Scripts\python.exe -m pytest tests/test_clean_text.py -q
.\.venv\Scripts\python.exe scripts/prepare_clean_text.py
.\.venv\Scripts\python.exe scripts/run_clean_text.py --config configs/clean_text_full.json
.\.venv\Scripts\python.exe scripts/build_clean_presentation.py
powershell -NoProfile -File scripts/export_presentation.ps1 -Previews
```

The config requests CUDA explicitly. Change `common.device` to `cpu` in a copied
config if GPU inference is unavailable. On Linux use `.venv/bin/python`.

Choose new preparation/experiment/presentation output directories for a new run.
`--resume` permits restarting an interrupted experiment only when its input,
configuration and model-code hashes match; its encoder checkpoint avoids redoing
finished batches. Completed output is never silently replaced.

After preparing the same clean-text corpus, reproduce the latest experiment with:

```powershell
.\.venv\Scripts\python.exe scripts/run_four_configurations.py --config configs/four_configuration_tuning.json
.\.venv\Scripts\python.exe scripts/report_four_configurations.py --config configs/four_configuration_tuning.json
.\.venv\Scripts\python.exe -m pytest tests -q
```

Choose a fresh output directory in a copied config for a new experiment. Completed
Legal-BERT embeddings are reused only after identity validation; if the old cache
is absent, the encoder runs afresh. Per-seed statuses, full assignments, vectors,
keywords, temporal tables and code snapshots are stored locally under
`results/experiments/four_configuration_tuning/` (Git-ignored). Compact evidence,
plots and the report are in `artifacts/four_configuration_tuning/`.

Open `Thesis_Model_Comparison.code-workspace` for the VS Code tasks.
CI runs offline synthetic correctness tests. The full experiment workflow is
manual-only and can take substantially longer on a CPU runner.

## Interpretation

All metrics are intrinsic and in-sample. The unit is a detected section or an
explicitly marked fallback document, not a supervised label. No accuracy/F1,
artificial BERTopic perplexity, expert scores or final winning model are invented.
Topic IDs differ between models. Yearly shares describe the eligible archive, not
all legislation enacted by the city. Document-weighted plots reduce unequal
section-count effects but do not resolve differing versions of the same ordinance.
