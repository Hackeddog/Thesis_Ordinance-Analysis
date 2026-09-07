# Thesis vault

Vault for the Davao City ordinance study. Open this folder (`Thesis_Obsidian/`)
as the vault root, not the project root.

## Required plugin

Install **Dataview** from Community Plugins. The generated index notes contain
live queries that render as plain code blocks without it.

## Folders

| Folder | Status |
|---|---|
| `Ordinances/` | **Generated.** Rewritten by every `--export-obsidian` run. Do not edit |
| `Analysis/` | Yours. Safe from the pipeline |

## Entry points

- [[_Corpus MOC]] once you have run an export
- [[00 Research log]] in Analysis

## Useful queries

Every flagged document across the corpus, weakest evidence first:

```dataview
TABLE folder_year, resolved_year, confidence_score, conflict_notes
FROM #ordinance
WHERE temporal_status != "valid"
SORT confidence_score ASC
```

Documents resolved on thin evidence, even where the folder agrees:

```dataview
TABLE ordinance_number, confidence_score, resolution_source
FROM #ordinance
WHERE confidence_score < 0.5
SORT confidence_score ASC
```

Amendment network:

```dataview
TABLE cited_ordinances, corpus_year
FROM #type/amendatory
SORT corpus_year ASC
```
