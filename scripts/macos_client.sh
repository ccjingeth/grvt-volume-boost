#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
VENV_DIR="${ROOT_DIR}/.venv-mac-client"
CMD="${1:-run}"

if [[ "$(uname -s)" != "Darwin" ]]; then
  echo "This script is for macOS only."
  exit 1
fi

setup_env() {
  python3 -m venv "${VENV_DIR}"
  # shellcheck disable=SC1091
  source "${VENV_DIR}/bin/activate"
  python -m pip install --upgrade pip
  python -m pip install -r "${ROOT_DIR}/requirements.txt"
  python -m playwright install chromium
}

run_gui() {
  # shellcheck disable=SC1091
  source "${VENV_DIR}/bin/activate"
  cd "${ROOT_DIR}"
  python volume_boost_gui.py
}

build_app() {
  cd "${ROOT_DIR}"
  ./scripts/build_macos.sh
}

run_doctor() {
  # shellcheck disable=SC1091
  source "${VENV_DIR}/bin/activate"
  cd "${ROOT_DIR}"
  python volume_boost.py doctor
}

case "${CMD}" in
  setup)
    setup_env
    ;;
  run)
    if [[ ! -d "${VENV_DIR}" ]]; then
      setup_env
    fi
    run_gui
    ;;
  build)
    build_app
    ;;
  doctor)
    if [[ ! -d "${VENV_DIR}" ]]; then
      setup_env
    fi
    run_doctor
    ;;
  *)
    echo "Usage: ./scripts/macos_client.sh [setup|run|build|doctor]"
    exit 1
    ;;
esac
