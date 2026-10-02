# Legal NLP EDA & Temporal Audit Report: 2025
*Generated automatically by `src/ordinance_eda_pipeline.py`*

Study window: 2016-2025 | confidence bar for misfiling: 0.45 | for relocation: 0.60

## 1. Executive summary and file inventory

Categories below are mutually exclusive, so the percentages sum to 100%.

| Classification | Count | Percentage |
|---|---|---|
| **Total documents scanned** | 31 | 100.0% |
| Temporally valid (matches folder) | 30 | 96.8% |
| Misfiled (in-window, wrong folder) | 0 | 0.0% |
| Out-of-scope year | 0 | 0.0% |
| Flagged for manual review | 1 | 3.2% |
| Unresolved (no year signal) | 0 | 0.0% |

| Extraction | Count | Percentage |
|---|---|---|
| Digital | 31 | 100.0% |
| Hybrid | 0 | 0.0% |
| OCR | 0 | 0.0% |
| Pages OCR'd in total | 0 | - |

Mean consensus confidence: **0.61** (median 0.55). Documents resolved on a single signal: 1 (3.2%).

## 2. Duplicate analysis

- Byte-identical files (SHA-256): **0** group(s) covering 0 file(s)
- Repeated ordinance numbers: **0** group(s) covering 0 file(s)
- Files with no parseable ordinance number: **0**

## 3. Signal extraction completeness

| Component signal | Extracted | Coverage |
|---|---|---|
| Enactment date | 20 / 31 | 64.5% |
| Ordinance number | 31 / 31 | 100.0% |
| Series header | 29 / 31 | 93.5% |
| Approval date | 29 / 31 | 93.5% |

Ordinance number source: filename 31/31, filename and header agree on 28. Citation-style references rejected before they could hijack the signal: **0**.

## 4. Corpus text characteristics

| Metric | Value |
|---|---|
| Mean characters | 16,511 |
| Median characters | 11,914 |
| Mean words | 2,629 |
| Shortest document | 3,739 chars |
| Longest document | 68,717 chars |
| Mean pages | 9.8 |
| Mean characters per page | 1,624 |
| Suspected incomplete (<300 chars) | 0 files |
| Low text density (<100 chars/page) | 0 files |

## 5. Temporal discrepancies and misfiled files

No confidently misfiled or out-of-scope ordinances detected.

### Flagged for manual review (not actioned)

| Filename | Resolved | Conf. | Agree | Reason |
|---|---|---|---|---|
| `Ordinance No. 0192-23 (2).pdf` | 1991 | 0.17 | 1/4 | enacted 1991 vs approved 2025; series 2025 vs ord-no 2023 |
