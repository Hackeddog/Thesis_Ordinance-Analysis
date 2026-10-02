# Legal NLP EDA & Temporal Audit Report: 2016
*Generated automatically by `src/ordinance_eda_pipeline.py`*

Study window: 2016-2025 | confidence bar for misfiling: 0.45 | for relocation: 0.60

## 1. Executive summary and file inventory

Categories below are mutually exclusive, so the percentages sum to 100%.

| Classification | Count | Percentage |
|---|---|---|
| **Total documents scanned** | 174 | 100.0% |
| Temporally valid (matches folder) | 168 | 96.6% |
| Misfiled (in-window, wrong folder) | 0 | 0.0% |
| Out-of-scope year | 0 | 0.0% |
| Flagged for manual review | 6 | 3.4% |
| Unresolved (no year signal) | 0 | 0.0% |

| Extraction | Count | Percentage |
|---|---|---|
| Digital | 163 | 93.7% |
| Hybrid | 11 | 6.3% |
| OCR | 0 | 0.0% |
| Pages OCR'd in total | 14 | - |

Mean consensus confidence: **0.53** (median 0.55). Documents resolved on a single signal: 23 (13.2%).

## 2. Duplicate analysis

- Byte-identical files (SHA-256): **0** group(s) covering 0 file(s)
- Repeated ordinance numbers: **0** group(s) covering 0 file(s)
- Files with no parseable ordinance number: **0**

## 3. Signal extraction completeness

| Component signal | Extracted | Coverage |
|---|---|---|
| Enactment date | 50 / 174 | 28.7% |
| Ordinance number | 174 / 174 | 100.0% |
| Series header | 132 / 174 | 75.9% |
| Approval date | 156 / 174 | 89.7% |

Ordinance number source: filename 174/174, filename and header agree on 83. Citation-style references rejected before they could hijack the signal: **0**.

> **Parser health warning.** Enactment-date coverage is 28.7%. An enactment clause appears in virtually every enacted ordinance, so a low rate here is a parsing failure, not a corpus property. Run `--debug-headers` on this folder and tune `ENACT_ANCHOR_RE` / `DATE_PATTERNS` against the real layout before treating any temporal verdict in this report as final.

## 4. Corpus text characteristics

| Metric | Value |
|---|---|
| Mean characters | 17,018 |
| Median characters | 12,790 |
| Mean words | 2,751 |
| Shortest document | 3,108 chars |
| Longest document | 186,351 chars |
| Mean pages | 11.8 |
| Mean characters per page | 1,383 |
| Suspected incomplete (<300 chars) | 0 files |
| Low text density (<100 chars/page) | 0 files |

## 5. Temporal discrepancies and misfiled files

No confidently misfiled or out-of-scope ordinances detected.

### Flagged for manual review (not actioned)

| Filename | Resolved | Conf. | Agree | Reason |
|---|---|---|---|---|
| `Ordinance No. 046-16.pdf` | 1991 | 0.28 | 1/3 | enacted 1991 vs approved 2016 |
| `Ordinance No. 0474-16.pdf` | 1991 | 0.28 | 1/3 | enacted 1991 vs approved 2016 |
| `Ordinance No. 0475-16.pdf` | 1991 | 0.17 | 1/4 | enacted 1991 vs approved 2016; series 2015 vs ord-no 2016 |
| `Ordinance No. 050-16.pdf` | 1991 | 0.28 | 1/3 | enacted 1991 vs approved 2016 |
| `Ordinance No. 0520-16.pdf` | 1991 | 0.23 | 1/3 | mismatch below confidence bar |
| `Ordinance No. 097-16.pdf` | 1991 | 0.28 | 1/3 | enacted 1991 vs approved 2016 |
