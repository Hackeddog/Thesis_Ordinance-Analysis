# Legal NLP EDA & Temporal Audit Report: 2016
*Generated automatically by `src/ordinance_eda_pipeline.py`*

Study window: 2016-2025 | confidence bar for misfiling: 0.45 | for relocation: 0.60

## 1. Executive summary and file inventory

Categories below are mutually exclusive, so the percentages sum to 100%.

| Classification | Count | Percentage |
|---|---|---|
| **Total documents scanned** | 180 | 100.0% |
| Temporally valid (matches folder) | 168 | 93.3% |
| Misfiled (in-window, wrong folder) | 1 | 0.6% |
| Out-of-scope year | 0 | 0.0% |
| Flagged for manual review | 11 | 6.1% |
| Unresolved (no year signal) | 0 | 0.0% |

| Extraction | Count | Percentage |
|---|---|---|
| Digital | 169 | 93.9% |
| Hybrid | 11 | 6.1% |
| OCR | 0 | 0.0% |
| Pages OCR'd in total | 14 | - |

Mean consensus confidence: **0.52** (median 0.55). Documents resolved on a single signal: 27 (15.0%).

## 2. Duplicate analysis

- Byte-identical files (SHA-256): **0** group(s) covering 0 file(s)
- Repeated ordinance numbers: **0** group(s) covering 0 file(s)
- Files with no parseable ordinance number: **0**

## 3. Signal extraction completeness

| Component signal | Extracted | Coverage |
|---|---|---|
| Enactment date | 56 / 180 | 31.1% |
| Ordinance number | 180 / 180 | 100.0% |
| Series header | 134 / 180 | 74.4% |
| Approval date | 160 / 180 | 88.9% |

Ordinance number source: filename 180/180, filename and header agree on 85. Citation-style references rejected before they could hijack the signal: **0**.

> **Parser health warning.** Enactment-date coverage is 31.1%. An enactment clause appears in virtually every enacted ordinance, so a low rate here is a parsing failure, not a corpus property. Run `--debug-headers` on this folder and tune `ENACT_ANCHOR_RE` / `DATE_PATTERNS` against the real layout before treating any temporal verdict in this report as final.

## 4. Corpus text characteristics

| Metric | Value |
|---|---|
| Mean characters | 17,002 |
| Median characters | 13,062 |
| Mean words | 2,747 |
| Shortest document | 3,108 chars |
| Longest document | 186,351 chars |
| Mean pages | 11.7 |
| Mean characters per page | 1,387 |
| Suspected incomplete (<300 chars) | 0 files |
| Low text density (<100 chars/page) | 0 files |

## 5. Temporal discrepancies and misfiled files

| Filename | Ord. No. | Status | Folder | Resolved | Conf. | Agree | Enacted | Ord-no | Series | Approved | Suggested path |
|---|---|---|---|---|---|---|---|---|---|---|---|
| `Ordinance No. 0134-16.pdf` | 0134-16 | misfiled | 2016 | **2017** | 0.53 | 2/3 | 2017 | 2016 | 2017 | - | `data/raw/2017/` |

### Flagged for manual review (not actioned)

| Filename | Resolved | Conf. | Agree | Reason |
|---|---|---|---|---|
| `Ordinance No. 0135-16.pdf` | 2017 | 0.33 | 1/2 | mismatch below confidence bar |
| `Ordinance No. 0137-16.pdf` | 2017 | 0.43 | 2/3 | mismatch below confidence bar |
| `Ordinance No. 033-16.pdf` | 1991 | 0.28 | 1/3 | enacted 1991 vs approved 2017 |
| `Ordinance No. 034-16.pdf` | 1991 | 0.17 | 1/4 | enacted 1991 vs approved 2017 |
| `Ordinance No. 040-16.pdf` | 1991 | 0.28 | 1/3 | enacted 1991 vs approved 2016 |
| `Ordinance No. 046-16.pdf` | 1991 | 0.28 | 1/3 | enacted 1991 vs approved 2016 |
| `Ordinance No. 0474-16.pdf` | 1991 | 0.28 | 1/3 | enacted 1991 vs approved 2016 |
| `Ordinance No. 0475-16.pdf` | 1991 | 0.17 | 1/4 | enacted 1991 vs approved 2016; series 2015 vs ord-no 2016 |
| `Ordinance No. 050-16.pdf` | 1991 | 0.28 | 1/3 | enacted 1991 vs approved 2016 |
| `Ordinance No. 0520-16.pdf` | 1991 | 0.23 | 1/3 | mismatch below confidence bar |
| `Ordinance No. 097-16.pdf` | 1991 | 0.28 | 1/3 | enacted 1991 vs approved 2016 |
