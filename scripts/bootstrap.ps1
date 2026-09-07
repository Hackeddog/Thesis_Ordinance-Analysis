# One-shot environment setup for Windows PowerShell.
# See SETUP.md for the manual walkthrough and the Tesseract install.
$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..")

Write-Host "==> Python"
python --version

Write-Host "==> Virtual environment"
if (-Not (Test-Path ".venv")) { python -m venv .venv }
& .\.venv\Scripts\Activate.ps1

Write-Host "==> Dependencies"
python -m pip install --quiet --upgrade pip
python -m pip install --quiet -r requirements.txt

Write-Host "==> Tesseract"
if (Get-Command tesseract -ErrorAction SilentlyContinue) {
    tesseract --version | Select-Object -First 1
} else {
    Write-Host "    NOT FOUND. Scanned ordinances will not be readable."
    Write-Host "    Install from the UB Mannheim Tesseract page, then add it to PATH."
}

Write-Host "==> Self-test"
python tests\test_pipeline.py

Write-Host ""
Write-Host "Setup complete. Next:"
Write-Host "  1. Copy the ordinance PDFs into data\raw\{year}\"
Write-Host "  2. python src\ordinance_eda_pipeline.py --year 2016 --debug-headers 10"
Write-Host "  3. Follow docs\EDA_PIPELINE_RUNBOOK.md from Step 1"
Write-Host ""
Write-Host "Remember to run .\.venv\Scripts\Activate.ps1 in every new terminal."
