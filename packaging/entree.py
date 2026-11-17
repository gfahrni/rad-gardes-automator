"""Point d'entrée du binaire PyInstaller (macOS et Windows)."""

from __future__ import annotations

import sys

from gardes_gui.app import main

if __name__ == "__main__":
    sys.exit(main())
