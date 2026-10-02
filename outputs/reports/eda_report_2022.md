# Legal NLP EDA & Temporal Audit Report: 2022
*Generated automatically by `src/ordinance_eda_pipeline.py`*

Study window: 2016-2025 | confidence bar for misfiling: 0.45 | for relocation: 0.60

## 1. Executive summary and file inventory

Categories below are mutually exclusive, so the percentages sum to 100%.

| Classification | Count | Percentage |
|---|---|---|
| **Total documents scanned** | 273 | 100.0% |
| Temporally valid (matches folder) | 272 | 99.6% |
| Misfiled (in-window, wrong folder) | 0 | 0.0% |
| Out-of-scope year | 0 | 0.0% |
| Flagged for manual review | 1 | 0.4% |
| Unresolved (no year signal) | 0 | 0.0% |

| Extraction | Count | Percentage |
|---|---|---|
| Digital | 273 | 100.0% |
| Hybrid | 0 | 0.0% |
| OCR | 0 | 0.0% |
| Pages OCR'd in total | 0 | - |

Mean consensus confidence: **0.86** (median 1.00). Documents resolved on a single signal: 7 (2.6%).

## 2. Duplicate analysis

- Byte-identical files (SHA-256): **0** group(s) covering 0 file(s)
- Repeated ordinance numbers: **0** group(s) covering 0 file(s)
- Files with no parseable ordinance number: **72**

## 3. Signal extraction completeness

| Component signal | Extracted | Coverage |
|---|---|---|
| Enactment date | 241 / 273 | 88.3% |
| Ordinance number | 201 / 273 | 73.6% |
| Series header | 260 / 273 | 95.2% |
| Approval date | 242 / 273 | 88.6% |

Ordinance number source: filename 178/273, filename and header agree on 26. Citation-style references rejected before they could hijack the signal: **7**.

## 4. Corpus text characteristics

| Metric | Value |
|---|---|
| Mean characters | 7,792 |
| Median characters | 5,234 |
| Mean words | 1,225 |
| Shortest document | 2,775 chars |
| Longest document | 116,250 chars |
| Mean pages | 4.3 |
| Mean characters per page | 1,704 |
| Suspected incomplete (<300 chars) | 0 files |
| Low text density (<100 chars/page) | 0 files |

## 5. Temporal discrepancies and misfiled files

No confidently misfiled or out-of-scope ordinances detected.

### Flagged for manual review (not actioned)

| Filename | Resolved | Conf. | Agree | Reason |
|---|---|---|---|---|
| `Ordinance No. 000902-22.pdf` | 2020 | 0.30 | 1/3 | enacted 2020 vs approved 2022 |
