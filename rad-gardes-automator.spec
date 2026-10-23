# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path

from PyInstaller.utils.hooks import collect_all

try:
    ROOT = Path(SPECPATH).resolve()
except NameError:  # pragma: no cover - fallback for direct execution
    ROOT = Path.cwd().resolve()

datas = [(str(ROOT / "examples"), "examples")]
binaries = []
hiddenimports = []

for package in ("ortools", "pymupdf"):
    package_datas, package_binaries, package_hiddenimports = collect_all(package)
    datas += package_datas
    binaries += package_binaries
    hiddenimports += package_hiddenimports

a = Analysis(
    [str(ROOT / "scripts" / "gardes_gui_entry.py")],
    pathex=[str(ROOT / "src")],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "pytest",
        "coverage",
        "tkinter",
        "unittest",
        "pydoc_data",
        "IPython",
        "jupyter",
        "notebook",
        "matplotlib",
        "scipy",
    ],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="RAD-Gardes-Automator",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name="RAD-Gardes-Automator",
)
