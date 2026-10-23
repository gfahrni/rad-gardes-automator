from __future__ import annotations

import sys
from pathlib import Path

from gardes_gui import paths


def test_source_paths() -> None:
    root = Path(__file__).resolve().parents[1]
    assert paths.is_frozen() is False
    assert paths.examples_dir() == root / "examples"
    assert paths.default_workdir() == root / "data" / "run"


def test_frozen_examples_from_bundle(monkeypatch, tmp_path: Path) -> None:
    bundle = tmp_path / "_internal"
    examples = bundle / "examples"
    examples.mkdir(parents=True)
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "_MEIPASS", str(bundle), raising=False)
    assert paths.examples_dir() == examples


def test_frozen_examples_next_to_executable(monkeypatch, tmp_path: Path) -> None:
    executable = tmp_path / "RAD-Gardes-Automator.exe"
    executable.write_bytes(b"")
    examples = tmp_path / "examples"
    examples.mkdir()
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "_MEIPASS", str(tmp_path / "_internal"), raising=False)
    monkeypatch.setattr(sys, "executable", str(executable))
    assert paths.examples_dir() == examples


def test_frozen_workdir_is_user_writable(monkeypatch) -> None:
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    assert paths.default_workdir() == (
        Path.home() / "Documents" / "RAD Gardes Automator" / "run"
    )
