# Legal NLP EDA & Temporal Audit Report: 2022
*Generated automatically by `src/ordinance_eda_pipeline.py`*

Study window: 2016-2025 | confidence bar for misfiling: 0.45 | for relocation: 0.60

## 1. Executive summary and file inventory

Categories below are mutually exclusive, so the percentages sum to 100%.

| Classification | Count | Percentage |
|---|---|---|
| **Total documents scanned** | 337 | 100.0% |
| Temporally valid (matches folder) | 334 | 99.1% |
| Misfiled (in-window, wrong folder) | 1 | 0.3% |
| Out-of-scope year | 1 | 0.3% |
| Flagged for manual review | 1 | 0.3% |
| Unresolved (no year signal) | 0 | 0.0% |

| Extraction | Count | Percentage |
|---|---|---|
| Digital | 336 | 99.7% |
| Hybrid | 0 | 0.0% |
| OCR | 1 | 0.3% |
| Pages OCR'd in total | 5 | - |

Mean consensus confidence: **0.87** (median 1.00). Documents resolved on a single signal: 4 (1.2%).

## 2. Duplicate analysis

- Byte-identical files (SHA-256): **59** group(s) covering 118 file(s)
- Repeated ordinance numbers: **28** group(s) covering 56 file(s)
- Files with no parseable ordinance number: **70**

| Ordinance No. | Files | Resolved years |
|---|---|---|
| `006-22` | `Ordinance No. 000006-22.pdf`, `Ordinance No. 006-22.pdf` | 2022 |
| `036-22` | `Ordinance No. 000036-22.pdf`, `Ordinance No. 036-22.pdf` | 2022 |
| `0855-22` | `Ordinance No. 000855-22.pdf`, `Ordinance No. 0855-22.pdf` | 2022 |
| `0857-22` | `Ordinance No. 000857-22.pdf`, `Ordinance No. 0857-22.pdf` | 2022 |
| `0859-22` | `Ordinance No. 000859-22.pdf`, `Ordinance No. 0859-22.pdf` | 2022 |
| `0863-22` | `Ordinance No. 000863-22.pdf`, `Ordinance No. 0863-22.pdf` | 2022 |
| `0873-22` | `Ordinance No. 000873-22.pdf`, `Ordinance No. 0873-22 (Creating Peace 911).pdf` | 2022 |
| `0874-22` | `Ordinance No. 000874-22.pdf`, `Ordinance No. 0874-22.pdf` | 2022 |
| `0876-22` | `Ordinance No. 000876-22.pdf`, `Ordinance No. 0876-22.pdf` | 2022 |
| `0881-22` | `Ordinance No. 000881-22.pdf`, `Ordinance No. 0881-22.pdf` | 2022 |
| `0885-22` | `Ordinance No. 000885-22.pdf`, `Ordinance No. 0885-22.pdf` | 2022 |
| `0892-22` | `Ordinance No. 000892-22.pdf`, `Ordinance No. 0892-22.pdf` | 2022 |
| `0893-22` | `Ordinance No. 000893-22.pdf`, `Ordinance No. 0893-22 (ALS).pdf` | 2022 |
| `0895-22` | `Ordinance No. 000895-22.pdf`, `Ordinance No. 0895-22.pdf` | 2022 |
| `0897-22` | `Ordinance No. 000897-22.pdf`, `Ordinance No. 0897-22 (Amend Organic Agri).pdf` | 2022 |
| `0923-22` | `Ordinance No. 000923-22.pdf`, `Ordinance No. 0923-22.pdf` | 2022 |
| `0925-22` | `Ordinance No. 000925-22.pdf`, `Ordinance No. 0925-22.pdf` | 2022 |
| `0926-22` | `Ordinance No. 000926-22.pdf`, `Ordinance No. 0926-22.pdf` | 2022 |
| `0927-22` | `Ordinance No. 000927-22.pdf`, `Ordinance No. 0927-22.pdf` | 2022 |
| `0929-22` | `Ordinance No. 000929-22.pdf`, `Ordinance No. 0929-22.pdf` | 2022 |
| `0932-22` | `Ordinance No. 000932-22.pdf`, `Ordinance No. 0932-22.pdf` | 2022 |
| `0939-22` | `Ordinance No. 000939-22.pdf`, `Ordinance No. 0939-22.pdf` | 2022 |
| `0947-22` | `Ordinance No. 000947-22.pdf`, `Ordinance No. 0947-22.pdf` | 2022 |
| `0951-22` | `Ordinance No. 000951-22.pdf`, `Ordinance No. 0951-22.pdf` | 2022 |
| `0952-22` | `Ordinance No. 000952-22.pdf`, `Ordinance No. 0952-22.pdf` | 2022 |
| `0953-22` | `Ordinance No. 000953-22.pdf`, `Ordinance No. 0953-22.pdf` | 2022 |
| `0959-22` | `Ordinance No. 000959-22.pdf`, `Ordinance No. 0959-22.pdf` | 2022 |
| `0988-22` | `Ordinance No. 000988-22.pdf`, `Ordinance No. 0988-22.pdf` | 2022 |

## 3. Signal extraction completeness

| Component signal | Extracted | Coverage |
|---|---|---|
| Enactment date | 297 / 337 | 88.1% |
| Ordinance number | 267 / 337 | 79.2% |
| Series header | 325 / 337 | 96.4% |
| Approval date | 296 / 337 | 87.8% |

Ordinance number source: filename 238/337, filename and header agree on 49. Citation-style references rejected before they could hijack the signal: **8**.

## 4. Corpus text characteristics

| Metric | Value |
|---|---|
| Mean characters | 8,250 |
| Median characters | 5,183 |
| Mean words | 1,291 |
| Shortest document | 2,775 chars |
| Longest document | 116,250 chars |
| Mean pages | 4.5 |
| Mean characters per page | 1,714 |
| Suspected incomplete (<300 chars) | 0 files |
| Low text density (<100 chars/page) | 0 files |

## 5. Temporal discrepancies and misfiled files

| Filename | Ord. No. | Status | Folder | Resolved | Conf. | Agree | Enacted | Ord-no | Series | Approved | Suggested path |
|---|---|---|---|---|---|---|---|---|---|---|---|
| `Ordinance No. 000916-22.pdf` | 0218-09 | out_of_scope | 2022 | **2009** | 0.55 | 2/4 | 2009 | 2009 | 2022 | 2022 | `data/raw/2009/` |
| `RESOLUTION NO 03253-19_Adopting CDP.pdf` | nan | misfiled | 2022 | **2019** | 0.75 | 3/3 | 2019 | - | 2019 | 2019 | `data/raw/2019/` |

### Flagged for manual review (not actioned)

| Filename | Resolved | Conf. | Agree | Reason |
|---|---|---|---|---|
| `Ordinance No. 000902-22.pdf` | 2020 | 0.30 | 1/3 | enacted 2020 vs approved 2022 |
