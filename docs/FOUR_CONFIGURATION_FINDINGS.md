# Four-configuration tuning results and research interpretation

**Completed experiment, 23 October 2026.** All **24/24 fits** succeeded: four
configurations × two models × seeds 42, 43, 44. These are actual full-corpus reruns,
not illustrative results or recycled historical clustering outputs. No source,
preprocessing, eligibility or temporal-window changes were made. The 2,118 source
documents contribute 7,832 modeling units across **2016–2025**.

The Initial and Conservative primary metrics reproduce the earlier full-corpus
results exactly to saved precision: topic counts, C_v, diversity, coverage and the
original seed-42-versus-43/44 ARI. See
[`previous_baseline_check.csv`](../artifacts/four_configuration_tuning/evidence/previous_baseline_check.csv).

**Recommendation: Conservative for Model A and Conservative for Model B**, using
seed 42 for the primary temporal analysis and seeds 43/44 as sensitivity checks.
This is a defensible, **provisional research choice**, not an expert-validated
optimum. Neither recommendation dominates every criterion.

## Parameters

Identical settings were tested for each representation:

| Configuration | UMAP neighbors | UMAP min_dist | HDBSCAN min_cluster_size | HDBSCAN min_samples |
|---|---:|---:|---:|---:|
| Initial | 15 | 0.0 | 15 | 5 |
| Conservative | 30 | 0.1 | 30 | 10 |
| Fine-grained | 15 | 0.0 | 8 | 3 |
| Coarse-grained | 30 | 0.1 | 60 | 15 |

UMAP dimensions=5, cosine metric, random initialization; HDBSCAN uses Euclidean
metric/EOM. Shared vocabulary, top-ten keywords, SVD seed 42, frozen Legal-BERT,
chunk pooling and all other representation settings are unchanged. These are joint
sensitivity contrasts, not isolated causal estimates of parameter effects.

## Main comparison

Topic counts, C_v, diversity, coverage and outliers below are **primary seed 42**.
`Aligned stability` is the mean symmetric size-weighted membership-Jaccard score
across all three seed pairs after Hungarian topic matching; it is not ARI.

| Model | Configuration | Topics | C_v | Diversity | Assigned / 7,832 | Coverage | Outliers | Aligned stability |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| A: Lexical | Initial | 202 | 0.7882 | 0.4694 | 7,088 | 90.50% | 744 (9.50%) | 0.7718 |
| A: Lexical | **Conservative** | **107** | **0.7960** | **0.5689** | **6,794** | **86.75%** | **1,038 (13.25%)** | **0.7929** |
| A: Lexical | Fine-grained | 341 | 0.7592 | 0.4333 | 7,069 | 90.26% | 763 (9.74%) | 0.7341 |
| A: Lexical | Coarse-grained | 49 | 0.7927 | 0.6289 | 6,727 | 85.89% | 1,105 (14.11%) | 0.8548 |
| B: Legal-BERT | Initial | 159 | 0.7813 | 0.4919 | 6,509 | 83.11% | 1,323 (16.89%) | 0.7653 |
| B: Legal-BERT | **Conservative** | **64** | **0.8171** | **0.5120** | **7,162** | **91.45%** | **670 (8.55%)** | **0.8992** |
| B: Legal-BERT | Fine-grained | 275 | 0.7534 | 0.4514 | 6,611 | 84.41% | 1,221 (15.59%) | 0.6814 |
| B: Legal-BERT | Coarse-grained | 36 | 0.8433 | 0.5718 | 7,004 | 89.43% | 828 (10.57%) | 0.9064 |

Every primary topic was scorable by the existing C_v calculation; no selected
keyword was absent from its token dictionary. Actual keyword slots, not K×10,
are used for diversity. This matters because some topics have fewer than ten
nonempty words. Full counts are in `evidence/coherence_audit.csv`.

### Repeated-seed evidence

| Model / configuration | C_v mean ± sample SD | Coverage mean ± sample SD (percentage points) | Original ARI mean | Cross-configuration temporal similarity |
|---|---:|---:|---:|---:|
| A / Initial | 0.7853 ± 0.0033 | 90.05 ± 0.70 | 0.5305 | 0.7354 |
| A / Conservative | 0.7970 ± 0.0058 | 87.60 ± 0.89 | 0.6110 | 0.7291 |
| A / Fine-grained | 0.7608 ± 0.0014 | 90.06 ± 0.24 | 0.3918 | 0.6772 |
| A / Coarse-grained | 0.7953 ± 0.0031 | 86.12 ± 0.67 | 0.7306 | 0.6187 |
| B / Initial | 0.7776 ± 0.0044 | 84.09 ± 0.85 | 0.5737 | 0.7007 |
| B / Conservative | 0.8147 ± 0.0035 | 91.51 ± 0.29 | 0.8559 | 0.7145 |
| B / Fine-grained | 0.7507 ± 0.0026 | 84.69 ± 1.16 | 0.3829 | 0.6409 |
| B / Coarse-grained | 0.8454 ± 0.0034 | 88.99 ± 0.48 | 0.8850 | 0.6640 |

Three seeds describe sensitivity, not population uncertainty or significance.
Original ARI includes noise as one cluster and averages seed 42 vs 43 and 42 vs 44.
Temporal similarity is 1 minus mean annual base-2 Jensen–Shannon divergence,
after membership alignment, averaged against the other three configurations. It
includes separate unmatched-topic bins and shared noise; it is **not temporal
accuracy** and can penalize legitimate topic splits/merges.

## Why Conservative for Model A

- Relative to Initial, Conservative approximately halves the nominal topic count
  (202→107), increases keyword diversity (0.4694→0.5689), and improves both original
  ARI (0.5305→0.6110) and aligned stability (0.7718→0.7929). Coherence is similar to
  slightly higher across the three seeds; no statistical superiority is claimed.
- The price is lower primary coverage: **294 additional units are outliers** versus
  Initial, a 3.75-percentage-point reduction. Initial remains a defensible alternative
  when retaining finer subjects and maximizing unit assignment is the priority.
- Fine-grained produces 341 topics but lower coherence, diversity and stability;
  primary coverage does not improve. Its seed-mean coverage exceeds Initial by
  only about 0.009 percentage points, which is not persuasive evidence for adopting
  substantially greater fragmentation. Formal numerical nondominance is not enough.
- Coarse-grained has better diversity and stability, but its largest topic contains
  **11.20% of all units**, compared with **2.99%** under Conservative, and uses broad
  terms such as `shall, section, city, person, office, health, public, children`.
  Its 49 nominal topics correspond to about 38.4 effective topics, versus 93.3
  effective topics for Conservative's 107. This favors caution about lost subject
  resolution despite good intrinsic scores.
- Conservative's average temporal similarity to other configurations is 0.7291,
  versus 0.6187 for Coarse-grained; within-Conservative seed temporal similarity is
  0.9339. These support a middle-resolution analysis but do not establish the
  correctness of individual historical trends.

**Judgment:** Conservative gives a more useful middle level of detail for ordinance
analysis than the fragmented Fine-grained solution or the broad Coarse-grained
solution. Coarse-grained remains a useful sensitivity analysis for broad themes.

## Why Conservative for Model B

- Conservative improves over Initial on the reported seed-mean coherence, diversity,
  coverage, aligned stability and cross-configuration temporal similarity. It also
  reduces assignment variability (coverage SD about 0.29 percentage points).
- Compared with Fine-grained, it trades 275 nominal clusters for 64, with much higher
  coherence and stability and **551 more assigned units** at seed 42. More small
  clusters did not yield more reliable policy detail.
- Coarse-grained is the strongest alternative: **it has higher C_v and diversity**
  and slightly better size-weighted alignment (0.9064 vs 0.8992). Conservative is
  **not** selected because it maximizes these metrics.
- Conservative retains **64 rather than 36 topics**, assigns **158 more units**
  (+2.02 percentage points), and has marginally better macro alignment (0.8716 vs
  0.8672). Effective topic counts are 36.1 versus 23.9. The small weighted-stability
  difference does not offset the loss of detail and coverage for this objective.
- Conservative and Coarse-grained have fairly similar aligned annual distributions
  (similarity **0.9051**), and both are highly seed-stable temporally (0.9787 and
  0.9828). Thus the decision is primarily about retained detail/coverage versus
  more coherent, broader clusters—not a claim that Coarse-grained is unstable.

**Judgment:** Conservative is the more defensible primary policy-resolution
compromise; retain Coarse-grained as the broad-theme robustness check. Conservative
still has a mixed large cluster and must not be presented as fully interpretable.

## Interpretation and temporal robustness

The selected semantic model has higher primary coverage (91.45% vs 86.75%) and
aligned stability (0.8992 vs 0.7929), while the selected lexical model has higher
keyword diversity (0.5689 vs 0.5120) and finer topic resolution. These are intrinsic
comparisons on the same units, not evidence that one model is legally more accurate.
Topic IDs and semantic categories do not align by number across models.

Some major trajectories survive tuning, but **not all annual distributions are
configuration-invariant**:

- Initial semantic road-closure topic 0 aligns with Conservative topic 3 with
  membership Jaccard **0.8739**. Their ten annual document-weighted trajectories
  correlate at **0.9425**, with mean absolute difference **0.61 percentage points**.
- Initial lexical authorization topic 0 aligns with Conservative topic 2 with
  trajectory correlation **0.9410** and mean absolute difference **0.23 percentage
  points**. These are illustrative inspected topics, not a census of valid trends.
- Fine-versus-Coarse annual-distribution similarities fall to **0.5107 (A)** and
  **0.5003 (B)**. Consequently, trends must be reported under a fixed declared
  configuration, with sensitivity plots, not selected opportunistically across runs.
- High correlation does not guarantee equal prevalence. The full alignment tables
  include absolute differences, unmatched topics and matched mass so that a smooth
  trajectory cannot conceal broad merging or disappearing subtopics.

### Source-linked spot checks — not expert ratings

| Configuration / topic | Evidence | Interpretation limitation |
|---|---|---|
| A Conservative / 0 | `2019/Ordinance No. 0708-19 (1).txt`, `section_455`, discusses chief-executive powers and contracting | A coherent legal-form or authority cluster need not be a distinct substantive policy field. |
| A Conservative / 3 | Keywords include `sectioii`, `tr`, `ordained`, `ard`, `deg` | OCR-heavy clusters remain despite verified source status. |
| B Conservative / 0 | `2025/Ordinance No. 0785-25.txt` fallback concerns staffing; `2023/Ordinance No. 0192-23 Anti-Bullying (2).txt`, section 21 concerns information dissemination | A large generic cluster mixes subjects; its 13.90% unit share warrants expert review. |
| B Fine-grained / 3 | Keywords include `separabiliw`, `unconstitutional`, `invalid`, `hereof` | Misspelled boilerplate can survive the unchanged deterministic filtering. |
| B Coarse-grained / 2 | Keywords include `effect`, `approval`, `immediately`, `effectmty`, `publication` | High coherence may reflect repeated effectivity clauses rather than substantive policy quality. |

These spot checks use saved keywords and source-linked representative units;
representativeness is based on cluster membership strength, not calibrated legal
confidence. No numerical expert ratings were inferred or filled in. The 597 fallback
documents, 45 additional same-number text versions and 28 date-disagreement flags
remain limitations. Year 2025 has only 32 source documents versus 298 in 2024;
normalized shares do not make those years equally representative of city legislation.

## Computational cost

The complete current experiment took **1,752.65 seconds (29.21 minutes)**, including
shared setup and post-fit alignment. Mean single-seed fit/evaluation wall times:

| Configuration | A: Lexical (seconds) | B: Legal-BERT (seconds) |
|---|---:|---:|
| Initial | 103.28 | 67.42 |
| Conservative | 69.66 | 50.45 |
| Fine-grained | 82.33 | 75.07 |
| Coarse-grained | 60.61 | 54.18 |

The first lexical fit includes library import/JIT overhead. Times include coherence
and output generation; they are not isolated clustering benchmarks. Lexical
representation construction took 4.51 s. Loading the validated semantic cache plus
required imports took 25.35 s. The cache's original GPU encoding session took
571.41 s, **historical cost, not fresh inference in this rerun**. Thus these timings
do not demonstrate that Legal-BERT is cheaper end-to-end. Process CPU time and
sampled whole-process resident-memory peaks are in `evidence/computational_cost.csv`.

## Thesis-ready tuning-results paragraph

> Four predeclared tuning configurations were evaluated for lexical and frozen
> Legal-BERT representations on an unchanged corpus of 7,832 units from 2,118
> source documents spanning 2016–2025. Twenty-four fits were completed using
> UMAP seeds 42, 43 and 44 with fixed representations and shared preprocessing.
> Conservative tuning was provisionally selected for both models because it
> balanced topic resolution, intrinsic coherence, diversity, assignment coverage,
> aligned seed stability and temporal sensitivity. At seed 42, the lexical model
> identified 107 topics (C_v=0.7960, diversity=0.5689, coverage=86.75%), and the
> semantic model identified 64 topics (C_v=0.8171, diversity=0.5120,
> coverage=91.45%). Mean size-weighted, topic-aligned seed stability was 0.7929
> and 0.8992, respectively. Fine-grained tuning increased topic counts but reduced
> coherence and stability. Coarse-grained tuning improved some intrinsic metrics
> while reducing topic detail; it was retained as a sensitivity alternative rather
> than automatically selected for its higher scores. Temporal distributions were
> seed-stable within the selected configurations but changed with granularity.
> These in-sample findings do not establish legal validity, predictive performance
> or causal policy trends; source-boundary checks and legal-expert review remain
> necessary.

## Deliverables and reproduction

- [Complete tables, charts and measured report](../artifacts/four_configuration_tuning/RESULTS.md)
- [Seven vector-quality figures in one PDF](../artifacts/four_configuration_tuning/Tuning_Comparison_Figures.pdf)
- [Full metric definitions and reproduction protocol](FOUR_CONFIGURATION_METHODS.md)
- Configurations: `configs/four_configuration_tuning.json`.
- Selection record: `configs/four_configuration_selection.json`.
- Full local outputs: `results/experiments/four_configuration_tuning/`.

To rerun the selected configuration with the identical protocol, copy the experiment
config, choose a fresh output directory, and rerun `scripts/run_four_configurations.py`.
The Conservative/seed_42 folders are the selected primary outputs; the full rerun
also reproduces their sensitivity checks. For cold encoding, explicitly set
`embedding_cache_source` to null; do not label cache reuse as fresh encoding.

This Markdown section was written **after experiment completion**. The original
reference thesis PDF was not edited; this is an editable, thesis-ready results
section for integration into the manuscript source.
