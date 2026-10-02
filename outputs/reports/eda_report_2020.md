# Legal NLP EDA & Temporal Audit Report: 2020
*Generated automatically by `src/ordinance_eda_pipeline.py`*

Study window: 2016-2025 | confidence bar for misfiling: 0.45 | for relocation: 0.60

## 1. Executive summary and file inventory

Categories below are mutually exclusive, so the percentages sum to 100%.

| Classification | Count | Percentage |
|---|---|---|
| **Total documents scanned** | 165 | 100.0% |
| Temporally valid (matches folder) | 163 | 98.8% |
| Misfiled (in-window, wrong folder) | 0 | 0.0% |
| Out-of-scope year | 0 | 0.0% |
| Flagged for manual review | 2 | 1.2% |
| Unresolved (no year signal) | 0 | 0.0% |

| Extraction | Count | Percentage |
|---|---|---|
| Digital | 160 | 97.0% |
| Hybrid | 5 | 3.0% |
| OCR | 0 | 0.0% |
| Pages OCR'd in total | 5 | - |

Mean consensus confidence: **0.85** (median 1.00). Documents resolved on a single signal: 3 (1.8%).

## 2. Duplicate analysis

- Byte-identical files (SHA-256): **0** group(s) covering 0 file(s)
- Repeated ordinance numbers: **0** group(s) covering 0 file(s)
- Files with no parseable ordinance number: **1**

## 3. Signal extraction completeness

| Component signal | Extracted | Coverage |
|---|---|---|
| Enactment date | 153 / 165 | 92.7% |
| Ordinance number | 164 / 165 | 99.4% |
| Series header | 158 / 165 | 95.8% |
| Approval date | 164 / 165 | 99.4% |

Ordinance number source: filename 164/165, filename and header agree on 142. Citation-style references rejected before they could hijack the signal: **0**.

## 4. Corpus text characteristics

| Metric | Value |
|---|---|
| Mean characters | 15,305 |
| Median characters | 10,561 |
| Mean words | 2,431 |
| Shortest document | 3,702 chars |
| Longest document | 107,451 chars |
| Mean pages | 10.3 |
| Mean characters per page | 1,401 |
| Suspected incomplete (<300 chars) | 0 files |
| Low text density (<100 chars/page) | 0 files |

## 5. Temporal discrepancies and misfiled files

No confidently misfiled or out-of-scope ordinances detected.

### Flagged for manual review (not actioned)

| Filename | Resolved | Conf. | Agree | Reason |
|---|---|---|---|---|
| `Ordinance No. 0123-19 (1).pdf` | 1991 | 0.17 | 1/4 | enacted 1991 vs approved 2020 |
| `Ordinance No. 0673-18.pdf` | 1991 | 0.17 | 1/4 | enacted 1991 vs approved 2019; series 2020 vs ord-no 2018 |
