# Legal NLP EDA & Temporal Audit Report: 2024
*Generated automatically by `src/ordinance_eda_pipeline.py`*

Study window: 2016-2025 | confidence bar for misfiling: 0.45 | for relocation: 0.60

## 1. Executive summary and file inventory

Categories below are mutually exclusive, so the percentages sum to 100%.

| Classification | Count | Percentage |
|---|---|---|
| **Total documents scanned** | 298 | 100.0% |
| Temporally valid (matches folder) | 298 | 100.0% |
| Misfiled (in-window, wrong folder) | 0 | 0.0% |
| Out-of-scope year | 0 | 0.0% |
| Flagged for manual review | 0 | 0.0% |
| Unresolved (no year signal) | 0 | 0.0% |

| Extraction | Count | Percentage |
|---|---|---|
| Digital | 297 | 99.7% |
| Hybrid | 1 | 0.3% |
| OCR | 0 | 0.0% |
| Pages OCR'd in total | 1 | - |

Mean consensus confidence: **0.84** (median 1.00). Documents resolved on a single signal: 9 (3.0%).

## 2. Duplicate analysis

- Byte-identical files (SHA-256): **0** group(s) covering 0 file(s)
- Repeated ordinance numbers: **0** group(s) covering 0 file(s)
- Files with no parseable ordinance number: **0**

## 3. Signal extraction completeness

| Component signal | Extracted | Coverage |
|---|---|---|
| Enactment date | 229 / 298 | 76.8% |
| Ordinance number | 298 / 298 | 100.0% |
| Series header | 276 / 298 | 92.6% |
| Approval date | 242 / 298 | 81.2% |

Ordinance number source: filename 296/298, filename and header agree on 47. Citation-style references rejected before they could hijack the signal: **1**.

## 4. Corpus text characteristics

| Metric | Value |
|---|---|
| Mean characters | 6,567 |
| Median characters | 5,150 |
| Mean words | 1,067 |
| Shortest document | 2,704 chars |
| Longest document | 65,861 chars |
| Mean pages | 4.0 |
| Mean characters per page | 1,670 |
| Suspected incomplete (<300 chars) | 0 files |
| Low text density (<100 chars/page) | 0 files |

## 5. Temporal discrepancies and misfiled files

No confidently misfiled or out-of-scope ordinances detected.

### Flagged for manual review (not actioned)

None.
