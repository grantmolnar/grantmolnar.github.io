# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path
import sys

from PyInstaller.utils.hooks import collect_data_files

ROOT = Path.cwd()
PACKAGE_DATA = collect_data_files(
    "adventure_graph",
    includes=[
        "py.typed",
        "resources/*.json",
        "interfaces/web/assets/*.css",
        "interfaces/web/assets/*.js",
    ],
)

analysis = Analysis(
    [str(ROOT / "packaging" / "desktop_entry.py")],
    pathex=[str(ROOT / "src")],
    binaries=[],
    datas=PACKAGE_DATA,
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "bandit",
        "hypothesis",
        "jsonschema",
        "pip_audit",
        "pytest",
        "pyright",
        "ruff",
    ],
    noarchive=False,
    optimize=1,
)
pyz = PYZ(analysis.pure)

executable = EXE(
    pyz,
    analysis.scripts,
    [],
    exclude_binaries=True,
    name="Adventure Graph",
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
)

bundle = COLLECT(
    executable,
    analysis.binaries,
    analysis.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="Adventure Graph",
)

if sys.platform == "darwin":
    app = BUNDLE(
        bundle,
        name="Adventure Graph.app",
        icon=None,
        bundle_identifier="com.grantmolnar.adventuregraph",
        info_plist={
            "CFBundleDisplayName": "Adventure Graph",
            "CFBundleName": "Adventure Graph",
            "NSHighResolutionCapable": True,
        },
    )
