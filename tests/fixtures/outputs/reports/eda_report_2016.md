# Legal NLP EDA & Temporal Audit Report: 2016
*Generated automatically by `src/ordinance_eda_pipeline.py`*

Study window: 2016-2024 | confidence bar for misfiling: 0.45 | for relocation: 0.60

## 1. Executive summary and file inventory

Categories below are mutually exclusive, so the percentages sum to 100%.

| Classification | Count | Percentage |
|---|---|---|
| **Total documents scanned** | 9 | 100.0% |
| Temporally valid (matches folder) | 7 | 77.8% |
| Misfiled (in-window, wrong folder) | 0 | 0.0% |
| Out-of-scope year | 1 | 11.1% |
| Flagged for manual review | 0 | 0.0% |
| Unresolved (no year signal) | 1 | 11.1% |

| Extraction | Count | Percentage |
|---|---|---|
| Digital | 9 | 100.0% |
| Hybrid | 0 | 0.0% |
| OCR | 0 | 0.0% |
| Pages OCR'd in total | 0 | - |

Mean consensus confidence: **0.78** (median 1.00). Documents resolved on a single signal: 2 (22.2%).

## 2. Duplicate analysis

- Byte-identical files (SHA-256): **1** group(s) covering 2 file(s)
- Repeated ordinance numbers: **1** group(s) covering 3 file(s)
- Files with no parseable ordinance number: **0**

| Ordinance No. | Files | Resolved years |
|---|---|---|
| `0116-16` | `Ord 0116-16 duplicate.pdf`, `Ordinance No. 0116-16 (copy).pdf`, `Ordinance No. 0116-16.pdf` | 2016 |

## 3. Signal extraction completeness

| Component signal | Extracted | Coverage |
|---|---|---|
| Enactment date | 6 / 9 | 66.7% |
| Ordinance number | 9 / 9 | 100.0% |
| Series header | 7 / 9 | 77.8% |
| Approval date | 7 / 9 | 77.8% |

Ordinance number source: filename 9/9, filename and header agree on 8. Citation-style references rejected before they could hijack the signal: **0**.

## 4. Corpus text characteristics

| Metric | Value |
|---|---|
| Mean characters | 285 |
| Median characters | 241 |
| Mean words | 45 |
| Shortest document | 0 chars |
| Longest document | 515 chars |
| Mean pages | 1.0 |
| Mean characters per page | 285 |
| Suspected incomplete (<300 chars) | 5 files |
| Low text density (<100 chars/page) | 1 files |

## 5. Temporal discrepancies and misfiled files

| Filename | Ord. No. | Status | Folder | Resolved | Conf. | Agree | Enacted | Ord-no | Series | Approved | Suggested path |
|---|---|---|---|---|---|---|---|---|---|---|---|
| `Ordinance No. 0230-10.pdf` | 0230-10 | out_of_scope | 2016 | **2010** | 1.00 | 4/4 | 2010 | 2010 | 2010 | 2010 | `data/raw/2010/` |

### Flagged for manual review (not actioned)

| Filename | Resolved | Conf. | Agree | Reason |
|---|---|---|---|---|
| `Ordinance No. 0999-16.pdf` | 2016 | 0.25 | 1/1 | no extractable text; filename-only inference |
