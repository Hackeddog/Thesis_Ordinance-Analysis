#!/usr/bin/env python3
"""
src/ordinance_eda_pipeline.py

Legal NLP Exploratory Data Analysis, Temporal Validation and Anomaly Routing
Engine for Davao City municipal ordinances.

v2 changes (see CHANGELOG at the bottom of this docstring):
  * Ordinance number is read from the FILENAME first and from a bounded HEADER
    REGION second, never from a free .search() over the whole body. Citations to
    amended ordinances in the title and whereas-clauses no longer hijack the
    signal.
  * Enactment and approval dates are found by ANCHOR + WINDOW scanning that
    crosses newlines and supports "this 15th day of March, 2016", ALL-CAPS
    months, and numeric dates. The old single-line regex is why coverage was
    3.9%.
  * confidence_score is now the weight of corroborating evidence, so a lone
    signal can no longer score 1.00.
  * Mutually exclusive `temporal_status` replaces the overlapping boolean
    counters, so report percentages sum to 100%.
  * Misfiling requires corroboration; weak cases route to MANUAL REVIEW instead
    of into the relocation queue. Relocation copies by default.
  * Duplicate detection now uses the ordinance NUMBER STRING (previously it
    deduped on (year, filename), which can never collide).
  * Per-page OCR fallback, extracted-text caching, and a --debug-headers mode
    for tuning the regexes against real files.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import logging
import platform
import re
import shutil
import subprocess
import sys
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

try:
    from PIL import Image
    import pytesseract
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False

try:
    import fitz  # PyMuPDF
    PDF_BACKEND = "pymupdf"
except ImportError:
    try:
        from pypdf import PdfReader
        PDF_BACKEND = "pypdf"
    except ImportError:
        try:
            import pdfplumber
            PDF_BACKEND = "pdfplumber"
        except ImportError:
            PDF_BACKEND = None

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("LegalNLP-EDA")
logging.getLogger("matplotlib").setLevel(logging.WARNING)
logging.getLogger("PIL").setLevel(logging.WARNING)

# --------------------------------------------------------------------------- #
# Configuration
# --------------------------------------------------------------------------- #

DEFAULT_WINDOW = (2016, 2024)      # nine-year study period; override on the CLI
MIN_YEAR, MAX_YEAR = 1900, 2035

HEADER_CHARS = 1800                # header region scanned for the self number
DATE_WINDOW = 400                  # chars scanned after a date anchor
OCR_PAGE_MIN_CHARS = 100           # per page, below this the page is rasterized
SPARSE_DOC_CHARS = 300             # whole-doc completeness flag
NO_TEXT_CHARS = 120                # below this there is effectively no text layer
CACHE_FORMAT_VERSION = 2           # invalidate caches when extraction semantics change
PIPELINE_SCHEMA_VERSION = "1.1"    # version of the generated record/data contract

# Evidence weights. confidence_score is the summed weight of AGREEING signals
# minus half the weight of DISAGREEING ones, so one lone signal caps out at its
# own weight and can never report 1.00.
WEIGHTS = {
    "detected_enactment_year": 0.45,
    "detected_ordinance_no_year": 0.25,
    "detected_series_year": 0.20,
    "detected_approval_year": 0.10,
}

MISFILE_MIN_CONFIDENCE = 0.45      # below this a mismatch is REVIEW, not misfiled
RELOCATE_MIN_CONFIDENCE = 0.60     # stricter bar before touching files on disk

MONTHS = {
    "january": 1, "jan": 1, "february": 2, "feb": 2, "march": 3, "mar": 3,
    "april": 4, "apr": 4, "may": 5, "june": 6, "jun": 6, "july": 7, "jul": 7,
    "august": 8, "aug": 8, "september": 9, "sept": 9, "sep": 9, "october": 10,
    "oct": 10, "november": 11, "nov": 11, "december": 12, "dec": 12,
}
MONTH_RE = r"(?:" + "|".join(sorted(MONTHS, key=len, reverse=True)) + r")"

# --------------------------------------------------------------------------- #
# Regex definitions
# --------------------------------------------------------------------------- #

# Ordinance number as it appears in a filename: "Ordinance No. 0118-16.pdf"
FILENAME_ORD_RE = re.compile(
    r"(?:ordinance|ord)\.?\s*(?:no\.?|number|#)?\s*(\d{1,5})\s*[-\u2013\u2014_\s]\s*(\d{2,4})\b",
    re.IGNORECASE,
)

# Ordinance number inside the document header. Strict shape: digits, separator,
# 2-4 digit suffix. No [\w\-]+ wildcard.
ORD_NO_RE = re.compile(
    r"ORDINANCE\s+(?:NO\.?|NUMBER|#)\s*(\d{1,5})\s*[-\u2013\u2014_]\s*(\d{2,4})\b",
    re.IGNORECASE,
)
# Number with no suffix, paired with a nearby "Series of YYYY".
ORD_NO_PLAIN_RE = re.compile(r"ORDINANCE\s+(?:NO\.?|NUMBER|#)\s*(\d{1,5})\b", re.IGNORECASE)

# Words that mark the FOLLOWING ordinance reference as somebody else's number.
CITATION_CUE_RE = re.compile(
    r"(amend(?:ing|ed|atory)?|repeal(?:ing|ed)?|supersed(?:ing|ed)?|revok(?:ing|ed)?"
    r"|pursuant\s+to|under|violation\s+of|otherwise\s+known\s+as|known\s+as|as\s+amended"
    r"|provided\s+(?:for\s+)?(?:in|by|under)|in\s+relation\s+to|amendment\s+to|section\s+\d+\s+of)"
    r"[^;:\n]{0,90}$",
    re.IGNORECASE,
)

# Matches "Series of 2016" and the session-header variant
# "22nd Regular Session / Series of 2016".
SERIES_RE = re.compile(r"SERIES\s*(?:OF|NO\.?)?\s*[,:]?\s*((?:19|20)\d{2})", re.IGNORECASE)
SESSION_RE = re.compile(
    r"\d{1,3}\s*(?:st|nd|rd|th)\s+(?:REGULAR|SPECIAL|INAUGURAL)\s+SESSION", re.IGNORECASE)
COUNCIL_RE = re.compile(r"(\d{1,2})\s*(?:st|nd|rd|th)\s+(?:CITY\s+)?COUNCIL", re.IGNORECASE)

ENACT_ANCHOR_RE = re.compile(
    r"\b(ENACTED|ENACTMENT|PASSED\s+AND\s+APPROVED|ADOPTED)\b"
    r"|(?:regular|special|inaugural)\s+session[^.\n]{0,60}held", re.IGNORECASE)
APPROVE_ANCHOR_RE = re.compile(r"\bAPPROVED\b|\bCITY\s+MAYOR\b|\bACTING\s+MAYOR\b", re.IGNORECASE)

DATE_PATTERNS = [
    re.compile(r"\b" + MONTH_RE + r"\.?\s+(\d{1,2})\s*(?:st|nd|rd|th)?\s*,?\s*((?:19|20)\d{2})\b",
               re.IGNORECASE),
    re.compile(r"\b(\d{1,2})\s*(?:st|nd|rd|th)?\s+(?:day\s+of\s+)?" + MONTH_RE +
               r"\.?\s*,?\s*((?:19|20)\d{2})\b", re.IGNORECASE),
    re.compile(r"\b\d{1,2}[/-]\d{1,2}[/-]((?:19|20)\d{2})\b"),
]
BARE_YEAR_RE = re.compile(r"\b((?:19|20)\d{2})\b")


# --------------------------------------------------------------------------- #
# Utilities
# --------------------------------------------------------------------------- #

def _plausible_year(value: Optional[int]) -> Optional[int]:
    if value is None:
        return None
    return int(value) if MIN_YEAR <= int(value) <= MAX_YEAR else None


def normalize_suffix_year(token: Optional[str]) -> Optional[int]:
    """Normalize an ordinance-number suffix to a 4-digit year.

    '16' -> 2016, '10' -> 2010, '99' -> 1999, '2016' -> 2016.
    A 3-digit token is a sequence number, not a year, and returns None.
    """
    if not token or not str(token).isdigit():
        return None
    token = str(token)
    if len(token) == 4:
        return _plausible_year(int(token))
    if len(token) == 2:
        value = int(token)
        pivot = MAX_YEAR % 100
        return _plausible_year(2000 + value if value <= pivot else 1900 + value)
    return None


def compute_file_hash(file_path: Path) -> str:
    hasher = hashlib.sha256()
    with open(file_path, "rb") as fh:
        while chunk := fh.read(8192):
            hasher.update(chunk)
    return hasher.hexdigest()


COUNCIL_ANCHOR_ORDINAL, COUNCIL_ANCHOR_YEAR = 18, 2016


def council_term_to_year(ordinal: int) -> Optional[int]:
    """First year of the Nth Davao City Council term.

    Anchored on a scanned header reading "18th City Council / 22nd Regular
    Session / Series of 2016", so the 18th council convened in 2016 and terms
    run three years (17th = 2013, 16th = 2010, 15th = 2007). Weak hint, used
    only when no other signal survives.
    """
    if ordinal <= 0:
        return None
    return _plausible_year(COUNCIL_ANCHOR_YEAR + (ordinal - COUNCIL_ANCHOR_ORDINAL) * 3)


# --------------------------------------------------------------------------- #
# Text extraction: per-page OCR fallback + on-disk cache
# --------------------------------------------------------------------------- #

def _pymupdf_pages(pdf_path: Path) -> List[str]:
    with fitz.open(str(pdf_path)) as doc:
        return [page.get_text() or "" for page in doc]


def _ocr_page(pdf_path: Path, page_index: int) -> str:
    if not OCR_AVAILABLE or PDF_BACKEND != "pymupdf":
        return ""
    try:
        with fitz.open(str(pdf_path)) as doc:
            pix = doc[page_index].get_pixmap(dpi=300)
            img = Image.open(io.BytesIO(pix.tobytes("png")))
            return pytesseract.image_to_string(img) or ""
    except Exception as exc:
        logger.error("OCR failed on %s page %d: %s", pdf_path.name, page_index + 1, exc)
        return ""


def extract_pdf_content(pdf_path: Path, cache_dir: Optional[Path] = None,
                        use_ocr: bool = True) -> Tuple[str, str, int, int]:
    """Return (text, extraction_method, page_count, ocr_page_count).

    Every page is checked individually. A born-digital ordinance with one
    scanned annex no longer skips OCR just because the document total clears a
    50-character bar, which is what the old whole-document threshold did.
    """
    if PDF_BACKEND is None:
        raise RuntimeError("Install pymupdf, pypdf or pdfplumber.")

    source_hash = compute_file_hash(pdf_path)
    cache_file = None
    if cache_dir is not None:
        cache_dir.mkdir(parents=True, exist_ok=True)
        cache_file = cache_dir / (pdf_path.stem + ".json")
        if cache_file.exists():
            try:
                blob = json.loads(cache_file.read_text(encoding="utf-8"))
                cache_matches = (
                    blob.get("cache_version") == CACHE_FORMAT_VERSION
                    and blob.get("source_hash") == source_hash
                    and blob.get("use_ocr") == bool(use_ocr)
                    and blob.get("backend") == PDF_BACKEND
                )
                if cache_matches:
                    return blob["text"], blob["method"], blob["pages"], blob["ocr_pages"]
                logger.info("Ignoring stale extraction cache: %s", cache_file)
            except Exception:
                logger.warning("Ignoring unreadable extraction cache: %s", cache_file)

    pages: List[str] = []
    try:
        if PDF_BACKEND == "pymupdf":
            pages = _pymupdf_pages(pdf_path)
        elif PDF_BACKEND == "pypdf":
            pages = [(p.extract_text() or "") for p in PdfReader(str(pdf_path)).pages]
        else:
            with pdfplumber.open(str(pdf_path)) as pdf:
                pages = [(p.extract_text() or "") for p in pdf.pages]
    except Exception as exc:
        logger.error("Digital extraction failed on %s: %s", pdf_path.name, exc)

    ocr_pages = 0
    ocr_needed = bool(pages) and any(
        len(page_text.strip()) < OCR_PAGE_MIN_CHARS for page_text in pages)
    if use_ocr and ocr_needed and (not OCR_AVAILABLE or PDF_BACKEND != "pymupdf"):
        logger.warning(
            "OCR fallback unavailable for %s (OCR packages/backend unavailable); "
            "low-text pages will remain incomplete.", pdf_path.name)
    if use_ocr:
        for i, page_text in enumerate(pages):
            if len(page_text.strip()) < OCR_PAGE_MIN_CHARS:
                recovered = _ocr_page(pdf_path, i)
                if len(recovered.strip()) > len(page_text.strip()):
                    pages[i] = recovered
                    ocr_pages += 1

    text = "\n".join(pages)
    if ocr_pages == 0:
        method = "Digital"
    elif ocr_pages == len(pages):
        method = "OCR"
    else:
        method = "Hybrid"

    if cache_file is not None:
        cache_file.write_text(json.dumps({
            "cache_version": CACHE_FORMAT_VERSION,
            "source_hash": source_hash,
            "use_ocr": bool(use_ocr),
            "backend": PDF_BACKEND,
            "text": text,
            "method": method,
            "pages": len(pages),
            "ocr_pages": ocr_pages,
        }, ensure_ascii=False, sort_keys=True), encoding="utf-8")
    return text, method, len(pages), ocr_pages


# --------------------------------------------------------------------------- #
# Date parsing helpers
# --------------------------------------------------------------------------- #

def _find_year_near(text: str, anchor_end: int, window: int = DATE_WINDOW,
                    allow_bare_year: bool = True) -> Tuple[Optional[int], str]:
    """Scan forward from an anchor for a full date, then a bare year.

    Crossing newlines is deliberate: in Davao ordinances the date routinely sits
    on the line below ENACTED or below the mayor's signature line.
    """
    segment = text[anchor_end:anchor_end + window]
    for pattern in DATE_PATTERNS:
        match = pattern.search(segment)
        if match:
            year = _plausible_year(int(match.groups()[-1]))
            if year:
                return year, "full_date"
    if allow_bare_year:
        match = BARE_YEAR_RE.search(segment[:window // 2])
        if match:
            year = _plausible_year(int(match.group(1)))
            if year:
                return year, "bare_year"
    return None, "none"


INSTRUMENT_REF_RE = re.compile(
    r"\bORDINANCE\s+(?:NO|NUMBER)|\bSERIES\s+OF\s+(?:19|20)\d{2}"
    r"|\bR\.?\s?A\.?\s*\d+|\bREPUBLIC\s+ACT", re.IGNORECASE)


def _is_cited_context(text: str, position: int) -> bool:
    """True when an anchor sits inside a reference to somebody else's instrument.

    Two conditions must both hold: a citation cue (amending, pursuant to, was
    approved on) AND an actual reference to another instrument nearby. Requiring
    both matters because operative text says "Section 4 is hereby amended to
    read as follows" immediately before the enactment clause, and a cue-only
    test suppressed the enactment date of every amendatory ordinance.
    """
    prefix = text[max(0, position - 120):position]
    has_cue = bool(CITATION_CUE_RE.search(prefix)) or bool(
        re.search(r"\bwas\s+(?:approved|enacted|passed)\b[^.;:]{0,40}$", prefix, re.IGNORECASE))
    return has_cue and bool(INSTRUMENT_REF_RE.search(prefix))


def extract_enactment_year(text: str) -> Tuple[Optional[int], str]:
    for anchor in ENACT_ANCHOR_RE.finditer(text):
        if _is_cited_context(text, anchor.start()):
            continue
        year, kind = _find_year_near(text, anchor.end())
        if year:
            return year, kind
    return None, "none"


def extract_approval_year(text: str) -> Tuple[Optional[int], str]:
    """Mayoral approval date.

    Scanned from the END of the document backwards: the mayor's approval is the
    last act on the page, whereas the first "approved" in a Davao ordinance is
    usually a whereas clause reciting when the AMENDED ordinance was approved.
    Reading forward is how a 2016 ordinance picked up approval year 2015.
    """
    explicit = re.compile(r"\bAPPROVED\b", re.IGNORECASE)
    for anchor in reversed(list(explicit.finditer(text))):
        if _is_cited_context(text, anchor.start()):
            continue
        year, kind = _find_year_near(text, anchor.end())
        if year:
            return year, kind
    # Date stamp above or below the signature block.
    for anchor in reversed(list(APPROVE_ANCHOR_RE.finditer(text))):
        lo = max(0, anchor.start() - DATE_WINDOW)
        year, kind = _find_year_near(text, lo, window=DATE_WINDOW * 2, allow_bare_year=False)
        if year:
            return year, kind
    return None, "none"


# --------------------------------------------------------------------------- #
# Text cleaning and preprocessing
# --------------------------------------------------------------------------- #

import unicodedata
from datetime import date, datetime

# Boilerplate lines that repeat on every ordinance and carry no topical signal.
BOILERPLATE_LINES = {
    "republic of the philippines", "city of davao", "davao city",
    "office of the sangguniang panlungsod", "sangguniang panlungsod",
    "office of the city council", "lungsod ng dabaw",
}
PAGE_FURNITURE_RE = re.compile(
    r"^\s*(?:-\s*\d+\s*-|\[?\d{1,3}\]?|page\s+\d+(?:\s+of\s+\d+)?"
    r"|p\.\s*\d+|\d+\s*\|\s*page)\s*$", re.IGNORECASE)
# A line that is mostly punctuation or stray glyphs: OCR debris.
NOISE_LINE_RE = re.compile(r"^[^A-Za-z0-9]{0,4}[^A-Za-z0-9\s]{2,}[^A-Za-z0-9]{0,4}$")
HYPHEN_BREAK_RE = re.compile(r"(\w)[-\u2010\u2011]\s*\n\s*(\w)")
MULTISPACE_RE = re.compile(r"[ \t\u00a0]{2,}")
BLANKLINES_RE = re.compile(r"\n{3,}")

# Conservative OCR repairs: only forms that are unambiguous in this corpus.
OCR_FIXES = [
    (re.compile(r"\bORDlNANCE\b", re.IGNORECASE), "ORDINANCE"),
    (re.compile(r"\bSANGGUN[1I]ANG\b", re.IGNORECASE), "SANGGUNIANG"),
    (re.compile(r"\bPANLUNGS0D\b", re.IGNORECASE), "PANLUNGSOD"),
    (re.compile(r"\bSER[1I]ES\b", re.IGNORECASE), "SERIES"),
    (re.compile(r"\bENACTEO\b", re.IGNORECASE), "ENACTED"),
    (re.compile(r"\bAPPR0VED\b", re.IGNORECASE), "APPROVED"),
    (re.compile(r"\bSECT[1I]ON\b", re.IGNORECASE), "SECTION"),
]

TITLE_RE = re.compile(
    r"(AN?\s+ORDINANCE\b[\s\S]{0,900}?)"
    r"(?=\n\s*\n|\bBE\s+IT\s+ORDAINED\b|\bWHEREAS\b|\bSECTION\s+1\b)",
    re.IGNORECASE)
SECTION_RE = re.compile(r"^\s*SEC(?:TION|\.)?\s*\d+", re.IGNORECASE | re.MULTILINE)
WHEREAS_RE = re.compile(r"\bWHEREAS\b", re.IGNORECASE)
SPONSOR_RE = re.compile(
    r"(?:SPONSOR|AUTHOR|PROPONENT)S?\s*[:\-]\s*([^\n]{3,120})", re.IGNORECASE)
MAYOR_NAME_RE = re.compile(
    r"([A-Z][A-Za-z.\-]+(?:\s+[A-Z][A-Za-z.\-]+){1,4})\s*\n\s*(?:CITY\s+MAYOR|ACTING\s+MAYOR)",
    re.IGNORECASE)
PRESIDING_RE = re.compile(
    r"([A-Z][A-Za-z.\-]+(?:\s+[A-Z][A-Za-z.\-]+){1,4})\s*\n\s*"
    r"(?:CITY\s+VICE[\s\-]?MAYOR|PRESIDING\s+OFFICER)", re.IGNORECASE)

STOPWORDS = {
    "an", "a", "the", "of", "to", "for", "and", "or", "in", "on", "at", "by",
    "with", "from", "this", "that", "these", "those", "be", "it", "is", "are",
    "was", "were", "shall", "may", "other", "purposes", "ordinance", "city",
    "davao", "hereby", "thereof", "therein", "such", "any", "all", "as", "its",
    "into", "under", "upon", "which", "who", "whom", "not", "no", "amending",
    "amended", "providing", "provided", "establishing", "known", "otherwise",
    "appropriating", "funds", "therefor", "certain", "same", "per", "also",
    "series", "purposes", "thereto", "pursuant", "repealing", "further",
}

# Clauses inside a title that describe the AMENDED instrument, not this one.
# "OTHERWISE KNOWN AS <popular title>" is deliberately NOT stripped: in an
# amendatory ordinance that clause often carries the only topical signal in the
# title, as in "...OTHERWISE KNOWN AS THE DAVAO CITY TRAFFIC CODE".
TITLE_NOISE_RE = re.compile(
    r"(?:,?\s*(?:SERIES\s+OF\s+(?:19|20)\d{2}|AS\s+AMENDED"
    r"|AND\s+FOR\s+OTHER\s+PURPOSES))", re.IGNORECASE)


def clean_ordinance_text(raw: str) -> Tuple[str, Dict[str, Any]]:
    """Normalise raw extracted text for downstream NLP.

    Returns (clean_text, stats). The cleaning is deliberately conservative:
    it removes page furniture and repeated masthead lines, rejoins words split
    across a line break, and normalises unicode and whitespace. It does NOT
    lowercase, stem, or strip stopwords, because the topic-modelling stage
    should own those decisions and because the temporal signals are extracted
    from the RAW text, never from this output.
    """
    if not raw:
        return "", {"clean_char_count": 0, "clean_word_count": 0,
                    "removed_chars": 0, "dropped_lines": 0, "rejoined_words": 0,
                    "noise_line_ratio": 0.0}

    original_len = len(raw)
    text = unicodedata.normalize("NFKC", raw)
    text = (text.replace("\u2018", "'").replace("\u2019", "'")
                .replace("\u201c", '"').replace("\u201d", '"')
                .replace("\u2013", "-").replace("\u2014", "-")
                .replace("\ufeff", ""))
    for pattern, replacement in OCR_FIXES:
        text = pattern.sub(replacement, text)

    rejoined = len(HYPHEN_BREAK_RE.findall(text))
    text = HYPHEN_BREAK_RE.sub(r"\1\2", text)

    kept, dropped, noise = [], 0, 0
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            kept.append("")
            continue
        if PAGE_FURNITURE_RE.match(stripped):
            dropped += 1
            continue
        if stripped.lower().strip(".,:;-") in BOILERPLATE_LINES:
            dropped += 1
            continue
        if NOISE_LINE_RE.match(stripped):
            dropped += 1
            noise += 1
            continue
        kept.append(MULTISPACE_RE.sub(" ", stripped))

    clean = BLANKLINES_RE.sub("\n\n", "\n".join(kept)).strip()
    total_lines = max(1, len(text.splitlines()))
    return clean, {
        "clean_char_count": len(clean),
        "clean_word_count": len(clean.split()),
        "removed_chars": original_len - len(clean),
        "dropped_lines": dropped,
        "rejoined_words": rejoined,
        "noise_line_ratio": round(noise / total_lines, 4),
    }


def _parse_date_string(fragment: str) -> Optional[str]:
    """Turn 'March 15, 2016' or '15th day of March, 2016' into '2016-03-15'."""
    for pattern in DATE_PATTERNS[:2]:
        match = pattern.search(fragment)
        if not match:
            continue
        month_word = re.search(MONTH_RE, match.group(0), re.IGNORECASE)
        if not month_word:
            continue
        month = MONTHS.get(month_word.group(0).lower().strip("."))
        digits = re.findall(r"\d{1,4}", match.group(0))
        day = next((int(d) for d in digits if len(d) <= 2 and 1 <= int(d) <= 31), None)
        year = _plausible_year(int(match.groups()[-1]))
        if month and day and year:
            try:
                return date(year, month, day).isoformat()
            except ValueError:
                return None
    return None


def extract_full_dates(text: str) -> Dict[str, Optional[str]]:
    """ISO enactment and approval dates, not just their years.

    The temporal validator only needs the year, but a dynamic topic model can
    use month-level resolution, and the Obsidian note should show the real date.
    """
    out: Dict[str, Optional[str]] = {"enactment_date": None, "approval_date": None}
    for anchor in ENACT_ANCHOR_RE.finditer(text):
        if _is_cited_context(text, anchor.start()):
            continue
        iso = _parse_date_string(text[anchor.end():anchor.end() + DATE_WINDOW])
        if iso:
            out["enactment_date"] = iso
            break
    explicit = re.compile(r"\bAPPROVED\b", re.IGNORECASE)
    for anchor in reversed(list(explicit.finditer(text))):
        if _is_cited_context(text, anchor.start()):
            continue
        iso = _parse_date_string(text[anchor.end():anchor.end() + DATE_WINDOW])
        if iso:
            out["approval_date"] = iso
            break
    return out


def _slug(value: str) -> str:
    value = unicodedata.normalize("NFKD", str(value)).encode("ascii", "ignore").decode()
    value = re.sub(r"[^A-Za-z0-9]+", "-", value).strip("-").lower()
    return value or "untitled"


def extract_document_metadata(raw_text: str, clean_text: str, filename: str,
                              self_number: Optional[str]) -> Dict[str, Any]:
    """Bibliographic and structural metadata, for the CSV and the vault note."""
    title_match = TITLE_RE.search(raw_text)
    title = ""
    if title_match:
        title = MULTISPACE_RE.sub(" ", title_match.group(1).replace("\n", " ")).strip()
        title = re.sub(r"\s*[.,;]\s*$", "", title)[:400]

    cited = []
    for match in ORD_NO_RE.finditer(raw_text):
        number = f"{match.group(1)}-{match.group(2)}"
        if number != self_number and number not in cited:
            cited.append(number)

    council = COUNCIL_RE.search(raw_text[:HEADER_CHARS])
    session = SESSION_RE.search(raw_text[:HEADER_CHARS])
    sponsor = SPONSOR_RE.search(raw_text)
    mayor = MAYOR_NAME_RE.search(raw_text)
    presiding = PRESIDING_RE.search(raw_text)

    # Keyword topics describe THIS ordinance, so strip the clauses that describe
    # the instrument it amends before extracting them.
    topical_title = TITLE_NOISE_RE.sub("", title)
    words = [w for w in re.findall(r"[A-Za-z]{4,}", topical_title.lower())
             if w not in STOPWORDS]
    seen, keywords = set(), []
    for word in words:
        if word not in seen:
            seen.add(word)
            keywords.append(word)
    keywords = keywords[:6]

    return {
        "title": title,
        "cited_ordinances": "; ".join(cited[:12]),
        "cited_ordinance_count": len(cited),
        "is_amendatory": bool(re.search(r"\bAMEND(?:ING|ED|ATORY)\b", title, re.IGNORECASE)),
        "council_term": int(council.group(1)) if council else None,
        "session_label": session.group(0).strip() if session else "",
        "sponsor": sponsor.group(1).strip() if sponsor else "",
        "approving_mayor": mayor.group(1).strip() if mayor else "",
        "presiding_officer": presiding.group(1).strip() if presiding else "",
        "section_count": len(SECTION_RE.findall(clean_text)),
        "whereas_count": len(WHEREAS_RE.findall(clean_text)),
        "subject_keywords": "; ".join(keywords),
    }


# --------------------------------------------------------------------------- #
# Ordinance number: filename first, bounded header second
# --------------------------------------------------------------------------- #

def parse_filename_ordinance(filename: str) -> Tuple[Optional[str], Optional[int]]:
    """'Ordinance No. 0118-16.pdf' -> ('0118-16', 2016)."""
    match = FILENAME_ORD_RE.search(Path(filename).stem)
    if not match:
        return None, None
    return f"{match.group(1)}-{match.group(2)}", normalize_suffix_year(match.group(2))


def parse_header_ordinance(text: str) -> Tuple[Optional[str], Optional[int], int]:
    """Find the document's OWN ordinance number in the header region.

    Returns (number, year, n_candidates_rejected_as_citations). Matches preceded
    by amending/repealing/pursuant-to language are discarded: in Davao titles
    such as "AN ORDINANCE AMENDING ORDINANCE NO. 0234-15 ..." that citation is
    the first match in the file and was previously winning outright.
    """
    header = text[:HEADER_CHARS]
    rejected = 0
    for match in ORD_NO_RE.finditer(header):
        prefix = header[max(0, match.start() - 100):match.start()]
        if CITATION_CUE_RE.search(prefix):
            rejected += 1
            continue
        return (f"{match.group(1)}-{match.group(2)}",
                normalize_suffix_year(match.group(2)), rejected)
    return None, None, rejected


def extract_series_year(text: str) -> Optional[int]:
    """Series year from the header region, skipping cited ordinances.

    A body-wide search picks up "Series of 1995" from an amended ordinance
    quoted in the title or whereas clauses, which is exactly how a correctly
    filed 2016 ordinance acquired a 1995 series year in the v1 report.
    """
    header = text[:HEADER_CHARS]
    for match in SERIES_RE.finditer(header):
        prefix = header[max(0, match.start() - 120):match.start()]
        if CITATION_CUE_RE.search(prefix):
            continue
        return _plausible_year(int(match.group(1)))
    return None


def extract_council_year(text: str) -> Optional[int]:
    match = COUNCIL_RE.search(text[:HEADER_CHARS])
    return council_term_to_year(int(match.group(1))) if match else None


def extract_year_signals(raw_text: str, filename: str = "") -> Dict[str, Any]:
    """Four independent year signals plus provenance for each."""
    file_no, file_year = parse_filename_ordinance(filename)
    head_no, head_year, rejected = parse_header_ordinance(raw_text)

    # Filename is authoritative for the self-number; the header corroborates it.
    ordinance_number = file_no or head_no
    ordinance_no_year = file_year if file_year is not None else head_year
    number_agreement = (file_no is not None and head_no is not None and file_no == head_no)

    enactment_year, enact_kind = extract_enactment_year(raw_text)
    approval_year, approval_kind = extract_approval_year(raw_text)

    return {
        "ordinance_number": ordinance_number,
        "ordinance_number_source": ("filename" if file_no else ("header" if head_no else "none")),
        "filename_header_number_match": number_agreement,
        "citation_candidates_rejected": rejected,
        "detected_series_year": extract_series_year(raw_text),
        "detected_ordinance_no_year": ordinance_no_year,
        "detected_enactment_year": enactment_year,
        "detected_approval_year": approval_year,
        "enactment_date_kind": enact_kind,
        "approval_date_kind": approval_kind,
        "council_term_year": extract_council_year(raw_text),
    }


# --------------------------------------------------------------------------- #
# Consensus resolution
# --------------------------------------------------------------------------- #

def resolve_ordinance_year(signals: Dict[str, Any], folder_year: int,
                           study_window: Tuple[int, int] = DEFAULT_WINDOW,
                           has_text: bool = True) -> Dict[str, Any]:
    """Weighted consensus with an honest confidence score.

    confidence_score = (weight of signals agreeing with the winner)
                     - 0.5 * (weight of signals disagreeing), clipped to [0, 1].

    So four agreeing signals give 1.00, enactment alone gives 0.45, and the
    ordinance-number suffix alone gives 0.25. The previous formula divided by
    the active weight, which handed 1.00 to every single-signal resolution and
    is why the 2016 report showed conf 1.00 on files with one usable field.
    """
    votes: Dict[int, float] = {}
    present: Dict[str, int] = {}
    for key, weight in WEIGHTS.items():
        year = signals.get(key)
        if year is not None:
            votes[year] = votes.get(year, 0.0) + weight
            present[key] = year

    resolved_year: Optional[int] = None
    if votes:
        # Ties broken by signal priority, not by dict insertion order.
        priority = list(WEIGHTS)
        def tie_key(year: int) -> Tuple[float, int]:
            best = min((priority.index(k) for k, v in present.items() if v == year),
                       default=len(priority))
            return (votes[year], -best)
        resolved_year = max(votes, key=tie_key)
    elif signals.get("council_term_year") is not None:
        resolved_year = signals["council_term_year"]

    agreeing = sum(w for k, w in WEIGHTS.items() if present.get(k) == resolved_year)
    disagreeing = sum(w for k, w in WEIGHTS.items()
                      if k in present and present[k] != resolved_year)
    confidence = 0.0 if resolved_year is None else max(0.0, min(1.0, agreeing - 0.5 * disagreeing))
    n_agree = sum(1 for k in present if present[k] == resolved_year)

    conflicts = []
    en, ap = signals.get("detected_enactment_year"), signals.get("detected_approval_year")
    if en and ap and en != ap:
        conflicts.append(f"enacted {en} vs approved {ap}")
    se, on = signals.get("detected_series_year"), signals.get("detected_ordinance_no_year")
    if se and on and se != on:
        conflicts.append(f"series {se} vs ord-no {on}")
    if signals.get("ordinance_number_source") == "header" and signals.get("ordinance_number"):
        conflicts.append("number read from header, filename unparsed")

    mismatch = resolved_year is not None and resolved_year != folder_year
    corroborated = n_agree >= 2 or signals.get("detected_enactment_year") == resolved_year

    if not has_text:
        # No usable text layer. The filename alone is not document evidence, so
        # the file is routed to review rather than silently counted as valid.
        conflicts.append("no extractable text; filename-only inference")
        status = "unresolved"
    elif resolved_year is None:
        status = "unresolved"
    elif mismatch and confidence >= MISFILE_MIN_CONFIDENCE and corroborated:
        status = "out_of_scope" if not (study_window[0] <= resolved_year <= study_window[1]) \
            else "misfiled"
    elif mismatch:
        status = "review"          # a mismatch we do not trust yet
    elif not (study_window[0] <= resolved_year <= study_window[1]):
        status = "out_of_scope"
    else:
        status = "valid"

    return {
        "resolved_year": resolved_year,
        "confidence_score": round(confidence, 2),
        "agreeing_signals": n_agree,
        "available_signals": len(present),
        "temporal_status": status,
        "is_misfiled": status in {"misfiled", "out_of_scope"} and mismatch,
        "is_out_of_scope": (resolved_year is not None
                            and not (study_window[0] <= resolved_year <= study_window[1])),
        "needs_review": status in {"review", "unresolved"},
        "conflict_notes": "; ".join(conflicts),
    }


# --------------------------------------------------------------------------- #
# Folder processing
# --------------------------------------------------------------------------- #

def process_year_folder(folder_year: int, base_raw_dir: Path,
                        study_window: Tuple[int, int],
                        cache_root: Optional[Path] = None,
                        use_ocr: bool = True,
                        overrides: Optional[Dict[str, Dict[str, Any]]] = None,
                        clean_text_root: Optional[Path] = None
                        ) -> List[Dict[str, Any]]:
    raw_folder = base_raw_dir / str(folder_year)
    records: List[Dict[str, Any]] = []
    if not raw_folder.exists():
        logger.warning("Raw directory does not exist: %s", raw_folder)
        return records

    pdf_files = sorted(raw_folder.glob("*.pdf"))
    logger.info("Analyzing %d PDF(s) in '%s'", len(pdf_files), raw_folder)
    cache_dir = (cache_root / str(folder_year)) if cache_root else None

    for pdf_path in pdf_files:
        text, method, page_count, ocr_pages = extract_pdf_content(
            pdf_path, cache_dir=cache_dir, use_ocr=use_ocr)
        signals = extract_year_signals(text, filename=pdf_path.name)
        resolution = resolve_ordinance_year(
            signals, folder_year, study_window,
            has_text=len(text.strip()) >= NO_TEXT_CHARS)

        # Cleaning and metadata run on a copy; the temporal signals above are
        # always taken from the RAW text so that cleaning can never move a year.
        clean_text, clean_stats = clean_ordinance_text(text)
        metadata = extract_document_metadata(text, clean_text, pdf_path.name,
                                             signals.get("ordinance_number"))
        metadata.update(extract_full_dates(text))

        clean_text_path = ""
        if clean_text_root is not None:
            target_dir = clean_text_root / str(folder_year)
            target_dir.mkdir(parents=True, exist_ok=True)
            target = target_dir / (pdf_path.stem + ".txt")
            target.write_text(clean_text, encoding="utf-8")
            clean_text_path = str(target)

        words = len(text.split())
        record = {
            "schema_version": PIPELINE_SCHEMA_VERSION,
            "filename": pdf_path.name,
            "file_path": str(pdf_path),
            "file_hash": compute_file_hash(pdf_path),
            "folder_year": folder_year,
            "extraction_method": method,
            "page_count": page_count,
            "ocr_page_count": ocr_pages,
            **signals,
            **resolution,
            "char_count": len(text),
            "word_count": words,
            "chars_per_page": round(len(text) / page_count, 1) if page_count else 0.0,
            "is_sparse": len(text.strip()) < SPARSE_DOC_CHARS,
            "resolution_source": "consensus",
            "manually_verified": False,
            **clean_stats,
            **metadata,
            "clean_text_path": clean_text_path,
        }

        override = (overrides or {}).get(pdf_path.name)
        if override:
            record = apply_year_override(record, override, study_window)
            logger.info("[OVERRIDE] %s | human verdict %s (was %s)",
                        pdf_path.name, record["resolved_year"], resolution["resolved_year"])
        records.append(record)

        status = record["temporal_status"]
        if status in {"misfiled", "out_of_scope"}:
            logger.warning(
                "[%s] %s | folder=%s -> resolved=%s (conf %.2f, %d/%d signals agree) | "
                "method=%s | enacted=%s ord_no=%s series=%s approved=%s%s",
                status.upper(), pdf_path.name, folder_year, record["resolved_year"],
                record["confidence_score"], record["agreeing_signals"],
                record["available_signals"], method,
                record["detected_enactment_year"], record["detected_ordinance_no_year"],
                record["detected_series_year"], record["detected_approval_year"],
                " | " + record["conflict_notes"] if record["conflict_notes"] else "")
        elif status in {"review", "unresolved"}:
            logger.warning(
                "[%s] %s | folder=%s resolved=%s (conf %.2f) | not actioned automatically%s",
                status.upper(), pdf_path.name, folder_year, record["resolved_year"],
                record["confidence_score"],
                " | " + record["conflict_notes"] if record["conflict_notes"] else "")

    return records


def debug_headers(folder_year: int, base_raw_dir: Path, sample: int = 8) -> None:
    """Dump the header region and the date-anchor neighbourhoods of N files.

    Run this FIRST on a new corpus. Regex tuning should be driven by the actual
    layout, not by assumption; a low enactment coverage number is a parser
    symptom, not a property of the documents.
    """
    raw_folder = base_raw_dir / str(folder_year)
    for pdf_path in sorted(raw_folder.glob("*.pdf"))[:sample]:
        text, method, pages, _ = extract_pdf_content(pdf_path, use_ocr=False)
        print("=" * 78)
        print(f"{pdf_path.name}  [{method}, {pages} page(s), {len(text)} chars]")
        print("--- header region ---")
        print(text[:600].strip())
        for label, pattern in (("ENACTED", ENACT_ANCHOR_RE), ("APPROVED", APPROVE_ANCHOR_RE)):
            hit = pattern.search(text)
            print(f"--- {label} anchor ---")
            print(text[hit.start():hit.start() + 220].strip() if hit else "(anchor not found)")
        print("--- parsed ---", extract_year_signals(text, pdf_path.name))


# --------------------------------------------------------------------------- #
# Relocation
# --------------------------------------------------------------------------- #

def execute_relocation(df: pd.DataFrame, base_raw_dir: Path, move: bool = False,
                       assume_yes: bool = False,
                       min_confidence: float = RELOCATE_MIN_CONFIDENCE) -> None:
    """Copy (default) or move confidently misfiled PDFs.

    Copy is the default because a corpus you are about to cite in a thesis
    should not be reshuffled destructively by a regex. Anything below the
    confidence bar is listed for manual review and left alone.
    """
    candidates = df[df["is_misfiled"] & df["resolved_year"].notnull()]
    eligible = candidates[candidates["confidence_score"] >= min_confidence]
    held = candidates[candidates["confidence_score"] < min_confidence]

    for _, row in held.iterrows():
        logger.warning("HELD FOR MANUAL REVIEW (conf %.2f < %.2f): %s",
                       row["confidence_score"], min_confidence, row["filename"])
    if eligible.empty:
        logger.info("No misfiled files clear the %.2f confidence bar for relocation.",
                    min_confidence)
        return

    action = "MOVE" if move else "COPY"
    print("\n" + "=" * 80)
    print(f"{action}: {len(eligible)} ordinance(s) eligible (confidence >= {min_confidence})")
    for _, row in eligible.iterrows():
        print(f"  - {row['filename']}: data/raw/{row['folder_year']}/ -> "
              f"data/raw/{int(row['resolved_year'])}/  "
              f"(conf {row['confidence_score']:.2f}, {row['agreeing_signals']} signals agree)")
    print("=" * 80)

    if not assume_yes and input(f"Execute {action.lower()}? [y/N]: ").strip().lower() not in {"y", "yes"}:
        logger.info("Relocation aborted by user.")
        return

    for _, row in eligible.iterrows():
        src = Path(row["file_path"])
        dest_dir = base_raw_dir / str(int(row["resolved_year"]))
        dest = dest_dir / src.name
        if not src.exists():
            logger.error("Source missing, skipped: %s", src)
            continue
        if dest.exists():
            logger.error("Destination exists, skipped: %s", dest)
            continue
        dest_dir.mkdir(parents=True, exist_ok=True)
        try:
            shutil.move(str(src), str(dest)) if move else shutil.copy2(str(src), str(dest))
            logger.info("%s: %s -> %s", action.title(), src.name, dest)
        except Exception as exc:
            logger.error("Failed to relocate %s: %s", src.name, exc)


# --------------------------------------------------------------------------- #
# Reporting
# --------------------------------------------------------------------------- #

STATUS_LABELS = {
    "valid": "Temporally valid (matches folder)",
    "misfiled": "Misfiled (in-window, wrong folder)",
    "out_of_scope": "Out-of-scope year",
    "review": "Flagged for manual review",
    "unresolved": "Unresolved (no year signal)",
}
STATUS_ORDER = ["valid", "misfiled", "out_of_scope", "review", "unresolved"]
STATUS_COLORS = {"valid": "#2a9d8f", "misfiled": "#e76f51", "out_of_scope": "#e9c46a",
                 "review": "#8ab6d6", "unresolved": "#adb5bd"}


def validate_pipeline_frame(df: pd.DataFrame, context: str = "pipeline output") -> None:
    """Validate the minimum data contract before writing thesis artifacts."""
    required = {
        "filename", "folder_year", "temporal_status", "resolved_year",
        "confidence_score", "is_sparse", "file_hash", "ordinance_number",
    }
    missing = sorted(required - set(df.columns))
    if missing:
        raise ValueError(f"{context} is missing required column(s): {', '.join(missing)}")
    unknown_statuses = sorted(set(df["temporal_status"].dropna()) - set(STATUS_ORDER))
    if unknown_statuses:
        raise ValueError(f"{context} contains unknown temporal status(es): {unknown_statuses}")
    if df[["folder_year", "filename"]].duplicated().any():
        raise ValueError(f"{context} contains duplicate folder-year/filename records")
    confidence = pd.to_numeric(df["confidence_score"], errors="coerce")
    if confidence.isna().any() or ((confidence < 0) | (confidence > 1)).any():
        raise ValueError(f"{context} contains confidence scores outside [0, 1]")


def _pct(part: int, whole: int) -> str:
    return f"{(part / whole * 100):.1f}%" if whole else "0.0%"


def _yr(value: Any) -> str:
    """Render a nullable year column as 2016, not 2016.0."""
    return "-" if value is None or pd.isnull(value) else str(int(value))


def generate_eda_markdown_report(df: pd.DataFrame, folder_year: int, report_path: Path,
                                 study_window: Tuple[int, int]) -> None:
    total = len(df)
    if total == 0:
        report_path.write_text(f"# EDA Report: {folder_year}\n\nNo PDF documents found.",
                               encoding="utf-8")
        return

    counts = {s: int((df["temporal_status"] == s).sum()) for s in STATUS_ORDER}
    method_counts = df["extraction_method"].value_counts().to_dict()

    # Duplicates: byte-identical files, and repeated ordinance NUMBERS.
    dup_hash_groups = df[df.duplicated(subset=["file_hash"], keep=False)]
    numbered = df[df["ordinance_number"].notnull()]
    dup_no_groups = numbered[numbered.duplicated(subset=["ordinance_number"], keep=False)]

    completeness = {
        "Enactment date": int(df["detected_enactment_year"].notnull().sum()),
        "Ordinance number": int(df["detected_ordinance_no_year"].notnull().sum()),
        "Series header": int(df["detected_series_year"].notnull().sum()),
        "Approval date": int(df["detected_approval_year"].notnull().sum()),
    }
    num_from_filename = int((df["ordinance_number_source"] == "filename").sum())
    num_agree = int(df["filename_header_number_match"].sum())
    rejected_citations = int(df["citation_candidates_rejected"].sum())

    lines = [
        f"# Legal NLP EDA & Temporal Audit Report: {folder_year}",
        "*Generated automatically by `src/ordinance_eda_pipeline.py`*",
        "",
        f"Study window: {study_window[0]}-{study_window[1]} | "
        f"confidence bar for misfiling: {MISFILE_MIN_CONFIDENCE:.2f} | "
        f"for relocation: {RELOCATE_MIN_CONFIDENCE:.2f}",
        "",
        "## 1. Executive summary and file inventory",
        "",
        "Categories below are mutually exclusive, so the percentages sum to 100%.",
        "",
        "| Classification | Count | Percentage |",
        "|---|---|---|",
        f"| **Total documents scanned** | {total} | 100.0% |",
    ]
    for status in STATUS_ORDER:
        lines.append(f"| {STATUS_LABELS[status]} | {counts[status]} | {_pct(counts[status], total)} |")
    lines += [
        "",
        "| Extraction | Count | Percentage |",
        "|---|---|---|",
    ]
    for method in ("Digital", "Hybrid", "OCR"):
        n = int(method_counts.get(method, 0))
        lines.append(f"| {method} | {n} | {_pct(n, total)} |")
    lines += [
        f"| Pages OCR'd in total | {int(df['ocr_page_count'].sum())} | - |",
        "",
        f"Mean consensus confidence: **{df['confidence_score'].mean():.2f}** "
        f"(median {df['confidence_score'].median():.2f}). "
        f"Documents resolved on a single signal: "
        f"{int((df['agreeing_signals'] <= 1).sum())} "
        f"({_pct(int((df['agreeing_signals'] <= 1).sum()), total)}).",
        "",
        "## 2. Duplicate analysis",
        "",
        f"- Byte-identical files (SHA-256): **{dup_hash_groups['file_hash'].nunique()}** "
        f"group(s) covering {len(dup_hash_groups)} file(s)",
        f"- Repeated ordinance numbers: **{dup_no_groups['ordinance_number'].nunique()}** "
        f"group(s) covering {len(dup_no_groups)} file(s)",
        f"- Files with no parseable ordinance number: **{total - len(numbered)}**",
        "",
    ]
    if not dup_no_groups.empty:
        lines += ["| Ordinance No. | Files | Resolved years |", "|---|---|---|"]
        for number, grp in dup_no_groups.groupby("ordinance_number"):
            files = ", ".join(f"`{f}`" for f in grp["filename"])
            years = ", ".join(str(y) for y in sorted(grp["resolved_year"].dropna().unique()))
            lines.append(f"| `{number}` | {files} | {years or 'n/a'} |")
        lines.append("")

    lines += [
        "## 3. Signal extraction completeness",
        "",
        "| Component signal | Extracted | Coverage |",
        "|---|---|---|",
    ]
    for name, count in completeness.items():
        lines.append(f"| {name} | {count} / {total} | {_pct(count, total)} |")
    lines += [
        "",
        f"Ordinance number source: filename {num_from_filename}/{total}, "
        f"filename and header agree on {num_agree}. "
        f"Citation-style references rejected before they could hijack the signal: "
        f"**{rejected_citations}**.",
        "",
    ]
    enact_cov = completeness["Enactment date"] / total
    if enact_cov < 0.5:
        lines += [
            f"> **Parser health warning.** Enactment-date coverage is {_pct(completeness['Enactment date'], total)}. "
            "An enactment clause appears in virtually every enacted ordinance, so a low rate here "
            "is a parsing failure, not a corpus property. Run `--debug-headers` on this folder and "
            "tune `ENACT_ANCHOR_RE` / `DATE_PATTERNS` against the real layout before treating any "
            "temporal verdict in this report as final.",
            "",
        ]

    lines += [
        "## 4. Corpus text characteristics",
        "",
        "| Metric | Value |",
        "|---|---|",
        f"| Mean characters | {int(df['char_count'].mean()):,} |",
        f"| Median characters | {int(df['char_count'].median()):,} |",
        f"| Mean words | {int(df['word_count'].mean()):,} |",
        f"| Shortest document | {int(df['char_count'].min()):,} chars |",
        f"| Longest document | {int(df['char_count'].max()):,} chars |",
        f"| Mean pages | {df['page_count'].mean():.1f} |",
        f"| Mean characters per page | {df['chars_per_page'].mean():,.0f} |",
        f"| Suspected incomplete (<{SPARSE_DOC_CHARS} chars) | {int(df['is_sparse'].sum())} files |",
        f"| Low text density (<{OCR_PAGE_MIN_CHARS} chars/page) | "
        f"{int((df['chars_per_page'] < OCR_PAGE_MIN_CHARS).sum())} files |",
        "",
        "## 5. Temporal discrepancies and misfiled files",
        "",
    ]

    actioned = df[df["temporal_status"].isin(["misfiled", "out_of_scope"])]
    if actioned.empty:
        lines += ["No confidently misfiled or out-of-scope ordinances detected.", ""]
    else:
        lines += [
            "| Filename | Ord. No. | Status | Folder | Resolved | Conf. | Agree | "
            "Enacted | Ord-no | Series | Approved | Suggested path |",
            "|---|---|---|---|---|---|---|---|---|---|---|---|",
        ]
        for _, r in actioned.sort_values(["resolved_year", "filename"]).iterrows():
            dest = (f"`data/raw/{int(r['resolved_year'])}/`"
                    if pd.notnull(r["resolved_year"]) else "`Manual review`")
            lines.append(
                f"| `{r['filename']}` | {r['ordinance_number'] or 'n/a'} | {r['temporal_status']} | "
                f"{r['folder_year']} | **{int(r['resolved_year'])}** | {r['confidence_score']:.2f} | "
                f"{r['agreeing_signals']}/{r['available_signals']} | "
                f"{_yr(r['detected_enactment_year'])} | {_yr(r['detected_ordinance_no_year'])} | "
                f"{_yr(r['detected_series_year'])} | {_yr(r['detected_approval_year'])} | {dest} |")
        lines.append("")

    review = df[df["temporal_status"].isin(["review", "unresolved"])]
    lines += ["### Flagged for manual review (not actioned)", ""]
    if review.empty:
        lines += ["None.", ""]
    else:
        lines += ["| Filename | Resolved | Conf. | Agree | Reason |", "|---|---|---|---|---|"]
        for _, r in review.iterrows():
            reason = r["conflict_notes"] or ("no year signal recovered"
                                             if pd.isnull(r["resolved_year"])
                                             else "mismatch below confidence bar")
            resolved = _yr(r["resolved_year"])
            lines.append(f"| `{r['filename']}` | {resolved} | {r['confidence_score']:.2f} | "
                         f"{r['agreeing_signals']}/{r['available_signals']} | {reason} |")
        lines.append("")

    report_path.write_text("\n".join(lines), encoding="utf-8")


def generate_eda_outputs(df: pd.DataFrame, folder_year: int, eda_csv_dir: Path,
                         report_dir: Path, figures_dir: Path,
                         study_window: Tuple[int, int]) -> None:
    validate_pipeline_frame(df, f"EDA output for folder {folder_year}")
    for directory in (eda_csv_dir, report_dir, figures_dir):
        directory.mkdir(parents=True, exist_ok=True)

    csv_path = eda_csv_dir / f"ordinances_eda_summary_{folder_year}.csv"
    df.to_csv(csv_path, index=False)
    logger.info("Saved CSV summary: %s", csv_path)

    report_path = report_dir / f"eda_report_{folder_year}.md"
    generate_eda_markdown_report(df, folder_year, report_path, study_window)
    logger.info("Saved Markdown report: %s", report_path)

    fig_path = figures_dir / f"temporal_distribution_{folder_year}.png"
    plot_year_figure(df, folder_year, fig_path)
    logger.info("Saved figure: %s", fig_path)


def plot_year_figure(df: pd.DataFrame, folder_year: int, fig_path: Path) -> None:
    """Three panels: mutually exclusive status, resolved-year spread, signal coverage.

    Plain matplotlib rather than seaborn: `sns.barplot(palette=...)` without a
    `hue` is deprecated and errors on newer seaborn.
    """
    counts = [int((df["temporal_status"] == s).sum()) for s in STATUS_ORDER]
    fig, axes = plt.subplots(1, 3, figsize=(16, 5))

    bars = axes[0].bar([s.replace("_", "\n") for s in STATUS_ORDER], counts,
                       color=[STATUS_COLORS[s] for s in STATUS_ORDER])
    axes[0].bar_label(bars, padding=3)
    axes[0].set_title(f"Temporal validation, data/raw/{folder_year}/", weight="bold")
    axes[0].set_ylabel("Ordinance count")
    axes[0].set_ylim(0, max(counts + [1]) * 1.18)

    resolved = df["resolved_year"].dropna().astype(int)
    if not resolved.empty:
        spread = resolved.value_counts().sort_index()
        colors = ["#2a9d8f" if y == folder_year else "#e76f51" for y in spread.index]
        bars2 = axes[1].bar([str(y) for y in spread.index], spread.values, color=colors)
        axes[1].bar_label(bars2, padding=3)
        axes[1].set_ylim(0, spread.max() * 1.18)
        axes[1].tick_params(axis="x", rotation=45)
    axes[1].set_title("Resolved year distribution", weight="bold")
    axes[1].set_xlabel("Resolved year")

    signals = {"Enact": "detected_enactment_year", "Ord-no": "detected_ordinance_no_year",
               "Series": "detected_series_year", "Approve": "detected_approval_year"}
    cov = [df[c].notnull().mean() * 100 for c in signals.values()]
    bars3 = axes[2].bar(list(signals), cov, color="#457b9d")
    axes[2].bar_label(bars3, fmt="%.0f%%", padding=3)
    axes[2].axhline(50, color="#e76f51", linestyle="--", linewidth=1)
    axes[2].set_ylim(0, 112)
    axes[2].set_ylabel("Coverage (%)")
    axes[2].set_title("Signal extraction coverage", weight="bold")

    for ax in axes:
        ax.grid(axis="y", linestyle="--", alpha=0.4)
        for side in ("top", "right"):
            ax.spines[side].set_visible(False)

    fig.suptitle(f"Ordinance corpus temporal integrity, folder {folder_year}", fontsize=13)
    fig.tight_layout()
    fig.savefig(fig_path, dpi=200)
    plt.close(fig)


def generate_corpus_outputs(df: pd.DataFrame, eda_csv_dir: Path, report_dir: Path,
                            figures_dir: Path) -> None:
    """Nine-year rollup: one CSV, one crosstab report, one figure."""
    df.to_csv(eda_csv_dir / "ordinances_eda_summary_ALL.csv", index=False)
    crosstab = pd.crosstab(df["folder_year"], df["temporal_status"])
    crosstab = crosstab.reindex(columns=STATUS_ORDER, fill_value=0)

    lines = ["# Corpus-wide temporal audit", "",
             f"Total documents across all year folders: **{len(df)}**", "",
             "| Folder year | " + " | ".join(STATUS_LABELS[s] for s in STATUS_ORDER) +
             " | Total | Mean conf. |",
             "|---" * (len(STATUS_ORDER) + 3) + "|"]
    for year, row in crosstab.iterrows():
        mean_conf = df.loc[df["folder_year"] == year, "confidence_score"].mean()
        lines.append(f"| {year} | " + " | ".join(str(int(row[s])) for s in STATUS_ORDER) +
                     f" | {int(row.sum())} | {mean_conf:.2f} |")
    dup = df[df.duplicated(subset=["file_hash"], keep=False)]
    numbered = df[df["ordinance_number"].notnull()]
    dup_no = numbered[numbered.duplicated(subset=["ordinance_number"], keep=False)]
    lines += ["",
              f"Cross-year byte duplicates: {dup['file_hash'].nunique()} group(s), "
              f"{len(dup)} file(s).",
              f"Cross-year repeated ordinance numbers: {dup_no['ordinance_number'].nunique()} "
              f"group(s), {len(dup_no)} file(s).", ""]
    (report_dir / "eda_report_CORPUS.md").write_text("\n".join(lines), encoding="utf-8")

    fig, ax = plt.subplots(figsize=(11, 5))
    bottom = [0] * len(crosstab)
    for status in STATUS_ORDER:
        vals = crosstab[status].tolist()
        ax.bar([str(y) for y in crosstab.index], vals, bottom=bottom,
               label=STATUS_LABELS[status], color=STATUS_COLORS[status])
        bottom = [b + v for b, v in zip(bottom, vals)]
    ax.set_title("Temporal validation by folder year", weight="bold")
    ax.set_xlabel("Folder year")
    ax.set_ylabel("Ordinance count")
    ax.legend(fontsize=8, frameon=False)
    ax.grid(axis="y", linestyle="--", alpha=0.4)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    fig.tight_layout()
    fig.savefig(figures_dir / "temporal_distribution_CORPUS.png", dpi=200)
    plt.close(fig)
    logger.info("Saved corpus-wide CSV, report and figure.")


# --------------------------------------------------------------------------- #
# Manual adjudication: human overrides beat every automated signal
# --------------------------------------------------------------------------- #

OVERRIDE_COLUMNS = ["filename", "correct_year", "verified_by", "evidence", "note"]


def override_paths_for_year(project_root: Path, year: int,
                            explicit: Optional[Path] = None) -> List[Path]:
    """Which override files apply to one folder year.

    Per-year files let team members adjudicate different years in parallel
    without ever touching the same file, so git never has to merge two people's
    judgements. A shared file is still honoured for corpus-wide decisions; the
    per-year file wins on any filename listed in both.

    Resolution order (later wins):
      1. data/manual_year_overrides.csv                (shared, optional)
      2. data/manual_year_overrides_{year}.csv         (per-year, preferred)
      3. --overrides FILE, or every *_{year}.csv inside --overrides DIR
    """
    base = project_root / "data"
    paths = [base / "manual_year_overrides.csv",
             base / f"manual_year_overrides_{year}.csv"]
    if explicit is not None:
        if explicit.is_dir():
            paths += sorted(explicit.glob(f"*{year}*.csv"))
        else:
            paths.append(explicit)
    return [p for p in paths if p.exists()]


def load_year_overrides(paths) -> Dict[str, Dict[str, Any]]:
    """Read one or more override CSVs into {filename: {...}}.

    A row here is a human adjudication and outranks all four automated signals.
    Keeping it in a version-controlled CSV rather than hand-editing the output
    means the correction survives the next pipeline run, and the reviewer and
    their evidence are on the record for the thesis appendix.
    """
    if isinstance(paths, (str, Path)):
        paths = [Path(paths)]
    merged: Dict[str, Dict[str, Any]] = {}
    for path in paths:
        for name, entry in _load_one_override_file(Path(path)).items():
            if name in merged and merged[name]["correct_year"] != entry["correct_year"]:
                logger.warning("Override conflict for %s: %s then %s; using %s (%s)",
                               name, merged[name]["correct_year"], entry["correct_year"],
                               entry["correct_year"], path.name)
            merged[name] = entry
    return merged


def _load_one_override_file(path: Path) -> Dict[str, Dict[str, Any]]:
    if not path.exists():
        return {}
    frame = pd.read_csv(path, dtype={"filename": str})
    missing = [c for c in ("filename", "correct_year") if c not in frame.columns]
    if missing:
        logger.error("Overrides file %s is missing column(s): %s", path, ", ".join(missing))
        return {}
    overrides: Dict[str, Dict[str, Any]] = {}
    for _, row in frame.iterrows():
        year = _plausible_year(int(row["correct_year"])) if pd.notnull(row["correct_year"]) else None
        if year is None:
            logger.error("Override for %s has an implausible year; skipped.", row["filename"])
            continue
        overrides[str(row["filename"]).strip()] = {
            "correct_year": year,
            "verified_by": row.get("verified_by", ""),
            "evidence": row.get("evidence", ""),
            "note": row.get("note", ""),
        }
    logger.info("Loaded %d manual year override(s) from %s", len(overrides), path)
    return overrides


def apply_year_override(record: Dict[str, Any], override: Dict[str, Any],
                        study_window: Tuple[int, int]) -> Dict[str, Any]:
    """Overwrite the resolution for one record with the human verdict."""
    year = override["correct_year"]
    record["resolved_year"] = year
    record["confidence_score"] = 1.0
    record["resolution_source"] = "manual_override"
    record["manually_verified"] = True
    record["agreeing_signals"] = record.get("available_signals", 0)
    in_window = study_window[0] <= year <= study_window[1]
    mismatch = year != record["folder_year"]
    record["temporal_status"] = ("out_of_scope" if not in_window
                                 else "misfiled" if mismatch else "valid")
    record["is_misfiled"] = mismatch
    record["is_out_of_scope"] = not in_window
    record["needs_review"] = False
    evidence = str(override.get("evidence") or "").strip()
    who = str(override.get("verified_by") or "").strip()
    stamp = "manually verified" + (f" by {who}" if who else "") + \
            (f"; evidence: {evidence}" if evidence else "")
    record["conflict_notes"] = stamp
    return record


def emit_override_templates(df: pd.DataFrame, project_root: Path) -> List[Path]:
    """One template per folder year, so each reviewer owns a separate file."""
    written = []
    for year, grp in df.groupby("folder_year"):
        path = project_root / "data" / f"manual_year_overrides_TEMPLATE_{year}.csv"
        if emit_override_template(grp, path) is not None:
            written.append(path)
    return written


def emit_override_template(df: pd.DataFrame, path: Path) -> Path:
    """Write a pre-filled adjudication sheet of every file the pipeline flagged.

    Open it, correct the `correct_year` column where the pipeline got it wrong,
    delete the rows where it got it right, then re-run. Rows you leave in are
    treated as ground truth.
    """
    flagged = df[df["temporal_status"] != "valid"].copy()
    if flagged.empty:
        logger.info("Nothing flagged for %s; no override template needed.", path.stem)
        return None
    template = pd.DataFrame({
        "filename": flagged["filename"],
        "correct_year": flagged["resolved_year"],
        "verified_by": "",
        "evidence": "",
        "note": ("pipeline said " + flagged["temporal_status"] + ", folder "
                 + flagged["folder_year"].astype(str) + ", conf "
                 + flagged["confidence_score"].round(2).astype(str)
                 + ", signals E/O/S/A = "
                 + flagged["detected_enactment_year"].map(_yr) + "/"
                 + flagged["detected_ordinance_no_year"].map(_yr) + "/"
                 + flagged["detected_series_year"].map(_yr) + "/"
                 + flagged["detected_approval_year"].map(_yr)),
    })
    path.parent.mkdir(parents=True, exist_ok=True)
    template.to_csv(path, index=False)
    logger.info("Override template written: %s (%d flagged file(s) to adjudicate)",
                path, len(template))
    return path


# --------------------------------------------------------------------------- #
# Corpus curation: quarantine, purge, restore
# --------------------------------------------------------------------------- #

REMOVAL_CATEGORIES = ("out_of_scope", "misfiled", "review", "unresolved",
                      "duplicate", "sparse")
# Files needing adjudication are excluded from the modelling manifest by default.
# Misfiled but confidently resolved files remain eligible and are re-dated.
DEFAULT_REMOVAL = ("out_of_scope", "review", "unresolved", "duplicate", "sparse")


def flag_removal_reasons(df: pd.DataFrame, categories: Tuple[str, ...]) -> pd.DataFrame:
    """Attach a `removal_reason` column. Empty string means keep.

    Duplicate resolution keeps one representative per group rather than deleting
    the whole group: for byte-identical files the first by (folder_year,
    filename); for a repeated ordinance number the copy whose folder matches its
    resolved year, then the highest confidence, then the longest text.
    """
    df = df.copy()
    df["removal_reason"] = ""
    # A human verdict protects a file from every removal rule except the one
    # the human themselves confirmed: a year outside the study window.
    protected = df.get("manually_verified", pd.Series(False, index=df.index)).fillna(False) \
        & (df["temporal_status"] != "out_of_scope")

    def mark(mask, reason: str) -> None:
        target = mask & (df["removal_reason"] == "") & ~protected
        df.loc[target, "removal_reason"] = reason

    # Reason precedence: temporal decisions are more informative than duplicate
    # or sparsity labels. Sparseness is checked last so a genuinely out-of-scope
    # ordinance is not filed under "sparse" merely because its text is thin.
    if "out_of_scope" in categories:
        mark(df["temporal_status"] == "out_of_scope", "out_of_scope")
    if "misfiled" in categories:
        mark(df["temporal_status"] == "misfiled", "misfiled")
    if "review" in categories:
        mark(df["temporal_status"] == "review", "low_confidence_review")
    if "unresolved" in categories:
        mark(df["temporal_status"] == "unresolved", "unresolved")

    if "duplicate" in categories:
        dup_losers = []
        for _, grp in df[df["file_hash"].notnull()].groupby("file_hash"):
            if len(grp) > 1:
                keep = grp.sort_values(["folder_year", "filename"]).index[0]
                dup_losers += [i for i in grp.index if i != keep]
        numbered = df[df["ordinance_number"].notnull()]
        for _, grp in numbered.groupby("ordinance_number"):
            if len(grp) > 1:
                ranked = grp.assign(
                    _folder_ok=(grp["folder_year"] == grp["resolved_year"]).astype(int)
                ).sort_values(["_folder_ok", "confidence_score", "char_count"],
                              ascending=[False, False, False])
                dup_losers += list(ranked.index[1:])
        mark(df.index.isin(set(dup_losers)), "duplicate")

    if "sparse" in categories:
        mark(df["is_sparse"], "sparse_or_unreadable")

    return df


def curate_corpus(df: pd.DataFrame, project_root: Path,
                  categories: Tuple[str, ...] = DEFAULT_REMOVAL,
                  quarantine_dir: Optional[Path] = None,
                  purge: bool = False, dry_run: bool = False,
                  assume_yes: bool = False) -> pd.DataFrame:
    """Move excluded PDFs out of data/raw/ into a quarantine tree.

    Files are MOVED, not deleted, and every move is written to a manifest so the
    operation is reversible with --restore and citable in the limitations
    section of the thesis. Actual deletion requires --purge plus a typed
    confirmation, because an irreversible delete driven by a regex is not a
    defensible data-cleaning step.
    """
    quarantine_dir = quarantine_dir or (project_root / "data" / "quarantine")
    manifest_path = project_root / "data" / "EDA" / "quarantine_manifest.csv"
    flagged = df[df["removal_reason"] != ""]

    if flagged.empty:
        logger.info("Nothing matched the removal categories %s.", ", ".join(categories))
        return df

    summary = flagged["removal_reason"].value_counts().to_dict()
    action = "PERMANENTLY DELETE" if purge else "QUARANTINE (move)"
    print("\n" + "=" * 80)
    print(f"{action}: {len(flagged)} of {len(df)} file(s) "
          f"({len(flagged) / len(df) * 100:.1f}% of the corpus)")
    for reason, count in sorted(summary.items()):
        print(f"  {reason:24} {count}")
    print("-" * 80)
    for _, row in flagged.sort_values(["removal_reason", "filename"]).iterrows():
        resolved = _yr(row["resolved_year"])
        print(f"  [{row['removal_reason']:20}] {row['filename']}  "
              f"(folder {row['folder_year']}, resolved {resolved}, "
              f"conf {row['confidence_score']:.2f})")
    print("=" * 80)

    if dry_run:
        logger.info("Dry run: no files touched.")
        return df

    if not assume_yes:
        if purge:
            print("This cannot be undone. Type DELETE in capitals to proceed.")
            if input("> ").strip() != "DELETE":
                logger.info("Purge aborted.")
                return df
        elif input("Proceed? [y/N]: ").strip().lower() not in {"y", "yes"}:
            logger.info("Curation aborted by user.")
            return df

    from datetime import datetime
    stamp = datetime.now().isoformat(timespec="seconds")
    manifest_rows = []
    for idx, row in flagged.iterrows():
        src = Path(row["file_path"])
        if not src.exists():
            logger.error("Source missing, skipped: %s", src)
            continue
        if purge:
            src.unlink()
            dest = ""
            logger.warning("Deleted: %s", src.name)
        else:
            dest_dir = quarantine_dir / row["removal_reason"] / str(row["folder_year"])
            dest_dir.mkdir(parents=True, exist_ok=True)
            dest = dest_dir / src.name
            if dest.exists():
                logger.error("Quarantine destination exists, skipped: %s", dest)
                continue
            shutil.move(str(src), str(dest))
            logger.info("Quarantined (%s): %s", row["removal_reason"], src.name)
        df.loc[idx, "file_path"] = str(dest)
        manifest_rows.append({
            "timestamp": stamp, "filename": row["filename"],
            "original_path": str(src), "quarantine_path": str(dest),
            "action": "purge" if purge else "quarantine",
            "removal_reason": row["removal_reason"], "folder_year": row["folder_year"],
            "resolved_year": row["resolved_year"], "confidence_score": row["confidence_score"],
            "ordinance_number": row["ordinance_number"],
        })

    if manifest_rows:
        manifest = pd.DataFrame(manifest_rows)
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        manifest.to_csv(manifest_path, mode="a", index=False,
                        header=not manifest_path.exists())
        logger.info("Manifest updated: %s (%d row(s))", manifest_path, len(manifest))
    return df


def restore_from_quarantine(project_root: Path, assume_yes: bool = False) -> None:
    """Undo every quarantine move recorded in the manifest."""
    manifest_path = project_root / "data" / "EDA" / "quarantine_manifest.csv"
    if not manifest_path.exists():
        logger.error("No manifest at %s; nothing to restore.", manifest_path)
        return
    manifest = pd.read_csv(manifest_path)
    movable = manifest[manifest["action"] == "quarantine"]
    if movable.empty:
        logger.info("Manifest contains no reversible moves (purged files are gone).")
        return
    print(f"Restoring {len(movable)} file(s) to their original folders.")
    if not assume_yes and input("Proceed? [y/N]: ").strip().lower() not in {"y", "yes"}:
        return
    restored = 0
    for _, row in movable.iterrows():
        src, dest = Path(row["quarantine_path"]), Path(row["original_path"])
        if not src.exists():
            continue
        if dest.exists():
            logger.warning("Restore destination exists, skipped: %s", dest)
            continue
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src), str(dest))
        restored += 1
    logger.info("Restored %d file(s). Delete or archive the manifest before re-running.",
                restored)


def build_corpus_index(df: pd.DataFrame, project_root: Path) -> Path:
    """Write the modelling manifest with explicit eligibility rules.

    `corpus_year` is the time bucket a dynamic topic model should use. A
    confidently resolved misfiled document is re-dated to its resolved year;
    unresolved and review records never silently enter the modelling corpus.
    """
    out = df.copy()
    validate_pipeline_frame(out, "corpus index")
    status = out["temporal_status"].astype(str)
    trusted = status.isin({"valid", "misfiled"}) \
        & out["confidence_score"].ge(MISFILE_MIN_CONFIDENCE) \
        & out["resolved_year"].notnull()
    out["corpus_year"] = out["folder_year"].where(~trusted, out["resolved_year"])
    out["corpus_year"] = out["corpus_year"].astype("Int64")
    removal_reason = (out["removal_reason"].fillna("")
                      if "removal_reason" in out.columns
                      else pd.Series("", index=out.index))
    out["included_in_corpus"] = (
        status.isin({"valid", "misfiled"})
        & (removal_reason == "")
        & ~out["is_sparse"].fillna(True)
    )

    path = project_root / "data" / "processed" / "corpus_index.csv"
    path.parent.mkdir(parents=True, exist_ok=True)
    columns = ["schema_version", "filename", "file_path", "file_hash",
               "ordinance_number", "title", "folder_year", "resolved_year",
               "corpus_year", "enactment_date", "approval_date", "temporal_status",
               "confidence_score", "removal_reason", "included_in_corpus",
               "clean_word_count", "word_count", "page_count", "section_count",
               "subject_keywords", "clean_text_path"]
    out[[c for c in columns if c in out.columns]].to_csv(path, index=False)
    kept = int(out["included_in_corpus"].sum())
    redated = int((trusted & (out["resolved_year"] != out["folder_year"])).sum())
    logger.info("Corpus index: %s | %d of %d documents included | %d re-dated to their "
                "resolved year", path, kept, len(out), redated)
    return path


def _git_revision(project_root: Path) -> str:
    """Return the current commit for provenance, or 'unknown' outside git."""
    try:
        result = subprocess.run(
            ["git", "-C", str(project_root), "rev-parse", "HEAD"],
            capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def write_run_manifest(df: pd.DataFrame, project_root: Path,
                       study_window: Tuple[int, int], options: Dict[str, Any]) -> Path:
    """Persist run configuration and source hashes beside the generated reports."""
    def json_value(value: Any) -> Any:
        if isinstance(value, Path):
            return str(value)
        if isinstance(value, (str, int, float, bool)) or value is None:
            return value
        if isinstance(value, (list, tuple)):
            return [json_value(item) for item in value]
        return str(value)

    documents = []
    for _, row in df.iterrows():
        documents.append({
            "filename": row.get("filename"),
            "folder_year": row.get("folder_year"),
            "file_hash": row.get("file_hash"),
            "temporal_status": row.get("temporal_status"),
            "resolved_year": row.get("resolved_year"),
            "included_in_corpus": bool(row.get("included_in_corpus", False)),
        })
    manifest = {
        "manifest_version": 1,
        "pipeline_schema_version": PIPELINE_SCHEMA_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "git_revision": _git_revision(project_root),
        "python_version": platform.python_version(),
        "pdf_backend": PDF_BACKEND,
        "ocr_packages_available": OCR_AVAILABLE,
        "study_window": list(study_window),
        "options": {key: json_value(value) for key, value in options.items()},
        "document_count": len(documents),
        "documents": documents,
    }
    path = project_root / "outputs" / "reports" / "run_manifest.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False, default=str),
                    encoding="utf-8")
    logger.info("Saved reproducibility manifest: %s", path)
    return path


# --------------------------------------------------------------------------- #
# Obsidian vault export
# --------------------------------------------------------------------------- #

VAULT_SUBDIR = "Ordinances"


def _yaml_scalar(value: Any) -> str:
    """Emit a YAML-safe scalar.

    JSON is a subset of YAML, so json.dumps handles the quoting, colons and
    embedded quotation marks that ordinance titles are full of.
    """
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, pd.Timestamp):
        return value.date().isoformat()
    return json.dumps(str(value), ensure_ascii=False)


def _note_stem(row: pd.Series) -> str:
    number = row.get("ordinance_number")
    if isinstance(number, str) and number:
        return f"Ordinance No. {number}"
    return Path(str(row["filename"])).stem


def build_obsidian_note(row: pd.Series, clean_text: str = "",
                        include_text: bool = True, text_chars: int = 12000) -> str:
    """One ordinance as an Obsidian note: YAML frontmatter plus a readable body."""
    number = row.get("ordinance_number") or ""
    stem = _note_stem(row)
    corpus_year = row.get("corpus_year", row.get("resolved_year"))

    tags = ["ordinance", "davao"]
    if pd.notnull(corpus_year):
        tags.append(f"year/{int(corpus_year)}")
    tags.append(f"status/{row.get('temporal_status', 'unknown')}")
    if row.get("is_amendatory"):
        tags.append("type/amendatory")
    if row.get("manually_verified"):
        tags.append("verified/manual")
    for keyword in str(row.get("subject_keywords") or "").split(";"):
        keyword = keyword.strip()
        if keyword:
            tags.append(f"topic/{_slug(keyword)}")

    front: Dict[str, Any] = {
        "title": row.get("title") or stem,
        "ordinance_number": number,
        "aliases": None,          # rendered manually below
        "corpus_year": int(corpus_year) if pd.notnull(corpus_year) else None,
        "folder_year": int(row["folder_year"]),
        "resolved_year": int(row["resolved_year"]) if pd.notnull(row.get("resolved_year")) else None,
        "enactment_date": row.get("enactment_date"),
        "approval_date": row.get("approval_date"),
        "series_year": int(row["detected_series_year"]) if pd.notnull(row.get("detected_series_year")) else None,
        "council_term": int(row["council_term"]) if pd.notnull(row.get("council_term")) else None,
        "session": row.get("session_label"),
        "sponsor": row.get("sponsor"),
        "approving_mayor": row.get("approving_mayor"),
        "presiding_officer": row.get("presiding_officer"),
        "temporal_status": row.get("temporal_status"),
        "confidence_score": row.get("confidence_score"),
        "resolution_source": row.get("resolution_source"),
        "manually_verified": bool(row.get("manually_verified", False)),
        "included_in_corpus": bool(row.get("included_in_corpus", True)),
        "extraction_method": row.get("extraction_method"),
        "page_count": int(row["page_count"]) if pd.notnull(row.get("page_count")) else None,
        "word_count": int(row["clean_word_count"]) if pd.notnull(row.get("clean_word_count")) else None,
        "section_count": int(row["section_count"]) if pd.notnull(row.get("section_count")) else None,
        "whereas_count": int(row["whereas_count"]) if pd.notnull(row.get("whereas_count")) else None,
        "source_pdf": row.get("file_path"),
        "sha256": str(row.get("file_hash") or "")[:16],
        "indexed": datetime.now().date().isoformat(),
    }

    lines = ["---"]
    for key, value in front.items():
        if key == "aliases":
            if number:
                lines.append(f"aliases: [{_yaml_scalar('Ordinance No. ' + number)}, "
                             f"{_yaml_scalar(number)}]")
            continue
        lines.append(f"{key}: {_yaml_scalar(value)}")
    lines.append("tags: [" + ", ".join(dict.fromkeys(tags)) + "]")
    lines += ["---", "", f"# {stem}", ""]

    if row.get("title"):
        lines += [f"> {row['title']}", ""]

    status = row.get("temporal_status")
    if status != "valid":
        callout = "warning" if status in {"misfiled", "out_of_scope"} else "question"
        lines += [f"> [!{callout}] Temporal status: {status}",
                  f"> Filed under {int(row['folder_year'])}, resolved to "
                  f"{_yr(row.get('resolved_year'))} at confidence "
                  f"{row.get('confidence_score', 0):.2f}.",
                  f"> {row.get('conflict_notes') or 'No conflicting signals recorded.'}", ""]

    lines += ["## Temporal signals", "",
              "| Signal | Year |", "| --- | --- |",
              f"| Enactment date | {_yr(row.get('detected_enactment_year'))} |",
              f"| Ordinance number suffix | {_yr(row.get('detected_ordinance_no_year'))} |",
              f"| Series header | {_yr(row.get('detected_series_year'))} |",
              f"| Approval date | {_yr(row.get('detected_approval_year'))} |",
              f"| **Resolved** | **{_yr(row.get('resolved_year'))}** |", ""]

    cited = [c.strip() for c in str(row.get("cited_ordinances") or "").split(";") if c.strip()]
    if cited:
        lines += ["## Cites or amends", ""]
        lines += [f"- [[Ordinance No. {c}]]" for c in cited]
        lines.append("")

    year_link = int(corpus_year) if pd.notnull(corpus_year) else int(row["folder_year"])
    lines += ["## Context", "",
              f"- Year index: [[_Index {year_link}]]",
              "- Corpus overview: [[_Corpus MOC]]", ""]

    if include_text and clean_text:
        body = clean_text[:text_chars]
        truncated = len(clean_text) > text_chars
        lines += ["## Cleaned text", ""]
        if truncated:
            lines.append(f"*Truncated to {text_chars:,} of {len(clean_text):,} characters. "
                         f"Full text: `{row.get('clean_text_path', '')}`*")
            lines.append("")
        lines += [body, ""]

    return "\n".join(lines)


def write_obsidian_vault(df: pd.DataFrame, vault_root: Path,
                         clean_text_root: Optional[Path] = None,
                         include_text: bool = True, text_chars: int = 12000) -> Dict[str, int]:
    """Write one note per ordinance, one index per year, and a corpus overview.

    The vault is a projection of the pipeline output, not a second source of
    truth: it is rewritten on every export. Keep researcher-authored notes in a
    separate vault folder so they are never overwritten.
    """
    base = vault_root / VAULT_SUBDIR
    base.mkdir(parents=True, exist_ok=True)
    written = 0

    for _, row in df.iterrows():
        year = row.get("corpus_year")
        year = int(year) if pd.notnull(year) else int(row["folder_year"])
        note_dir = base / str(year)
        note_dir.mkdir(parents=True, exist_ok=True)

        clean_text = ""
        if include_text and clean_text_root is not None:
            candidate = Path(str(row.get("clean_text_path") or ""))
            if candidate.exists():
                clean_text = candidate.read_text(encoding="utf-8", errors="ignore")

        note = build_obsidian_note(row, clean_text, include_text, text_chars)
        (note_dir / f"{_note_stem(row)}.md").write_text(note, encoding="utf-8")
        written += 1

    # Per-year index notes.
    for year, grp in df.groupby(df["corpus_year"].fillna(df["folder_year"]).astype(int)):
        counts = grp["temporal_status"].value_counts().to_dict()
        lines = ["---",
                 f"title: {_yaml_scalar(f'Ordinance index {year}')}",
                 f"corpus_year: {year}",
                 f"document_count: {len(grp)}",
                 "tags: [index, ordinance, davao, " + f"year/{year}]",
                 "---", "",
                 f"# Ordinance index {year}", "",
                 f"{len(grp)} document(s) indexed under corpus year {year}.", "",
                 "| Status | Count |", "| --- | --- |"]
        lines += [f"| {status} | {counts.get(status, 0)} |" for status in STATUS_ORDER]
        lines += ["", "## Documents", "",
                  "| Ordinance | Title | Status | Conf. | Enacted |",
                  "| --- | --- | --- | --- | --- |"]
        for _, row in grp.sort_values("filename").iterrows():
            title = str(row.get("title") or "")[:80]
            lines.append(f"| [[{_note_stem(row)}]] | {title} | {row.get('temporal_status')} "
                         f"| {row.get('confidence_score', 0):.2f} "
                         f"| {row.get('enactment_date') or '-'} |")
        lines += ["", "## Live query", "",
                  "```dataview", "TABLE ordinance_number, temporal_status, confidence_score, enactment_date",
                  f'FROM #ordinance AND "{VAULT_SUBDIR}/{year}"',
                  "SORT ordinance_number ASC", "```", "",
                  "Back to [[_Corpus MOC]]", ""]
        (base / str(year) / f"_Index {year}.md").write_text("\n".join(lines), encoding="utf-8")

    # Corpus map of content.
    crosstab = pd.crosstab(df["folder_year"], df["temporal_status"]).reindex(
        columns=STATUS_ORDER, fill_value=0)
    moc = ["---", "title: \"Davao City ordinance corpus\"",
           f"document_count: {len(df)}",
           f"generated: {datetime.now().isoformat(timespec='seconds')}",
           "tags: [moc, ordinance, davao]", "---", "",
           "# Davao City ordinance corpus", "",
           f"{len(df)} document(s) across {df['folder_year'].nunique()} year folder(s). "
           "Generated by `src/ordinance_eda_pipeline.py`; this folder is overwritten on "
           "every export, so keep your own notes elsewhere in the vault.", "",
           "| Folder year | " + " | ".join(STATUS_ORDER) + " | Total | Index |",
           "|---" * (len(STATUS_ORDER) + 3) + "|"]
    for year, row in crosstab.iterrows():
        moc.append(f"| {year} | " + " | ".join(str(int(row[s])) for s in STATUS_ORDER) +
                   f" | {int(row.sum())} | [[_Index {year}]] |")
    moc += ["", "## Needs attention", "",
            "```dataview", "TABLE folder_year, resolved_year, confidence_score, conflict_notes",
            "FROM #ordinance", 'WHERE temporal_status != "valid"',
            "SORT confidence_score ASC", "```", "",
            "## Amendment network", "",
            "```dataview", "TABLE cited_ordinances", "FROM #type/amendatory",
            "SORT corpus_year ASC", "```", ""]
    (base / "_Corpus MOC.md").write_text("\n".join(moc), encoding="utf-8")

    logger.info("Obsidian vault written: %s | %d note(s), %d year index/indices",
                base, written, df["folder_year"].nunique())
    return {"notes": written, "indices": int(df["folder_year"].nunique())}


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #

def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Legal NLP ordinance EDA and temporal validation pipeline")
    parser.add_argument("--year", type=int, nargs="+", default=None,
                        help="Target folder year(s), e.g. --year 2016 2017")
    parser.add_argument("--all-years", action="store_true",
                        help="Process every numeric year folder under data/raw/")
    parser.add_argument("--window-min", type=int, default=DEFAULT_WINDOW[0])
    parser.add_argument("--window-max", type=int, default=DEFAULT_WINDOW[1])
    parser.add_argument("--fix-misfiled", action="store_true",
                        help="Relocate confidently misfiled PDFs (copies by default)")
    parser.add_argument("--move", action="store_true",
                        help="With --fix-misfiled, move instead of copy")
    parser.add_argument("--yes", action="store_true", help="Skip the confirmation prompt")
    parser.add_argument("--min-confidence", type=float, default=RELOCATE_MIN_CONFIDENCE,
                        help="Confidence bar for automatic relocation")
    parser.add_argument("--no-ocr", action="store_true", help="Disable the OCR fallback")
    parser.add_argument("--no-cache", action="store_true", help="Ignore cached extracted text")
    parser.add_argument("--debug-headers", type=int, default=0, metavar="N",
                        help="Print the header and date anchors of N files, then exit")

    curate = parser.add_argument_group("corpus curation")
    curate.add_argument("--remove-misfiled", action="store_true",
                        help="Remove excluded documents from data/raw/. Files are MOVED to "
                             "data/quarantine/<reason>/<year>/ and logged to a manifest, not "
                             "deleted. Default categories: "
                             + ", ".join(DEFAULT_REMOVAL))
    curate.add_argument("--remove-categories", nargs="+", default=list(DEFAULT_REMOVAL),
                        choices=list(REMOVAL_CATEGORIES), metavar="CAT",
                        help="Override which categories --remove-misfiled acts on: "
                             + ", ".join(REMOVAL_CATEGORIES))
    curate.add_argument("--purge", action="store_true",
                        help="With --remove-misfiled, DELETE instead of quarantining. "
                             "Irreversible; requires typing DELETE unless --yes.")
    curate.add_argument("--dry-run", action="store_true",
                        help="Print what --remove-misfiled would do and touch nothing")
    curate.add_argument("--restore", action="store_true",
                        help="Move every quarantined file back to its original folder")

    adjudicate = parser.add_argument_group("manual adjudication")
    adjudicate.add_argument("--overrides", type=Path, default=None,
                            help="Extra overrides CSV, or a directory of them. Always read: "
                                 "data/manual_year_overrides.csv (shared) and "
                                 "data/manual_year_overrides_{year}.csv (per year)")
    adjudicate.add_argument("--emit-override-template", action="store_true",
                            help="Write one data/manual_year_overrides_TEMPLATE_{year}.csv per "
                                 "folder year, pre-filled for hand adjudication, then exit")

    vault = parser.add_argument_group("cleaning and Obsidian export")
    vault.add_argument("--no-clean-text", action="store_true",
                       help="Skip writing cleaned text to data/processed/clean_text/")
    vault.add_argument("--export-obsidian", action="store_true",
                       help="Write one Obsidian note per ordinance plus year indices and a MOC")
    vault.add_argument("--obsidian-vault", type=Path, default=None,
                       help="Vault root (default: <project>/obsidian)")
    vault.add_argument("--obsidian-no-text", action="store_true",
                       help="Frontmatter and metadata only; omit the cleaned body text")
    vault.add_argument("--obsidian-text-chars", type=int, default=12000,
                       help="Characters of cleaned text embedded per note (default 12000)")
    vault.add_argument("--obsidian-corpus-only", action="store_true",
                       help="Export only documents where included_in_corpus is true")
    args = parser.parse_args(argv)

    project_root = Path(__file__).resolve().parent.parent
    base_raw_dir = project_root / "data" / "raw"
    eda_csv_dir = project_root / "data" / "EDA"
    report_dir = project_root / "outputs" / "reports"
    figures_dir = project_root / "outputs" / "figures"
    cache_root = None if args.no_cache else project_root / "data" / "interim" / "text"
    clean_text_root = None if args.no_clean_text else \
        project_root / "data" / "processed" / "clean_text"
    vault_root = args.obsidian_vault or (project_root / "Thesis_Obsidian")

    study_window = (args.window_min, args.window_max)
    if args.all_years:
        years = sorted(int(d.name) for d in base_raw_dir.iterdir()
                       if d.is_dir() and d.name.isdigit())
    elif args.year:
        years = args.year
    else:
        years = list(range(study_window[0], study_window[1] + 1))

    if args.restore:
        restore_from_quarantine(project_root, assume_yes=args.yes)
        return 0

    if args.debug_headers:
        for year in years:
            debug_headers(year, base_raw_dir, sample=args.debug_headers)
        return 0

    all_records: List[Dict[str, Any]] = []
    for year in years:
        logger.info("========== Processing year folder: %s ==========", year)
        year_overrides = load_year_overrides(
            override_paths_for_year(project_root, year, args.overrides))
        records = process_year_folder(year, base_raw_dir, study_window,
                                      cache_root=cache_root, use_ocr=not args.no_ocr,
                                      overrides=year_overrides,
                                      clean_text_root=clean_text_root)
        if records:
            generate_eda_outputs(pd.DataFrame(records), year, eda_csv_dir,
                                 report_dir, figures_dir, study_window)
            all_records.extend(records)

    if not all_records:
        logger.warning("No documents processed; nothing to report.")
        return 0

    full_df = pd.DataFrame(all_records)
    validate_pipeline_frame(full_df, "corpus rollup")

    if args.emit_override_template:
        emit_override_templates(full_df, project_root)
        return 0

    generate_corpus_outputs(full_df, eda_csv_dir, report_dir, figures_dir)
    verified = int(full_df["manually_verified"].sum())
    if verified:
        logger.info("%d document(s) carried a manual override this run.", verified)

    if args.fix_misfiled:
        execute_relocation(full_df, base_raw_dir, move=args.move,
                           assume_yes=args.yes, min_confidence=args.min_confidence)

    full_df = flag_removal_reasons(full_df, tuple(args.remove_categories))
    if args.remove_misfiled or args.dry_run:
        full_df = curate_corpus(full_df, project_root,
                                categories=tuple(args.remove_categories),
                                purge=args.purge, dry_run=args.dry_run,
                                assume_yes=args.yes)

    index_path = build_corpus_index(full_df, project_root)
    full_df.to_csv(eda_csv_dir / "ordinances_eda_summary_ALL.csv", index=False)
    # Keep the exact run configuration and source hashes beside the reports.
    # This is the provenance record to preserve with any thesis result.
    index_df = pd.read_csv(index_path)
    manifest_df = full_df.merge(
        index_df[["filename", "folder_year", "corpus_year", "included_in_corpus"]],
        on=["filename", "folder_year"], how="left")
    write_run_manifest(manifest_df, project_root, study_window, vars(args))

    if args.export_obsidian:
        export_df = full_df.copy()
        # corpus_year lives in the index; use folder_year too because filenames
        # are not guaranteed to be unique across year folders.
        index_df = pd.read_csv(index_path, usecols=["filename", "folder_year",
                                                    "corpus_year", "included_in_corpus"])
        export_df = export_df.merge(index_df, on=["filename", "folder_year"], how="left")
        if args.obsidian_corpus_only:
            export_df = export_df[export_df["included_in_corpus"].fillna(True)]
        write_obsidian_vault(export_df, vault_root,
                             clean_text_root=clean_text_root,
                             include_text=not args.obsidian_no_text,
                             text_chars=args.obsidian_text_chars)
    return 0


if __name__ == "__main__":
    sys.exit(main())
