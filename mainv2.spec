# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.utils.hooks import collect_data_files
import os

# Collect all data files in core/, db/, and resources/
datas = []

# Include the TOML and text files in core/
datas += [
    ('core/gameconfig.toml', 'core'),
    ('core/prize_arrangement.toml', 'core'),
    ('core/requirements.txt', 'core'),
]

# Include database and JSON files
datas += [
    ('db/prizes.db', 'db'),
    ('db/prizes.json', 'db'),
]

# Include image resources
datas += [
    ('resources/DOST_seal.svg', 'resources'),
    ('resources/dost_logo.png', 'resources'),
]

a = Analysis(
    ['mainv2.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='mainv2',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # set to False if you want to hide console window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
