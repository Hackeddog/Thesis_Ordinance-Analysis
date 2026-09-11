$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
$python = Join-Path $projectRoot ".venv\Scripts\python.exe"

if (-not (Test-Path $python)) {
    $python = "python"
}

Push-Location $projectRoot
try {
    & $python -m streamlit run app/main.py
} finally {
    Pop-Location
}
