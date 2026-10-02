# Legal NLP EDA & Temporal Audit Report: 2023
*Generated automatically by `src/ordinance_eda_pipeline.py`*

Study window: 2016-2025 | confidence bar for misfiling: 0.45 | for relocation: 0.60

## 1. Executive summary and file inventory

Categories below are mutually exclusive, so the percentages sum to 100%.

| Classification | Count | Percentage |
|---|---|---|
| **Total documents scanned** | 219 | 100.0% |
| Temporally valid (matches folder) | 219 | 100.0% |
| Misfiled (in-window, wrong folder) | 0 | 0.0% |
| Out-of-scope year | 0 | 0.0% |
| Flagged for manual review | 0 | 0.0% |
| Unresolved (no year signal) | 0 | 0.0% |

| Extraction | Count | Percentage |
|---|---|---|
| Digital | 219 | 100.0% |
| Hybrid | 0 | 0.0% |
| OCR | 0 | 0.0% |
| Pages OCR'd in total | 0 | - |

Mean consensus confidence: **0.88** (median 1.00). Documents resolved on a single signal: 1 (0.5%).

## 2. Duplicate analysis

- Byte-identical files (SHA-256): **0** group(s) covering 0 file(s)
- Repeated ordinance numbers: **0** group(s) covering 0 file(s)
- Files with no parseable ordinance number: **4**

## 3. Signal extraction completeness

| Component signal | Extracted | Coverage |
|---|---|---|
| Enactment date | 176 / 219 | 80.4% |
| Ordinance number | 215 / 219 | 98.2% |
| Series header | 216 / 219 | 98.6% |
| Approval date | 191 / 219 | 87.2% |

Ordinance number source: filename 213/219, filename and header agree on 30. Citation-style references rejected before they could hijack the signal: **2**.

## 4. Corpus text characteristics

| Metric | Value |
|---|---|
| Mean characters | 6,404 |
| Median characters | 4,902 |
| Mean words | 1,003 |
| Shortest document | 2,602 chars |
| Longest document | 45,035 chars |
| Mean pages | 3.7 |
| Mean characters per page | 1,635 |
| Suspected incomplete (<300 chars) | 0 files |
| Low text density (<100 chars/page) | 0 files |

## 5. Temporal discrepancies and misfiled files

No confidently misfiled or out-of-scope ordinances detected.

### Flagged for manual review (not actioned)

None.
