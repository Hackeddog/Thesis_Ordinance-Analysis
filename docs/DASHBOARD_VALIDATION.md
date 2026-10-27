# Fresh-run and dashboard validation

## Completed locally

- Full Python suite: **64 passed** (19 dependency/deprecation warnings).
- Bun data/export/static-server suite: **9 passed**, 107 assertions.
- Real Chromium suite using Bun-native CDP: passed.
- Automated axe WCAG 2 A/AA and WCAG 2.1 AA rules: no violations at **1440×1000**, **390×844**, and **768×844**.
- No document-wide horizontal overflow at phone/tablet widths; wide heatmaps scroll inside their own container.
- Model/year selectors, keyword search, category filtering, no-match state, pagination, topic selection, exact annual tables, keyboard activation/focus, and actual PDF download verified.
- GitHub-Pages-style subdirectory hosting verified on a local HTTP prefix proxy.
- HTTP failure for the real data file produces an explicit error, not placeholder results.
- No uncaught page JavaScript exceptions in the browser suite.
- Downloaded PDF bytes and all exported download/data SHA-256 checksums verified.

Screenshots and full local test logs are in ignored `test-results/dashboard/` and repository-root `*.log` files. Run `bun run test:browser` to reproduce screenshots. Automated checks do not constitute a complete manual accessibility audit.

## Research execution

All **six fresh fits** completed: two representations × seeds 42, 43, 44.
The run took **16.81 minutes**, including fresh frozen-encoder inference over
**11,546 chunks**, clustering, evaluation, export, and seed comparison.
Encoder metadata records `cache_used: false` and `resume_start_chunk: 0`.
Legal-BERT was not fine-tuned. Primary seed topic counts: **49 lexical / 36 semantic**.
The input remained **2,118 source documents / 7,832 model units**.

Publication validates every saved model artifact against its run fingerprint,
source/override/preparation identity, completed statuses, ordered assignment rows,
metric counts, yearly denominators, annual weight conservation, title scopes, and
figure/PDF/PPTX completeness. Historical Conservative artifacts were not modified.
These checks establish execution and export consistency—not legal validity,
representativeness, causal interpretation, or expert approval.

## Deployment status

The branch is prepared for GitHub Pages; **local browser verification is not an
online deployment**. The contributor account has push access but not repository-admin
permission. The owner must enable Pages and set `ENABLE_DASHBOARD_PAGES=true` before
the deploy job runs. See [dashboard setup](../dashboard/README.md).
