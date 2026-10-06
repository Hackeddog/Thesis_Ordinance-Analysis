"""Shared lexical/semantic clustering and intrinsic evaluation for clean-text units.

Extracted from the prior tested model implementation; no archival-format loader.
"""
import itertools
import json
import logging
import re
import numpy as np
import pandas as pd
LOG = logging.getLogger("clean-model")


def build_vocabulary(docs, args):
    from sklearn.feature_extraction.text import CountVectorizer, ENGLISH_STOP_WORDS
    stop = set(ENGLISH_STOP_WORDS) if args.stopwords == "english" else set()
    if args.extra_stopwords:
        stop.update(s.strip().lower() for s in args.extra_stopwords.read_text(encoding="utf-8").splitlines()
                    if s.strip() and not s.lstrip().startswith("#"))
    common = dict(lowercase=True, strip_accents="unicode", stop_words=sorted(stop) or None,
                  ngram_range=(1, args.ngram_max), token_pattern=r"(?u)\b[a-zA-Z][a-zA-Z]+\b")
    vectorizer = CountVectorizer(**common, min_df=args.min_df, max_df=args.max_df,
                                 max_features=args.max_features)
    try:
        counts = vectorizer.fit_transform(docs)
    except ValueError as exc:
        raise ValueError(f"Cannot build vocabulary: {exc}. Review text, stopwords, and --min-df.") from exc
    if counts.shape[1] < 2:
        raise ValueError("Fewer than two usable vocabulary terms remain.")
    empty = np.flatnonzero(np.asarray(counts.sum(axis=1)).ravel() == 0)
    if len(empty):
        raise ValueError(f"{len(empty)} sections have no retained terms (data rows {(empty[:10]+1).tolist()}); "
                         "review them or lower --min-df. No rows have been silently removed.")
    # Freeze document-derived vocabulary so c-TF-IDF does not refilter it by cluster frequency.
    frozen = dict(common, vocabulary=vectorizer.vocabulary_)
    return counts, vectorizer.get_feature_names_out(), frozen


def lexical_vectors(counts, args):
    """Create document-level lexical vectors for clustering.

    c-TF-IDF is class-based and therefore cannot be computed before an initial
    clustering assignment. The lexical branch uses TF-IDF/SVD for that initial
    assignment, then applies the same BERTopic c-TF-IDF topic representation as
    the embedding branch.
    """
    from sklearn.decomposition import TruncatedSVD
    from sklearn.feature_extraction.text import TfidfTransformer
    from sklearn.preprocessing import normalize
    tfidf = TfidfTransformer(norm="l2", use_idf=True, smooth_idf=True).fit_transform(counts)
    components = min(args.svd_components, counts.shape[0] - 1, counts.shape[1] - 1)
    if components < 1:
        raise ValueError("Insufficient rows or vocabulary for TruncatedSVD.")
    svd = TruncatedSVD(n_components=components, random_state=args.seed)
    vectors = normalize(svd.fit_transform(tfidf)).astype("float32")
    return vectors, {"svd_components_actual": components,
                     "svd_explained_variance_ratio_sum": float(svd.explained_variance_ratio_.sum())}


def keyword_metrics(topic_words, counts, terms, top_n):
    """Intrinsic diagnostics only. NPMI uses whole-section binary co-occurrence, not sliding windows."""
    lists = [[w for w in words[:top_n] if w] for topic, words in topic_words.items() if topic != -1]
    flat = list(itertools.chain.from_iterable(lists))
    diversity = len(set(flat)) / len(flat) if flat else None
    term_index = {word: i for i, word in enumerate(terms)}
    selected = sorted({term_index[w] for w in flat if w in term_index})
    if not selected:
        return {"topic_diversity": diversity, "section_npmi": None, "npmi_topics_scored": 0}
    presence = (counts[:, selected] > 0).astype(np.float64)
    joint = (presence.T @ presence).toarray() / counts.shape[0]
    local = {str(terms[col]): i for i, col in enumerate(selected)}
    topic_scores = []
    for words in lists:
        scores = []
        for a, b in itertools.combinations(dict.fromkeys(words), 2):
            if a not in local or b not in local:
                continue
            i, j = local[a], local[b]
            pij, pi, pj = joint[i, j], joint[i, i], joint[j, j]
            if pij == 0:
                scores.append(-1.0)
            elif pij >= 1 - 1e-12:
                scores.append(0.0)  # ubiquitous pair has no discriminative information
            else:
                scores.append(float(np.log(pij / (pi * pj)) / -np.log(pij)))
        if scores:
            topic_scores.append(float(np.mean(scores)))
    return {"topic_diversity": diversity, "section_npmi": float(np.mean(topic_scores)) if topic_scores else None,
            "npmi_topics_scored": len(topic_scores)}


def cv_coherence(topic_words, docs, top_n):
    """Calculate c_v coherence when gensim is available; return None otherwise."""
    topics = [[word for word in words[:top_n] if word] for topic, words in topic_words.items()
              if topic != -1 and words]
    if not topics:
        return None
    try:
        from gensim.corpora import Dictionary
        from gensim.models.coherencemodel import CoherenceModel
        tokenized = [re.findall(r"[a-zA-Z]{2,}", doc.lower()) for doc in docs]
        dictionary = Dictionary(tokenized)
        topics = [[word for word in topic if word in dictionary.token2id] for topic in topics]
        topics = [topic for topic in topics if len(topic) >= 2]
        if not topics:
            return None
        return float(CoherenceModel(topics=topics, texts=tokenized, dictionary=dictionary,
                                    coherence="c_v", processes=1).get_coherence())
    except Exception as exc:
        LOG.warning("Could not calculate c_v coherence: %s", exc)
        return None


def clustering_stability(vectors, primary_labels, args):
    """Estimate label stability over independent UMAP/HDBSCAN seeds."""
    from sklearn.metrics import adjusted_rand_score
    if args.stability_runs <= 1:
        return None
    from hdbscan import HDBSCAN
    from umap import UMAP
    scores = []
    for run in range(1, args.stability_runs):
        reducer = UMAP(n_neighbors=min(args.neighbors, len(vectors) - 1),
                       n_components=min(args.umap_components, len(vectors) - 2),
                       min_dist=args.min_dist, metric="cosine", init="random",
                       random_state=args.seed + run, n_jobs=1)
        clusterer = HDBSCAN(min_cluster_size=args.min_cluster_size, min_samples=args.min_samples,
                            metric="euclidean", cluster_selection_method="eom",
                            prediction_data=False, core_dist_n_jobs=1)
        labels = clusterer.fit_predict(reducer.fit_transform(vectors))
        scores.append(float(adjusted_rand_score(primary_labels, labels)))
    return float(np.mean(scores)) if scores else None


def yearly_prevalence(df, labels):
    assignments = df.assign(topic=np.asarray(labels, dtype=int))
    observed = assignments.groupby(["year", "topic"]).size()
    # Explicit zeroes for every model topic in every observed year.
    index = pd.MultiIndex.from_product([sorted(df.year.unique()), sorted(set(labels))], names=["year", "topic"])
    out = observed.reindex(index, fill_value=0).rename("section_count").reset_index()
    out["total_sections_in_year"] = out.year.map(df.groupby("year").size())
    out["section_share"] = out.section_count / out.total_sections_in_year
    return out


def json_write(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False, default=str), encoding="utf-8")


def fit_branch(name, vectors, df, counts, terms, frozen, args, meta):
    from sklearn.feature_extraction.text import CountVectorizer
    from bertopic import BERTopic
    from bertopic.vectorizers import ClassTfidfTransformer
    from scipy import sparse

    class FiniteClassTfidfTransformer(ClassTfidfTransformer):
        """Prevent zero-frequency vocabulary columns from producing infinity."""
        def fit(self, X, multiplier=None):
            with np.errstate(divide="ignore", invalid="ignore"):
                result = super().fit(X, multiplier=multiplier)
            diagonal = np.asarray(self._idf_diag.diagonal()).ravel()
            diagonal[~np.isfinite(diagonal)] = 0.0
            self._idf_diag = sparse.diags(diagonal, offsets=0,
                                          shape=(len(diagonal), len(diagonal)), format="csr")
            return result
    from hdbscan import HDBSCAN
    from umap import UMAP
    out = args.output / name
    out.mkdir(parents=True, exist_ok=True)
    docs = df.text.tolist()
    if not np.isfinite(vectors).all() or np.any(np.linalg.norm(vectors, axis=1) < 1e-10):
        raise ValueError(f"{name} produced a non-finite or zero-length vector.")
    reducer = UMAP(n_neighbors=min(args.neighbors, len(df) - 1),
                   n_components=min(args.umap_components, len(df) - 2),
                   min_dist=args.min_dist, metric="cosine", init="random", random_state=args.seed, n_jobs=1)
    clusterer = HDBSCAN(min_cluster_size=args.min_cluster_size, min_samples=args.min_samples,
                        metric="euclidean", cluster_selection_method="eom", prediction_data=True,
                        core_dist_n_jobs=1)
    model = BERTopic(embedding_model=None, umap_model=reducer, hdbscan_model=clusterer,
                    vectorizer_model=CountVectorizer(**frozen),
                    ctfidf_model=FiniteClassTfidfTransformer(bm25_weighting=False, reduce_frequent_words=False),
                    top_n_words=args.top_words, calculate_probabilities=False, verbose=True)
    labels, strengths = model.fit_transform(docs, embeddings=vectors)
    labels = np.asarray(labels, dtype=int)
    assignments = df.copy()
    assignments["topic"] = labels
    assignments["is_outlier"] = labels == -1
    if strengths is not None and np.asarray(strengths).ndim == 1:
        assignments["membership_strength"] = strengths  # not calibrated semantic confidence
    assignments.to_csv(out / "section_topics.csv", index=False)
    # Persist vector-to-section/year associations so embeddings are auditable and reusable.
    vector_metadata = assignments[[col for col in ["ordinance_id", "section_id", "year", "source_file",
                                                    "topic", "is_outlier"]
                                   if col in assignments]].copy()
    vector_metadata.insert(0, "vector_row", np.arange(len(assignments)))
    vector_metadata.to_csv(out / "vector_metadata.csv", index=False)
    np.save(out / "section_vectors.npy", vectors)
    np.savez_compressed(out / "vector_store.npz", vectors=vectors,
                        years=df.year.to_numpy(dtype=np.int32),
                        vector_row=np.arange(len(df), dtype=np.int32))
    info = model.get_topic_info().copy()
    for col in info.columns:
        info[col] = info[col].map(lambda v: json.dumps(v.tolist() if isinstance(v, np.ndarray) else v, ensure_ascii=False) if isinstance(v, (list, tuple, dict, np.ndarray)) else v)
    info.to_csv(out / "topics.csv", index=False)
    words, keyword_rows = {}, []
    for topic in sorted(set(labels.tolist())):
        pairs = [(w, float(score)) for w, score in (model.get_topic(topic) or []) if w]
        words[topic] = [w for w, score in pairs]
        keyword_rows.extend({"topic": topic, "rank": rank, "term": w, "ctfidf_weight": score}
                            for rank, (w, score) in enumerate(pairs, 1))
    pd.DataFrame(keyword_rows, columns=["topic", "rank", "term", "ctfidf_weight"]).to_csv(out / "topic_keywords.csv", index=False)
    representative_rows = []
    for topic in sorted(set(labels.tolist()) - {-1}):
        # Select actual assigned rows, preserving provenance even when text is repeated.
        ranked = assignments[assignments.topic == topic]
        if "membership_strength" in ranked:
            ranked = ranked.sort_values("membership_strength", ascending=False)
        for rank, row in enumerate(ranked.head(3).to_dict("records"), 1):
            representative_rows.append({"rank": rank, **row})
    pd.DataFrame(representative_rows, columns=["rank"] + assignments.columns.tolist()).to_csv(out / "representative_sections.csv", index=False)
    review_rows = []
    for topic in sorted(set(labels.tolist()) - {-1}):
        ranked = assignments[assignments.topic == topic]
        review_rows.append({
            "topic": topic,
            "keywords": "; ".join(words.get(topic, [])[:args.top_words]),
            "section_count": len(ranked),
            "representative_sections": "; ".join((ranked.ordinance_id.astype(str) + "/" + ranked.section_id.astype(str)).head(3)),
            "legal_label": "",
            "legal_relevance_1_to_5": "",
            "legal_coherence_1_to_5": "",
            "label_appropriateness_1_to_5": "",
            "temporal_interpretation_1_to_5": "",
            "overall_quality_1_to_5": "",
            "legal_notes": "",
        })
    pd.DataFrame(review_rows, columns=["topic", "keywords", "section_count",
                                       "representative_sections", "legal_label",
                                       "legal_relevance_1_to_5", "legal_coherence_1_to_5",
                                       "label_appropriateness_1_to_5", "temporal_interpretation_1_to_5",
                                       "overall_quality_1_to_5", "legal_notes"]).to_csv(out / "expert_review_template.csv", index=False)
    prevalence = yearly_prevalence(df, labels)
    prevalence.to_csv(out / "yearly_prevalence.csv", index=False)
    if len(set(labels) - {-1}) and df.year.nunique() >= 2:
        try:
            temporal = model.topics_over_time(
                docs, timestamps=pd.to_datetime(df.year.astype(str) + "-01-01").tolist(),
                evolution_tuning=False, global_tuning=False)
        except Exception as exc:
            LOG.warning("Could not calculate topics over time for %s: %s", name, exc)
            temporal = pd.DataFrame()
    else:
        temporal = pd.DataFrame()
    temporal.to_csv(out / "yearly_topic_keywords.csv", index=False)
    np.save(out / "umap_vectors.npy", reducer.embedding_)
    model_metrics = keyword_metrics(words, counts, terms, args.top_words)
    model_metrics["cv_coherence"] = cv_coherence(words, docs, args.top_words)
    model_metrics["cv_note"] = "c_v on unigram topic terms only; this run uses a shared unigram vocabulary"
    model_metrics["cv_excluded_phrase_terms"] = sum(" " in w for t, ws in words.items() if t != -1 for w in ws[:args.top_words])
    model_metrics["topic_coverage"] = float((labels != -1).mean())
    model_metrics["stability_ari_mean"] = clustering_stability(vectors, labels, args)
    metrics = {"model": name, "sections": len(df), "topics_excluding_outliers": len(set(labels) - {-1}),
               "outlier_sections": int((labels == -1).sum()), "outlier_fraction": float((labels == -1).mean()),
               **model_metrics}
    json_write(out / "metrics.json", metrics)
    json_write(out / "model_metadata.json", meta)
    if metrics["topics_excluding_outliers"] == 0:
        LOG.warning("%s produced only outliers. Do not interpret outliers as a substantive topic.", name)
    if not args.skip_html:
        from plotly import express as px
        plot_data = prevalence.copy()
        plot_data["topic"] = plot_data.topic.map(lambda t: "Outliers (-1)" if t == -1 else f"Topic {t}")
        fig = px.line(plot_data, x="year", y="section_share", color="topic", markers=True,
                      title=f"{name}: yearly section-level topic prevalence",
                      labels={"section_share": "Share of all sections in year"})
        fig.update_xaxes(dtick=1)
        fig.write_html(str(out / "yearly_trends.html"), include_plotlyjs=True)
    return labels, metrics
