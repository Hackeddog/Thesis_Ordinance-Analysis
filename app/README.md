# Ordinance Lab dashboard

A small local Streamlit dashboard around the existing ordinance EDA CLI.

## Start it

From the repository root:

```bash
python -m pip install -r requirements.txt
python -m streamlit run app/main.py
```

Or use the Make target:

```bash
make app
```

On Windows PowerShell, you can also run:

```powershell
.\scripts\run_app.ps1
```

Open the local URL printed by Streamlit. The dashboard is intentionally in
**safe audit mode** for the first version: it can run the existing audit, inspect
outputs, filter the document register, read generated reports, and review the
thesis checklist. It does not move, quarantine, purge, or restore files.

## Layout

- `main.py` contains the UI and presentation logic.
- `services.py` contains pipeline calls and data-loading helpers.
- `__init__.py` keeps the dashboard easy to extend as new pages are added.

Future additions should go through `services.py` rather than duplicating parser
logic in the UI.
