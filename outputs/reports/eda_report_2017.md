# Legal NLP EDA & Temporal Audit Report: 2017
*Generated automatically by `src/ordinance_eda_pipeline.py`*

Study window: 2016-2025 | confidence bar for misfiling: 0.45 | for relocation: 0.60

## 1. Executive summary and file inventory

Categories below are mutually exclusive, so the percentages sum to 100%.

| Classification | Count | Percentage |
|---|---|---|
| **Total documents scanned** | 204 | 100.0% |
| Temporally valid (matches folder) | 196 | 96.1% |
| Misfiled (in-window, wrong folder) | 0 | 0.0% |
| Out-of-scope year | 0 | 0.0% |
| Flagged for manual review | 8 | 3.9% |
| Unresolved (no year signal) | 0 | 0.0% |

| Extraction | Count | Percentage |
|---|---|---|
| Digital | 198 | 97.1% |
| Hybrid | 6 | 2.9% |
| OCR | 0 | 0.0% |
| Pages OCR'd in total | 6 | - |

Mean consensus confidence: **0.43** (median 0.35). Documents resolved on a single signal: 46 (22.5%).

## 2. Duplicate analysis

- Byte-identical files (SHA-256): **0** group(s) covering 0 file(s)
- Repeated ordinance numbers: **0** group(s) covering 0 file(s)
- Files with no parseable ordinance number: **0**

## 3. Signal extraction completeness

| Component signal | Extracted | Coverage |
|---|---|---|
| Enactment date | 47 / 204 | 23.0% |
| Ordinance number | 204 / 204 | 100.0% |
| Series header | 95 / 204 | 46.6% |
| Approval date | 182 / 204 | 89.2% |

Ordinance number source: filename 204/204, filename and header agree on 113. Citation-style references rejected before they could hijack the signal: **2**.

> **Parser health warning.** Enactment-date coverage is 23.0%. An enactment clause appears in virtually every enacted ordinance, so a low rate here is a parsing failure, not a corpus property. Run `--debug-headers` on this folder and tune `ENACT_ANCHOR_RE` / `DATE_PATTERNS` against the real layout before treating any temporal verdict in this report as final.

## 4. Corpus text characteristics

| Metric | Value |
|---|---|
| Mean characters | 21,743 |
| Median characters | 14,751 |
| Mean words | 3,518 |
| Shortest document | 3,319 chars |
| Longest document | 607,712 chars |
| Mean pages | 14.5 |
| Mean characters per page | 1,356 |
| Suspected incomplete (<300 chars) | 0 files |
| Low text density (<100 chars/page) | 0 files |

## 5. Temporal discrepancies and misfiled files

No confidently misfiled or out-of-scope ordinances detected.

### Flagged for manual review (not actioned)

| Filename | Resolved | Conf. | Agree | Reason |
|---|---|---|---|---|
| `Ordinance No. 0152-17.pdf` | 1991 | 0.28 | 1/3 | enacted 1991 vs approved 2017 |
| `Ordinance No. 0157-17.pdf` | 1991 | 0.28 | 1/3 | enacted 1991 vs approved 2017 |
| `Ordinance No. 0166-17.pdf` | 1991 | 0.28 | 1/3 | enacted 1991 vs approved 2017 |
| `Ordinance No. 0212-17.pdf` | 1991 | 0.28 | 1/3 | enacted 1991 vs approved 2017 |
| `Ordinance No. 0223-17.pdf` | 1991 | 0.28 | 1/3 | enacted 1991 vs approved 2010 |
| `Ordinance No. 033-16.pdf` | 1991 | 0.28 | 1/3 | enacted 1991 vs approved 2017 |
| `Ordinance No. 034-16.pdf` | 1991 | 0.17 | 1/4 | enacted 1991 vs approved 2017 |
| `Ordinance No. 040-16.pdf` | 1991 | 0.28 | 1/3 | enacted 1991 vs approved 2016 |
