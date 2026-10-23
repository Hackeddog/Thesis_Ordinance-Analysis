# Four-configuration tuning: protocol and reproducibility

## Scope and preserved methodology

This experiment extends `research/clean-text-full-corpus` at `71de6cbd`, not the
older sampled/Obsidian workflow. The active study window is **2016–2025**. The
unchanged preparation contains 2,118 source documents (2,073 ordinance numbers),
7,832 units (7,235 numbered sections and 597 fallback documents), derived from
2,283 cleaned TXT files. The 150 duplicate copies, 13 out-of-scope groups, two
unusable groups, 45 additional text variants and 28 date flags retain the original
handling. See `CLEAN_TEXT_RUNBOOK.md`; none of those limitations is newly resolved.

The runner verifies every TXT byte hash, human year-override file, preparation
code hash and prepared CSV hash against the original preparation manifest. No
source text, eligibility, extraction, dates, stopwords or temporal denominator
changes. Both models receive identical ordered eligible units and vocabulary.

- Model A: document TF-IDF → normalized 100-dimensional SVD → UMAP → HDBSCAN → c-TF-IDF.
- Model B: frozen `nlpaueb/legal-bert-base-uncased`, revision
  `15b570cbf88259610b082a167dacc190124f60f6`, all-content-token mean over every
  non-overlapping chunk → normalized vectors → same clustering and c-TF-IDF.
- Shared vocabulary: English stopwords, Unicode accent stripping, alphabetic
  tokens of length at least two, unigrams, min_df=1, max_df=1.0, max_features=50,000.
- Fixed UMAP: cosine metric, 5 dimensions, random initialization, n_jobs=1.
- Fixed HDBSCAN: Euclidean metric, EOM selection, core_dist_n_jobs=1,
  prediction_data=True. c-TF-IDF BM25 and frequent-word reduction remain disabled.
- Top ten actual nonempty keywords; no manual merging, outlier reassignment,
  fine-tuning of BERT, learning-rate search or changes to temporal keyword tuning.

## Predeclared configurations (same for both models)

| Configuration | UMAP neighbors | UMAP min_dist | HDBSCAN min_cluster_size | HDBSCAN min_samples |
|---|---:|---:|---:|---:|
| Initial | 15 | 0.0 | 15 | 5 |
| Conservative | 30 | 0.1 | 30 | 10 |
| Fine-grained | 15 | 0.0 | 8 | 3 |
| Coarse-grained | 30 | 0.1 | 60 | 15 |

Initial and Conservative are unchanged references. Fine-grained holds Initial's
UMAP fixed and relaxes cluster size/density to test smaller subjects and potential
fragmentation. Coarse-grained holds Conservative's UMAP fixed and increases size/
density requirements to test broad themes and loss of rare subjects. Both HDBSCAN
parameters change together: these are **joint sensitivity contrasts, not causal
one-parameter ablations**. Four settings cannot estimate independent parameter
importance. More topics or a higher intrinsic score is not itself the objective.

Seeds **42, 43, 44** are identical across models/configurations. Seed 42 remains the
primary reported fit. Every seed now performs a full BERTopic fit and exports
keywords, assignments and temporal outputs, rather than the previous helper's
unsaved UMAP/HDBSCAN-only repeats. SVD is fixed at seed 42 and Legal-BERT is frozen:
stability measures downstream clustering sensitivity, **not end-to-end representation
uncertainty**, bootstrap sensitivity or unseen-document generalization.

Numerical library thread caps are explicitly recorded (four); UMAP and HDBSCAN
settings remain single-worker. Exact reruns can still vary across software,
hardware, compiler and floating-point settings. No bitwise cross-machine guarantee.

## Measurements

All primary-topic metrics exclude topic -1 unless explicitly stated. Repeat means
and sample SDs use three seeds, not three independent corpora. They are descriptive
sensitivity summaries, not confidence intervals, significance tests or a held-out
validation score. No quality score is filled with zero if unavailable.

### Original metrics, unchanged calculations

- **Topics:** number of unique assigned labels other than -1.
- **C_v:** original Gensim `CoherenceModel`, unigram top words, regex-tokenized full
  eligible texts, default c_v sliding window (110), processes=1, mean across
  scorable topics. Terms absent from the dictionary are discarded and topics with
  fewer than two retained terms are omitted. A separate output audit records the
  number scored. This is intrinsic lexical coherence, not legal correctness.
- **Diversity:** unique words across all actual top-word slots / total actual slots.
  Denominator is not forced to K×10 when a topic has fewer words. Different topic
  counts change this metric's opportunity for repetition; comparisons need context.
- **Coverage:** non-outlier units / 7,832; exact assigned and outlier counts saved.
  Also report documents with any/all units assigned, not conflate unit coverage
  with document coverage. Outlier rate is coverage's complement, not an independent
  quality criterion.
- **Section NPMI:** retained supplementary whole-unit binary co-occurrence diagnostic;
  not equivalent to C_v or sliding-window NPMI.
- **Original seed ARI:** mean ARI of seed 42 vs 43 and 42 vs 44, noise as one label.
  Retained for comparison to earlier results. Also report all-three-pair mean ARI
  and ARI on jointly assigned units (with its changing subset denominator).
  ARI is label-permutation invariant, not accuracy; dominant/noise clusters can
  produce misleadingly favorable agreement.

### Added topic alignment and temporal sensitivity

For each pair of label arrays on the exact same ordered units:

1. Exclude noise from candidate topics; form a topic-by-topic membership Jaccard
   matrix `|A ∩ B| / |A ∪ B|` over all units, not only jointly assigned ones.
2. Hungarian assignment maximizes total Jaccard. Retain only positive-overlap
   pairs. Persist intersections, sizes, Jaccard and unmatched topic counts.
3. **Symmetric macro stability:** `2 × sum(matched Jaccards)/(K_A+K_B)`.
   **Size-weighted stability:** `sum((size_A+size_B)×J)/(assigned_A+assigned_B)`.
   Unmatched topics contribute zero. Report all three seed pairs and their means.
   These measures penalize splits/merges deliberately; broad cluster agreement
   is not proof of good subject resolution. Two all-noise solutions receive null
   topic-alignment scores, even though ARI and noise-distribution agreement are 1.

Temporal procedures remain those of the original pipeline: BERTopic annual
keywords use `evolution_tuning=False, global_tuning=False`; annual unit shares
include outliers. Primary interpretation uses **document-weighted shares**: divide
each document's weight one among its units' topics, then divide by the number of
documents in the year. Zero topic/year cells are explicit. Different text variants
are still different source documents, not silently collapsed ordinance identities.
Annual document counts range from 32 (2025) to 298 (2024); 2025 is therefore a
particularly thin archive slice. Normalized shares do not equalize sampling
uncertainty or prove that the collection covers a full legislative year.

Compare every configuration pair within each model at seed 42 and every seed pair
within a configuration. Use the same Jaccard alignment to define common topic bins;
keep unmatched topics in separate bins and noise in one explicit shared bin. For
each year compute base-2 Jensen–Shannon **divergence** (square of SciPy's distance)
and total variation. Annual means weight the ten observed years equally.
`Temporal similarity = 1 - mean annual JS divergence`. A configuration's
cross-configuration mean is its mean similarity to the other three, **not a
comparison to truth** or an independent score. Shared outlier mass may inflate
similarity; annual outlier shares and matched mass are available for inspection.
One-to-one matching penalizes legitimate changes in topic granularity. Do not rank
models using this metric alone.

Matched-topic annual Pearson correlations and absolute share errors are also
saved. Constant trajectories yield null correlation; unmatched trajectories are
not scored. Correlations can be high despite different prevalence, so they are
supplementary. Major-topic plots use the largest Initial document-weighted topics
as a fixed visual reference, not an assertion that Initial is optimal.

### Cost and degeneracy diagnostics

- Wall seconds per seed cover fitting, intrinsic evaluation, temporal keyword
  calculation, and artifact saving. Shared vocabulary and representation times,
  plus total session time, are reported separately. Do not compare old bundled
  three-seed timings directly with new single-seed timings.
- Frozen embeddings may be reused only after ordered-text/model/token-budget/
  pooling identity and encoder-code validation. Cache byte hashes are saved. Historic
  GPU encoding time is provenance, **not current GPU inference time**. Change
  `embedding_cache_source` to null and use a fresh output to benchmark cold encoding.
- Process CPU seconds and 100-ms sampled peak resident memory are measured.
  RSS includes shared vectors/imports and allocator retention from preceding runs,
  can miss brief peaks and is not incremental model RAM, VRAM or whole-machine usage.
- Record largest-topic share, median topic size and effective topic count
  `exp(entropy(assigned-topic proportions))` to detect nominally many topics
  dominated by one broad cluster. No hardware-cost significance claims from one
  machine, fixed execution order or three seeds. The first lexical fit also bears
  one-time library import/Numba JIT overhead; cold-start and warmed timings are not
  interchangeable algorithm-speed measurements.

## Selection policy and expert interpretation

No automatically maximized composite score. Assess coherence, diversity, both
stability summaries, coverage, concentration and temporal evidence together.
Inspect keywords and source-linked representative sections for major and weak
clusters. Prefer an interpretable, reasonably stable policy resolution without
excessive fragmentation or broad catch-all clusters. Explicitly describe Pareto
trade-offs. Keyword inspection by this analysis is **not legal-expert validation**;
expert review templates remain blank and recommendations are provisional.

## Reproduce

Use the existing mise-managed Python 3.12 environment and pinned
`requirements-models.txt` (the measured installation uses torch 2.8.0+cu126).
From the project root, in PowerShell:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_four_configuration_tuning.py -q
.\.venv\Scripts\python.exe scripts/run_four_configurations.py --config configs/four_configuration_tuning.json
.\.venv\Scripts\python.exe scripts/report_four_configurations.py --config configs/four_configuration_tuning.json
```

For a new run, copy the config and choose a **new output directory**. For recovery,
use `--resume` with exactly the same config, input, code and installed package
versions. Completed per-seed artifacts are hash-validated before reuse; failed
runs are retried. Previous experiment output is never overwritten. Model outputs
include assignments, representative sections, vectors, reduced vectors, keywords,
annual tables and review templates, not a pickled live BERTopic estimator.

Full evidence is under `results/experiments/four_configuration_tuning/` (Git-ignored).
Compact evidence, figures (PNG/PDF/SVG), tables and the generated report are under
`artifacts/four_configuration_tuning/`. Source snapshots, packages, all settings,
input/cache hashes and per-run statuses accompany the full results. Reports require
all 24 fits to be completed. A failed/partial run remains identified as such and
cannot silently update the research conclusions.
