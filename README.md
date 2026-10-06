# Temporal Analysis of Davao City Ordinances

Legal NLP pipeline for exploratory data analysis, temporal validation and corpus
curation over Davao City municipal ordinances, feeding a BERTopic-based dynamic
topic model.

## New: two-model pilot and presentation

See [the comparison runbook](docs/TWO_MODEL_COMPARISON.md) for the lexical vs
Legal-BERT pipelines, reproducible parameter trials, VS Code tasks and GitHub Actions.
The [initial-results presentation](artifacts/pilot/Ordinance_Two_Model_Initial_Results.pptx)
and [PNG evidence](artifacts/pilot/figures/) report a shared 200-section exploratory
sample across **2016–2025**, not a validated full-corpus result. Source OCR is mostly
unverified; no expert scores or final model winner are claimed.

## Start here

| You want to | Read |
|---|---|
| Set the project up from scratch | [`SETUP.md`](SETUP.md) |
| Run the pipeline day to day | [`docs/EDA_PIPELINE_RUNBOOK.md`](docs/EDA_PIPELINE_RUNBOOK.md) |
| Understand the classification logic | Appendix C of the runbook |
| Work alongside teammates | Appendix F of the runbook |

## Quick start

```bash
mise install
mise exec -- python -m venv .venv && source .venv/bin/activate
python -m pip install -r requirements.txt
python tests/test_pipeline.py                                    # verify the install
python src/ordinance_eda_pipeline.py --year 2016 --debug-headers 10   # inspect first
python src/ordinance_eda_pipeline.py --all-years --export-obsidian    # then audit
```

## What the pipeline does

1. Extracts text from each ordinance PDF, with per-page OCR fallback
2. Reads four independent year signals: enactment date, ordinance number
   suffix, series header, mayoral approval date
3. Resolves a consensus year with a confidence score reflecting corroboration
4. Classifies each document as valid, misfiled, out of scope, review or
   unresolved, relative to the folder it was filed in
5. Cleans the text and extracts bibliographic metadata
6. Routes flagged documents to per-year human adjudication sheets
7. Curates the corpus, quarantining rather than deleting
8. Emits summary CSVs, Markdown reports, figures, a modelling manifest, and an
   Obsidian vault of one note per ordinance

## Corpus provenance

Fill this in when you place the PDFs. It is required for the methodology
chapter and you will not remember it later.

| Field | Value |
|---|---|
| Source | `TODO: URL or office` |
| Collected on | `TODO: date` |
| Study window | 2016 to 2025 (newer milestone; some legacy EDA defaults end in 2024) |
| Documents per year | `TODO: 2016: n, 2017: n, ...` |
| Corpus distributed via | `TODO: shared drive path, LFS, or zip + SHA-256` |

## Two rules that protect the results

**Never report a number from a run whose enactment-date coverage is below 50%.**
The report prints a parser-health warning when this happens. An enactment clause
appears in essentially every enacted ordinance, so a low recovery rate is a
parser failure, not a property of the corpus. An earlier version of this
pipeline reported 3.9% coverage and 18 misfiled ordinances for 2016; both were
regex bugs.

**Use `corpus_year`, not `folder_year`, as the time index.** A misfiled but
in-window ordinance is re-dated rather than discarded. Grouping by the directory
it happened to sit in reintroduces every misfiling the pipeline just detected.

## Repository conventions

- Legacy EDA outputs are overwritten on every run; new model experiments refuse to overwrite existing outputs. Snapshot to `data/versions/` before any
  change you might want to compare against
- `data/interim/` is a cache. Delete it after editing a regex, or the pipeline
  reads stale text and your fix appears to do nothing
- `Thesis_Obsidian/Ordinances/` is generated. Keep your own notes in
  `Thesis_Obsidian/Analysis/`
- Adjudication files (`data/manual_year_overrides_*.csv`) and the quarantine
  manifest are tracked in git. They are the audit trail and no re-run can
  reproduce them

## Citation

`TODO: thesis title, authors, institution, year`
