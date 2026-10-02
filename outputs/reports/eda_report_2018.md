# Legal NLP EDA & Temporal Audit Report: 2018
*Generated automatically by `src/ordinance_eda_pipeline.py`*

Study window: 2016-2025 | confidence bar for misfiling: 0.45 | for relocation: 0.60

## 1. Executive summary and file inventory

Categories below are mutually exclusive, so the percentages sum to 100%.

| Classification | Count | Percentage |
|---|---|---|
| **Total documents scanned** | 249 | 100.0% |
| Temporally valid (matches folder) | 248 | 99.6% |
| Misfiled (in-window, wrong folder) | 0 | 0.0% |
| Out-of-scope year | 0 | 0.0% |
| Flagged for manual review | 1 | 0.4% |
| Unresolved (no year signal) | 0 | 0.0% |

| Extraction | Count | Percentage |
|---|---|---|
| Digital | 244 | 98.0% |
| Hybrid | 5 | 2.0% |
| OCR | 0 | 0.0% |
| Pages OCR'd in total | 6 | - |

Mean consensus confidence: **0.67** (median 0.55). Documents resolved on a single signal: 3 (1.2%).

## 2. Duplicate analysis

- Byte-identical files (SHA-256): **0** group(s) covering 0 file(s)
- Repeated ordinance numbers: **0** group(s) covering 0 file(s)
- Files with no parseable ordinance number: **0**

## 3. Signal extraction completeness

| Component signal | Extracted | Coverage |
|---|---|---|
| Enactment date | 138 / 249 | 55.4% |
| Ordinance number | 249 / 249 | 100.0% |
| Series header | 242 / 249 | 97.2% |
| Approval date | 248 / 249 | 99.6% |

Ordinance number source: filename 249/249, filename and header agree on 192. Citation-style references rejected before they could hijack the signal: **1**.

## 4. Corpus text characteristics

| Metric | Value |
|---|---|
| Mean characters | 13,309 |
| Median characters | 8,118 |
| Mean words | 2,111 |
| Shortest document | 4,991 chars |
| Longest document | 144,329 chars |
| Mean pages | 9.6 |
| Mean characters per page | 1,315 |
| Suspected incomplete (<300 chars) | 0 files |
| Low text density (<100 chars/page) | 0 files |

## 5. Temporal discrepancies and misfiled files

No confidently misfiled or out-of-scope ordinances detected.

### Flagged for manual review (not actioned)

| Filename | Resolved | Conf. | Agree | Reason |
|---|---|---|---|---|
| `Ordinance No. 0249-17.pdf` | 2008 | 0.17 | 1/4 | enacted 2008 vs approved 2017; series 2018 vs ord-no 2017 |
