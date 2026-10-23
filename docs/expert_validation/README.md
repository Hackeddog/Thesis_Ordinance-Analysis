# Expert-validation revision package — EV-1.0

This package was prepared after reviewing the actual 56-page thesis in
`Downloads/CS_Undergraduate_Thesis_Template__Copy_-13.pdf`, especially Chapter 3,
PDF pages 41–43 (printed pages 36–38), Tables 5–6, the research questions, and
Chapter 2's legal-expert review discussion. It is not based only on a generic
questionnaire or the older 12-page RRL file.

## Deliverables

1. **`chapter3_revised.md`** — thesis-ready replacement for *Model Evaluation and Expert Validation*, retaining the five dimensions and the original below-3.00 review rule.
2. **`questionnaire.md`** — Sections A–E, sixteen rated statements, a consistent five-point agreement scale, separate NA, source-based accuracy questions, temporal questions, comments, and a final two-model comparison.
3. **`administration_and_scoring.md`** — prospective sampling, packet preparation, workload, Google Forms setup, item mapping, missingness, aggregation, agreement, and feedback procedures.
4. **`review_notes.md`** — source/page audit, changes and reasons, and exact alignment edits needed for the research question, objectives, tuning table, temporal wording, and outdated corpus/result references.
5. **`templates/`** — machine-readable item bank and blank registration/response/feedback tables. These contain no expert responses.

Editable DOCX, printable PDF, and browser-printable HTML versions of the four main
documents are generated in `artifacts/expert_validation/`. The original PDFs are
not overwritten. Integrate the replacement into the editable thesis source and
apply that manuscript's final typography, table numbering, and citation numbering.

## Key decisions

- Keep **Legal Coherence, Thematic Relevance, Label Appropriateness, Temporal Interpretation, and Overall Research Quality**. Limit the last dimension to the supplied outputs, not certification of the entire algorithm or thesis.
- Keep ratings **1 Strongly Disagree → 5 Strongly Agree**; provide **Not Applicable / Unable to Assess** separately. Neutral does not mean insufficient information.
- Preserve the existing **unrounded topic-dimension mean <3.00** review trigger as a study-defined action rule. Preserve the scoring-band boundaries while clarifying that the middle band is mixed/neutral, not automatic acceptance. No new empirical validation threshold is claimed.
- Propose **four topics per model and three examples per topic**, rather than asking reviewers to assess all 171 selected-run topics. Include random and difficult examples, not only high-ranked representatives.
- Review the frozen **Conservative / seed 42** outputs of both models. The four-configuration experiment is completed; expert recruitment, packet selection, data collection, and human validation are still proposed.
- Keep automated metrics and expert judgments separate. No invented technical accuracy score, expert score, agreement coefficient, or recruited participant.

## Before distribution

- Obtain the applicable institutional permissions and finish the participant-information/consent arrangements; fill researcher/supervisor contact and withdrawal/storage details.
- Confirm the proposed sampling and scoring protocol with the adviser, and check reviewer burden before formal collection.
- Generate and verify the eight source-linked packets and draft labels, maintaining equivalent materials for both systems. The questionnaire is ready as an instrument, but **the actual review packets have not been assembled by this documentation task**.
- Keep the system-code key and identifiable records in a restricted, non-public location. Blank templates can be version-controlled; completed personal data should not be published in the repository.
- Distribute the profile once, the topic form for each packet, and the final comparison once. No Google Form has been created or launched.

## Rebuild the editable and printable documents

From the repository root, using the existing mise-managed Python environment:

```powershell
.\.venv\Scripts\python.exe scripts/build_expert_validation_documents.py
```

The exporter uses only the Python standard library and the already-installed
PyMuPDF. It does not install packages or change the modeling environment. It
produces an export manifest with input/output hashes and the reviewed thesis
fingerprint. Rendering and schema checks verify document construction, **not
expert validity of the instrument**.

## Relationship to the completed tuning study

The revision does not alter model inputs, assignments, metric calculations, or
previously published tuning artifacts. Expert judgments will be an additional,
source-based interpretation of the selected output sample. If later feedback
changes labels, assignments, source handling, or temporal interpretations, those
changes will be versioned, with affected analyses rerun where necessary. Previous
ratings will not automatically validate revised outputs.
