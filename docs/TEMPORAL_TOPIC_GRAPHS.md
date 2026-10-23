# Temporal-only topic graphs and descriptive titles

## Open the outputs

Under `artifacts/temporal_topics/`:

- `Temporal_Topic_Summaries.pdf`: eight temporal-only graph pages.
- `Temporal_Topic_Summaries.pptx`: graph-only slides for reuse in the presentation.
- `figures/`: eight high-resolution PNGs, four for each model.
- `tables/all_topic_titles.csv`: titles, keywords, labeling method, category and temporal statistics for all 171 non-outlier model-local topics (107 lexical; 64 semantic).
- `tables/selected_topic_temporal_summaries.csv`: peak year(s), 2025 shares and 2016–2025 changes for plotted topic selections.
- `tables/*_labeled_temporal_data.csv`: complete source temporal observations joined to titles.
- `manifest.json`: configuration, seed, parameters, topic counts, source hashes, denominator, selection policy and confirmation that the models were not rerun.

These reuse **Conservative, seed 42, for both models**, from the completed four-configuration experiment. The completed full-run temporal tables, keywords and metrics were checked byte-for-byte against the compact evidence before rendering. No new training, topic merging, source modification or manual numerical adjustment is performed.

| Parameter | Value |
|---|---:|
| UMAP n_neighbors | 30 |
| UMAP n_components | 5 |
| UMAP min_dist | 0.1 |
| HDBSCAN min_cluster_size | 30 |
| HDBSCAN min_samples | 10 |

Each figure explicitly identifies Conservative and seed 42. Long-form tables and topic catalogs also carry configuration and seed columns; wide yearly-mix tables inherit the run identity in the package manifest. Conservative remains a provisional selection, pending expert validation.

The previous **Initial** package (202 lexical and 159 semantic topics) is preserved unchanged in `artifacts/temporal_topics_initial/`. It is historical evidence, not the selected-run package. The current figures are selected-topic views; the tables include every topic, not only those plotted.

## Four graphs per model

1. **Leading-topic heatmap:** top eight clusters by their summed fractional-document contributions across 2016–2025. Both heatmaps use the same numeric color limits.
2. **Leading-topic trajectories:** one line panel per leading cluster, with a draft title, its supporting words and peak-share annotation.
3. **Selected interpretable trajectories:** policy/governance labels only, taking the largest cluster per repeated title. This is a disclosed subset—not a replacement for the leading-cluster view and not a merge of clusters with similar titles.
4. **Yearly composition:** the leading topics, other assigned topics and outliers. Every year's column sums to 100%; yearly document counts are displayed.

All graphs have a temporal axis. There are no model-quality bar charts, word clouds or static topic-size plots in this graph package.

## What the topic titles mean

Titles are **draft descriptive aids**, not expert ratings or proof that a cluster forms a single legally coherent policy category.

Conservative-specific keyword-only overrides are recorded in `configs/temporal_topic_titles_conservative.json`. They are bound to the configuration, seed and exact keyword-file hashes. Required supporting words must exist in that model/topic's keyword list. These overrides are labeled `draft_keyword_review`: no new source-excerpt review or expert validation is claimed. The Initial overrides in `configs/temporal_topic_titles.json` are historical and are not reused.

Other titles use deterministic, rank-weighted keyword rules requiring at least two supporting terms. The full keyword list, matched terms and label method are retained in the catalog. Unclear or OCR-dominated words are labeled as such instead of being assigned an invented policy meaning. Mixed clusters remain mixed: lexical topic 18 combines establishment, DQR, vehicle and single-use-product terms; semantic topic 0 is broad administrative/regulatory wording; semantic topic 24 combines amusement and trade-event exemptions. None is presented as a single narrow policy theme.

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

A new output path is required to preserve earlier outputs. Input defaults to the committed compact evidence in `artifacts/four_configuration_tuning/evidence/conservative`, with labels from `configs/temporal_topic_titles_conservative.json`, so the graphs can be rebuilt without the large embedding cache or retraining. The generator checks the completed report's source hashes and verifies both models' measured configuration, seed and parameters before creating output. `--top-n` accepts 1–8.

For another tuning configuration, provide `--source` pointing to that configuration's compact evidence and `--titles` pointing to a separately reviewed, run-scoped title configuration with matching keyword hashes. Topic numbers and Initial overrides are not portable between runs. The untouched Initial package remains available for historical comparisons.
