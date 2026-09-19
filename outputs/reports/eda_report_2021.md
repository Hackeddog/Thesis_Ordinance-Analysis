# Legal NLP EDA & Temporal Audit Report: 2021
*Generated automatically by `src/ordinance_eda_pipeline.py`*

Study window: 2016-2025 | confidence bar for misfiling: 0.45 | for relocation: 0.60

## 1. Executive summary and file inventory

Categories below are mutually exclusive, so the percentages sum to 100%.

| Classification | Count | Percentage |
|---|---|---|
| **Total documents scanned** | 247 | 100.0% |
| Temporally valid (matches folder) | 211 | 85.4% |
| Misfiled (in-window, wrong folder) | 0 | 0.0% |
| Out-of-scope year | 0 | 0.0% |
| Flagged for manual review | 23 | 9.3% |
| Unresolved (no year signal) | 13 | 5.3% |

| Extraction | Count | Percentage |
|---|---|---|
| Digital | 237 | 96.0% |
| Hybrid | 10 | 4.0% |
| OCR | 0 | 0.0% |
| Pages OCR'd in total | 14 | - |

Mean consensus confidence: **0.47** (median 0.45). Documents resolved on a single signal: 86 (34.8%).

## 2. Duplicate analysis

- Byte-identical files (SHA-256): **0** group(s) covering 0 file(s)
- Repeated ordinance numbers: **0** group(s) covering 0 file(s)
- Files with no parseable ordinance number: **118**

## 3. Signal extraction completeness

| Component signal | Extracted | Coverage |
|---|---|---|
| Enactment date | 120 / 247 | 48.6% |
| Ordinance number | 129 / 247 | 52.2% |
| Series header | 133 / 247 | 53.8% |
| Approval date | 163 / 247 | 66.0% |

Ordinance number source: filename 122/247, filename and header agree on 48. Citation-style references rejected before they could hijack the signal: **5**.

> **Parser health warning.** Enactment-date coverage is 48.6%. An enactment clause appears in virtually every enacted ordinance, so a low rate here is a parsing failure, not a corpus property. Run `--debug-headers` on this folder and tune `ENACT_ANCHOR_RE` / `DATE_PATTERNS` against the real layout before treating any temporal verdict in this report as final.

## 4. Corpus text characteristics

| Metric | Value |
|---|---|
| Mean characters | 10,905 |
| Median characters | 5,576 |
| Mean words | 1,721 |
| Shortest document | 2,745 chars |
| Longest document | 66,108 chars |
| Mean pages | 6.6 |
| Mean characters per page | 1,656 |
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
| `Ordinance No. 000757-21.pdf` | 2019 | 0.00 | 0/0 | mismatch below confidence bar |
| `Ordinance No. 000766-21.pdf` | 2019 | 0.00 | 0/0 | mismatch below confidence bar |
| `Ordinance No. 000780-21.pdf` | 2019 | 0.00 | 0/0 | mismatch below confidence bar |
| `Ordinance No. 000782-21.pdf` | 2022 | 0.10 | 1/1 | mismatch below confidence bar |
| `Ordinance No. 000789-21.pdf` | 2022 | 0.10 | 1/1 | mismatch below confidence bar |
| `Ordinance No. 000791-21.pdf` | 2019 | 0.00 | 0/0 | mismatch below confidence bar |
| `Ordinance No. 000808-21.pdf` | 2022 | 0.10 | 1/1 | mismatch below confidence bar |
| `Ordinance No. 000812-21.pdf` | 2019 | 0.00 | 0/0 | mismatch below confidence bar |
| `Ordinance No. 000817-21.pdf` | - | 0.00 | 0/0 | no year signal recovered |
| `Ordinance No. 000820-21.pdf` | - | 0.00 | 0/0 | no year signal recovered |
| `Ordinance No. 000823-21.pdf` | - | 0.00 | 0/0 | no year signal recovered |
| `Ordinance No. 000830-21.pdf` | - | 0.00 | 0/0 | no year signal recovered |
| `Ordinance No. 000831-21.pdf` | - | 0.00 | 0/0 | no year signal recovered |
| `Ordinance No. 000832-21.pdf` | 2019 | 0.00 | 0/0 | mismatch below confidence bar |
| `Ordinance No. 000835-21.pdf` | - | 0.00 | 0/0 | no year signal recovered |
| `Ordinance No. 000842-21.pdf` | - | 0.00 | 0/0 | no year signal recovered |
| `Ordinance No. 000843-21.pdf` | 2019 | 0.00 | 0/0 | mismatch below confidence bar |
| `Ordinance No. 000850-21.pdf` | 2020 | 0.10 | 1/1 | mismatch below confidence bar |
| `Ordinance No. 0475-21.pdf` | 2023 | 0.17 | 1/4 | enacted 2023 vs approved 2019 |
| `Ordinance No. 0477-21.pdf` | 2027 | 0.17 | 1/4 | enacted 2027 vs approved 2020 |
| `Ordinance No. 0492-21.pdf` | 1991 | 0.28 | 1/3 | enacted 1991 vs approved 2021 |
| `Ordinance No. 0632-21.pdf` | 1981 | 0.17 | 1/4 | enacted 1981 vs approved 2021; series 1997 vs ord-no 2021 |
| `Ordinance No. 0736-21001.pdf` | 1991 | 0.30 | 1/3 | enacted 1991 vs approved 2021 |
| `Ordinance No. 0784-21.pdf` | 1991 | 0.17 | 1/4 | enacted 1991 vs approved 2022; series 2022 vs ord-no 2021 |
