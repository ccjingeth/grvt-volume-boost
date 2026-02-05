#!/usr/bin/env bash
set -euo pipefail

NAME="${1:-GRVTVolumeBoost}"
ENTRY="${2:-volume_boost_gui.py}"
OUT_DIR="${3:-dist}"
BROWSER_DIR="${4:-playwright-browsers}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
VENV_DIR="${ROOT_DIR}/.venv-build-macos"

cd "${ROOT_DIR}"

echo "== Building macOS app (${NAME}) =="

mkdir -p "${BROWSER_DIR}"
export PLAYWRIGHT_BROWSERS_PATH="${ROOT_DIR}/${BROWSER_DIR}"

if command -v python3.11 >/dev/null 2>&1; then
  BASE_PYTHON="python3.11"
elif command -v python >/dev/null 2>&1; then
  BASE_PYTHON="python"
elif command -v python3 >/dev/null 2>&1; then
  BASE_PYTHON="python3"
else
  echo "python/python3 not found." >&2
  exit 1
fi

if [[ ! -d "${VENV_DIR}" ]]; then
  "${BASE_PYTHON}" -m venv "${VENV_DIR}"
fi

PYTHON_BIN="${VENV_DIR}/bin/python"

"${PYTHON_BIN}" -m pip install --upgrade pip
"${PYTHON_BIN}" -m pip install -r requirements.txt pyinstaller

echo "Installing Playwright Chromium into ${PLAYWRIGHT_BROWSERS_PATH}"
"${PYTHON_BIN}" -m playwright install chromium

echo "Running PyInstaller..."
"${PYTHON_BIN}" -m PyInstaller \
  --noconfirm \
  --clean \
  --windowed \
  --name "${NAME}" \
  --distpath "${OUT_DIR}" \
  --collect-all playwright \
  --collect-all playwright_stealth \
  --collect-submodules eth_account \
  --collect-submodules eth_keys \
  --collect-submodules eth_utils \
  "${ENTRY}"

APP_PATH="${OUT_DIR}/${NAME}.app"
if [[ ! -d "${APP_PATH}" ]]; then
  echo "Expected app bundle not found: ${APP_PATH}" >&2
  exit 1
fi

# Keep bundled Playwright browsers inside the app so QR login works without extra download.
TARGET_BROWSER_DIR="${APP_PATH}/Contents/MacOS/${BROWSER_DIR}"
rm -rf "${TARGET_BROWSER_DIR}"
cp -R "${BROWSER_DIR}" "${TARGET_BROWSER_DIR}"

echo "Build complete: ${APP_PATH}"
