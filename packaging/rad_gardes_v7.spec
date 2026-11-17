# -*- mode: python ; coding: utf-8 -*-
"""Spec PyInstaller unique : .app sur macOS, dossier portable (onedir) sur Windows.

macOS  : pyinstaller packaging/rad_gardes_v7.spec --noconfirm
Windows: pyinstaller packaging\\rad_gardes_v7.spec --noconfirm

L'application embarque le moteur, l'interface PySide6 et les exemples
synthétiques de ``examples/``. Le self-test ``--self-test`` et le smoke test
``--smoke-test`` sont exposés par ``gardes_gui.app:main``.
"""

from __future__ import annotations

import sys
from pathlib import Path

from PyInstaller.utils.hooks import collect_all

RACINE = Path(SPECPATH).resolve().parent
NOM = "RAD Gardes V7"
VERSION = "7.2.0"

datas = [(str(RACINE / "examples"), "examples")]
binaries = []
hiddenimports = []

for paquet in ("ortools", "pdfplumber", "pdfminer"):
    paquet_datas, paquet_binaries, paquet_hiddenimports = collect_all(paquet)
    datas += paquet_datas
    binaries += paquet_binaries
    hiddenimports += paquet_hiddenimports

a = Analysis(
    [str(RACINE / "packaging" / "entree.py")],
    pathex=[str(RACINE / "src")],
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
        # Inutilisé par l'application ; retire SQLite et, sur macOS, les
        # bibliothèques ICU dont il dépend (~38 Mo).
        "sqlite3",
        "_sqlite3",
    ],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name=NOM,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(RACINE / "packaging" / ("icone.icns" if sys.platform == "darwin" else "icone.ico")),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name=NOM,
)

if sys.platform == "darwin":
    app = BUNDLE(
        coll,
        name=f"{NOM}.app",
        icon=str(RACINE / "packaging" / "icone.icns"),
        bundle_identifier="ch.gfahrni.radgardes.v7",
        info_plist={
            "CFBundleName": NOM,
            "CFBundleDisplayName": NOM,
            "CFBundleShortVersionString": VERSION,
            "CFBundleVersion": VERSION,
            "NSHighResolutionCapable": True,
            "LSMinimumSystemVersion": "13.0",
            "LSApplicationCategoryType": "public.app-category.medical",
            "NSHumanReadableCopyright": "MIT — RAD Gardes Automator",
        },
    )
