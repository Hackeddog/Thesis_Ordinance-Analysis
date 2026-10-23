# Review Notes and Manuscript Integration Checklist

## Actual sources reviewed

The principal source is **`Downloads/CS_Undergraduate_Thesis_Template__Copy_-13.pdf`**, a 56-page thesis titled *Temporal Analysis of Davao City Ordinances Using BERTopic-Based Dynamic Topic Modeling*, dated April 2026. Despite its filename, it is not an empty formatting template.

- SHA-256: `4acb1916ef522c4dd15a36eb0cdccc5fafa60c37eddd829b0183a9214985d22e`.
- Research questions/objectives: PDF page 7, printed page 2.
- Scope: PDF page 8, printed page 3.
- Evaluation and expert-review rationale in Chapter 2: PDF pages 18–21, printed pages 13–16.
- Chapter 3: PDF pages 26–44, printed pages 21–39.
- Model Evaluation and Expert Validation: PDF pages 41–43, printed pages 36–38.
- Table 5: five expert dimensions, PDF page 42, printed page 37.
- Table 6 and the below-3.00 rule: PDF page 43, printed page 38.
- Ethical considerations: PDF page 44, printed page 39.
- Chapter 4 includes earlier Initial/Conservative results and draft-label figures, PDF pages 45–53.

The other file, **`Downloads/Thesis_Corpuz, Lamsin, Nuril.pdf`**, is a 12-page Chapter 2/RRL document, not the Chapter 3 authority for this revision. It is byte-identical to the repository's local reference copy. Its SHA-256 is `9e1c891f9fc4ea3a13b010fb29402ef31dc40149c1456f090c33dcca7bd6710c`.

Implementation checks use `src/clean_model.py`, `src/clean_encoder.py`, the frozen four-configuration evidence, `configs/four_configuration_selection.json`, and `docs/FOUR_CONFIGURATION_METHODS.md` / `FOUR_CONFIGURATION_FINDINGS.md`. The completed experiment has 24 fits and a provisional Conservative selection for both models; it contains no completed expert ratings.

## What is retained and what changes

| Existing material or gap | Evidence in manuscript | Revision and reason |
|---|---|---|
| Five dimensions | Table 5 lists Legal Coherence, Thematic Relevance, Label Appropriateness, Temporal Interpretation, Overall Research Quality. | Retain all five names; map them to 16 concrete statements. Source support is explicit within Legal Coherence. |
| Five-point agreement scale | PDF page 41. | Retain anchors 1–5 exactly; make NA / Unable to Assess available for every rated item. Neutral is not the same as insufficient information. |
| Mean formula | Equation 3.1 and PDF page 43. | Retain available-valid-rating mean; add distributions, medians, denominators, complete-dimension rules, and separate missing/NA counts. |
| Interpretation table | Table 6 uses 4.21–5.00, 3.41–4.20, 2.61–3.40, 1.81–2.60, 1.00–1.80. | Preserve numerical boundaries; state continuous intervals for unrounded scores. Clarify the middle label so neutral does not imply acceptance. All bands are study-defined, not empirically validated thresholds. |
| Below-3.00 review trigger | Stated on PDF pages 41 and 43. | Retain, apply to unrounded topic-dimension means, and distinguish review action from the descriptive band and from a pass/fail standard. No new numeric quality cutoff. |
| Semantic-only emphasis | Expert paragraph refers to Legal-BERT and BERTopic rather than explicitly both models. | Specify equivalent review of Model A and Model B; use neutral codes and identical criteria. |
| Unspecified experts | No operational eligibility or recruitment procedure in the subsection. | Propose relevance-based legal/legislative/policy/ordinance experience and a small, prospective panel; do not invent credentials, minimum experience, names, or recruited participants. |
| Unspecified selected topics | The subsection says “selected topics” without a selection rule or workload. | Propose four per model, with prevalence, seeded random, and stability-risk roles, and three varied examples per topic. This implements Chapter 2's recommendation to include random or borderline members. |
| Research-wide quality claim | Overall Research Quality includes methodological appropriateness of the whole research. | Restrict the rated construct to usefulness, source transparency, and limitations of supplied outputs. Reviewers are not asked to certify technical metrics or the entire thesis. |
| Content accuracy not operationalized | Labels and relevance are described but source support and membership errors need clearer questions. | Define content-based accuracy explicitly; it is not supervised classification accuracy or a ground-truth topic benchmark. |
| Temporal judgments underspecified | General reference to topic changes and ordinance examples. | Provide denominators, document-weighted shares, resolved years, yearly keywords, source context, and a claim to assess; prohibit unsupported causal or legal conclusions. |
| No missingness/agreement procedure | No specific handling beyond “valid responses.” | Separate missing and NA, prevent forced neutral ratings, retain dissent, and report descriptive inter-rater agreement only where overlapping independent ratings exist. |
| Refinement without version control | Researchers may revise labels or interpretations. | Log the decision and evidence; distinguish label-only edits from assignment/preprocessing/year changes requiring recomputation and possible re-review. |

The revised academic text is in `chapter3_revised.md`. The questionnaire, operational guide, item bank, and blank registers are separate appendices/support materials. The five original dimensions are not silently replaced with unrelated constructs.

## Required alignment edits elsewhere in the manuscript

These are integration instructions, not claims that the original PDF or editable thesis source has been changed.

### 1. Update research question 4 and objective 4

RQ4 currently mentions only Initial and Conservative. Suggested replacement:

> How do the four tuning configurations—Initial, Conservative, Fine-grained, and Coarse-grained—affect the number of topics and the performance of each model?

Specific objective 4:

> Evaluate how Initial, Conservative, Fine-grained, and Coarse-grained parameter settings affect the number of topics and the performance of each model.

Research questions 1–3 will remain the substantive identification, document-weighted temporal analysis, and automated model-comparison questions. Expert review will support their interpretation, not redefine automated stability or coverage as human ratings.

### 2. Update Table 4 and the shared-settings explanation

| Parameter | Initial | Conservative | Fine-grained | Coarse-grained |
|---|---:|---:|---:|---:|
| Primary UMAP seed | 42 | 42 | 42 | 42 |
| Additional UMAP seeds | 43, 44 | 43, 44 | 43, 44 | 43, 44 |
| UMAP neighbors | 15 | 30 | 15 | 30 |
| UMAP dimensions | 5 | 5 | 5 | 5 |
| UMAP min_dist | 0.0 | 0.1 | 0.0 | 0.1 |
| HDBSCAN min_cluster_size | 15 | 30 | 8 | 60 |
| HDBSCAN min_samples | 5 | 10 | 3 | 15 |

Both models use UMAP/HDBSCAN; it is not applied only to the Legal-BERT representation. The lexical representation is TF-IDF followed by SVD before clustering, not c-TF-IDF computed before classes exist. c-TF-IDF represents topics after clustering in both models. SVD and Legal-BERT representations remain fixed while UMAP seeds vary. Four configurations multiplied by two models and three seeds produced 24 completed fits, not 24 expert-reviewed outputs.

### 3. Correct the temporal-settings explanation

The explanation on PDF page 41 overstates what disabling `evolution_tuning` and `global_tuning` achieves. Suggested replacement:

> Setting evolution_tuning=False and global_tuning=False disables BERTopic's optional temporal and global topic-representation smoothing. The vocabulary, embeddings, and topic assignments are nevertheless obtained from the complete modeling corpus. These settings do not make the analysis a causal, forecasting, or held-out temporal evaluation. Yearly summaries will be interpreted descriptively using the resolved study-year assignments and document-weighted denominators.

### 4. Separate historical EDA from the active modeling dataset

The manuscript mixes a nine-year description (PDF page 27), a ten-year scope, historical PDF-audit counts, and the later model input. The active modeling experiment uses **2016–2025**, 2,118 source documents and 7,832 units from cleaned TXT, with existing human year corrections. It includes 597 fallback documents, 45 additional same-number text variants, and 28 retained date-disagreement flags.

There is also an arithmetic issue in Table 3 (PDF page 38): the displayed Valid rows sum to **2,112**, but the printed Valid total is **2,118**. The displayed 10 misfiled entries plus the row-sum 2,112 equal the printed total 2,122. These historical counts must be reconciled with their own audit sources, not silently overwritten with later modeling counts. Source verification is not the same as expert validation of extracted sections or topic meaning.

Historical Obsidian/LLM/PDF-extraction plans may be described as earlier stages where supported, but must not be presented as active dependencies of the clean-TXT modeling run. The revised expert section does not rewrite those upstream procedures or assume they were all executed as originally proposed.

### 5. Keep results and topic identities version-specific

The table on PDF page 41 reports Initial-run metrics (202 lexical and 159 semantic topics), not the selected Conservative expert-review outputs (107 and 64). Preserve it only as a clearly labeled historical result or replace the results presentation in Chapter 4 with the completed four-configuration evidence. Do not insert expert-rating columns containing inferred values.

The earlier Chapter 4 topic figures and draft titles must not be reused as if their topic IDs belonged to the Conservative runs. The selected-run packets will need their own verified draft labels and source references. The four-configuration findings already explain why Conservative is provisional and why the highest C_v is not automatically the selected setting.

### 6. Preserve future tense and ethical status

The automated experiment is completed; expert recruitment and review are not. Use future tense for sampling, recruitment, distribution, scoring, agreement analysis, and feedback procedures. “Validated topics” in planned outputs should be qualified as topics that will be reviewed, not a present assertion that all topics are validated. Retain the original informed-consent, voluntary-participation, confidentiality, and institutional-approval requirements.

## Scope of this revision

The PDFs in Downloads have not been overwritten. No editable manuscript source was supplied, so the deliverables provide replacement text and editable/printable review documents for integration into the actual thesis source. No participants, survey responses, agreement coefficients, expert endorsements, completed human procedures, or new empirical acceptance thresholds have been invented. References (9; 13; 15) in the replacement text are already in the supplied thesis bibliography; their numbering should be reconciled when the manuscript is edited.
