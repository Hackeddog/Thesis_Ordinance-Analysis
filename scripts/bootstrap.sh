#!/usr/bin/env bash
# One-shot environment setup for macOS and Linux. See SETUP.md for the manual
# walkthrough and for the Tesseract install, which this script only checks.
set -euo pipefail
cd "$(dirname "$0")/.."

echo "==> Python"
python3 --version

echo "==> Virtual environment"
[ -d .venv ] || python3 -m venv .venv
# shellcheck disable=SC1091
source .venv/bin/activate

echo "==> Dependencies"
python -m pip install --quiet --upgrade pip
python -m pip install --quiet -r requirements.txt

echo "==> Tesseract"
if command -v tesseract >/dev/null 2>&1; then
  tesseract --version | head -1
else
  echo "    NOT FOUND. Scanned ordinances will not be readable."
  echo "    macOS: brew install tesseract | Debian: sudo apt install tesseract-ocr"
fi

echo "==> Self-test"
python tests/test_pipeline.py

cat <<'MSG'

Setup complete. Next:
  1. Copy the ordinance PDFs into data/raw/{year}/
  2. python src/ordinance_eda_pipeline.py --year 2016 --debug-headers 10
  3. Follow docs/EDA_PIPELINE_RUNBOOK.md from Step 1

Remember to `source .venv/bin/activate` in every new terminal.
MSG
