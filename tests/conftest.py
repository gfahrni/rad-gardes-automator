from __future__ import annotations

import os
from pathlib import Path

import pytest

# Doit être défini avant l'import de PySide6.
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "examples"


@pytest.fixture(scope="session")
def examples() -> Path:
    return EXAMPLES


@pytest.fixture(scope="session")
def pdf(examples: Path) -> Path:
    return examples / "exemple-calcul-gardes.pdf"


@pytest.fixture(scope="session")
def planning_xlsx(examples: Path) -> Path:
    return examples / "exemple-planning-vide.xlsx"


@pytest.fixture(scope="session")
def wishes_xlsx(examples: Path) -> Path:
    return examples / "exemple-souhaits-garde.xlsx"


@pytest.fixture(scope="session")
def qapp():
    from PySide6.QtWidgets import QApplication

    app = QApplication.instance() or QApplication([])
    yield app
