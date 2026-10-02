# Legal NLP EDA & Temporal Audit Report: 2019
*Generated automatically by `src/ordinance_eda_pipeline.py`*

Study window: 2016-2025 | confidence bar for misfiling: 0.45 | for relocation: 0.60

## 1. Executive summary and file inventory

Categories below are mutually exclusive, so the percentages sum to 100%.

| Classification | Count | Percentage |
|---|---|---|
| **Total documents scanned** | 266 | 100.0% |
| Temporally valid (matches folder) | 264 | 99.2% |
| Misfiled (in-window, wrong folder) | 0 | 0.0% |
| Out-of-scope year | 0 | 0.0% |
| Flagged for manual review | 2 | 0.8% |
| Unresolved (no year signal) | 0 | 0.0% |

| Extraction | Count | Percentage |
|---|---|---|
| Digital | 251 | 94.4% |
| Hybrid | 14 | 5.3% |
| OCR | 1 | 0.4% |
| Pages OCR'd in total | 19 | - |

Mean consensus confidence: **0.64** (median 0.55). Documents resolved on a single signal: 10 (3.8%).

## 2. Duplicate analysis

- Byte-identical files (SHA-256): **0** group(s) covering 0 file(s)
- Repeated ordinance numbers: **0** group(s) covering 0 file(s)
- Files with no parseable ordinance number: **9**

## 3. Signal extraction completeness

| Component signal | Extracted | Coverage |
|---|---|---|
| Enactment date | 122 / 266 | 45.9% |
| Ordinance number | 257 / 266 | 96.6% |
| Series header | 244 / 266 | 91.7% |
| Approval date | 258 / 266 | 97.0% |

Ordinance number source: filename 257/266, filename and header agree on 220. Citation-style references rejected before they could hijack the signal: **1**.

> **Parser health warning.** Enactment-date coverage is 45.9%. An enactment clause appears in virtually every enacted ordinance, so a low rate here is a parsing failure, not a corpus property. Run `--debug-headers` on this folder and tune `ENACT_ANCHOR_RE` / `DATE_PATTERNS` against the real layout before treating any temporal verdict in this report as final.

## 4. Corpus text characteristics

| Metric | Value |
|---|---|
| Mean characters | 16,221 |
| Median characters | 8,744 |
| Mean words | 2,579 |
| Shortest document | 3,560 chars |
| Longest document | 444,640 chars |
| Mean pages | 10.9 |
| Mean characters per page | 1,388 |
| Suspected incomplete (<300 chars) | 0 files |
| Low text density (<100 chars/page) | 0 files |

## 5. Temporal discrepancies and misfiled files

No confidently misfiled or out-of-scope ordinances detected.

### Flagged for manual review (not actioned)

| Filename | Resolved | Conf. | Agree | Reason |
|---|---|---|---|---|
| `Davao City Forest Land Use Plan (2019-2023) (1).pdf` | 2018 | 0.40 | 1/2 | enacted 2018 vs approved 2004 |
| `Ordinance No. 0672-18.pdf` | 1991 | 0.17 | 1/4 | enacted 1991 vs approved 2019 |
