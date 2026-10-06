# Clean-text full-corpus experiment

## Authority and scope

The researcher confirmed that `data/processed/clean_text` is the verified cleaned
source. No source TXT is edited, relocated or deleted by preparation. Verification
is recorded as **user-confirmed**, not as an independent new audit of PDF originals.
The input files match the cleaned-text tree on the repository's `verified-data`
branch at `cbafc7f`; this does not mean the branch's name supersedes measured audit
findings.

The previous workflow and presentation remain in Git on
`research/two-model-comparison` (`300680b`). This branch removes the former archive,
web interface, extraction scripts and note-derived intermediate results. They are
not model inputs or dependencies in this run.

## Preparation rules

`scripts/prepare_clean_text.py` is the complete preparation implementation.

- Decode TXT as UTF-8 strictly; record original byte hashes and relative paths.
- Normalize whitespace only for duplicate-content identification. Keep all source
  copies on disk. Record a canonical file and every duplicate relationship.
- Ordinance numbers normalize leading zeroes; differing text versions sharing a
  number are **not** arbitrarily merged. Model document IDs include a content-hash
  suffix so lineage is unique. Therefore source-document count and distinct
  ordinance-number count are reported separately.
- Existing `data/manual_year_overrides_YYYY.csv` corrections take priority across
  duplicates. Conflicting human corrections are excluded for review.
- Without a correction, a unique researcher-verified folder year is used. Cross-year
  identical copies require an explicit enactment year matching a candidate folder;
  unresolved copies are excluded instead of selecting a year arbitrarily.
- Corrected years outside 2016–2025 are excluded, even if the original folder is in
  range. Date-candidate disagreements with assigned years remain flags. The plots
  use **resolved study year**, not a newly validated full enactment date.
- Detect line-start `SECTION`, `SECTI0N` or `SEC.` numbering. Start after the operative
  clause when available to avoid introductory tables of contents. Missing/repeated
  section numbers use an explicitly marked whole-document fallback.
- Omit the prefix before the first detected section. Trim line-start ENACTED,
  CERTIFIED CORRECT, ATTESTED or APPROVED signature blocks. Remove sections whose
  heading starts effectivity, separability, severability or repealing clause.
  This is a deterministic modeling policy, not a revision to the legal source.
- Require at least three alphabetic tokens per extracted unit. A shared vocabulary
  eligibility check records any additional empty-token units before either model.

These rules can still misinterpret OCR, quoted amendments, section headers or
signature blocks. A source's verified status does not imply these derived boundaries
have been expert-reviewed. Audit fields and source hashes permit that review.

### Actual preparation

| Item | Count |
|---|---:|
| Source TXT files | 2,283 |
| Duplicate copies (whitespace-equivalent contents) | 150 |
| Distinct contents | 2,133 |
| Human-corrected out-of-scope contents | 13 |
| No usable extracted text | 2 |
| Included source documents | 2,118 |
| Numbered-section units | 7,235 |
| Whole-document fallback units | 597 |
| Total model units | 7,832 |
| Explicit boilerplate units omitted | 623 |
| Additional differing text versions sharing ordinance numbers | 45 |
| Extracted date disagreements retained as flags | 28 |

The source dates use 82 human corrections and 2,036 verified folder assignments.
All eligible documents are included; there is no year-balanced sampling. Do not
claim that all remaining records are distinct ordinances or that all automated
section/year issues have been independently re-verified.

## Models and fair comparison

`src/clean_model.py` contains the shared representation/evaluation functions.
Model A uses document TF-IDF followed by normalized SVD for initial clustering;
c-TF-IDF can only be calculated after cluster classes exist. Model B supplies
normalized Legal-BERT vectors instead. Both then use UMAP, HDBSCAN and c-TF-IDF.

The vocabulary, exact ordered units, years, topic-word count and metric inputs are
shared. Encoder weights are frozen. The revision is pinned to
`15b570cbf88259610b082a167dacc190124f60f6` of
`nlpaueb/legal-bert-base-uncased`.

`src/clean_encoder.py` batches chunks across source units. Every non-overlapping
chunk fits the model's token limit; no long unit is silently truncated. Content-token
sums exclude padding and special tokens. Float32 encoder outputs are aggregated in
float64 and finally L2-normalized to float32 section vectors. Checkpoints record the
next completed chunk and validated input/model identity. A completed embedding cache
is shared between parameter trials.

`configs/clean_text_full.json` defines two **joint sensitivity configurations**:

| Trial | Neighbors | Min distance | Min cluster size | Min samples |
|---|---:|---:|---:|---:|
| initial | 15 | 0.0 | 15 | 5 |
| conservative | 30 | 0.1 | 30 | 10 |

Shared: seed 42; SVD 100 components; UMAP 5 dimensions; unigram vocabulary;
min_df 1; up to 50,000 terms; top 10 keywords; one primary plus two additional seeds.
These are not independently isolated parameter effects or held-out hyperparameter
selection. No learning rate or training epochs apply to a frozen BERT encoder.

## Metrics and temporal denominators

- C_v: Gensim sliding-window coherence on the same texts and unigram topic keywords.
- Diversity: distinct top keywords / all actual keyword slots, excluding outliers.
- Coverage: non-outlier units / all modeled units. Report the complementary outlier rate.
- Seed stability: mean ARI versus two additional UMAP seeds, with outliers treated as
  one cluster. Dominant clusters may inflate this value; it is not corpus-resampling
  stability or legal validity.
- Section NPMI: supplementary whole-unit co-occurrence diagnostic, not C_v.
- Cross-model ARI: partition agreement, not accuracy or a model-quality score.
- Yearly unit share: topic units / all modeled units in that year, including outliers.
- Document-weighted share: each source document contributes weight 1 divided among
  its unit topics, then normalize by documents in the year. This reduces long-document
  dominance but does not collapse different text versions of a shared ordinance number.

Topic IDs are model-local. Top-eight heatmaps omit other topics and need not sum to
100%. Corpus sizes differ by year; neither document counts nor topic shares prove
citywide policy activity or causation. Holdouts and legal-expert ratings remain pending.

## Evidence and execution

`results/experiments/clean_text_preparation/`: per-file and per-document audits,
prepared units, year counts, code/input/override hashes.

`results/experiments/clean_text_full/`: exact configuration and package versions,
input units, common vocabulary, encoder checkpoint/cache, all trial artifacts,
yearly tables, cross-model agreement and full-precision metrics. Large regenerable
text/vector artifacts are ignored by Git.

`artifacts/clean_text_full/`: new PPTX/PDF, rendered PNG diagrams/tables/charts, and
compact JSON/CSV evidence copied only from a completed experiment. Parameter images
are genuine rendered configuration data, not screenshots of a nonexistent UI.

The deck must not copy metrics from the earlier 200-unit sample. Cross-run changes
cannot be attributed solely to the text input: corpus size, preprocessing, model
batching and cluster settings differ. Changes in the input corpus are disclosed.

## Next research steps

1. Review the 45 additional text variants sharing IDs and 28 date-disagreement flags.
2. Validate fallback boundaries and the boilerplate/signature policy against a stratified
   selection of verified TXT sources; distinguish clerical and substantive topics.
3. Predefine ordinance-grouped development and held-out sets (including text variants).
4. Expand seeds and bootstrap sensitivity only after freezing the reviewed corpus.
5. Have experts complete the blank five-dimension 1–5/N/A topic review; flag mean
   dimension scores below 3.00. Never infer these ratings from intrinsic metrics.

## Automation and environment

Python is pinned through `.mise.toml`. Dependencies use `requirements-models.txt`;
the optional local CUDA wheel is installed explicitly, not through a PATH change.
The local run uses a GTX 1650 with `torch==2.8.0+cu126`. Record actual versions from
the experiment manifest; CPU and GPU floating-point results can differ slightly.

CI tests use a tiny random local encoder and unmistakably synthetic texts for
correctness only. Those vectors/results never enter the research presentation.
The full-corpus workflow is manually triggered and uses CPU on hosted runners;
it is intentionally not run on every push. PowerPoint PDF export is Windows-only;
the platform-independent generator produces the editable PPTX and PNGs.
