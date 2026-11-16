"""Point d'entrée du binaire (PyInstaller, macOS et Windows)."""

import sys

from gardes_simple.cli import main

if __name__ == "__main__":
    sys.exit(main())
