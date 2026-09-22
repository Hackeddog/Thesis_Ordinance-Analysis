# Legal NLP EDA & Temporal Audit Report: 2025
*Generated automatically by `src/ordinance_eda_pipeline.py`*

Study window: 2016-2024 | confidence bar for misfiling: 0.45 | for relocation: 0.60

## 1. Executive summary and file inventory

Categories below are mutually exclusive, so the percentages sum to 100%.

| Classification | Count | Percentage |
|---|---|---|
| **Total documents scanned** | 30 | 100.0% |
| Temporally valid (matches folder) | 0 | 0.0% |
| Misfiled (in-window, wrong folder) | 0 | 0.0% |
| Out-of-scope year | 30 | 100.0% |
| Flagged for manual review | 0 | 0.0% |
| Unresolved (no year signal) | 0 | 0.0% |

| Extraction | Count | Percentage |
|---|---|---|
| Digital | 30 | 100.0% |
| Hybrid | 0 | 0.0% |
| OCR | 0 | 0.0% |
| Pages OCR'd in total | 0 | - |

Mean consensus confidence: **0.62** (median 0.55). Documents resolved on a single signal: 0 (0.0%).

## 2. Duplicate analysis

- Byte-identical files (SHA-256): **0** group(s) covering 0 file(s)
- Repeated ordinance numbers: **0** group(s) covering 0 file(s)
- Files with no parseable ordinance number: **0**

## 3. Signal extraction completeness

| Component signal | Extracted | Coverage |
|---|---|---|
| Enactment date | 19 / 30 | 63.3% |
| Ordinance number | 30 / 30 | 100.0% |
| Series header | 28 / 30 | 93.3% |
| Approval date | 28 / 30 | 93.3% |

Ordinance number source: filename 30/30, filename and header agree on 27. Citation-style references rejected before they could hijack the signal: **0**.

## 4. Corpus text characteristics

| Metric | Value |
|---|---|
| Mean characters | 15,990 |
| Median characters | 11,754 |
| Mean words | 2,554 |
| Shortest document | 3,739 chars |
| Longest document | 68,717 chars |
| Mean pages | 9.7 |
| Mean characters per page | 1,601 |
| Suspected incomplete (<300 chars) | 0 files |
| Low text density (<100 chars/page) | 0 files |

## 5. Temporal discrepancies and misfiled files

| Filename | Ord. No. | Status | Folder | Resolved | Conf. | Agree | Enacted | Ord-no | Series | Approved | Suggested path |
|---|---|---|---|---|---|---|---|---|---|---|---|
| `Ordinance No. 018-25.pdf` | 018-25 | out_of_scope | 2025 | **2025** | 0.55 | 3/3 | - | 2025 | 2025 | 2025 | `data/raw/2025/` |
| `Ordinance No. 0735-25.pdf` | 0735-25 | out_of_scope | 2025 | **2025** | 0.70 | 2/2 | 2025 | 2025 | - | - | `data/raw/2025/` |
| `Ordinance No. 0736-25.pdf` | 0736-25 | out_of_scope | 2025 | **2025** | 0.60 | 2/3 | 2025 | 2025 | 2024 | - | `data/raw/2025/` |
| `Ordinance No. 0739-25.pdf` | 0739-25 | out_of_scope | 2025 | **2025** | 0.33 | 3/4 | 1991 | 2025 | 2025 | 2025 | `data/raw/2025/` |
| `Ordinance No. 0741-25.pdf` | 0741-25 | out_of_scope | 2025 | **2025** | 0.55 | 3/3 | - | 2025 | 2025 | 2025 | `data/raw/2025/` |
| `Ordinance No. 0742-25.pdf` | 0742-25 | out_of_scope | 2025 | **2025** | 1.00 | 4/4 | 2025 | 2025 | 2025 | 2025 | `data/raw/2025/` |
| `Ordinance No. 0754-25.pdf` | 0754-25 | out_of_scope | 2025 | **2025** | 0.33 | 3/4 | 1991 | 2025 | 2025 | 2025 | `data/raw/2025/` |
| `Ordinance No. 0756-25 Service Contract Agreement, LTFRB et al..pdf` | 0756-25 | out_of_scope | 2025 | **2025** | 0.55 | 3/3 | - | 2025 | 2025 | 2025 | `data/raw/2025/` |
| `Ordinance No. 0758-25.pdf` | 0758-25 | out_of_scope | 2025 | **2025** | 0.55 | 3/3 | - | 2025 | 2025 | 2025 | `data/raw/2025/` |
| `Ordinance No. 0760-25.pdf` | 0760-25 | out_of_scope | 2025 | **2025** | 0.33 | 3/4 | 1991 | 2025 | 2025 | 2025 | `data/raw/2025/` |
| `Ordinance No. 0765-25.pdf` | 0765-25 | out_of_scope | 2025 | **2025** | 0.33 | 3/4 | 1991 | 2025 | 2025 | 2025 | `data/raw/2025/` |
| `Ordinance No. 0766-25.pdf` | 0766-25 | out_of_scope | 2025 | **2025** | 0.33 | 3/4 | 1991 | 2025 | 2025 | 2025 | `data/raw/2025/` |
| `Ordinance No. 0767-25.pdf` | 0767-25 | out_of_scope | 2025 | **2025** | 0.33 | 3/4 | 1991 | 2025 | 2025 | 2025 | `data/raw/2025/` |
| `Ordinance No. 0772-25.pdf` | 0772-25 | out_of_scope | 2025 | **2025** | 0.33 | 3/4 | 1991 | 2025 | 2025 | 2025 | `data/raw/2025/` |
| `Ordinance No. 0773-25.pdf` | 0773-25 | out_of_scope | 2025 | **2025** | 0.85 | 3/4 | 2025 | 2025 | 2025 | 2024 | `data/raw/2025/` |
| `Ordinance No. 0774-25.pdf` | 0774-25 | out_of_scope | 2025 | **2025** | 0.55 | 3/3 | - | 2025 | 2025 | 2025 | `data/raw/2025/` |
| `Ordinance No. 0776-25.pdf` | 0776-25 | out_of_scope | 2025 | **2025** | 1.00 | 4/4 | 2025 | 2025 | 2025 | 2025 | `data/raw/2025/` |
| `Ordinance No. 0778-25.pdf` | 0778-25 | out_of_scope | 2025 | **2025** | 1.00 | 4/4 | 2025 | 2025 | 2025 | 2025 | `data/raw/2025/` |
| `Ordinance No. 0779-25.pdf` | 0779-25 | out_of_scope | 2025 | **2025** | 0.55 | 3/3 | - | 2025 | 2025 | 2025 | `data/raw/2025/` |
| `Ordinance No. 0782-25.pdf` | 0782-25 | out_of_scope | 2025 | **2025** | 1.00 | 4/4 | 2025 | 2025 | 2025 | 2025 | `data/raw/2025/` |
| `Ordinance No. 0783-25.pdf` | 0783-25 | out_of_scope | 2025 | **2025** | 1.00 | 4/4 | 2025 | 2025 | 2025 | 2025 | `data/raw/2025/` |
| `Ordinance No. 0784-25.pdf` | 0784-25 | out_of_scope | 2025 | **2025** | 1.00 | 4/4 | 2025 | 2025 | 2025 | 2025 | `data/raw/2025/` |
| `Ordinance No. 0785-25.pdf` | 0785-25 | out_of_scope | 2025 | **2025** | 0.33 | 3/4 | 1991 | 2025 | 2025 | 2025 | `data/raw/2025/` |
| `Ordinance No. 0787-25.pdf` | 0787-25 | out_of_scope | 2025 | **2025** | 0.55 | 3/3 | - | 2025 | 2025 | 2025 | `data/raw/2025/` |
| `Ordinance No. 0789-25 (7-14-25).pdf` | 0789-25 | out_of_scope | 2025 | **2025** | 1.00 | 4/4 | 2025 | 2025 | 2025 | 2025 | `data/raw/2025/` |
| `Ordinance No. 0791-25.pdf` | 0791-25 | out_of_scope | 2025 | **2025** | 1.00 | 4/4 | 2025 | 2025 | 2025 | 2025 | `data/raw/2025/` |
| `Ordinance No. 0792-25.pdf` | 0792-25 | out_of_scope | 2025 | **2025** | 0.55 | 3/3 | - | 2025 | 2025 | 2025 | `data/raw/2025/` |
| `Ordinance No. 0795-25.pdf` | 0795-25 | out_of_scope | 2025 | **2025** | 0.55 | 3/3 | - | 2025 | 2025 | 2025 | `data/raw/2025/` |
| `Ordinance No. 0828-25.pdf` | 0828-25 | out_of_scope | 2025 | **2025** | 0.35 | 2/2 | - | 2025 | - | 2025 | `data/raw/2025/` |
| `Ordinance No. 0835-25 (unsigned).pdf` | 0835-25 | out_of_scope | 2025 | **2025** | 0.55 | 3/3 | - | 2025 | 2025 | 2025 | `data/raw/2025/` |

### Flagged for manual review (not actioned)

None.
