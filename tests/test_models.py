"""Fast correctness tests; no network or pretrained encoder download."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd
import pytest
from scipy.sparse import csr_matrix

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "scripts")]
import model_ordinances as model
from run_comparison import prepare_sample


def options(tmp_path, **kwargs):
    values = dict(input=tmp_path / "input.csv", ordinance_column="ordinance_id", section_column="section_id",
                  year_column="year", text_column="text", strict_section_count=False,
                  include_temporal_status="valid", require_verified=False)
    values.update(kwargs)
    return argparse.Namespace(**values)


def rows():
    return pd.DataFrame([{"ordinance_id": f"ord-{y}-{n}", "section_id": "section_1", "year": y,
                          "text": f"public health community services {n}", "temporal_status": "valid",
                          "verification_status": "unverified"} for y in [2016, 2017] for n in range(5)])


def test_csv_rejects_duplicate_sections(tmp_path):
    df = rows()
    pd.concat([df, df.iloc[:1]]).to_csv(tmp_path / "input.csv", index=False)
    with pytest.raises(ValueError, match="Duplicate"):
        model.load_sections(options(tmp_path))


def test_csv_rejects_conflicting_years(tmp_path):
    df = rows()
    df.loc[1, ["ordinance_id", "section_id", "year"]] = [df.loc[0, "ordinance_id"], "section_2", 2017]
    df.to_csv(tmp_path / "input.csv", index=False)
    with pytest.raises(ValueError, match="conflicting"):
        model.load_sections(options(tmp_path))


def test_yearly_prevalence_includes_outliers_and_zero_cells():
    df = pd.DataFrame({"year": [2016, 2016, 2017]})
    table = model.yearly_prevalence(df, [0, -1, 1])
    assert len(table) == 6
    assert table.groupby("year").section_share.sum().eq(1).all()
    assert table.query("year == 2017 and topic == 0").section_count.iloc[0] == 0
    assert table.query("year == 2016 and topic == -1").section_share.iloc[0] == .5


def test_no_topics_have_null_metrics_not_fake_zero():
    metrics = model.keyword_metrics({-1: ["health", "care"]}, csr_matrix([[1, 1]]), ["health", "care"], 10)
    assert metrics["topic_diversity"] is None
    assert metrics["section_npmi"] is None


def test_keyword_metrics_excludes_outliers():
    metrics = model.keyword_metrics({0: ["health", "care"], -1: ["noise"]},
                                    csr_matrix([[1, 1, 0], [1, 1, 0], [0, 0, 1]]),
                                    ["health", "care", "noise"], 2)
    assert metrics["topic_diversity"] == 1
    assert metrics["section_npmi"] == pytest.approx(1)


def test_sample_is_balanced_and_repeatable(tmp_path):
    source = tmp_path / "source.csv"
    rows().to_csv(source, index=False)
    config = dict(years=[2016, 2017], sections_per_year=2, allow_unverified=True, seed=42)
    a, audit = prepare_sample(source, config)
    b, _ = prepare_sample(source, config)
    pd.testing.assert_frame_equal(a, b)
    assert a.groupby("year").size().tolist() == [2, 2]
    assert audit.verified_sections.sum() == 0
    with pytest.raises(ValueError, match="only 0 eligible"):
        prepare_sample(source, {**config, "allow_unverified": False})


def test_sample_rejects_missing_year(tmp_path):
    source = tmp_path / "source.csv"
    rows().to_csv(source, index=False)
    with pytest.raises(ValueError, match="Year 2025"):
        prepare_sample(source, dict(years=[2025], sections_per_year=2, seed=42, allow_unverified=True))


def test_cache_requires_exact_ordered_text(tmp_path):
    docs = ["health services", "road transport"]
    args = argparse.Namespace(semantic_cache=tmp_path, encoder="test", encoder_revision="sha", max_tokens=512)
    identity = {"ordered_text_sha256": hashlib.sha256(json.dumps(docs, ensure_ascii=False).encode()).hexdigest(),
                "encoder": "test", "encoder_revision_requested": "sha", "max_tokens_requested": 512}
    (tmp_path / "model_metadata.json").write_text(json.dumps(identity))
    np.save(tmp_path / "section_vectors.npy", np.ones((2, 3), dtype="float32"))
    vectors, meta = model.cached_semantic_vectors(docs, args)
    assert vectors.shape == (2, 3) and meta["cache_used"]
    with pytest.raises(ValueError, match="does not match"):
        model.cached_semantic_vectors(docs[::-1], args)


def test_section_parser_does_not_use_table_of_contents():
    text = "SECTION 1. Contents\nBe it ordained by the council\nSECTION 1. Health services\nCommunity health care services shall be established."
    parsed = model._markdown_sections(text)
    assert len(parsed) == 1
    assert "Community health" in parsed[0][1]


def test_semantic_chunking_with_local_tiny_bert(tmp_path):
    """Regression: fast prepare_for_model cannot build special-token masks.

    Tiny random weights are used ONLY for this offline correctness test.
    """
    from transformers import BertConfig, BertModel, BertTokenizer
    checkpoint = tmp_path / "tiny-bert"
    checkpoint.mkdir()
    vocab = checkpoint / "vocab.txt"
    vocab.write_text("[PAD]\n[UNK]\n[CLS]\n[SEP]\n[MASK]\npublic\nhealth\nservices\n", encoding="utf-8")
    BertTokenizer(vocab_file=str(vocab)).save_pretrained(checkpoint)
    BertModel(BertConfig(vocab_size=8, hidden_size=8, num_hidden_layers=1,
                        num_attention_heads=2, intermediate_size=16,
                        max_position_embeddings=16)).save_pretrained(checkpoint)
    args = argparse.Namespace(encoder=str(checkpoint), encoder_revision="main", device="cpu",
                              seed=42, max_tokens=8, batch_size=2)
    vectors, meta = model.semantic_vectors(["public health services " * 8, "public health"], args)
    assert vectors.shape == (2, 8)
    assert np.isfinite(vectors).all()
    assert np.allclose(np.linalg.norm(vectors, axis=1), 1)
    assert meta["sections_with_multiple_chunks"] == 1
    assert meta["total_chunks"] == 5


def test_lexical_integration(tmp_path):
    """Exercise BERTopic fit/export on unmistakably synthetic data, not research evidence."""
    import subprocess
    vocabulary = ["health clinic doctor medicine patient", "roads traffic vehicle transport parking",
                  "waste recycling garbage environment collection"]
    records = [{"ordinance_id": f"synthetic-{i}", "section_id": "section_1", "year": 2016 + i % 2,
                "text": vocabulary[i % 3] + " " + vocabulary[i % 3]} for i in range(30)]
    source = tmp_path / "synthetic.csv"
    pd.DataFrame(records).to_csv(source, index=False)
    out = tmp_path / "run"
    command = [sys.executable, str(ROOT / "src/model_ordinances.py"), "--input", str(source),
               "--output", str(out), "--models", "lexical", "--neighbors", "3", "--min-cluster-size", "3",
               "--min-samples", "1", "--min-df", "1", "--ngram-max", "1", "--top-words", "3",
               "--stability-runs", "1", "--skip-html"]
    subprocess.run(command, check=True, capture_output=True, text=True, timeout=240)
    metrics = json.loads((out / "lexical/metrics.json").read_text())
    assert metrics["sections"] == 30
    assert 0 <= metrics["topic_coverage"] <= 1
    assert (out / "comparison_metrics.csv").exists()
    yearly = pd.read_csv(out / "lexical/yearly_prevalence.csv")
    assert np.allclose(yearly.groupby("year").section_share.sum(), 1)
