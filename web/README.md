# Ordinance Lab website

This is the browser-based version of the dashboard. It uses a small
Node.js-compatible server with a vanilla HTML/CSS/JavaScript frontend and calls
the existing Python pipeline for audits.

## Run from VS Code

1. Open the repository root in VS Code.
2. Press `F5`.
3. Select **Ordinance Lab website** if prompted.
4. Open `http://localhost:3000` if the browser does not open automatically.

The server uses the repository `.venv` Python interpreter when available and
falls back to `python`.

## Run without the debugger

From the repository root:

```bash
bun run start
```

The website starts at `http://localhost:3000` and opens the browser.

## Design boundary

The website supports safe auditing, browsing, and PDF uploads into
`data/raw/<year>/`. Uploads never silently overwrite an existing file; replacing
one requires an explicit checkbox and creates a backup under
`data/versions/uploads/`. After an upload, the audit refreshes the CSV database
and optionally syncs generated Obsidian notes. It does not quarantine, purge, or
restore PDFs. The backend is intentionally kept small so future features can be
added as API routes without duplicating the Python parser.
