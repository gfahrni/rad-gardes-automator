#!/usr/bin/env bash
# Construit l'application macOS et son archive : dist/RAD Gardes V7.app
# et dist/RAD-Gardes-V7-macos-<arch>.zip.
set -euo pipefail

RACINE="$(cd "$(dirname "$0")/.." && pwd)"
cd "$RACINE"

VENV="${BUILD_VENV:-$RACINE/.build-venv}"
export UV_CACHE_DIR="${UV_CACHE_DIR:-/tmp/uv-cache}"
export PYINSTALLER_CONFIG_DIR="${PYINSTALLER_CONFIG_DIR:-/tmp/pyinstaller-config}"

if [ ! -x "$VENV/bin/python" ]; then
  uv venv "$VENV" --python 3.12
fi
uv pip install --python "$VENV/bin/python" -e ".[build]"

"$VENV/bin/pyinstaller" packaging/rad_gardes_v7.spec \
  --noconfirm --clean --distpath dist --workpath .build-work

APP="dist/RAD Gardes V7.app"
ARCH="$(uname -m)"
ZIP="dist/RAD-Gardes-V7-macos-${ARCH}.zip"

# Signature ad-hoc : l'app se lance localement, sans identité développeur.
codesign --force --deep --sign - "$APP" >/dev/null 2>&1 || true
xattr -cr "$APP"

# ditto préserve les liens symboliques et les permissions des frameworks Qt ;
# --norsrc/--noextattr évitent les fichiers AppleDouble « ._ » dans le ZIP.
ditto -c -k --keepParent --norsrc --noextattr "$APP" "$ZIP"

echo "App macOS : $RACINE/$APP"
echo "Archive   : $RACINE/$ZIP"
