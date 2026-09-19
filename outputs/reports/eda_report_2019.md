# Legal NLP EDA & Temporal Audit Report: 2019
*Generated automatically by `src/ordinance_eda_pipeline.py`*

Study window: 2016-2025 | confidence bar for misfiling: 0.45 | for relocation: 0.60

## 1. Executive summary and file inventory

Categories below are mutually exclusive, so the percentages sum to 100%.

| Classification | Count | Percentage |
|---|---|---|
| **Total documents scanned** | 265 | 100.0% |
| Temporally valid (matches folder) | 239 | 90.2% |
| Misfiled (in-window, wrong folder) | 9 | 3.4% |
| Out-of-scope year | 0 | 0.0% |
| Flagged for manual review | 17 | 6.4% |
| Unresolved (no year signal) | 0 | 0.0% |

| Extraction | Count | Percentage |
|---|---|---|
| Digital | 252 | 95.1% |
| Hybrid | 13 | 4.9% |
| OCR | 0 | 0.0% |
| Pages OCR'd in total | 13 | - |

Mean consensus confidence: **0.63** (median 0.55). Documents resolved on a single signal: 7 (2.6%).

## 2. Duplicate analysis

- Byte-identical files (SHA-256): **0** group(s) covering 0 file(s)
- Repeated ordinance numbers: **0** group(s) covering 0 file(s)
- Files with no parseable ordinance number: **1**

## 3. Signal extraction completeness

| Component signal | Extracted | Coverage |
|---|---|---|
| Enactment date | 123 / 265 | 46.4% |
| Ordinance number | 264 / 265 | 99.6% |
| Series header | 250 / 265 | 94.3% |
| Approval date | 263 / 265 | 99.2% |

Ordinance number source: filename 264/265, filename and header agree on 226. Citation-style references rejected before they could hijack the signal: **1**.

> **Parser health warning.** Enactment-date coverage is 46.4%. An enactment clause appears in virtually every enacted ordinance, so a low rate here is a parsing failure, not a corpus property. Run `--debug-headers` on this folder and tune `ENACT_ANCHOR_RE` / `DATE_PATTERNS` against the real layout before treating any temporal verdict in this report as final.

## 4. Corpus text characteristics

| Metric | Value |
|---|---|
| Mean characters | 16,532 |
| Median characters | 9,351 |
| Mean words | 2,628 |
| Shortest document | 3,560 chars |
| Longest document | 444,640 chars |
| Mean pages | 11.2 |
| Mean characters per page | 1,386 |
| Suspected incomplete (<300 chars) | 0 files |
| Low text density (<100 chars/page) | 0 files |

## 5. Temporal discrepancies and misfiled files

| Filename | Ord. No. | Status | Folder | Resolved | Conf. | Agree | Enacted | Ord-no | Series | Approved | Suggested path |
|---|---|---|---|---|---|---|---|---|---|---|---|
| `Ordinance No. 0100-19 (1).pdf` | 0100-19 | misfiled | 2019 | **2020** | 0.62 | 3/4 | 2020 | 2019 | 2020 | 2020 | `data/raw/2020/` |
| `Ordinance No. 0126-19 (1).pdf` | 0126-19 | misfiled | 2019 | **2020** | 0.62 | 3/4 | 2020 | 2019 | 2020 | 2020 | `data/raw/2020/` |
| `Ordinance No. 0129-19 (1).pdf` | 0129-19 | misfiled | 2019 | **2020** | 0.62 | 3/4 | 2020 | 2019 | 2020 | 2020 | `data/raw/2020/` |
| `Ordinance No. 0130-19 (1).pdf` | 0130-19 | misfiled | 2019 | **2020** | 0.62 | 3/4 | 2020 | 2019 | 2020 | 2020 | `data/raw/2020/` |
| `Ordinance No. 0133-19 (1).pdf` | 0133-19 | misfiled | 2019 | **2020** | 0.62 | 3/4 | 2020 | 2019 | 2020 | 2020 | `data/raw/2020/` |
| `Ordinance No. 0142-19 (1).pdf` | 0142-19 | misfiled | 2019 | **2020** | 0.62 | 3/4 | 2020 | 2019 | 2020 | 2020 | `data/raw/2020/` |
| `Ordinance No. 0167-19 (1).pdf` | 0167-19 | misfiled | 2019 | **2020** | 0.62 | 3/4 | 2020 | 2019 | 2020 | 2020 | `data/raw/2020/` |
| `Ordinance No. 063-19 (1).pdf` | 063-19 | misfiled | 2019 | **2020** | 0.53 | 2/3 | 2020 | 2019 | 2020 | - | `data/raw/2020/` |
| `Ordinance No. 075-19 (1).pdf` | 075-19 | misfiled | 2019 | **2020** | 0.62 | 3/4 | 2020 | 2019 | 2020 | 2020 | `data/raw/2020/` |

### Flagged for manual review (not actioned)

| Filename | Resolved | Conf. | Agree | Reason |
|---|---|---|---|---|
| `Davao City Forest Land Use Plan (2019-2023) (1).pdf` | 2018 | 0.40 | 1/2 | enacted 2018 vs approved 2004 |
| `Ordinance No. 0103-19 (1).pdf` | 2020 | 0.33 | 2/4 | mismatch below confidence bar |
| `Ordinance No. 0105-19 (1).pdf` | 2029 | 0.33 | 2/4 | series 2020 vs ord-no 2019 |
| `Ordinance No. 0114-19 (1).pdf` | 2020 | 0.18 | 2/3 | series 2020 vs ord-no 2019 |
| `Ordinance No. 0121-19 (1).pdf` | 2020 | 0.18 | 2/3 | series 2020 vs ord-no 2019 |
| `Ordinance No. 0123-19 (1).pdf` | 1991 | 0.17 | 1/4 | enacted 1991 vs approved 2020 |
| `Ordinance No. 0124-19 (1).pdf` | 2020 | 0.18 | 2/3 | series 2020 vs ord-no 2019 |
| `Ordinance No. 0125-19 (1).pdf` | 2020 | 0.33 | 2/4 | mismatch below confidence bar |
| `Ordinance No. 0143-19 (1).pdf` | 2020 | 0.18 | 2/3 | series 2020 vs ord-no 2019 |
| `Ordinance No. 0150-19 (1).pdf` | 2020 | 0.33 | 2/4 | mismatch below confidence bar |
| `Ordinance No. 0156-19 (1).pdf` | 2020 | 0.18 | 2/3 | series 2020 vs ord-no 2019 |
| `Ordinance No. 0174-19 (1).pdf` | 1991 | 0.17 | 1/4 | enacted 1991 vs approved 2021; series 2021 vs ord-no 2019 |
| `Ordinance No. 065-19 (1).pdf` | 2020 | 0.18 | 2/3 | series 2020 vs ord-no 2019 |
| `Ordinance No. 0678-19 (1).pdf` | 1997 | 0.28 | 1/3 | enacted 1997 vs approved 2019 |
| `Ordinance No. 0702-19 (1).pdf` | 1991 | 0.17 | 1/4 | enacted 1991 vs approved 2010 |
| `Ordinance No. 0781-19 (1).pdf` | 1955 | 0.17 | 1/4 | enacted 1955 vs approved 2012 |
| `Ordinance No. 087-19 (1).pdf` | 2021 | 0.18 | 2/3 | series 2021 vs ord-no 2019 |
