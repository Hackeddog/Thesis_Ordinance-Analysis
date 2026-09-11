# Obsidian, the model, and the website

## Current architecture

The project has one source of truth and two projections:

```text
data/raw/<year>/*.pdf
        |
        v
src/ordinance_eda_pipeline.py
        |
        +--> data/processed/corpus_index.csv  --> modelling input
        +--> data/processed/clean_text/       --> document text
        +--> Thesis_Obsidian/Ordinances/      --> Obsidian browsing layer
        +--> outputs/reports/                 --> audit evidence
```

Obsidian is currently a readable research layer, not the modelling database.
This prevents hand-edited notes from silently changing the corpus used in the
thesis.

## Sync from the website

The browser website now has **Refresh Obsidian notes** enabled by default. When
an audit runs, it passes `--export-obsidian` to the existing Python pipeline.
After uploading a PDF, the website runs a full audit and refreshes the generated
notes automatically.

The generated notes are stored in:

```text
Thesis_Obsidian/Ordinances/<corpus_year>/
```

Keep researcher-authored notes in `Thesis_Obsidian/Analysis/`; generated notes
may be rewritten on every audit.

## Feed the model

The model should read the modelling manifest, not arbitrary Obsidian markdown:

```python
import pandas as pd

index = pd.read_csv("data/processed/corpus_index.csv")
corpus = index[index["included_in_corpus"]].copy()
texts = [
    open(path, encoding="utf-8").read()
    for path in corpus["clean_text_path"]
]
timestamps = corpus["corpus_year"].astype(int).tolist()
```

The model stage should then write its outputs to a separate location such as:

```text
outputs/model/
Thesis_Obsidian/Analysis/Topic Model Results.md
```

Recommended model metadata to preserve:

- model and library versions
- random seed
- preprocessing configuration
- corpus-index hash or run-manifest path
- topic count/settings
- topic stability results

## Showing model results in the website

The next website extension can add a model-results API route that reads
`outputs/model/` and a new **Topics** page. The website should display model
outputs and links to Obsidian, while the Python model stage remains responsible
for computation and reproducibility.

For direct Obsidian links, use an `obsidian://open` URI only on the same machine
where Obsidian is installed. A normal browser cannot safely open arbitrary local
files by path.
