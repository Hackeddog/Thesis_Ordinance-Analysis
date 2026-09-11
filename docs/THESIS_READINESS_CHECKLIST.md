# Thesis-readiness checklist

This project is a document-ingestion, temporal-audit, and corpus-curation
pipeline. It should not be treated as a validated thesis-results pipeline
until the checks below are completed.

## Implemented safeguards

- [x] Raw temporal signals are separated from cleaned NLP text.
- [x] Per-page OCR fallback is available when PyMuPDF, Pillow, pytesseract,
      and the Tesseract binary are installed.
- [x] Extraction caches validate the source PDF hash, OCR setting, backend, and
      cache format before reuse.
- [x] Pipeline records have a minimum schema and confidence range validation.
- [x] Review and unresolved records are excluded from the modelling manifest by
      default.
- [x] Confidently resolved misfiled records use `corpus_year`, not `folder_year`.
- [x] `outputs/reports/run_manifest.json` records configuration, source hashes,
      software context, and the code revision.
- [x] Synthetic regression tests cover cache invalidation and corpus eligibility.

## Required before reporting thesis findings

### Corpus provenance

- [ ] Complete the provenance table in `README.md`.
- [ ] Record the source office or URL, collection date, study window, and
      acquisition method.
- [ ] Publish a corpus manifest or archive checksum for the exact PDF set.
- [ ] Preserve the run manifest with every frozen result.

### Temporal validation

- [ ] Create a manually verified gold sample stratified by year, extraction
      method, and parser status.
- [ ] Record reviewer identity, evidence, and adjudication decisions in the
      override CSVs.
- [ ] Report precision, recall, unresolved rate, and inter-rater agreement.
- [ ] Perform sensitivity analysis for confidence thresholds and signal weights.
- [ ] Investigate every low enactment-date coverage warning before proceeding.

### Text quality and preprocessing

- [ ] Quantify digital, hybrid, and OCR extraction rates.
- [ ] Inspect OCR quality on a representative sample and record the Tesseract
      version and language configuration.
- [ ] Report missing text, sparse documents, duplicates, and repeated boilerplate.
- [ ] Define and freeze tokenization, stopword, lemmatization/stemming, and
      phrase-handling rules before modelling.
- [ ] Keep the cleaned text and corpus index tied by stable file hashes.

### Topic modelling and temporal analysis

- [ ] Add a deterministic modelling-stage entry point after corpus validation.
- [ ] Fix random seeds and record model/library versions.
- [ ] Evaluate topic stability across seeds and preprocessing variants.
- [ ] Explain why `corpus_year` is the appropriate time index.
- [ ] Report sensitivity to excluded, unresolved, and manually adjudicated files.

## Reproducible run sequence

```bash
python tests/test_pipeline.py
python src/ordinance_eda_pipeline.py --all-years --debug-headers 10
python src/ordinance_eda_pipeline.py --all-years --emit-override-template
# Complete and review the override CSVs, then:
python src/ordinance_eda_pipeline.py --all-years --export-obsidian
```

Do not cite a run until its source PDFs, override files, commit revision, and
`outputs/reports/run_manifest.json` have been preserved together.
