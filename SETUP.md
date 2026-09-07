# Setup from zero

Getting this project from an empty folder to a first validated EDA run. Budget
about an hour, most of it waiting on installs.

Once setup is done, day-to-day operation lives in
[`docs/EDA_PIPELINE_RUNBOOK.md`](docs/EDA_PIPELINE_RUNBOOK.md). This file is
only for the first time.

## Contents

1. [What you need](#1-what-you-need)
2. [Get the project](#2-get-the-project)
3. [Create the virtual environment](#3-create-the-virtual-environment)
4. [Install Python dependencies](#4-install-python-dependencies)
5. [Install Tesseract](#5-install-tesseract-ocr-fallback)
6. [Verify the install before touching real data](#6-verify-the-install-before-touching-real-data)
7. [Put the corpus in place](#7-put-the-corpus-in-place)
8. [Start version control](#8-start-version-control)
9. [Open the Obsidian vault](#9-open-the-obsidian-vault)
10. [First real run](#10-first-real-run)
11. [If you are joining an existing project](#11-if-you-are-joining-an-existing-project)
12. [Folder reference](#12-folder-reference)

## 1. What you need

| Requirement | Version | Check with |
|---|---|---|
| Python | 3.10 or newer | `python --version` |
| Git | any recent | `git --version` |
| Tesseract OCR | 5.x | `tesseract --version` |
| Obsidian | any | optional, for the vault |

On Windows use PowerShell, not `cmd`. On macOS install Homebrew first if you do
not have it.

## 2. Get the project

If you were given this folder as an archive, unzip it and rename it to whatever
you like. If it is already a git repository, clone it instead.

```bash
cd ~/projects            # or wherever you keep work
# unzip ordinance-thesis.zip
cd ordinance-thesis
```

Confirm you are in the right place:

```bash
ls
# expect: data  docs  outputs  scripts  src  tests  Thesis_Obsidian  Makefile  README.md ...
```

Every path in this project is relative to this folder. Run all commands from
here, never from inside `src/`.

## 3. Create the virtual environment

A virtual environment keeps these dependencies out of your system Python.

macOS / Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Your prompt should now show `(.venv)`. You must re-activate it in every new
terminal session. If PowerShell refuses to run the activation script:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

## 4. Install Python dependencies

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

This installs PyMuPDF, pandas, matplotlib, pytesseract and Pillow. The topic
modelling libraries are commented out in `requirements.txt`; install them when
you reach that stage, not now, because they pull in PyTorch.

Verify:

```bash
python -c "import fitz, pandas, matplotlib, pytesseract; print('imports OK')"
```

## 5. Install Tesseract (OCR fallback)

`pytesseract` is only a wrapper. Without the Tesseract binary, scanned
ordinances yield no text and land in the `unresolved` bucket with no warning
that OCR was unavailable.

| Platform | Command |
|---|---|
| Windows | Download the installer from the UB Mannheim Tesseract page, then add its folder to `PATH` |
| macOS | `brew install tesseract` |
| Ubuntu / Debian | `sudo apt install tesseract-ocr` |

```bash
tesseract --version    # expect: tesseract 5.x
```

On Windows, if the command is not found after installing, either add
`C:\Program Files\Tesseract-OCR` to your `PATH` or set the binary explicitly
near the top of `src/ordinance_eda_pipeline.py`:

```python
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
```

If you cannot install it right now, carry on and pass `--no-ocr`, but record
that as a limitation: any scanned document will be excluded from the corpus.

## 6. Verify the install before touching real data

The project ships synthetic ordinance PDFs that reproduce every failure mode the
pipeline is designed to catch. Run the self-test:

```bash
python tests/test_pipeline.py
```

Expected tail:

```
7. End-to-end run over the fixtures
  [PASS] exit code: 0
  [PASS] produced data/EDA/ordinances_eda_summary_2016.csv
  ...
All checks passed.
```

33 checks cover suffix-year normalisation, the council-term anchor, text
cleaning, per-document year resolution, citation filtering, ISO date parsing,
and a full end-to-end run that writes every artifact including the Obsidian
notes.

**If anything fails, stop here.** A failing self-test on synthetic data means
the environment is wrong, and every number you produce afterwards will be
wrong too. The fixtures live in `tests/fixtures/` and are safe to delete.

Re-run this command after every regex change. It is the cheapest regression
test you have.

## 7. Put the corpus in place

The PDFs are not in version control. Copy them into the year folders:

```
data/raw/2016/Ordinance No. 0116-16.pdf
data/raw/2016/Ordinance No. 0118-16.pdf
data/raw/2017/...
```

Two things matter:

**Filenames carry a signal.** The pipeline reads the ordinance number from the
filename first, because in the source repository that is authoritative. Keep the
`Ordinance No. NNNN-YY.pdf` shape. Renaming files to `scan001.pdf` throws away a
signal worth 0.25 of the confidence score.

**One folder per year, named with four digits.** `--all-years` discovers year
folders by looking for purely numeric directory names.

Then record where the corpus came from, in `README.md`: the source URL, the
collection date, and the file count per year. Nine months from now you will need
this for the methodology chapter and you will not remember.

## 8. Start version control

```bash
git init
git add .
git commit -m "Initial project scaffold"
```

`.gitignore` is already configured. Confirm it is doing the right thing:

```bash
git status --short
```

You should see the scaffold, the scripts and the docs, but **no** PDFs, no
`data/interim/`, and no generated notes under `Thesis_Obsidian/Ordinances/`.

What is deliberately tracked, and why:

| Tracked | Reason |
|---|---|
| `src/`, `tests/`, `docs/` | The code and its documentation |
| `data/manual_year_overrides*.csv` | Human adjudications. Irreplaceable; no re-run reproduces them |
| `data/EDA/quarantine_manifest.csv` | The record of what left the corpus |
| `outputs/reports/*.md` | Small, and `git diff` shows how your numbers moved |
| `.gitkeep` files | Git cannot record an empty directory |

## 9. Open the Obsidian vault

In Obsidian choose **Open folder as vault** and select `Thesis_Obsidian/`, not
the project root. Install the **Dataview** community plugin; the generated index
notes contain live Dataview queries that will otherwise render as code blocks.

Keep your own writing in `Thesis_Obsidian/Analysis/`. Everything under
`Thesis_Obsidian/Ordinances/` is regenerated on every export and your edits
there will be destroyed.

## 10. First real run

Do not jump straight to `--all-years`. Inspect the documents first:

```bash
python src/ordinance_eda_pipeline.py --year 2016 --debug-headers 10 \
  > outputs/reports/header_debug_2016.txt
```

Read that file. Then follow
[`docs/EDA_PIPELINE_RUNBOOK.md`](docs/EDA_PIPELINE_RUNBOOK.md) from Step 1.

Shortcuts, if you have `make`:

```bash
make help          # list every target
make test          # the self-test from section 6
make debug         # header inspection
make audit-2016    # audit one year
make audit         # audit all years
make vault         # audit and export the Obsidian notes
```

The single most important habit: **do not report a number from a run whose
enactment-date coverage is below 50%.** The report prints a warning when that
happens. An enactment clause exists in essentially every enacted ordinance, so a
low rate means the parser is broken, not the corpus.

## 11. If you are joining an existing project

```bash
git clone <repo-url>
cd ordinance-thesis
python3 -m venv .venv && source .venv/bin/activate
python -m pip install -r requirements.txt
python tests/test_pipeline.py
```

Then obtain `data/raw/` from whoever holds it, as described in that project's
README, and read Appendix F of the runbook before you adjudicate anything. In
short: one reviewer per year, one owner for the parser file, and agree the
adjudication standard before you start.

## 12. Folder reference

```
ordinance-thesis/
  src/
    ordinance_eda_pipeline.py     The pipeline. One owner on a team
  tests/
    make_fixtures.py              Generates synthetic ordinance PDFs
    test_pipeline.py              33-check self-test
  docs/
    EDA_PIPELINE_RUNBOOK.md       Day-to-day operating manual
  data/
    raw/{2016..2024}/             Source PDFs. Not in git
    interim/                      Extracted-text cache. Delete freely
    processed/                    corpus_index.csv and clean_text/
    EDA/                          Summary CSVs and the quarantine manifest
    quarantine/                   Excluded documents. Reversible
    versions/                     Your frozen run snapshots
    manual_year_overrides_{year}.csv   Human adjudications. Tracked
  outputs/
    reports/                      Markdown audit reports. Tracked
    figures/                      PNG figures. Not in git
  Thesis_Obsidian/
    Ordinances/                   GENERATED. Overwritten on every export
    Analysis/                     Your notes. Safe
  Makefile                        Shortcuts for the runbook steps
  requirements.txt
  .gitignore
```

Directories the pipeline creates on demand do not need to exist in advance, but
the `.gitkeep` files keep the structure alive through a clone.
