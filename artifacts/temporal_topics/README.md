# Temporal topic graphs

Eight temporal-only PNGs, an eight-page PDF, and a graph-only PowerPoint. These summarize completed **Conservative · seed 42** results for both models; no models were retrained during rendering.

Parameters: `{"min_cluster_size": 30, "min_dist": 0.1, "min_samples": 10, "neighbors": 30, "umap_components": 5}`.

All 171 non-outlier topics are included in the tables: 107 lexical and 64 semantic. Figures show selected topics, not one figure for every topic.

Run identity and input hashes are recorded in manifest.json. Topic-ID overrides are scoped to this run's keyword fingerprints; Initial topic labels are not carried over. Labels are keyword-based drafts, not expert validation or source-excerpt review.

- Leading-topic heatmaps and trajectories retain procedural/OCR-heavy topics when they rank highly.
- Interpretable trajectories are a disclosed policy/governance subset: the largest cluster per draft title, not a merging of clusters.
- Yearly composition retains other assigned topics and outliers so every year totals 100%.
- tables/all_topic_titles.csv lists all model-local topics and their keyword-based draft titles.
- tables/selected_topic_temporal_summaries.csv records peak year(s), endpoint shares and descriptive change.

Shares are document-weighted. Source documents, not all city ordinances, form the denominator. Titles are descriptive aids, not expert-approved categories. Equal titles across models do not establish alignment. Source verification does not make OCR/procedural clusters substantive policy themes.
