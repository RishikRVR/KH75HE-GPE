# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.utils.hooks import collect_submodules, collect_dynamic_libs

APP_NAME = "KH75 HE Gamepad Emulator"
SCRIPT = "KH75HE-GPE.py"
ICON = "KH75HE-GPE.ico"

# Collect vgamepad's Python modules.
hiddenimports = [
    "hid",
    "vgamepad",
    "tkinter",
]

hiddenimports += collect_submodules("vgamepad")

# IMPORTANT:
# vgamepad uses ViGEmClient.dll through ctypes.
# PyInstaller needs the DLL explicitly collected.
binaries = collect_dynamic_libs("vgamepad")

datas = [

    ("KH75HE-GPE.png", "."),

]

a = Analysis(
    [SCRIPT],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name=APP_NAME,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=ICON,
)