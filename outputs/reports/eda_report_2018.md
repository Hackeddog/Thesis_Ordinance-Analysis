# Legal NLP EDA & Temporal Audit Report: 2018
*Generated automatically by `src/ordinance_eda_pipeline.py`*

Study window: 2016-2025 | confidence bar for misfiling: 0.45 | for relocation: 0.60

## 1. Executive summary and file inventory

Categories below are mutually exclusive, so the percentages sum to 100%.

| Classification | Count | Percentage |
|---|---|---|
| **Total documents scanned** | 248 | 100.0% |
| Temporally valid (matches folder) | 232 | 93.5% |
| Misfiled (in-window, wrong folder) | 8 | 3.2% |
| Out-of-scope year | 0 | 0.0% |
| Flagged for manual review | 8 | 3.2% |
| Unresolved (no year signal) | 0 | 0.0% |

| Extraction | Count | Percentage |
|---|---|---|
| Digital | 242 | 97.6% |
| Hybrid | 6 | 2.4% |
| OCR | 0 | 0.0% |
| Pages OCR'd in total | 7 | - |

Mean consensus confidence: **0.68** (median 0.55). Documents resolved on a single signal: 4 (1.6%).

## 2. Duplicate analysis

- Byte-identical files (SHA-256): **0** group(s) covering 0 file(s)
- Repeated ordinance numbers: **0** group(s) covering 0 file(s)
- Files with no parseable ordinance number: **0**

## 3. Signal extraction completeness

| Component signal | Extracted | Coverage |
|---|---|---|
| Enactment date | 150 / 248 | 60.5% |
| Ordinance number | 248 / 248 | 100.0% |
| Series header | 242 / 248 | 97.6% |
| Approval date | 247 / 248 | 99.6% |

Ordinance number source: filename 248/248, filename and header agree on 195. Citation-style references rejected before they could hijack the signal: **1**.

## 4. Corpus text characteristics

| Metric | Value |
|---|---|
| Mean characters | 12,951 |
| Median characters | 7,765 |
| Mean words | 2,053 |
| Shortest document | 4,991 chars |
| Longest document | 144,329 chars |
| Mean pages | 9.3 |
| Mean characters per page | 1,313 |
| Suspected incomplete (<300 chars) | 0 files |
| Low text density (<100 chars/page) | 0 files |

## 5. Temporal discrepancies and misfiled files

| Filename | Ord. No. | Status | Folder | Resolved | Conf. | Agree | Enacted | Ord-no | Series | Approved | Suggested path |
|---|---|---|---|---|---|---|---|---|---|---|---|
| `Ordinance No. 0631-18.pdf` | 0631-18 | misfiled | 2018 | **2019** | 0.62 | 3/4 | 2019 | 2018 | 2019 | 2019 | `data/raw/2019/` |
| `Ordinance No. 0632-18.pdf` | 0632-18 | misfiled | 2018 | **2019** | 0.48 | 2/4 | 2019 | 2018 | 2019 | 2018 | `data/raw/2019/` |
| `Ordinance No. 0642-18.pdf` | 0642-18 | misfiled | 2018 | **2019** | 0.48 | 2/4 | 2019 | 2018 | 2019 | 2018 | `data/raw/2019/` |
| `Ordinance No. 0647-18.pdf` | 0647-18 | misfiled | 2018 | **2019** | 0.62 | 3/4 | 2019 | 2018 | 2019 | 2019 | `data/raw/2019/` |
| `Ordinance No. 0653-18.pdf` | 0653-18 | misfiled | 2018 | **2019** | 0.62 | 3/4 | 2019 | 2018 | 2019 | 2019 | `data/raw/2019/` |
| `Ordinance No. 0657-18.pdf` | 0657-18 | misfiled | 2018 | **2019** | 0.62 | 3/4 | 2019 | 2018 | 2019 | 2019 | `data/raw/2019/` |
| `Ordinance No. 0658-18.pdf` | 0658-18 | misfiled | 2018 | **2019** | 0.62 | 3/4 | 2019 | 2018 | 2019 | 2019 | `data/raw/2019/` |
| `Ordinance No. 0668-18.pdf` | 0668-18 | misfiled | 2018 | **2019** | 0.62 | 3/4 | 2019 | 2018 | 2019 | 2019 | `data/raw/2019/` |

### Flagged for manual review (not actioned)

| Filename | Resolved | Conf. | Agree | Reason |
|---|---|---|---|---|
| `Ordinance No. 0592-18.pdf` | 2019 | 0.18 | 2/3 | series 2019 vs ord-no 2018 |
| `Ordinance No. 0643-18.pdf` | 2019 | 0.33 | 2/4 | mismatch below confidence bar |
| `Ordinance No. 0644-18.pdf` | 2019 | 0.33 | 2/4 | mismatch below confidence bar |
| `Ordinance No. 0645-18.pdf` | 2019 | 0.18 | 2/3 | series 2019 vs ord-no 2018 |
| `Ordinance No. 0648-18.pdf` | 2019 | 0.33 | 2/4 | mismatch below confidence bar |
| `Ordinance No. 0655-18.pdf` | 2019 | 0.33 | 2/4 | mismatch below confidence bar |
| `Ordinance No. 0672-18.pdf` | 1991 | 0.17 | 1/4 | enacted 1991 vs approved 2019 |
| `Ordinance No. 0673-18.pdf` | 1991 | 0.17 | 1/4 | enacted 1991 vs approved 2019; series 2020 vs ord-no 2018 |
