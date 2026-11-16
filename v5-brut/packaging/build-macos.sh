#!/usr/bin/env bash
# Construit l'application macOS : dist/RAD Gardes V5.app
set -euo pipefail
RACINE="$(cd "$(dirname "$0")/.." && pwd)"
cd "$RACINE"

export UV_CACHE_DIR="${UV_CACHE_DIR:-/tmp/uv-cache}"
export PYINSTALLER_CONFIG_DIR="${PYINSTALLER_CONFIG_DIR:-/tmp/pyinstaller-config}"

uv venv .build-venv --python 3.12
uv pip install --python .build-venv/bin/python pyinstaller openpyxl==3.1.5

.build-venv/bin/pyinstaller packaging/rad_gardes_v5.spec \
  --noconfirm --clean --distpath dist --workpath .build-work

codesign --force --deep --sign - "dist/RAD Gardes V5.app" >/dev/null 2>&1 || true
echo "App macOS : $RACINE/dist/RAD Gardes V5.app"
