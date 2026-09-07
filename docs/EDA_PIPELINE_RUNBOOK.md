# EDA pipeline runbook

How to run `src/ordinance_eda_pipeline.py` on the Davao City ordinance corpus,
from a clean checkout to a model-ready dataset.

**Read this first:** the loop that determines whether your numbers are
trustworthy is Steps 1 to 5. Steps 6 to 9 are mechanical once the parser is
honest. Do not skip Step 1.

If you are joining a project already in progress, read
[Appendix F](#appendix-f-working-as-a-team) before you run anything.

## Contents

- [Step 0. Back up and install](#step-0-back-up-and-install)
- [Step 1. Look at the documents before trusting any number](#step-1-look-at-the-documents-before-trusting-any-number)
- [Step 2. Tune the regexes against what you saw](#step-2-tune-the-regexes-against-what-you-saw)
- [Step 3. First real audit, one year](#step-3-first-real-audit-one-year)
- [Step 4. All nine years](#step-4-all-nine-years)
- [Step 5. Adjudicate the flags by hand](#step-5-adjudicate-the-flags-by-hand)
- [Step 6. Relocate the real misfilings](#step-6-relocate-the-real-misfilings-optional)
- [Step 7. Curate the corpus](#step-7-curate-the-corpus)
- [Step 8. Hand off to the model](#step-8-hand-off-to-the-model)
- [Step 9. Freeze the run](#step-9-freeze-the-run)
- [Appendix A. Full flag reference](#appendix-a-full-flag-reference)
- [Appendix B. Output files](#appendix-b-output-files)
- [Appendix C. How the classification works](#appendix-c-how-the-classification-works)
- [Appendix D. Troubleshooting](#appendix-d-troubleshooting)
- [Appendix E. .gitignore](#appendix-e-gitignore)
- [Appendix F. Working as a team](#appendix-f-working-as-a-team)

## Step 0. Back up and install

Nothing the pipeline writes is versioned. Every run overwrites the previous
CSVs, reports and figures in place, so snapshot a baseline before you start.

```bash
cp -r data/EDA outputs data/raw _baseline_$(date +%Y%m%d)
pip install pymupdf pandas matplotlib pytesseract pillow
tesseract --version
```

`tesseract` is a system binary, not the Python wrapper. If it is missing, OCR
silently recovers nothing and every scanned ordinance lands in the
`unresolved` bucket. Install it, or run with `--no-ocr` and state the gap as a
limitation.

Required layout. The script derives every path from its own parent's parent, so
it must live in `src/`.

```
project/
  src/ordinance_eda_pipeline.py
  data/raw/2016/*.pdf
  data/raw/2017/*.pdf
  ...
```

Everything else (`data/EDA/`, `data/interim/`, `data/processed/`,
`outputs/reports/`, `outputs/figures/`) is created on demand.

**Fresh clone?** The PDFs are not in git. See
[Appendix F](#appendix-f-working-as-a-team) for how to obtain `data/raw/`.

## Step 1. Look at the documents before trusting any number

```bash
python src/ordinance_eda_pipeline.py --year 2016 --debug-headers 10 \
  > outputs/reports/header_debug_2016.txt
```

This prints the header region and both date-anchor neighbourhoods for ten files,
then exits without writing any dataset. Read the file and check three things per
sample:

1. Does the header region contain the ordinance number and `Series of YYYY`?
2. Does the `ENACTED` anchor land on the real enactment clause, not on a
   whereas clause citing an amended ordinance?
3. Does the `APPROVED` anchor land on the mayor's signature block?

This is the step that separates a parser failure from a corpus finding. An
earlier pipeline version reported 3.9% enactment-date coverage and 18 misfiled
ordinances for 2016; both were regex bugs, not properties of the documents.

## Step 2. Tune the regexes against what you saw

Edit only the constants near the top of the file.

| Symptom in the debug dump | Constant to change |
|---|---|
| Header cut off before the series line | Raise `HEADER_CHARS` (default 1800) |
| Date sits far below its anchor | Raise `DATE_WINDOW` (default 400) |
| Enactment phrasing not matched | Add the verb to `ENACT_ANCHOR_RE` |
| A cited ordinance still wins the signal | Add the phrasing to `CITATION_CUE_RE` |
| Council-term inference is off | Re-anchor `COUNCIL_ANCHOR_ORDINAL` / `COUNCIL_ANCHOR_YEAR` |

Re-run Step 1 after each change until the anchors land correctly. Iterate here,
not later. A rule fixed at this stage corrects a whole class of files at once; a
manual override in Step 5 corrects exactly one.

On a team, one person owns this file. See
[Appendix F](#appendix-f-working-as-a-team).

## Step 3. First real audit, one year

```bash
python src/ordinance_eda_pipeline.py --year 2016 --window-min 2016 --window-max 2024
```

Open `outputs/reports/eda_report_2016.md` and go straight to section 3, signal
extraction completeness.

> **Gate: if enactment-date coverage is under 50%, stop and return to Step 2.**

The report prints a parser-health warning automatically when this happens. An
enactment clause appears in virtually every enacted ordinance, so a low rate is
a parsing failure. Do not proceed on a broken primary signal; everything
downstream inherits the error.

Also sanity-check section 1: the classification categories are mutually
exclusive, so the percentages must sum to 100%.

## Step 4. All nine years

```bash
python src/ordinance_eda_pipeline.py --all-years --window-min 2016 --window-max 2024
```

Read `outputs/reports/eda_report_CORPUS.md`, which crosstabs classification
against folder year. One year with a wildly different flag rate usually means a
different scanning batch or a different source repository, not a different
legislature. Investigate before you accept it.

## Step 5. Adjudicate the flags by hand

Generate a pre-filled adjudication sheet, **one per folder year**:

```bash
python src/ordinance_eda_pipeline.py --all-years --emit-override-template
```

```
data/manual_year_overrides_TEMPLATE_2016.csv
data/manual_year_overrides_TEMPLATE_2017.csv
...
```

Each file lists only that year's flagged documents, pre-filled with the
pipeline's guess and the signals behind it:

```csv
filename,correct_year,verified_by,evidence,note
Ordinance No. 0230-10.pdf,2010,,,"pipeline said out_of_scope, folder 2016, conf 1.0, signals E/O/S/A = 2010/2010/2010/2010"
```

For each row, open the PDF and look at the header. Then:

- **Pipeline was wrong:** correct `correct_year`, fill in `verified_by` and
  `evidence` (e.g. "header reads 18th City Council, Series of 2016").
- **Pipeline was right:** delete the row.

Rename the finished file to drop `_TEMPLATE`, then commit it:

```bash
mv data/manual_year_overrides_TEMPLATE_2016.csv data/manual_year_overrides_2016.csv
git add data/manual_year_overrides_2016.csv
python src/ordinance_eda_pipeline.py --all-years
```

### Where overrides are read from

Per folder year, later wins on any filename listed twice:

1. `data/manual_year_overrides.csv` (shared, optional, corpus-wide decisions)
2. `data/manual_year_overrides_{year}.csv` (per year, the normal case)
3. `--overrides FILE`, or every matching `*{year}*.csv` inside `--overrides DIR`

A disagreement between two files is logged, not resolved silently:

```
WARNING  Override conflict for Ordinance No. 0230-10.pdf: 2010 then 2016; using 2016 (manual_year_overrides_2016.csv)
```

The per-year split exists so several people can adjudicate different years in
parallel without ever editing the same file, which means git never has to merge
two reviewers' judgements.

### What an override does

`resolution_source` becomes `manual_override`, `confidence_score` becomes 1.00,
the status is recomputed, and the file is protected from quarantine in Step 7.
The one thing an override cannot protect against is itself: if you declare a
year outside the study window, the file still leaves the corpus, because that is
the exclusion you just confirmed.

Repeat Steps 4 and 5 until the remaining flags are all genuine.

**Do not fix a false positive by editing the output CSV or moving the file
yourself.** Both are regenerated on the next run and your correction is lost.

Ten overrides is normal curation. A hundred means the parser still needs work,
so go back to Step 2.

## Step 6. Relocate the real misfilings (optional)

```bash
python src/ordinance_eda_pipeline.py --all-years --fix-misfiled
```

Copies confidently misfiled PDFs into `data/raw/{resolved_year}/` after a
confirmation prompt. Copy is the default; `--move` opts into the destructive
version. Relocation requires `confidence_score >= 0.60` plus at least two
agreeing signals, refuses to overwrite an existing destination, and lists
everything below the bar as held for manual review.

**This step is optional.** If you feed `corpus_year` to your model (Step 8), the
folder layout no longer matters and you can skip it entirely. On a team it is
usually better skipped: moving files between year folders reshuffles the corpus
under whoever else is mid-adjudication.

## Step 7. Curate the corpus

Always dry-run first.

```bash
python src/ordinance_eda_pipeline.py --all-years --dry-run
python src/ordinance_eda_pipeline.py --all-years --remove-misfiled
```

Removed files are **moved** to `data/quarantine/<reason>/<year>/`, never
deleted, and every move is appended to `data/EDA/quarantine_manifest.csv`.
Undo the whole operation with:

```bash
python src/ordinance_eda_pipeline.py --restore
```

Default removal categories are `out_of_scope`, `duplicate` and `sparse`.
Override with `--remove-categories`.

| Category | Removes | Default |
|---|---|---|
| `out_of_scope` | Resolved year outside the study window | yes |
| `duplicate` | Byte-identical files and repeated ordinance numbers, keeping one representative per group | yes |
| `sparse` | Under 300 extracted characters: failed OCR or a broken PDF | yes |
| `misfiled` | In-window but in the wrong folder | no, re-dated instead |
| `review` | Mismatch below the confidence bar | no |
| `unresolved` | No year signal recovered | no |

**Why `misfiled` is not removed by default.** A misfiled but in-window
ordinance is good data in the wrong drawer. Deleting a 2017 ordinance because it
sat in `data/raw/2016/` discards a valid document and biases the 2017 time slice
downward, which is a direct hit to what a dynamic topic model measures. Those
documents are re-dated via `corpus_year` instead.

Curation is a whole-corpus operation. Run it once, after every year has been
adjudicated, not per person.

`--purge` deletes instead of quarantining and requires typing `DELETE` in
capitals. Avoid it. A manifest turns "N documents excluded" into a claim your
panel can verify.

## Step 8. Hand off to the model

`data/processed/corpus_index.csv` is the input to the topic-modelling stage.

```python
import pandas as pd

index = pd.read_csv("data/processed/corpus_index.csv")
corpus = index[index["included_in_corpus"]]
# Use corpus_year as the time bucket, NOT folder_year.
timestamps = corpus["corpus_year"]
```

`corpus_year` carries the resolved year for trusted resolutions and the folder
year otherwise, so a misfiled ordinance is re-dated rather than lost. Using
`folder_year` here silently reintroduces every misfiling you just detected.

## Step 9. Freeze the run

```bash
cp -r data/EDA outputs data/processed _frozen_$(date +%Y%m%d)
git add data/manual_year_overrides*.csv data/EDA/quarantine_manifest.csv \
        src/ordinance_eda_pipeline.py outputs/reports/
git commit -m "EDA run $(date +%Y-%m-%d): parser tuned, N overrides, M excluded"
```

Snapshot before any further change, or you lose the before-and-after comparison
the methodology chapter needs. The override files and the manifest are the audit
trail: which automated verdicts a human overruled, and what left the corpus.

## Appendix A. Full flag reference

### Scope

| Flag | Effect |
|---|---|
| `--year Y [Y ...]` | Process specific folder year(s) |
| `--all-years` | Process every numeric year folder under `data/raw/` |
| `--window-min Y` / `--window-max Y` | Study window bounds (default 2016-2024) |

### Extraction

| Flag | Effect |
|---|---|
| `--no-ocr` | Disable the per-page OCR fallback |
| `--no-cache` | Ignore cached extracted text and re-parse every PDF |
| `--debug-headers N` | Print headers and date anchors for N files, then exit |

### Relocation

| Flag | Effect |
|---|---|
| `--fix-misfiled` | Copy confidently misfiled PDFs to their resolved-year folder |
| `--move` | With `--fix-misfiled`, move instead of copy |
| `--min-confidence F` | Confidence bar for relocation (default 0.60) |

### Curation

| Flag | Effect |
|---|---|
| `--remove-misfiled` | Quarantine the flagged categories |
| `--remove-categories CAT [CAT ...]` | Choose which categories to act on |
| `--dry-run` | Print the removal plan and touch nothing |
| `--purge` | Delete instead of quarantine; requires typing `DELETE` |
| `--restore` | Move every quarantined file back |

### Adjudication

| Flag | Effect |
|---|---|
| `--overrides PATH` | Extra overrides CSV, or a directory of them. The shared and per-year files are always read |
| `--emit-override-template` | Write one template per folder year, then exit |

### General

| Flag | Effect |
|---|---|
| `--yes` | Skip confirmation prompts (scripted runs only) |

## Appendix B. Output files

### Per year folder processed

| Path | Contents |
|---|---|
| `data/EDA/ordinances_eda_summary_{year}.csv` | One row per PDF, 33 columns |
| `outputs/reports/eda_report_{year}.md` | Sections 1 to 5 audit report |
| `outputs/figures/temporal_distribution_{year}.png` | Status, resolved-year spread, signal coverage |

### Corpus rollup, once per run

| Path | Contents |
|---|---|
| `data/EDA/ordinances_eda_summary_ALL.csv` | Every row from every year folder |
| `outputs/reports/eda_report_CORPUS.md` | Folder-year by status crosstab, cross-year duplicates |
| `outputs/figures/temporal_distribution_CORPUS.png` | Stacked bar, status by folder year |
| `data/processed/corpus_index.csv` | The modelling manifest |

### Conditional

| Path | Written when |
|---|---|
| `data/interim/text/{year}/{stem}.json` | Always, unless `--no-cache`. Regenerable cache |
| `data/manual_year_overrides_TEMPLATE_{year}.csv` | `--emit-override-template`. One per year |
| `data/raw/{resolved_year}/*.pdf` | `--fix-misfiled` |
| `data/quarantine/<reason>/<year>/*.pdf` | `--remove-misfiled` |
| `data/EDA/quarantine_manifest.csv` | `--remove-misfiled`. Appended, never overwritten |

### Hand-authored inputs, never generated

| Path | Purpose |
|---|---|
| `data/manual_year_overrides_{year}.csv` | Per-year human verdicts. One owner each |
| `data/manual_year_overrides.csv` | Optional shared verdicts, lowest precedence |

`--debug-headers` writes nothing; redirect stdout if you want to keep it.

## Appendix C. How the classification works

### The four year signals

| Signal | Weight | Source |
|---|---|---|
| Enactment date | 0.45 | `ENACTED` / `ADOPTED` anchor plus a forward date scan |
| Ordinance number suffix | 0.25 | Filename first, bounded header region second |
| Series header | 0.20 | `Series of YYYY` in the header, skipping cited ordinances |
| Approval date | 0.10 | `APPROVED` scanned backwards from the end of the document |

### Confidence

```
confidence_score = (weight of agreeing signals) - 0.5 x (weight of disagreeing signals)
```

Clipped to [0, 1]. Four agreeing signals give 1.00; enactment alone gives 0.45;
a lone ordinance-number suffix gives 0.25. A single signal can never report
1.00, which is the point: an earlier version divided by the active weight and
handed 1.00 to every single-signal resolution.

A manual override sets confidence to 1.00 by definition.

### Status

Mutually exclusive, so report percentages sum to 100%.

| Status | Meaning |
|---|---|
| `valid` | Resolved year matches the folder year and sits in the study window |
| `misfiled` | In-window, wrong folder, corroborated above the 0.45 bar |
| `out_of_scope` | Resolved year outside the study window |
| `review` | Year mismatch that is not trusted yet |
| `unresolved` | No year signal recovered, or no extractable text |

A mismatch is only called `misfiled` when confidence clears 0.45 **and** either
two signals agree or the enactment date supports it. Everything weaker routes to
`review` rather than into the relocation or removal queue.

If you change `WEIGHTS`, `MISFILE_MIN_CONFIDENCE` or `RELOCATE_MIN_CONFIDENCE`,
update this appendix in the same commit. Otherwise the runbook starts lying
about the code.

## Appendix D. Troubleshooting

| Symptom | Cause and fix |
|---|---|
| `Raw directory does not exist` | Year folder missing, or a fresh clone with no corpus. Appendix F |
| Enactment coverage stuck near zero | Regex does not match the real layout. Step 1, then Step 2 |
| A regex change appears to do nothing | Stale text cache. Delete `data/interim/` or pass `--no-cache` |
| Everything lands in `unresolved` | `tesseract` binary missing, or the PDFs have no text layer |
| Correctly filed ordinance flagged as misfiled | A cited ordinance is winning a signal. Extend `CITATION_CUE_RE`, then override if the scan is genuinely unparseable |
| My overrides were ignored | Wrong filename in the CSV, or the file is not named `manual_year_overrides_{year}.csv`. Check the run log for `Loaded N manual year override(s)` |
| `Override conflict for ...` | The shared and per-year files disagree. Delete the stale row from the shared file |
| Peers see different flags for the same year | One of you has uncommitted override files, or different parser constants. Compare `git status` and `git log src/` |
| `Destination exists, skipped` | The file is already in the target folder. Harmless |
| Yesterday's report is gone | Outputs are overwritten every run. Step 0 and Step 9 exist for this |

## Appendix E. .gitignore

The nesting idiom matters. A pattern like `data/raw/*` excludes the directory
`data/raw/2016` itself, and git never descends into an excluded directory, so no
negation inside it can fire. The year folders then vanish on clone and the
pipeline finds nothing.

```gitignore
# Data: ignore contents, keep the folder structure
data/raw/**
!data/raw/**/
!data/raw/**/.gitkeep

data/processed/**
!data/processed/**/
!data/processed/**/.gitkeep

# Regenerable caches and curation side-effects
data/interim/
data/quarantine/

# EDA tables are regenerated every run; the audit trail is not
data/EDA/*
!data/EDA/.gitkeep
!data/EDA/quarantine_manifest.csv

# Hand-authored adjudications: always tracked
!data/manual_year_overrides.csv
!data/manual_year_overrides_[0-9][0-9][0-9][0-9].csv

# Regenerated templates: never tracked
data/manual_year_overrides_TEMPLATE_*.csv

# Frozen run snapshots
_baseline_*/
_frozen_*/

# Outputs: keep the reports, drop the figures
outputs/figures/**
!outputs/figures/**/
!outputs/figures/**/.gitkeep

# Python
__pycache__/
*.pyc
.venv/
venv/
env/

# Jupyter
.ipynb_checkpoints/

# OS / editor
.DS_Store
Thumbs.db
.vscode/settings.json

# Secrets / logs
.env
*.log
```

The four-digit glob keeps the real per-year files and excludes the templates
without relying on rule ordering.

Git cannot record an empty directory, so add one marker per folder:

```bash
for y in 2016 2017 2018 2019 2020 2021 2022 2023 2024; do
  mkdir -p data/raw/$y && touch data/raw/$y/.gitkeep
done
touch data/EDA/.gitkeep data/processed/.gitkeep outputs/figures/.gitkeep
```

Keep `outputs/reports/` tracked: the markdown files are small, and `git diff`
across runs shows exactly how the numbers moved after each parser change.

Never ignore `data/manual_year_overrides*.csv` or
`data/EDA/quarantine_manifest.csv`. Without them in version control, "N
documents excluded after review" is an unverifiable claim, and a dead laptop
destroys hours of adjudication that no re-run can reproduce.

If any of this was committed before the rules existed:

```bash
git rm -r --cached data/interim data/quarantine -q
git add -A
git commit -m "Fix gitignore: preserve raw year folders, untrack regenerable caches"
```

## Appendix F. Working as a team

### Getting the corpus

The PDFs are not in git, so a fresh clone has empty year folders. Pick one
distribution method and write it into the README:

| Method | Notes |
|---|---|
| Shared cloud folder | Simplest. Sync Drive/OneDrive into `data/raw/`. Likely already available through the university |
| Git LFS | Everything in one clone, but check the host's LFS quota first; free tiers are small |
| Zip plus checksum | Distribute once, publish the SHA-256 in the README. Crude but pins exactly which corpus version produced a result |

### Splitting the work by year

This is what the per-year override files are for.

| Artifact | Owner | Conflict risk |
|---|---|---|
| `data/manual_year_overrides_{year}.csv` | One reviewer per year | None, separate files |
| `src/ordinance_eda_pipeline.py` | One owner for the whole team | High, this is the file that genuinely conflicts |
| `outputs/reports/*.md` | Regenerated, commit from one machine | Medium, avoid parallel commits |
| Curation (Step 7) | Run once, by one person, after all years are adjudicated | High if run in parallel |

Two rules that matter more than the git mechanics:

**Agree the adjudication standard before anyone starts.** If reviewer A calls a
file misfiled on the strength of the series header while reviewer B calls the
same pattern unresolved, your nine-year series carries a reviewer artifact
instead of a temporal signal. Write down what counts as sufficient evidence, and
have two people adjudicate the same ten files early to check you agree.

**One person owns the parser.** Three people tuning `CITATION_CUE_RE` on
parallel branches will cost more time than the CSVs ever would. Route regex
changes through the owner, and have everyone `git pull` before a run so the
whole team is classifying with the same rules.

### Keeping runs comparable

A result is only reproducible if the parser constants and the override files
match. Before comparing two reports, confirm both were produced from the same
commit:

```bash
git log -1 --format=%h -- src/ordinance_eda_pipeline.py
```

Put that hash in the commit message when you freeze a run (Step 9).
