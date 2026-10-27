# Davao Ordinance Observatory

A read-only thesis dashboard made with **plain HTML, CSS, and JavaScript**.
No React, UI framework, charting library, backend API, database, or build step.
Charts are accessible HTML tables and native SVG. The production site loads only
its own static files; no external fonts, analytics, or CDN dependencies.

The active results are **fresh Coarse-grained / seed 42** outputs for both
representations, with seeds 43/44 providing sensitivity evidence. Conservative
outputs remain historical research evidence outside this dashboard.

## Open in VS Code

Open the **repository root** (not just this dashboard folder):

```powershell
code C:\Users\BloodMank\Desktop\Thesis\Thesis_Model_Comparison
```

1. Run `mise install` if Bun is not available.
2. Press **F5**, select **Dashboard: open in Edge**.
   The launch task starts the local static preview automatically.
3. Alternatively, run **Terminal → Run Task → Dashboard: serve**, then open
   **http://127.0.0.1:3000**.

Or use the integrated terminal:

```powershell
bun run dev
```

Use Ctrl+C to stop the terminal server (or terminate the VS Code task).
If port 3000 is already in use, stop that preview or set `$env:PORT=3001` before
`bun run dev` and visit the new port. The F5 launch URL defaults to port 3000.

Do not double-click `index.html`: browsers restrict JavaScript module/data access
under `file://`. HTTP hosting is required. Preview binds only to 127.0.0.1.

## Edit the interface

| File | Responsibility |
|---|---|
| `index.html` | Semantic sections, controls, download links |
| `styles.css` | Responsive layout, typography, colors |
| `app.js` | UI state, filters, tables, native SVG charts |
| `data-utils.js` | Validation and pure calculations |
| `data/results.json` | Exported real model results; do not hand-edit |
| `downloads/` | Generated figures, tables, manifests, checksums |

The interface has model and year selectors, an eight-topic heatmap, archive-size
bars, annual composition, searchable/paginated topic details, exact annual values,
metrics, provenance, and downloads. All topics remain searchable; procedural and
unclear clusters are not hidden. There are no upload, training, or editing controls
on the public site.

The topic-detail selection is independent of search filtering: if a search returns
zero results, the existing detail remains visible with an explicit notice.
Switching models resets search/category/topic selection because IDs are model-local.
Annual chart percentages are document-weighted; metric coverage is unit-weighted.

## Tests

Production preview needs no package installation. Browser testing tools are dev-only:

```powershell
bun install --frozen-lockfile
bun run test
bunx playwright install chromium
bun run test:browser
```

The browser suite exercises real data, responsive layouts, controls, downloads,
keyboard focus, subdirectory hosting, unavailable-data handling, and automated
WCAG A/AA checks. Screenshots go to ignored `test-results/dashboard/`.
Automated accessibility checks do not replace a full manual accessibility audit.
Chromium is installed through Playwright; the suite drives it through Bun's native
WebSocket/CDP support to avoid Windows Node-pipe compatibility problems. Axe runs
inside the real browser. JavaScript tooling still runs on Bun, not Node.

## Publish online — repository owner action required

The current authenticated contributor can push code but does **not** have
repository-admin permission. A live deployment cannot be claimed until the owner
enables GitHub Pages.

1. Confirm there is no existing Pages site that should be preserved.
2. In **Settings → Pages → Build and deployment**, choose **GitHub Actions**.
3. In **Settings → Secrets and variables → Actions → Variables**, add repository
   variable `ENABLE_DASHBOARD_PAGES` with value `true`.
4. If the `github-pages` environment restricts deployment branches, allow
   `research/coarse-grained-dashboard` (or the final merged branch).
5. Rerun the latest **Publish coarse-grained dashboard** workflow on this branch.
   If GitHub requires a fresh event, push a dashboard documentation change.
   Manual dispatch also works once the workflow is available on the default branch.

The workflow always validates the site, but deployment is skipped until that
explicit opt-in is set. It deploys **only `dashboard/`**, never the full repository,
raw source text, local environment, embeddings, or reviewer data.

Expected URL **after successful deployment**:
`https://hackeddog.github.io/Thesis_Ordinance-Analysis/`

If the branch is merged into `main`, update the workflow's push branch filter.
Any static host can serve `dashboard/` directly; relative paths support project
subdirectories. There is no server-side training in production.

## Regenerate the data

Use [the fresh-run guide](../docs/COARSE_GRAINED_DASHBOARD.md).
The publisher refuses to overwrite a completed publication. Never replace the
JSON manually or reuse Conservative topic labels. The data, figure exports, and
checksums must all describe the same completed run.
