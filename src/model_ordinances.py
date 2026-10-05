#!/usr/bin/env python3
"""Compare a Legal-BERT embedding path with a lexical TF-IDF/c-TF-IDF path.

The unit of analysis is an ordinance section. Markdown input is the generated
Obsidian YAML export from the EDA pipeline; CSV input must contain one row per
section. Both branches cluster document representations with UMAP/HDBSCAN and
use class-based c-TF-IDF for comparable topic-word representations.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import itertools
import json
import logging
import random
import re
from pathlib import Path

import numpy as np
import pandas as pd
SECTION_HEADER_RE = re.compile(r"^\s*SECTION\s+([0-9]+[A-Za-z]?)\s*[.:]?\s*(.*)$", re.IGNORECASE | re.MULTILINE)
FRONTMATTER_BOUNDARY_RE = re.compile(r"^---\s*$")

LOG = logging.getLogger("ordinance-modeling")


def arguments():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--input", required=True, type=Path, help="Markdown ordinance, recursive Markdown directory, or section CSV")
    p.add_argument("--input-format", choices=["auto", "markdown", "csv"], default="auto")
    p.add_argument("--prepare-only", action="store_true", help="Export parsed sections and input audit without fitting models")
    p.add_argument("--include-temporal-status", default="valid", help="Comma-separated allowed YAML temporal_status values")
    p.add_argument("--require-verified", action="store_true", help="Require YAML verification_status: verified")
    p.add_argument("--strict-section-count", action="store_true", help="Exclude notes with declared/detected count mismatch")
    p.add_argument("--allow-excluded", action="store_true", help="Explicitly permit training despite excluded notes")
    p.add_argument("--output", type=Path, default=Path("results"))
    p.add_argument("--text-column", default="text")
    p.add_argument("--ordinance-column", default="ordinance_id")
    p.add_argument("--section-column", default="section_id")
    p.add_argument("--year-column", default="year")
    p.add_argument("--models", choices=["both", "semantic", "lexical"], default="both")
    p.add_argument("--encoder", default="nlpaueb/legal-bert-base-uncased")
    p.add_argument("--device", default="auto", help="auto, cpu, cuda, cuda:0, or mps")
    p.add_argument("--batch-size", type=int, default=8)
    p.add_argument("--max-tokens", type=int, default=512)
    p.add_argument("--svd-components", type=int, default=100)
    p.add_argument("--neighbors", type=int, default=15)
    p.add_argument("--umap-components", type=int, default=5)
    p.add_argument("--min-cluster-size", type=int, default=10)
    p.add_argument("--min-samples", type=int, default=5)
    p.add_argument("--min-df", type=int, default=2)
    p.add_argument("--max-df", type=float, default=1.0)
    p.add_argument("--max-features", type=int, default=50000)
    p.add_argument("--ngram-max", type=int, default=2)
    p.add_argument("--top-words", type=int, default=10)
    p.add_argument("--stability-runs", type=int, default=3,
                   help="Additional UMAP/HDBSCAN runs used to estimate clustering stability")
    p.add_argument("--stopwords", choices=["english", "none"], default="english")
    p.add_argument("--extra-stopwords", type=Path, help="Optional UTF-8 file, one token per line")
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--validate-only", action="store_true", help="Check input without loading modeling dependencies")
    p.add_argument("--skip-html", action="store_true")
    return p.parse_args()


def _allowed_statuses(args):
    return {value.strip() for value in args.include_temporal_status.split(",") if value.strip()}


def _parse_frontmatter(markdown, path):
    """Read YAML frontmatter without treating the body as YAML."""
    lines = markdown.splitlines()
    if not lines or not FRONTMATTER_BOUNDARY_RE.match(lines[0]):
        raise ValueError(f"{path} has no YAML frontmatter")
    try:
        end = next(i for i in range(1, len(lines)) if FRONTMATTER_BOUNDARY_RE.match(lines[i]))
    except StopIteration as exc:
        raise ValueError(f"{path} has an unterminated YAML frontmatter block") from exc
    try:
        import yaml
        data = yaml.safe_load("\n".join(lines[1:end])) or {}
    except ImportError as exc:
        raise RuntimeError("Markdown input requires PyYAML; install it from requirements.txt") from exc
    except Exception as exc:
        raise ValueError(f"Invalid YAML frontmatter in {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError(f"YAML frontmatter in {path} must be a mapping")
    return data, "\n".join(lines[end + 1:])


def _markdown_sections(body):
    """Extract explicit SECTION blocks from an exported Obsidian ordinance note."""
    marker = re.search(r"(?im)^##\s+Cleaned text\s*$", body)
    text = body[marker.end():] if marker else body
    # Large generated notes may contain only a preview and point to the full
    # cleaned text file. Prefer the full source when it is still available.
    external = re.search(r"Full text:\s*`([^`]+)`", text, re.IGNORECASE)
    if external:
        external_path = Path(external.group(1))
        if external_path.exists():
            text = external_path.read_text(encoding="utf-8")
    text = re.sub(r"(?m)^```.*$", "", text).strip()
    # Ignore a table of contents. The operative ordinance normally begins
    # after the introductory "Be it ordained" clause.
    operative = re.search(r"\bbe\s+it\s+ordained\b", text, re.IGNORECASE)
    if operative:
        text = text[operative.start():]
    matches = list(SECTION_HEADER_RE.finditer(text))
    sections = []
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        heading = match.group(2).strip()
        content = " ".join(part.strip() for part in text[match.end():end].splitlines())
        section_text = " ".join(part for part in (heading, content) if part).strip()
        section_text = re.sub(r"\s+", " ", section_text)
        # Bare OCR headings and page furniture are not modelable sections.
        if len(section_text) >= 20:
            sections.append((f"section_{match.group(1)}", section_text))
    return sections


def _year_from_metadata(metadata, path):
    value = metadata.get("corpus_year") or metadata.get("resolved_year") or metadata.get("year")
    if value is None and metadata.get("date_enacted"):
        value = str(metadata["date_enacted"])[:4]
    if value is None:
        match = re.search(r"(?:^|[\\/])((?:19|20)\d{2})(?:[\\/]|$)", str(path))
        value = match.group(1) if match else None
    try:
        year = int(float(value))
    except (TypeError, ValueError):
        raise ValueError(f"No valid corpus year found for {path}")
    if not 1678 <= year <= 2261:
        raise ValueError(f"Invalid corpus year {year} in {path}")
    return year


def _apply_metadata_filters(df, args):
    """Apply corpus curation decisions before either model sees a section."""
    if args.strict_section_count:
        if "section_count" not in df:
            raise ValueError("--strict-section-count requires section_count metadata in CSV input")
        declared = pd.to_numeric(df["section_count"], errors="coerce")
        if declared.isna().any():
            raise ValueError("section_count contains a non-numeric value")
        detected = df.groupby("ordinance_id")["section_id"].transform("count")
        mismatch = declared.astype(int) != detected
        if mismatch.any():
            bad = df.loc[mismatch, "ordinance_id"].drop_duplicates().head(10).tolist()
            raise ValueError(f"Declared/detected section count mismatch for ordinances: {bad}")
    allowed = _allowed_statuses(args)
    if "temporal_status" in df:
        excluded = ~df["temporal_status"].isin(allowed)
        if excluded.any():
            LOG.warning("Excluding %s sections with temporal status outside %s", int(excluded.sum()), sorted(allowed))
            df = df.loc[~excluded].copy()
    elif args.include_temporal_status != "valid":
        raise ValueError("--include-temporal-status requires a temporal_status column in CSV input")
    if args.require_verified:
        if "verification_status" not in df:
            raise ValueError("--require-verified requires verification_status metadata")
        verified = df["verification_status"].str.lower().eq("verified")
        if (~verified).any():
            LOG.warning("Excluding %s unverified sections", int((~verified).sum()))
            df = df.loc[verified].copy()
    return df


def load_markdown_sections(args):
    """Load generated Obsidian ordinance notes as section-level records."""
    paths = [args.input] if args.input.is_file() else sorted(args.input.rglob("*.md"))
    rows, audits, manifest = [], [], []
    allowed = _allowed_statuses(args)
    for path in paths:
        if path.name.startswith("_"):
            continue
        try:
            markdown = path.read_text(encoding="utf-8-sig")
            metadata, body = _parse_frontmatter(markdown, path)
            status = str(metadata.get("temporal_status", "unknown"))
            ordinance_id = str(metadata.get("ordinance_number") or metadata.get("ordinance_id") or path.stem).strip()
            year = _year_from_metadata(metadata, path)
            sections = _markdown_sections(body)
            declared = metadata.get("section_count")
            declared_count = int(declared) if declared not in (None, "", "null") else None
            warnings = []
            if declared_count is not None and declared_count != len(sections):
                warnings.append(f"declared section_count={declared_count}, detected={len(sections)}")
            if not sections:
                raise ValueError("no explicit SECTION blocks detected")
            section_ids = [section_id for section_id, _ in sections]
            if len(section_ids) != len(set(section_ids)):
                raise ValueError("duplicate section identifiers detected; review OCR/section parsing")
            if args.strict_section_count and warnings:
                raise ValueError(warnings[0])
            if status not in allowed:
                raise ValueError(f"temporal_status={status!r} is not included")
            if args.require_verified and str(metadata.get("verification_status", "")).lower() != "verified":
                raise ValueError("verification_status is not verified")
            for section_id, text in sections:
                rows.append({"ordinance_id": ordinance_id, "section_id": section_id,
                             "year": year, "text": text, "temporal_status": status,
                             "verification_status": str(metadata.get("verification_status", "")),
                             "section_count": len(sections),
                             "source_file": str(metadata.get("source_file", path.name)),
                             "source_note": str(path), "title": str(metadata.get("title", ""))})
            audits.append({"source_note": str(path), "ordinance_id": ordinance_id,
                           "status": "included", "reason": "; ".join(warnings),
                           "detected_sections": len(sections), "declared_sections": declared_count})
            manifest.append({"source_note": str(path), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
        except RuntimeError:
            raise
        except Exception as exc:
            audits.append({"source_note": str(path), "status": "excluded", "reason": str(exc),
                           "detected_sections": 0, "declared_sections": None})
            LOG.warning("%s: excluded (%s)", path, exc)
    df = pd.DataFrame(rows)
    if not df.empty:
        # Repeated ordinance numbers can occur in multiple archive folders.
        # Keep the most complete note and record the duplicate in the audit.
        sizes = df.groupby(["ordinance_id", "source_note"]).size().reset_index(name="n")
        chosen = sizes.sort_values("n", ascending=False).drop_duplicates("ordinance_id")
        keep = set(zip(chosen.ordinance_id, chosen.source_note))
        duplicate_pairs = set(zip(sizes.ordinance_id, sizes.source_note)) - keep
        if duplicate_pairs:
            LOG.warning("Ignoring %s duplicate ordinance note(s)", len(duplicate_pairs))
            df = df[df.apply(lambda row: (row.ordinance_id, row.source_note) in keep, axis=1)].copy()
        df = _apply_metadata_filters(df, args)
    return df, audits, [], manifest


def write_input_reports(output, df, audits, manifest):
    pd.DataFrame(audits).to_csv(output / "input_audit.csv", index=False)
    df.to_csv(output / "prepared_sections.csv", index=False)
    json_write(output / "input_manifest.json", manifest)


def load_sections(args):
    source = pd.read_csv(args.input, dtype=str, keep_default_na=False, encoding="utf-8-sig")
    mapping = {"ordinance_id": args.ordinance_column, "section_id": args.section_column,
               "year": args.year_column, "text": args.text_column}
    if len(set(mapping.values())) != 4:
        raise ValueError("The four input column names must be distinct.")
    missing = set(mapping.values()) - set(source.columns)
    if missing:
        raise ValueError(f"Missing CSV columns: {sorted(missing)}")
    df = pd.DataFrame({dest: source[src].astype(str).str.strip() for dest, src in mapping.items()})
    for optional in ["temporal_status", "verification_status", "source_file", "title", "section_count"]:
        if optional in source.columns:
            df[optional] = source[optional].astype(str).str.strip()
    df["text"] = df["text"].map(lambda s: re.sub(r"\s+", " ", s).strip())
    for name in mapping:
        bad = df.index[df[name].eq("")].tolist()
        if bad:
            raise ValueError(f"Empty {name} at CSV data rows {[i + 1 for i in bad[:10]]}.")
    years = pd.to_numeric(df["year"], errors="coerce")
    if years.isna().any() or (years % 1 != 0).any() or (~years.between(1678, 2261)).any():
        raise ValueError("year must contain integer calendar years in the supported datetime range 1678..2261.")
    df["year"] = years.astype(int)
    if df.duplicated(["ordinance_id", "section_id"]).any():
        raise ValueError("Duplicate (ordinance_id, section_id) pairs. Use a unique section identifier per ordinance.")
    if df.groupby("ordinance_id")["year"].nunique().gt(1).any():
        raise ValueError("An ordinance has conflicting enactment years across its sections.")
    if df.empty:
        raise ValueError("The input CSV contains no sections.")
    df = _apply_metadata_filters(df, args)
    if df.empty:
        raise ValueError("No sections remain after metadata filtering.")
    if df.text.duplicated().any():
        LOG.warning("%s repeated section texts retained. Review repeated legal boilerplate.", df.text.duplicated().sum())
    return df


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


def semantic_vectors(docs, args):
    from sklearn.preprocessing import normalize
    import torch
    from transformers import AutoModel, AutoTokenizer
    torch.manual_seed(args.seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(args.seed)
    mps_available = hasattr(torch.backends, "mps") and torch.backends.mps.is_available()
    if args.device == "auto":
        device = "cuda" if torch.cuda.is_available() else ("mps" if mps_available else "cpu")
    else:
        device = args.device
        if device.startswith("cuda") and not torch.cuda.is_available():
            raise ValueError("CUDA was requested but is not available")
        if device == "mps" and not mps_available:
            raise ValueError("MPS was requested but is not available")
    tokenizer = AutoTokenizer.from_pretrained(args.encoder)
    encoder = AutoModel.from_pretrained(args.encoder).to(device).eval()
    limit = min(args.max_tokens, getattr(encoder.config, "max_position_embeddings", args.max_tokens))
    if tokenizer.model_max_length < 1000000:
        limit = min(limit, tokenizer.model_max_length)
    budget = limit - tokenizer.num_special_tokens_to_add(pair=False)
    if budget < 1:
        raise ValueError("--max-tokens is too small for this tokenizer.")
    all_vectors, chunk_counts = [], []
    # Non-overlapping chunks: aggregate real token vectors, excluding padding and special tokens.
    # This is token-count-weighted mean pooling across all chunks in the section.
    with torch.inference_mode():
        for i, doc in enumerate(docs):
            ids = tokenizer(doc, add_special_tokens=False, truncation=False, verbose=False)["input_ids"]
            if not ids:
                raise ValueError(f"Empty tokenized section at row {i + 1}")
            chunks = [ids[j:j + budget] for j in range(0, len(ids), budget)]
            summed, total = None, 0
            for start in range(0, len(chunks), args.batch_size):
                prepared = [tokenizer.prepare_for_model(c, add_special_tokens=True,
                             return_attention_mask=True, return_special_tokens_mask=True, truncation=False)
                            for c in chunks[start:start + args.batch_size]]
                batch = tokenizer.pad(prepared, padding=True, return_tensors="pt")
                special = batch.pop("special_tokens_mask").to(device)
                batch = {k: v.to(device) for k, v in batch.items()}
                hidden = encoder(**batch).last_hidden_state
                mask = batch["attention_mask"].bool() & ~special.bool()
                current = (hidden * mask.unsqueeze(-1)).sum(dim=(0, 1)).float().cpu()
                summed = current if summed is None else summed + current
                total += int(mask.sum().item())
            if total == 0:
                raise ValueError(f"No content tokens at row {i + 1}")
            all_vectors.append((summed / total).numpy())
            chunk_counts.append(len(chunks))
            if (i + 1) % 100 == 0:
                LOG.info("Encoded %s/%s sections", i + 1, len(docs))
    vectors = normalize(np.vstack(all_vectors)).astype("float32")
    meta = {"encoder": args.encoder, "resolved_model_revision": getattr(encoder.config, "_commit_hash", None),
            "pooling": "token-weighted mean, excluding special tokens and padding; nonoverlapping chunks",
            "max_tokens_actual": limit, "device": device,
            "total_chunks": sum(chunk_counts), "sections_with_multiple_chunks": sum(n > 1 for n in chunk_counts)}
    del encoder
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
    return vectors, meta


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
                       min_dist=0.0, metric="cosine", init="random",
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
                   min_dist=0.0, metric="cosine", init="random", random_state=args.seed, n_jobs=1)
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
                                                    "source_note", "topic", "is_outlier"]
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
            "representative_sections": "; ".join(ranked.section_id.astype(str).head(3)),
            "legal_label": "",
            "legal_relevance_1_to_5": "",
            "legal_coherence_1_to_5": "",
            "legal_notes": "",
        })
    pd.DataFrame(review_rows, columns=["topic", "keywords", "section_count",
                                       "representative_sections", "legal_label",
                                       "legal_relevance_1_to_5", "legal_coherence_1_to_5",
                                       "legal_notes"]).to_csv(out / "expert_review_template.csv", index=False)
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


def main():
    args = arguments()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    positive = ["batch_size", "max_tokens", "svd_components", "umap_components", "min_samples",
                "min_df", "max_features", "ngram_max", "top_words", "stability_runs"]
    if any(getattr(args, k) < 1 for k in positive) or args.neighbors < 2 or args.min_cluster_size < 2:
        raise ValueError("Dimensions/counts must be positive; neighbors and min-cluster-size must be at least 2.")
    if not 0 < args.max_df <= 1:
        raise ValueError("--max-df must be in (0, 1].")
    if args.prepare_only and args.validate_only:
        raise ValueError("Choose either --prepare-only or --validate-only, not both.")
    if not args.input.exists():
        raise ValueError(f"Input does not exist: {args.input}")
    input_format = args.input_format
    if input_format == "auto":
        input_format = "markdown" if args.input.is_dir() or args.input.suffix.lower() == ".md" else "csv"
    audits, metadata, manifest = [], [], []
    if input_format == "markdown":
        df, audits, metadata, manifest = load_markdown_sections(args)
        for item in audits:
            if item["status"] != "included":
                LOG.warning("%s: %s (%s)", item["source_note"], item["status"], item["reason"])
    else:
        df = load_sections(args)
        manifest = [{"source_note": args.input.name, "sha256": hashlib.sha256(args.input.read_bytes()).hexdigest()}]
    # Preparation is allowed for a single ordinance and writes audit reports even if no usable sections remain.
    if not args.validate_only:
        if args.output.exists() and (not args.output.is_dir() or any(args.output.iterdir())):
            raise ValueError("Output directory is not empty. Choose a new --output for each run.")
        args.output.mkdir(parents=True, exist_ok=True)
        if input_format == "markdown":
            write_input_reports(args.output, df, audits, manifest)
        else:
            df.to_csv(args.output / "prepared_sections.csv", index=False)
            json_write(args.output / "input_manifest.json", manifest)
    if args.prepare_only:
        LOG.info("Prepared %s sections. Review %s before training. No models trained.", len(df), args.output)
        return
    exclusions = [item for item in audits if item["status"] == "excluded"]
    if exclusions and not args.allow_excluded:
        raise ValueError(f"{len(exclusions)} notes excluded. Review --prepare-only reports; fix the notes or explicitly use --allow-excluded.")
    if df.empty:
        raise ValueError("No usable sections remain. Review input audit and parser requirements.")
    counts, terms, frozen = build_vocabulary(df.text.tolist(), args)
    LOG.info("Validated %s sections, %s ordinances, %s years, %s vocabulary terms", len(df),
             df.ordinance_id.nunique(), df.year.nunique(), len(terms))
    if args.validate_only:
        print("Input and shared vocabulary validation passed. No models were trained.")
        return
    if len(df) < 5:
        raise ValueError("At least 5 sections are required to execute training; meaningful analysis needs a larger corpus. Use --prepare-only for a single sample.")
    if args.min_cluster_size > len(df) or args.min_samples >= len(df):
        raise ValueError("Clustering settings exceed dataset size. Reduce --min-cluster-size / --min-samples.")
    random.seed(args.seed)
    np.random.seed(args.seed)
    packages = {}
    for package in ["numpy", "pandas", "scikit-learn", "bertopic", "umap-learn", "hdbscan", "torch", "transformers", "plotly", "PyYAML", "gensim"]:
        try:
            packages[package] = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            packages[package] = "not installed"
    json_write(args.output / "run_config.json", {"arguments": vars(args), "packages": packages,
               "input_format": input_format, "input_manifest": manifest,
               "unit_of_analysis": "ordinance section", "time_field": "corpus_year, then resolved_year, then date_enacted; conflicts rejected" if input_format == "markdown" else "CSV year",
               "prevalence_denominator": "all retained sections in each year, including outliers"})
    pd.DataFrame({"term": terms}).to_csv(args.output / "shared_vocabulary.csv", index=False)
    df.to_csv(args.output / "normalized_input.csv", index=False)
    labels_by_model, metrics = {}, []
    selected = ["lexical", "semantic"] if args.models == "both" else [args.models]
    for name in selected:
        LOG.info("Starting %s model", name)
        if name == "lexical":
            vectors, meta = lexical_vectors(counts, args)
        else:
            vectors, meta = semantic_vectors(df.text.tolist(), args)
        meta = {**meta,
                "clustering_representation": ("document-level TF-IDF + TruncatedSVD"
                                              if name == "lexical" else "Legal-BERT mean-pooled embeddings"),
                "topic_representation": "BERTopic class-based c-TF-IDF after clustering",
                "clusterer": "HDBSCAN",
                "reducer": "UMAP",
                "stability_runs": args.stability_runs}
        labels, scores = fit_branch(name, vectors, df, counts, terms, frozen, args, meta)
        labels_by_model[name] = labels
        metrics.append(scores)
    pd.DataFrame(metrics).to_csv(args.output / "comparison_metrics.csv", index=False)
    if len(labels_by_model) == 2:
        from sklearn.metrics import adjusted_rand_score
        a, b = labels_by_model["semantic"], labels_by_model["lexical"]
        both = (a != -1) & (b != -1)
        json_write(args.output / "cross_model_agreement.json", {
            "ari_all_sections_outliers_treated_as_one_cluster": float(adjusted_rand_score(a, b)),
            "jointly_assigned_sections": int(both.sum()),
            "ari_jointly_assigned": float(adjusted_rand_score(a[both], b[both])) if both.sum() >= 2 else None,
            "note": "ARI measures partition agreement, not quality or stability. Topic IDs are model-specific."})
        pd.crosstab(pd.Series(a, name="semantic_topic"), pd.Series(b, name="lexical_topic")).to_csv(args.output / "topic_overlap_counts.csv")
    LOG.info("Completed. Results: %s", args.output.resolve())


if __name__ == "__main__":
    main()
