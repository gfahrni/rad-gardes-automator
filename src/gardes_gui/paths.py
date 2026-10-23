from __future__ import annotations

import sys
from pathlib import Path


def is_frozen() -> bool:
    """Vrai lorsque l'application tourne depuis un exécutable PyInstaller."""
    return bool(getattr(sys, "frozen", False))


def source_root() -> Path:
    """Racine du dépôt en mode source : .../src/gardes_gui/paths.py -> racine."""
    return Path(__file__).resolve().parents[2]


def bundle_root() -> Path:
    """Répertoire des ressources embarquées par PyInstaller."""
    if is_frozen():
        return Path(getattr(sys, "_MEIPASS", Path(sys.executable).resolve().parent))
    return source_root()


def examples_dir() -> Path:
    """Trouve le dossier examples/ en source, en onedir ou en onefile."""
    if is_frozen():
        candidates = [
            bundle_root() / "examples",
            Path(sys.executable).resolve().parent / "examples",
        ]
        for candidate in candidates:
            if candidate.is_dir():
                return candidate
        return candidates[0]
    return source_root() / "examples"


def default_workdir() -> Path:
    """Dossier de sortie par défaut, toujours inscriptible par l'utilisateur."""
    if is_frozen():
        return Path.home() / "Documents" / "RAD Gardes Automator" / "run"
    return source_root() / "data" / "run"
