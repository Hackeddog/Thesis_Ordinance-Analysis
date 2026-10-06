# Clean-text full-corpus initial results

Full eligible cleaned-TXT corpus, not a sample. Source verification is user-confirmed; duplicate, year and extraction audits are reported separately. Intrinsic in-sample results and joint parameter sensitivity, not a held-out model winner or expert validation.

```csv
model,sections,topics_excluding_outliers,outlier_sections,outlier_fraction,topic_diversity,section_npmi,npmi_topics_scored,cv_coherence,cv_note,cv_excluded_phrase_terms,topic_coverage,stability_ari_mean,trial,fit_evaluation_seconds,neighbors,min_dist,min_cluster_size,min_samples
lexical,7832,202,744,0.0949948927477017,0.4694290045477514,0.4966922226322597,202,0.7881963346372433,c_v on unigram topic terms only; this run uses a shared unigram vocabulary,0,0.9050051072522982,0.5304985426347679,initial,123.10015289997682,15,0.0,15,5
semantic,7832,159,1323,0.1689223697650664,0.4919093851132686,0.4590794544949825,159,0.7812564405202568,c_v on unigram topic terms only; this run uses a shared unigram vocabulary,0,0.8310776302349336,0.5736626135282662,initial,101.87820630008356,15,0.0,15,5
lexical,7832,107,1038,0.1325331971399387,0.5688509021842355,0.498245577805617,107,0.7960078467872019,c_v on unigram topic terms only; this run uses a shared unigram vocabulary,0,0.8674668028600613,0.6110451103877009,conservative,100.175271499902,30,0.1,30,10
semantic,7832,64,670,0.0855464759959142,0.512,0.5164796216827772,64,0.8171384684123674,c_v on unigram topic terms only; this run uses a shared unigram vocabulary,0,0.9144535240040856,0.8558821310521992,conservative,82.71693899994716,30,0.1,30,10
```

No source TXT files were modified. See evidence/ for hashes, per-file audit and source-linked excerpts.
