# Legal NLP EDA & Temporal Audit Report: 2021
*Generated automatically by `src/ordinance_eda_pipeline.py`*

Study window: 2016-2025 | confidence bar for misfiling: 0.45 | for relocation: 0.60

## 1. Executive summary and file inventory

Categories below are mutually exclusive, so the percentages sum to 100%.

| Classification | Count | Percentage |
|---|---|---|
| **Total documents scanned** | 233 | 100.0% |
| Temporally valid (matches folder) | 213 | 91.4% |
| Misfiled (in-window, wrong folder) | 0 | 0.0% |
| Out-of-scope year | 0 | 0.0% |
| Flagged for manual review | 7 | 3.0% |
| Unresolved (no year signal) | 13 | 5.6% |

| Extraction | Count | Percentage |
|---|---|---|
| Digital | 224 | 96.1% |
| Hybrid | 9 | 3.9% |
| OCR | 0 | 0.0% |
| Pages OCR'd in total | 13 | - |

Mean consensus confidence: **0.49** (median 0.45). Documents resolved on a single signal: 71 (30.5%).

## 2. Duplicate analysis

- Byte-identical files (SHA-256): **0** group(s) covering 0 file(s)
- Repeated ordinance numbers: **0** group(s) covering 0 file(s)
- Files with no parseable ordinance number: **106**

## 3. Signal extraction completeness

| Component signal | Extracted | Coverage |
|---|---|---|
| Enactment date | 116 / 233 | 49.8% |
| Ordinance number | 127 / 233 | 54.5% |
| Series header | 131 / 233 | 56.2% |
| Approval date | 155 / 233 | 66.5% |

Ordinance number source: filename 120/233, filename and header agree on 49. Citation-style references rejected before they could hijack the signal: **3**.

> **Parser health warning.** Enactment-date coverage is 49.8%. An enactment clause appears in virtually every enacted ordinance, so a low rate here is a parsing failure, not a corpus property. Run `--debug-headers` on this folder and tune `ENACT_ANCHOR_RE` / `DATE_PATTERNS` against the real layout before treating any temporal verdict in this report as final.

## 4. Corpus text characteristics

| Metric | Value |
|---|---|
| Mean characters | 10,896 |
| Median characters | 5,690 |
| Mean words | 1,719 |
| Shortest document | 2,745 chars |
| Longest document | 66,108 chars |
| Mean pages | 6.7 |
| Mean characters per page | 1,650 |
| Suspected incomplete (<300 chars) | 0 files |
| Low text density (<100 chars/page) | 0 files |

## 5. Temporal discrepancies and misfiled files

No confidently misfiled or out-of-scope ordinances detected.

### Flagged for manual review (not actioned)

| Filename | Resolved | Conf. | Agree | Reason |
|---|---|---|---|---|
| `Ordinance No. 000670-21.pdf` | - | 0.00 | 0/0 | no year signal recovered |
| `Ordinance No. 000675-21.pdf` | - | 0.00 | 0/0 | no year signal recovered |
| `Ordinance No. 000684-21.pdf` | 2027 | 0.30 | 1/3 | enacted 2027 vs approved 2021 |
| `Ordinance No. 000687-21.pdf` | 2019 | 0.00 | 0/0 | mismatch below confidence bar |
| `Ordinance No. 000691-21.pdf` | 2019 | 0.00 | 0/0 | mismatch below confidence bar |
| `Ordinance No. 000696-21.pdf` | - | 0.00 | 0/0 | no year signal recovered |
| `Ordinance No. 000700-21.pdf` | - | 0.00 | 0/0 | no year signal recovered |
| `Ordinance No. 000705-21.pdf` | - | 0.00 | 0/0 | no year signal recovered |
| `Ordinance No. 000708-21.pdf` | 2019 | 0.00 | 0/0 | mismatch below confidence bar |
| `Ordinance No. 000729-21.pdf` | 2019 | 0.00 | 0/0 | mismatch below confidence bar |
| `Ordinance No. 000730-21.pdf` | - | 0.00 | 0/0 | no year signal recovered |
| `Ordinance No. 000745-21.pdf` | 2027 | 0.10 | 1/1 | mismatch below confidence bar |
| `Ordinance No. 000817-21.pdf` | - | 0.00 | 0/0 | no year signal recovered |
| `Ordinance No. 000820-21.pdf` | - | 0.00 | 0/0 | no year signal recovered |
| `Ordinance No. 000823-21.pdf` | - | 0.00 | 0/0 | no year signal recovered |
| `Ordinance No. 000830-21.pdf` | - | 0.00 | 0/0 | no year signal recovered |
| `Ordinance No. 000831-21.pdf` | - | 0.00 | 0/0 | no year signal recovered |
| `Ordinance No. 000835-21.pdf` | - | 0.00 | 0/0 | no year signal recovered |
| `Ordinance No. 000842-21.pdf` | - | 0.00 | 0/0 | no year signal recovered |
| `Ordinance No. 0174-19 (1).pdf` | 1991 | 0.17 | 1/4 | enacted 1991 vs approved 2021; series 2021 vs ord-no 2019 |
