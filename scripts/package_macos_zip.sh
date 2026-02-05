#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
DIST_DIR="${ROOT_DIR}/dist"
APP_NAME="GRVTVolumeBoost.app"
APP_PATH="${DIST_DIR}/${APP_NAME}"
PKG_DIR="${DIST_DIR}/GRVTVolumeBoost-macos-arm64"
ZIP_PATH="${DIST_DIR}/GRVTVolumeBoost-macos-arm64.zip"

if [[ ! -d "${APP_PATH}" ]]; then
  echo "App not found: ${APP_PATH}" >&2
  echo "Run ./scripts/macos_client.sh build first." >&2
  exit 1
fi

rm -rf "${PKG_DIR}"
mkdir -p "${PKG_DIR}"

cp -R "${APP_PATH}" "${PKG_DIR}/${APP_NAME}"

cat > "${PKG_DIR}/Start.command" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
open "${SCRIPT_DIR}/GRVTVolumeBoost.app"
EOF
chmod +x "${PKG_DIR}/Start.command"

cat > "${PKG_DIR}/README_START.txt" <<'EOF'
macOS 一键启动说明:
1) 首次打开请右键 GRVTVolumeBoost.app -> 打开
2) 或双击 "Start.command"
3) 如提示权限，请在 系统设置 -> 隐私与安全性 中允许
EOF

rm -f "${ZIP_PATH}"
ditto -c -k --sequesterRsrc --keepParent "${PKG_DIR}" "${ZIP_PATH}"

echo "Created: ${ZIP_PATH}"
