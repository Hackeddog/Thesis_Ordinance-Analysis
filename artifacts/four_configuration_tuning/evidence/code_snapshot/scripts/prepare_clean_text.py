"""Read only cleaned TXT sources; audit duplicates, dates and model-unit extraction."""
from __future__ import annotations
import argparse
from collections import defaultdict
import csv
import hashlib
import json
from pathlib import Path
import re

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
HEADER = re.compile(r"(?im)^[ \t]*(?:SECTION|SECTI0N|SEC\.)[ \t]+([0-9]+[A-Za-z]?|[IVXLCDM]+)[ \t]*[.:-]?[ \t]*")
SIGNATURE = re.compile(r"(?im)^[ \t]*(?:ENACTED\b|CERTIFIED\s+CORRECT\b|ATTESTED\b|APPROVED\s*:)" )
BOILERPLATE = re.compile(r"^(?:effectivity|separability|severability|repealing\s+clause)\b", re.I)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def identity(filename):
    match = re.search(r"(?:No\.?\s*)?(\d{1,5})\s*-\s*(\d{2,4})(?!\d)", filename, re.I)
    return f"{int(match[1])}-{match[2]}" if match else Path(filename).stem.lower()


def overrides(paths):
    records = defaultdict(list)
    for path in paths:
        with path.open(encoding="utf-8-sig", newline="") as handle:
            for row in csv.DictReader(handle):
                try:
                    value = float(row.get("correct_year", ""))
                    if not value.is_integer():
                        continue
                    year = int(value)
                except ValueError:
                    continue
                records[identity(row["filename"])].append({"year": year, "file": path.name,
                    "reviewer": row.get("verified_by", ""), "evidence": row.get("evidence", "")})
    return records


def enacted_year(text):
    # Anchored enactment clauses only; never infer enactment from every cited year.
    found = set()
    for match in re.finditer(r"(?im)^\s*ENACTED\b([^\n]*(?:\n[^\n]*)?)", text[-6000:]):
        found.update(int(y) for y in re.findall(r"\b(?:19|20)\d{2}\b", match[1][:180]))
    return next(iter(found)) if len(found) == 1 else None


def segment(text):
    """Numbered sections when detectable; whole-document fallback rather than silent loss."""
    text = text.replace("\r\n", "\n").replace("\x00", " ")
    operative = re.search(r"\bbe\s+it\s+ordained\b", text, re.I)
    start = operative.start() if operative else 0
    body = text[start:]
    headings = list(HEADER.finditer(body))
    # Repeated section numbers usually mean a table of contents or embedded amendments.
    repeated = len({m[1].lower() for m in headings}) != len(headings)
    audit = {"preamble_chars_omitted": start, "signature_chars_omitted": 0,
             "boilerplate_units_omitted": 0, "repeated_heading_numbers": repeated}
    if not headings or repeated:
        chunks = [("document", body, "document_fallback")]
    else:
        chunks = [(f"section_{m[1]}", body[m.end():headings[i+1].start() if i+1 < len(headings) else len(body)], "legal_section")
                  for i, m in enumerate(headings)]
        audit["preamble_chars_omitted"] += headings[0].start()
    units = []
    for sid, content, kind in chunks:
        signature = SIGNATURE.search(content)
        if signature:
            audit["signature_chars_omitted"] += len(content) - signature.start()
            content = content[:signature.start()]
        content = re.sub(r"\s+", " ", content).strip()
        if kind == "legal_section" and BOILERPLATE.match(content):
            audit["boilerplate_units_omitted"] += 1
            continue
        if len(re.findall(r"[A-Za-z]{2,}", content)) >= 3:
            units.append({"section_id": sid, "text": content, "unit_type": kind})
    return units, audit


def prepare(root, output):
    root, output = Path(root), Path(output)
    if output.exists():
        raise ValueError("Output already exists; choose a fresh preparation directory")
    files = sorted(root.rglob("*.txt"))
    if not files:
        raise ValueError(f"No TXT files found: {root}")
    correction_files = sorted((ROOT / "data").glob("manual_year_overrides_*.csv"))
    corrections = overrides(correction_files)
    groups = defaultdict(list)
    for path in files:
        raw = path.read_bytes()
        text = raw.decode("utf-8-sig", errors="strict")
        # Whitespace-equivalent documents count as duplicate content; bytes are still recorded.
        normalized = re.sub(r"\s+", " ", text).strip()
        year_match = re.search(r"(?:^|/)(20\d{2})(?:/|$)", path.relative_to(root).as_posix())
        groups[digest(normalized.encode())].append({"path": path.relative_to(root).as_posix(),
            "id": identity(path.name), "folder_year": int(year_match[1]) if year_match else None,
            "sha256": digest(raw), "text": text})
    file_audit, rows, doc_audit = [], [], []
    for content_hash, copies in sorted(groups.items()):
        candidates = [x for c in copies for x in corrections.get(c["id"], [])]
        human_years = {x["year"] for x in candidates}
        folders = {c["folder_year"] for c in copies} - {None}
        enacted = enacted_year(copies[0]["text"])
        reason = ""
        if len(human_years) > 1:
            year, source, reason = None, "conflicting_human_overrides", "conflicting human year overrides"
        elif human_years:
            year, source = next(iter(human_years)), "human_year_override"
        elif len(folders) == 1:
            year, source = next(iter(folders)), "user_verified_folder"
        elif enacted in folders:
            year, source = enacted, "explicit_enactment_resolves_duplicate_folders"
        else:
            year, source, reason = None, "unresolved_duplicate_year", "duplicate contents have ambiguous folder years"
        if year is not None and not 2016 <= year <= 2025:
            reason = "outside 2016-2025 after human date correction"
        canonical = min(copies, key=lambda c: (c["folder_year"] != year, c["path"]))
        units, extraction = segment(canonical["text"])
        if not units and not reason:
            reason = "no usable text after deterministic extraction"
        # Content identity preserves distinct versions rather than merging differing text by number alone.
        document_id = canonical["id"] + "@" + content_hash[:12]
        for copy in copies:
            status = "excluded" if reason else ("included" if copy is canonical else "duplicate_copy")
            file_audit.append({k: v for k, v in copy.items() if k != "text"} | {
                "status": status, "reason": reason, "canonical_path": canonical["path"],
                "content_sha256": content_hash, "resolved_year": year, "year_source": source})
        doc_audit.append({"ordinance_id": document_id, "ordinance_number": canonical["id"],
                          "source_file": canonical["path"], "source_copies": len(copies), "year": year,
                          "year_source": source, "explicit_enacted_year": enacted,
                          "date_disagreement_flag": enacted is not None and enacted != year,
                          "manual_evidence": json.dumps(candidates, ensure_ascii=False),
                          "status": "excluded" if reason else "included", "reason": reason,
                          "units": len(units) if not reason else 0, **extraction})
        if reason:
            continue
        for unit in units:
            rows.append({"ordinance_id": document_id, "ordinance_number": canonical["id"],
                         "year": year, "source_file": canonical["path"],
                         "source_sha256": canonical["sha256"], "temporal_status": "valid",
                         "verification_status": "verified", "verification_basis": "user-confirmed cleaned TXT corpus",
                         "year_source": source, "section_count": len(units), **unit})
    output.mkdir(parents=True)
    frame = pd.DataFrame(rows).sort_values(["year", "ordinance_id", "section_id"]).reset_index(drop=True)
    documents = pd.DataFrame(doc_audit)
    files_frame = pd.DataFrame(file_audit)
    frame.to_csv(output / "sections.csv", index=False)
    documents.to_csv(output / "document_audit.csv", index=False)
    files_frame.to_csv(output / "file_audit.csv", index=False)
    document_years = documents[documents.status.eq("included")].groupby("year").size()
    summary = frame.groupby("year").agg(units=("text", "size"), documents=("ordinance_id", "nunique"))
    summary["fallback_documents"] = frame[frame.unit_type.eq("document_fallback")].groupby("year").size().reindex(summary.index, fill_value=0)
    summary.to_csv(output / "yearly_corpus.csv")
    manifest = {"source_directory": str(root), "input_format": "cleaned TXT only", "source_files": len(files),
                "content_groups": len(groups), "duplicate_copies": len(files) - len(groups),
                "included_documents": int(frame.ordinance_id.nunique()), "model_units": len(frame),
                "excluded_content_groups": int(documents.status.eq("excluded").sum()),
                "verification_basis": "User confirmation; not an independent re-verification of PDF contents",
                "source_manifest_sha256": digest(json.dumps(sorted((x["path"], x["sha256"]) for x in file_audit)).encode()),
                "sections_sha256": digest((output / "sections.csv").read_bytes()),
                "preparation_code_sha256": digest(Path(__file__).read_bytes()),
                "override_files": {p.name: digest(p.read_bytes()) for p in correction_files},
                "distinct_versions_same_number": int(frame[["ordinance_id", "ordinance_number"]].drop_duplicates().ordinance_number.duplicated().sum()),
                "unit_types": frame.unit_type.value_counts().to_dict(),
                "signature_chars_omitted": int(documents.signature_chars_omitted.sum()),
                "boilerplate_units_omitted": int(documents.boilerplate_units_omitted.sum()),
                "remaining_date_disagreements": int(documents.query("status == 'included'").date_disagreement_flag.sum()),
                "extraction_policy": "Numbered sections; whole-document fallback for missing/repeated headings. Drop effectivity/separability/repealing-clause units; trim explicit signature blocks. No source files modified."}
    (output / "preparation.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in manifest.items() if k not in ["override_files"]}, indent=2))
    return frame, manifest


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source", type=Path, default=ROOT / "data/processed/clean_text")
    p.add_argument("--output", type=Path, default=ROOT / "results/experiments/clean_text_preparation")
    a = p.parse_args()
    prepare(a.source, a.output)
