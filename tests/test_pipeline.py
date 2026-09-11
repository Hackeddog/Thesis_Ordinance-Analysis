#!/usr/bin/env python3
"""Self-test: run the pipeline over the synthetic fixtures and assert behaviour.

Run this after installing dependencies and after any regex change. It needs no
real ordinances, so it works on a fresh clone.
"""
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

import make_fixtures  # noqa: E402  (same directory)
import ordinance_eda_pipeline as pipe  # noqa: E402

FAILURES = []


def check(label: str, actual, expected) -> None:
    ok = actual == expected
    print(f"  [{'PASS' if ok else 'FAIL'}] {label}: {actual!r}"
          + ("" if ok else f" (expected {expected!r})"))
    if not ok:
        FAILURES.append(label)


def main() -> int:
    fixtures = make_fixtures.build()
    raw = fixtures / "data" / "raw" / "2016"

    print("\n1. Suffix-year normalisation")
    check("'16' -> 2016", pipe.normalize_suffix_year("16"), 2016)
    check("'10' -> 2010", pipe.normalize_suffix_year("10"), 2010)
    check("'99' -> 1999", pipe.normalize_suffix_year("99"), 1999)
    check("3-digit suffix is not a year", pipe.normalize_suffix_year("456"), None)

    print("\n2. Council-term anchor (18th City Council = 2016)")
    check("15th council", pipe.council_term_to_year(15), 2007)
    check("18th council", pipe.council_term_to_year(18), 2016)

    print("\n3. Text cleaning")
    noisy = ("REPUBLIC OF THE PHILIPPINES\nCITY OF DAVAO\nPage 3 of 12\n~~~~~\n"
             "AN ORDI-\nNANCE  REGULATING   markets\n\n\n\n- 4 -\n")
    clean, stats = pipe.clean_ordinance_text(noisy)
    check("boilerplate and furniture removed", clean, "AN ORDINANCE REGULATING markets")
    check("hyphen break rejoined", stats["rejoined_words"], 1)

    print("\n4. Per-document resolution")
    expected = {
        "Ordinance No. 0116-16.pdf":       (2016, "valid"),
        "Ordinance No. 0118-16.pdf":       (2016, "valid"),
        "Ordinance No. 0301-16.pdf":       (2016, "valid"),
        "Ordinance No. 0512-16.pdf":       (2016, "valid"),
        "Ordinance No. 0230-10.pdf":       (2010, "out_of_scope"),
        "Ordinance No. 0135-16.pdf":       (2016, "valid"),
        "Ordinance No. 0999-16.pdf":       (2016, "unresolved"),
    }
    for name, (year, status) in expected.items():
        text, _, _, _ = pipe.extract_pdf_content(raw / name, use_ocr=False)
        signals = pipe.extract_year_signals(text, filename=name)
        result = pipe.resolve_ordinance_year(
            signals, 2016, (2016, 2024),
            has_text=len(text.strip()) >= pipe.NO_TEXT_CHARS)
        check(f"{name} year", result["resolved_year"], year)
        check(f"{name} status", result["temporal_status"], status)

    print("\n5. Citation filtering (the 18 phantom misfilings)")
    text, _, _, _ = pipe.extract_pdf_content(raw / "Ordinance No. 0118-16.pdf", use_ocr=False)
    signals = pipe.extract_year_signals(text, filename="Ordinance No. 0118-16.pdf")
    check("own number, not the amended one", signals["ordinance_number"], "0118-16")
    check("approval year not taken from the whereas clause",
          signals["detected_approval_year"], 2016)
    meta = pipe.extract_document_metadata(text, text, "Ordinance No. 0118-16.pdf", "0118-16")
    check("amended ordinance captured as a citation", meta["cited_ordinances"], "0234-15")
    check("topical keywords survive the title cleanup", meta["subject_keywords"], "traffic; code")

    print("\n6. Full ISO dates")
    dates = pipe.extract_full_dates(text)
    check("enactment date", dates["enactment_date"], "2016-04-05")
    check("approval date", dates["approval_date"], "2016-04-12")

    print("\n7. Cache invalidation and corpus eligibility")
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        same_name = tmp_path / "same.pdf"
        cache = tmp_path / "cache"
        shutil.copy2(raw / "Ordinance No. 0116-16.pdf", same_name)
        pipe.extract_pdf_content(same_name, cache_dir=cache, use_ocr=False)
        shutil.copy2(raw / "Ordinance No. 0118-16.pdf", same_name)
        changed, _, _, _ = pipe.extract_pdf_content(same_name, cache_dir=cache, use_ocr=False)
        check("cache invalidates when source bytes change", "0118-16" in changed, True)

        frame = pd.DataFrame([
            {"schema_version": pipe.PIPELINE_SCHEMA_VERSION, "filename": "valid.pdf",
             "folder_year": 2016, "resolved_year": 2016, "temporal_status": "valid",
             "confidence_score": 1.0, "is_sparse": False, "file_hash": "a",
             "ordinance_number": "0001-16", "char_count": 1000, "manually_verified": False},
            {"schema_version": pipe.PIPELINE_SCHEMA_VERSION, "filename": "review.pdf",
             "folder_year": 2016, "resolved_year": None, "temporal_status": "review",
             "confidence_score": 0.2, "is_sparse": False, "file_hash": "b",
             "ordinance_number": "0002-16", "char_count": 1000, "manually_verified": False},
            {"schema_version": pipe.PIPELINE_SCHEMA_VERSION, "filename": "unresolved.pdf",
             "folder_year": 2016, "resolved_year": None, "temporal_status": "unresolved",
             "confidence_score": 0.0, "is_sparse": False, "file_hash": "c",
             "ordinance_number": None, "char_count": 100, "manually_verified": False},
        ])
        eligible = pipe.flag_removal_reasons(frame, pipe.DEFAULT_REMOVAL)
        index_root = tmp_path / "project"
        index = pd.read_csv(pipe.build_corpus_index(eligible, index_root))
        included = dict(zip(index["filename"], index["included_in_corpus"]))
        check("valid records enter corpus", bool(included["valid.pdf"]), True)
        check("review records stay out of corpus", bool(included["review.pdf"]), False)
        check("unresolved records stay out of corpus", bool(included["unresolved.pdf"]), False)

    print("\n8. End-to-end run over the fixtures")
    proc = subprocess.run(
        [sys.executable, str(fixtures / "src" / "ordinance_eda_pipeline.py"),
         "--year", "2016", "--window-min", "2016", "--window-max", "2024",
         "--export-obsidian", "--no-cache"],
        cwd=fixtures, capture_output=True, text=True)
    check("exit code", proc.returncode, 0)
    for artifact in ["data/EDA/ordinances_eda_summary_2016.csv",
                     "outputs/reports/eda_report_2016.md",
                     "outputs/figures/temporal_distribution_2016.png",
                     "data/processed/corpus_index.csv",
                     "Thesis_Obsidian/Ordinances/_Corpus MOC.md",
                     "Thesis_Obsidian/Ordinances/2016/Ordinance No. 0116-16.md",
                     "outputs/reports/run_manifest.json"]:
        check(f"produced {artifact}", (fixtures / artifact).exists(), True)

    print("\n" + "=" * 60)
    if FAILURES:
        print(f"{len(FAILURES)} check(s) FAILED: " + ", ".join(FAILURES))
        return 1
    print("All checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
