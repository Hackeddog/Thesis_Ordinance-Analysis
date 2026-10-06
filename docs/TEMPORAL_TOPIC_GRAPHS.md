# Temporal-only topic graphs and descriptive titles

## Open the outputs

Under `artifacts/temporal_topics/`:

- `Temporal_Topic_Summaries.pdf`: eight temporal-only graph pages.
- `Temporal_Topic_Summaries.pptx`: graph-only slides for reuse in the presentation.
- `figures/`: eight high-resolution PNGs, four for each model.
- `tables/all_topic_titles.csv`: titles, keywords, labeling method, category and temporal statistics for all 361 non-outlier model-local topics (202 lexical; 159 semantic).
- `tables/selected_topic_temporal_summaries.csv`: peak year(s), 2025 shares and 2016–2025 changes for plotted topic selections.
- `tables/*_labeled_temporal_data.csv`: complete source temporal observations joined to titles.
- `manifest.json`: source hashes, denominator, selection policy and confirmation that the models were not rerun.

These reuse the **initial configuration** of the completed clean-text full-corpus experiment. No new training, topic merging, source modification or manual numerical adjustment is performed.

## Four graphs per model

1. **Leading-topic heatmap:** top eight clusters by their summed fractional-document contributions across 2016–2025. Both heatmaps use the same numeric color limits.
2. **Leading-topic trajectories:** one line panel per leading cluster, with a draft title, its supporting words and peak-share annotation.
3. **Selected interpretable trajectories:** policy/governance labels only, taking the largest cluster per repeated title. This is a disclosed subset—not a replacement for the leading-cluster view and not a merge of clusters with similar titles.
4. **Yearly composition:** the leading topics, other assigned topics and outliers. Every year's column sums to 100%; yearly document counts are displayed.

All graphs have a temporal axis. There are no model-quality bar charts, word clouds or static topic-size plots in this graph package.

## What the topic titles mean

Titles are **draft descriptive aids**, not expert ratings or proof that a cluster forms a single legally coherent policy category.

The leading clusters received keyword-grounded labels checked against representative source excerpts, recorded in `configs/temporal_topic_titles.json`. Overrides require specified supporting words to exist in that exact model/topic's keyword list; incompatible results fail rather than silently inheriting a label.

Other titles use deterministic, rank-weighted keyword rules requiring at least two supporting terms. The full keyword list, matched terms and label method are retained in the catalog. Unclear or OCR-dominated words are labeled as such instead of being assigned an invented policy meaning. Mixed clusters remain mixed; for example, the cluster combining vehicle, DQR, establishment and single-use-product terms is not presented as purely a plastics-policy topic.

Examples:

| Clustered words | Draft descriptive title |
|---|---|
| calamity, fund, assistance | Disaster relief and calamity funding |
| street, closure, traffic | Temporary road closures and traffic control |
| zoning, reclassification, land | Land-use zoning and reclassification |
| contract, powers, executive | Mayoral contracting powers |
| memorandum, agreement, authorizing | Agreements and mayoral authorization |

Procedural and OCR-heavy clusters remain in the leading-topic charts when they rank highly. The separate interpretable subset must not be used to conceal their presence in the model output. Expert review is still needed for **all** titles, including rule-generated policy/governance labels.

## Temporal calculation

For source document d and topic t:

`document_topic_share(d,t) = units of d assigned to t / all modeled units of d`

For year y:

`yearly_share(t,y) = sum(document_topic_share(d,t) for d in y) / source_documents(y)`

Thus every source document contributes total weight 1 across its topics and outliers. Longer documents do not automatically dominate because they contain more extracted units. This does not collapse differing text versions that share an ordinance number.

The denominator includes outliers. An absent topic-year cell is zero only when that year has an observed corpus; the generator rejects missing years or inconsistent denominators. The graphs describe the eligible archive, not every ordinance enacted by the city. In particular, 2025 has only 32 included source documents.

The ranking uses summed fractional-document weights, **not** the unweighted sum of yearly percentages, which would over-weight years with small corpora. Peak-year and endpoint summaries are descriptive; they do not establish statistical significance, policy causation or reliable emergence/decline outside this archive.

Topic IDs are local to each model. Identical titles across models suggest a similar keyword interpretation, not an established one-to-one cluster alignment.

## Regenerate

```powershell
.\.venv\Scripts\python.exe scripts/build_temporal_graphs.py --output artifacts/temporal_topics_rerender
.\.venv\Scripts\python.exe -m pytest tests/test_temporal_graphs.py -q
```

A new output path is required to preserve earlier outputs. Input defaults to the committed compact evidence in `artifacts/clean_text_full/evidence`, so the graphs can be rebuilt without the large embedding cache. `--top-n` accepts 1–8. Draft-title rules must be re-reviewed for a different clustering run; topic numbers are not portable between runs.
