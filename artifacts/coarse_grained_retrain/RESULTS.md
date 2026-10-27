# Fresh coarse-grained retraining

Completed 6 fresh fits; seeds [42, 43, 44]; primary seed 42.
Unchanged corpus: 2,118 source documents / 7,832 model units.
Fresh lexical representation and frozen Legal-BERT inference; no prior embedding cache reused. Legal-BERT was not fine-tuned.

| Model | Topics | C_v | Unit coverage | Mean aligned seed stability |
|---|---:|---:|---:|---:|
| Lexical | 49 | 0.7927 | 85.89% | 0.8548 |
| Legal-BERT | 36 | 0.8433 | 89.43% | 0.9064 |

Coarse-grained selected by the research team for the active broad-theme analysis. This is a study decision, not proof of superiority or expert validation. Conservative results are retained unchanged as historical evidence.

Temporal titles are keyword-derived drafts, not expert-approved categories. Procedural, mixed and OCR-heavy topics remain visible.
Annual shares are document-weighted, include outliers, and describe the eligible archive, not all city legislation. Only 32 documents represent 2025.

The temporal renderer records `models_rerun: false` because rendering does not train models. This report records the separate fresh retraining and binds its evidence by SHA-256.
Historical Conservative artifacts are preserved unchanged. Their labels and expert-review scope do not validate the new coarse-grained outputs.

Measured total run wall time: 1008.44 seconds.
No expert scores, predictive accuracy, causal trend claims, or external validation are inferred.
