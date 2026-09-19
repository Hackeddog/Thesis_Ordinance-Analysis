# Legal NLP EDA & Temporal Audit Report: 2024
*Generated automatically by `src/ordinance_eda_pipeline.py`*

Study window: 2016-2025 | confidence bar for misfiling: 0.45 | for relocation: 0.60

## 1. Executive summary and file inventory

Categories below are mutually exclusive, so the percentages sum to 100%.

| Classification | Count | Percentage |
|---|---|---|
| **Total documents scanned** | 312 | 100.0% |
| Temporally valid (matches folder) | 308 | 98.7% |
| Misfiled (in-window, wrong folder) | 0 | 0.0% |
| Out-of-scope year | 0 | 0.0% |
| Flagged for manual review | 3 | 1.0% |
| Unresolved (no year signal) | 1 | 0.3% |

| Extraction | Count | Percentage |
|---|---|---|
| Digital | 311 | 99.7% |
| Hybrid | 1 | 0.3% |
| OCR | 0 | 0.0% |
| Pages OCR'd in total | 1 | - |

Mean consensus confidence: **0.83** (median 1.00). Documents resolved on a single signal: 13 (4.2%).

## 2. Duplicate analysis

- Byte-identical files (SHA-256): **13** group(s) covering 26 file(s)
- Repeated ordinance numbers: **13** group(s) covering 26 file(s)
- Files with no parseable ordinance number: **1**

| Ordinance No. | Files | Resolved years |
|---|---|---|
| `0499-24` | `Ordinance No. 0499-24 (1).pdf`, `Ordinance No. 0499-24 - Copy (1).pdf` | 2024.0 |
| `0679-24` | `Ordinance No. 0679-24 QRF Gen. Luna, Quezon (1).pdf`, `Ordinance No. 0679-24 QRF Gen. Luna, Quezon - Copy (1).pdf` | 2024.0 |
| `0680-24` | `Ordinance No. 0680-24 QRF Calaca City, Batangas (1).pdf`, `Ordinance No. 0680-24 QRF Calaca City, Batangas - Copy (1).pdf` | 2024.0 |
| `0681-24` | `Ordinance No. 0681-24 QRF Naga City (1).pdf`, `Ordinance No. 0681-24 QRF Naga City - Copy (1).pdf` | 2024.0 |
| `0682-24` | `Ordinance No. 0682-24 QRF Calbayog City, Samar (1).pdf`, `Ordinance No. 0682-24 QRF Calbayog City, Samar - Copy (1).pdf` | 2024.0 |
| `0683-24` | `Ordinance No. 0683-24 QRF Calamba, Laguna (1).pdf`, `Ordinance No. 0683-24 QRF Calamba, Laguna - Copy (1).pdf` | 2024.0 |
| `0684-24` | `Ordinance No. 0684-24 QRF Sto. Tomas, Batangas (1).pdf`, `Ordinance No. 0684-24 QRF Sto. Tomas, Batangas - Copy.pdf` | 2024.0 |
| `0685-24` | `Ordinance No. 0685-24 QRF San Pedro, Laguna - Copy.pdf`, `Ordinance No. 0685-24 QRF San Pedro, Laguna.pdf` | 2024.0 |
| `0686-24` | `Ordinance No. 0686-24 QRF Dagupan, Pangasinan (1).pdf`, `Ordinance No. 0686-24 QRF Dagupan, Pangasinan - Copy (1).pdf` | 2024.0 |
| `0687-24` | `Ordinance No. 0687-24 QRF Tanauan, Batangas (1).pdf`, `Ordinance No. 0687-24 QRF Tanauan, Batangas - Copy (1).pdf` | 2024.0 |
| `0688-24` | `Ordinance No. 0688-24 QRF Batangas, Batangas (1).pdf`, `Ordinance No. 0688-24 QRF Batangas, Batangas - Copy (1).pdf` | 2024.0 |
| `0689-24` | `Ordinance No. 0689-24 QRF Biñan, Laguna (1).pdf`, `Ordinance No. 0689-24 QRF Biñan, Laguna - Copy (1).pdf` | 2024.0 |
| `0690-24` | `Ordinance No. 0690-24 QRF Province of Batangas (1).pdf`, `Ordinance No. 0690-24 QRF Province of Batangas - Copy (1).pdf` | 2024.0 |

## 3. Signal extraction completeness

| Component signal | Extracted | Coverage |
|---|---|---|
| Enactment date | 240 / 312 | 76.9% |
| Ordinance number | 311 / 312 | 99.7% |
| Series header | 289 / 312 | 92.6% |
| Approval date | 248 / 312 | 79.5% |

Ordinance number source: filename 309/312, filename and header agree on 52. Citation-style references rejected before they could hijack the signal: **1**.

## 4. Corpus text characteristics

| Metric | Value |
|---|---|
| Mean characters | 6,782 |
| Median characters | 5,201 |
| Mean words | 1,098 |
| Shortest document | 2,704 chars |
| Longest document | 66,665 chars |
| Mean pages | 4.1 |
| Mean characters per page | 1,677 |
| Suspected incomplete (<300 chars) | 0 files |
| Low text density (<100 chars/page) | 0 files |

## 5. Temporal discrepancies and misfiled files

No confidently misfiled or out-of-scope ordinances detected.

### Flagged for manual review (not actioned)

| Filename | Resolved | Conf. | Agree | Reason |
|---|---|---|---|---|
| `Ordinance No. 0636-24 Relief on Surcharge and Interest (1).pdf` | 2021 | 0.23 | 1/3 | mismatch below confidence bar |
| `Ordinance No. 0657-24002 (1).pdf` | - | 0.00 | 0/0 | no year signal recovered |
| `Ordinance No. 0700-24 Granting Insular Oil Corp. (1).pdf` | 1991 | 0.23 | 1/3 | mismatch below confidence bar |
| `Ordinance No. 0724-24 (1).pdf` | 1991 | 0.17 | 1/4 | enacted 1991 vs approved 2025 |
