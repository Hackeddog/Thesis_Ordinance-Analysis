# Legal NLP EDA & Temporal Audit Report: 2020
*Generated automatically by `src/ordinance_eda_pipeline.py`*

Study window: 2016-2025 | confidence bar for misfiling: 0.45 | for relocation: 0.60

## 1. Executive summary and file inventory

Categories below are mutually exclusive, so the percentages sum to 100%.

| Classification | Count | Percentage |
|---|---|---|
| **Total documents scanned** | 147 | 100.0% |
| Temporally valid (matches folder) | 144 | 98.0% |
| Misfiled (in-window, wrong folder) | 0 | 0.0% |
| Out-of-scope year | 0 | 0.0% |
| Flagged for manual review | 3 | 2.0% |
| Unresolved (no year signal) | 0 | 0.0% |

| Extraction | Count | Percentage |
|---|---|---|
| Digital | 143 | 97.3% |
| Hybrid | 4 | 2.7% |
| OCR | 0 | 0.0% |
| Pages OCR'd in total | 4 | - |

Mean consensus confidence: **0.91** (median 1.00). Documents resolved on a single signal: 3 (2.0%).

## 2. Duplicate analysis

- Byte-identical files (SHA-256): **0** group(s) covering 0 file(s)
- Repeated ordinance numbers: **0** group(s) covering 0 file(s)
- Files with no parseable ordinance number: **0**

## 3. Signal extraction completeness

| Component signal | Extracted | Coverage |
|---|---|---|
| Enactment date | 142 / 147 | 96.6% |
| Ordinance number | 147 / 147 | 100.0% |
| Series header | 140 / 147 | 95.2% |
| Approval date | 147 / 147 | 100.0% |

Ordinance number source: filename 147/147, filename and header agree on 128. Citation-style references rejected before they could hijack the signal: **0**.

## 4. Corpus text characteristics

| Metric | Value |
|---|---|
| Mean characters | 15,615 |
| Median characters | 10,809 |
| Mean words | 2,482 |
| Shortest document | 4,699 chars |
| Longest document | 107,451 chars |
| Mean pages | 10.3 |
| Mean characters per page | 1,415 |
| Suspected incomplete (<300 chars) | 0 files |
| Low text density (<100 chars/page) | 0 files |

## 5. Temporal discrepancies and misfiled files

No confidently misfiled or out-of-scope ordinances detected.

### Flagged for manual review (not actioned)

| Filename | Resolved | Conf. | Agree | Reason |
|---|---|---|---|---|
| `Ordinance No. 0236-20.pdf` | 1991 | 0.17 | 1/4 | enacted 1991 vs approved 2019 |
| `Ordinance No. 0238-20.pdf` | 1991 | 0.17 | 1/4 | enacted 1991 vs approved 2020; series 1985 vs ord-no 2020 |
| `Ordinance No. 0240-20.pdf` | 1991 | 0.28 | 1/3 | enacted 1991 vs approved 2020 |
