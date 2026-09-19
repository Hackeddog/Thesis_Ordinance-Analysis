# Legal NLP EDA & Temporal Audit Report: 2023
*Generated automatically by `src/ordinance_eda_pipeline.py`*

Study window: 2016-2025 | confidence bar for misfiling: 0.45 | for relocation: 0.60

## 1. Executive summary and file inventory

Categories below are mutually exclusive, so the percentages sum to 100%.

| Classification | Count | Percentage |
|---|---|---|
| **Total documents scanned** | 223 | 100.0% |
| Temporally valid (matches folder) | 219 | 98.2% |
| Misfiled (in-window, wrong folder) | 0 | 0.0% |
| Out-of-scope year | 0 | 0.0% |
| Flagged for manual review | 4 | 1.8% |
| Unresolved (no year signal) | 0 | 0.0% |

| Extraction | Count | Percentage |
|---|---|---|
| Digital | 223 | 100.0% |
| Hybrid | 0 | 0.0% |
| OCR | 0 | 0.0% |
| Pages OCR'd in total | 0 | - |

Mean consensus confidence: **0.87** (median 1.00). Documents resolved on a single signal: 1 (0.4%).

## 2. Duplicate analysis

- Byte-identical files (SHA-256): **0** group(s) covering 0 file(s)
- Repeated ordinance numbers: **2** group(s) covering 4 file(s)
- Files with no parseable ordinance number: **4**

| Ordinance No. | Files | Resolved years |
|---|---|---|
| `0192-23` | `Ordinance No. 0192-23 (2).pdf`, `Ordinance No. 0192-23 Anti-Bullying (2).pdf` | 1991, 2023 |
| `0337-23` | `Ordinance No. 000337-23 (2).pdf`, `Ordinance No. 0337-23 (2).pdf` | 2023 |

## 3. Signal extraction completeness

| Component signal | Extracted | Coverage |
|---|---|---|
| Enactment date | 179 / 223 | 80.3% |
| Ordinance number | 219 / 223 | 98.2% |
| Series header | 220 / 223 | 98.7% |
| Approval date | 194 / 223 | 87.0% |

Ordinance number source: filename 217/223, filename and header agree on 31. Citation-style references rejected before they could hijack the signal: **2**.

## 4. Corpus text characteristics

| Metric | Value |
|---|---|
| Mean characters | 6,499 |
| Median characters | 4,902 |
| Mean words | 1,018 |
| Shortest document | 2,602 chars |
| Longest document | 45,035 chars |
| Mean pages | 3.7 |
| Mean characters per page | 1,638 |
| Suspected incomplete (<300 chars) | 0 files |
| Low text density (<100 chars/page) | 0 files |

## 5. Temporal discrepancies and misfiled files

No confidently misfiled or out-of-scope ordinances detected.

### Flagged for manual review (not actioned)

| Filename | Resolved | Conf. | Agree | Reason |
|---|---|---|---|---|
| `Ordinance No. 0192-23 (2).pdf` | 1991 | 0.17 | 1/4 | enacted 1991 vs approved 2025; series 2025 vs ord-no 2023 |
| `Ordinance No. 0362-23 (2).pdf` | 2024 | 0.33 | 2/4 | mismatch below confidence bar |
| `Ordinance No. 0375-23 (2).pdf` | 2024 | 0.33 | 2/4 | mismatch below confidence bar |
| `Ordinance No. 0382-23 (2).pdf` | 2024 | 0.33 | 2/4 | mismatch below confidence bar |
