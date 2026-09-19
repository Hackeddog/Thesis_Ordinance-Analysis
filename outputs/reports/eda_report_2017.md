# Legal NLP EDA & Temporal Audit Report: 2017
*Generated automatically by `src/ordinance_eda_pipeline.py`*

Study window: 2016-2025 | confidence bar for misfiling: 0.45 | for relocation: 0.60

## 1. Executive summary and file inventory

Categories below are mutually exclusive, so the percentages sum to 100%.

| Classification | Count | Percentage |
|---|---|---|
| **Total documents scanned** | 216 | 100.0% |
| Temporally valid (matches folder) | 193 | 89.4% |
| Misfiled (in-window, wrong folder) | 0 | 0.0% |
| Out-of-scope year | 0 | 0.0% |
| Flagged for manual review | 23 | 10.6% |
| Unresolved (no year signal) | 0 | 0.0% |

| Extraction | Count | Percentage |
|---|---|---|
| Digital | 209 | 96.8% |
| Hybrid | 7 | 3.2% |
| OCR | 0 | 0.0% |
| Pages OCR'd in total | 7 | - |

Mean consensus confidence: **0.42** (median 0.35). Documents resolved on a single signal: 44 (20.4%).

## 2. Duplicate analysis

- Byte-identical files (SHA-256): **0** group(s) covering 0 file(s)
- Repeated ordinance numbers: **0** group(s) covering 0 file(s)
- Files with no parseable ordinance number: **0**

## 3. Signal extraction completeness

| Component signal | Extracted | Coverage |
|---|---|---|
| Enactment date | 43 / 216 | 19.9% |
| Ordinance number | 216 / 216 | 100.0% |
| Series header | 109 / 216 | 50.5% |
| Approval date | 195 / 216 | 90.3% |

Ordinance number source: filename 216/216, filename and header agree on 122. Citation-style references rejected before they could hijack the signal: **2**.

> **Parser health warning.** Enactment-date coverage is 19.9%. An enactment clause appears in virtually every enacted ordinance, so a low rate here is a parsing failure, not a corpus property. Run `--debug-headers` on this folder and tune `ENACT_ANCHOR_RE` / `DATE_PATTERNS` against the real layout before treating any temporal verdict in this report as final.

## 4. Corpus text characteristics

| Metric | Value |
|---|---|
| Mean characters | 21,449 |
| Median characters | 14,783 |
| Mean words | 3,467 |
| Shortest document | 3,460 chars |
| Longest document | 607,712 chars |
| Mean pages | 14.4 |
| Mean characters per page | 1,346 |
| Suspected incomplete (<300 chars) | 0 files |
| Low text density (<100 chars/page) | 0 files |

## 5. Temporal discrepancies and misfiled files

No confidently misfiled or out-of-scope ordinances detected.

### Flagged for manual review (not actioned)

| Filename | Resolved | Conf. | Agree | Reason |
|---|---|---|---|---|
| `Ordinance No. 0152-17.pdf` | 1991 | 0.28 | 1/3 | enacted 1991 vs approved 2017 |
| `Ordinance No. 0157-17.pdf` | 1991 | 0.28 | 1/3 | enacted 1991 vs approved 2017 |
| `Ordinance No. 0166-17.pdf` | 1991 | 0.28 | 1/3 | enacted 1991 vs approved 2017 |
| `Ordinance No. 0170-17.pdf` | 2018 | 0.18 | 2/3 | series 2018 vs ord-no 2017 |
| `Ordinance No. 0177-14.pdf` | 2014 | 0.25 | 1/1 | mismatch below confidence bar |
| `Ordinance No. 0212-17.pdf` | 1991 | 0.28 | 1/3 | enacted 1991 vs approved 2017 |
| `Ordinance No. 0223-17.pdf` | 1991 | 0.28 | 1/3 | enacted 1991 vs approved 2010 |
| `Ordinance No. 0249-17.pdf` | 2008 | 0.17 | 1/4 | enacted 2008 vs approved 2017; series 2018 vs ord-no 2017 |
| `Ordinance No. 0262-17.pdf` | 2018 | 0.18 | 2/3 | series 2018 vs ord-no 2017 |
| `Ordinance No. 0319-17.pdf` | 2018 | 0.18 | 2/3 | series 2018 vs ord-no 2017 |
| `Ordinance No. 0320-17.pdf` | 2018 | 0.18 | 2/3 | series 2018 vs ord-no 2017 |
| `Ordinance No. 0326-17.pdf` | 2018 | 0.18 | 2/3 | series 2018 vs ord-no 2017 |
| `Ordinance No. 0327-17.pdf` | 2018 | 0.18 | 2/3 | series 2018 vs ord-no 2017 |
| `Ordinance No. 0328-17.pdf` | 2018 | 0.18 | 2/3 | series 2018 vs ord-no 2017 |
| `Ordinance No. 0329-17.pdf` | 2018 | 0.18 | 2/3 | series 2018 vs ord-no 2017 |
| `Ordinance No. 0333-17.pdf` | 2018 | 0.18 | 2/3 | series 2018 vs ord-no 2017 |
| `Ordinance No. 0361-17.pdf` | 2018 | 0.18 | 2/3 | series 2018 vs ord-no 2017 |
| `Ordinance No. 0369-17.pdf` | 2018 | 0.18 | 2/3 | series 2018 vs ord-no 2017 |
| `Ordinance No. 0370-17.pdf` | 2018 | 0.18 | 2/3 | series 2018 vs ord-no 2017 |
| `Ordinance No. 0371-17.pdf` | 2018 | 0.43 | 2/3 | mismatch below confidence bar |
| `Ordinance No. 0375-17.pdf` | 2018 | 0.18 | 2/3 | series 2018 vs ord-no 2017 |
| `Ordinance No. 0376-17.pdf` | 2018 | 0.18 | 2/3 | series 2018 vs ord-no 2017 |
| `Ordinance No. 0380-17.pdf` | 2018 | 0.18 | 2/3 | series 2018 vs ord-no 2017 |
