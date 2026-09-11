"""Small service layer for the local Ordinance Lab dashboard.

The UI intentionally calls the existing CLI instead of duplicating pipeline
logic. Future features such as adjudication and curation can be added here
without turning the Streamlit page into a second pipeline implementation.
"""

from __future__ import annotations

import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PIPELINE = PROJECT_ROOT / "src" / "ordinance_eda_pipeline.py"
SUMMARY_DIR = PROJECT_ROOT / "data" / "EDA"
REPORT_DIR = PROJECT_ROOT / "outputs" / "reports"
RAW_DIR = PROJECT_ROOT / "data" / "raw"


@dataclass
class RunResult:
    """Captured result from one non-destructive audit run."""

    returncode: int
    output: str

    @property
    def succeeded(self) -> bool:
        return self.returncode == 0


def available_years() -> list[int]:
    """Return raw-data folders that contain at least one PDF."""
    if not RAW_DIR.exists():
        return []
    years = []
    for folder in RAW_DIR.iterdir():
        if folder.is_dir() and folder.name.isdigit():
            years.append(int(folder.name))
    return sorted(years)


def raw_pdf_count() -> int:
    return sum(len(list(RAW_DIR.joinpath(str(year)).glob("*.pdf")))
               for year in available_years())


def run_audit(year: Optional[int], window_min: int, window_max: int,
              use_ocr: bool = True, use_cache: bool = True) -> RunResult:
    """Run the existing CLI in safe audit mode.

    This does not relocate, quarantine, purge, or restore files. Those actions
    remain deliberately outside the first dashboard version.
    """
    command = [sys.executable, str(PIPELINE),
               "--window-min", str(window_min), "--window-max", str(window_max)]
    if year is None:
        command.append("--all-years")
    else:
        command.extend(["--year", str(year)])
    if not use_ocr:
        command.append("--no-ocr")
    if not use_cache:
        command.append("--no-cache")

    completed = subprocess.run(
        command,
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    output = (completed.stdout or "") + (completed.stderr or "")
    return RunResult(completed.returncode, output.strip())


def load_table(year: Optional[int] = None) -> Optional[pd.DataFrame]:
    """Load the latest summary and attach modelling eligibility when available."""
    path = (SUMMARY_DIR / "ordinances_eda_summary_ALL.csv"
            if year is None
            else SUMMARY_DIR / f"ordinances_eda_summary_{year}.csv")
    if not path.exists():
        return None
    summary = pd.read_csv(path)
    index_path = PROJECT_ROOT / "data" / "processed" / "corpus_index.csv"
    if index_path.exists() and {"filename", "folder_year"}.issubset(summary.columns):
        index = pd.read_csv(index_path)
        columns = ["filename", "folder_year", "corpus_year", "included_in_corpus"]
        available = [column for column in columns if column in index.columns]
        summary = summary.merge(
            index[available],
            on=[column for column in ("filename", "folder_year") if column in available],
            how="left",
            suffixes=("", "_index"),
        )
    if "included_in_corpus" not in summary.columns:
        summary["included_in_corpus"] = False
    return summary


def read_report(year: Optional[int] = None) -> Optional[str]:
    path = (REPORT_DIR / "eda_report_CORPUS.md"
            if year is None else REPORT_DIR / f"eda_report_{year}.md")
    return path.read_text(encoding="utf-8") if path.exists() else None


def read_checklist() -> str:
    path = PROJECT_ROOT / "docs" / "THESIS_READINESS_CHECKLIST.md"
    return path.read_text(encoding="utf-8") if path.exists() else "Checklist unavailable."


def latest_manifest() -> Optional[dict]:
    import json

    path = REPORT_DIR / "run_manifest.json"
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def status_counts(table: pd.DataFrame) -> pd.DataFrame:
    """Return a stable status-count table for display."""
    order = ["valid", "misfiled", "out_of_scope", "review", "unresolved"]
    counts = table["temporal_status"].value_counts().reindex(order, fill_value=0)
    return counts.rename("Documents").to_frame()
