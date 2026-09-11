# Convenience targets. Run `make help` for the list.
PY ?= python
SRC = src/ordinance_eda_pipeline.py
WINDOW = --window-min 2016 --window-max 2024

.PHONY: help install app fixtures test debug audit-2016 audit dry-run curate adjudicate vault freeze clean-cache

help:
	@grep -E '^[a-z-]+:.*?##' $(MAKEFILE_LIST) | sed 's/:.*##/\t/' | column -t -s "$$(printf '\t')"

install:  ## Install Python dependencies
	$(PY) -m pip install -r requirements.txt

app:  ## Launch the local Ordinance Lab dashboard
	$(PY) -m streamlit run app/main.py

fixtures:  ## Generate synthetic test PDFs into tests/fixtures/
	$(PY) tests/make_fixtures.py

test: fixtures  ## Run the pipeline self-test against the fixtures
	$(PY) tests/test_pipeline.py

debug:  ## Inspect real headers before trusting any number (Step 1)
	$(PY) $(SRC) --year 2016 --debug-headers 10 > outputs/reports/header_debug_2016.txt
	@echo "Wrote outputs/reports/header_debug_2016.txt -- read it before continuing."

audit-2016:  ## Audit one year (Step 3)
	$(PY) $(SRC) --year 2016 $(WINDOW)

audit:  ## Audit every year folder (Step 4)
	$(PY) $(SRC) --all-years $(WINDOW)

adjudicate:  ## Emit one adjudication template per year (Step 5)
	$(PY) $(SRC) --all-years $(WINDOW) --emit-override-template

dry-run:  ## Show what curation would remove, touch nothing (Step 7)
	$(PY) $(SRC) --all-years $(WINDOW) --dry-run

curate:  ## Quarantine excluded documents (Step 7)
	$(PY) $(SRC) --all-years $(WINDOW) --remove-misfiled

vault:  ## Audit and export the Obsidian notes (Step 8)
	$(PY) $(SRC) --all-years $(WINDOW) --export-obsidian

freeze:  ## Snapshot the current run (Step 9)
	cp -r data/EDA outputs data/processed data/versions/frozen_$$(date +%Y%m%d)
	@echo "Snapshot written to data/versions/frozen_$$(date +%Y%m%d)"

clean-cache:  ## Delete the extracted-text cache (do this after editing a regex)
	rm -rf data/interim/text
