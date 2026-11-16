# -*- mode: python ; coding: utf-8 -*-
"""Spec PyInstaller unique : .app sur macOS, dossier portable (onedir) sur Windows.

macOS  : pyinstaller packaging/rad_gardes_v5.spec --noconfirm
Windows: pyinstaller packaging\\rad_gardes_v5.spec --noconfirm
"""

import sys
from pathlib import Path

RACINE = Path(SPECPATH).resolve().parent  # dossier v5-brut/
NOM = "RAD Gardes V5"
VERSION = "5.0.0"

a = Analysis(
    [str(RACINE / "packaging" / "entree.py")],
    pathex=[str(RACINE)],
    binaries=[],
    datas=[],
    hiddenimports=[],
    excludes=["pytest", "numpy", "pandas", "PIL", "setuptools", "pip"],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name=NOM,
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
        bundle_identifier="ch.gfahrni.radgardes.v5",
        info_plist={
            "CFBundleName": NOM,
            "CFBundleDisplayName": NOM,
            "CFBundleShortVersionString": VERSION,
            "CFBundleVersion": VERSION,
            "NSHighResolutionCapable": True,
            "LSMinimumSystemVersion": "13.0",
            "LSApplicationCategoryType": "public.app-category.medical",
        },
    )
