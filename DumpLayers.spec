# -*- mode: python ; coding: utf-8 -*-
# 👑 dump_layers.pyはjw_cadの外部変形(A_SAVE.BAT)から起動される単体ツール。
# mark_point.pyと同じ理由(2026-09-10、同僚PCにPython無し)で単独exe化する。
# MarkPoint.specと同じ方針、詳細はそちらのコメント参照。

a = Analysis(
    ['dump_layers.py'],
    pathex=[],
    binaries=[],
    datas=[],
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
    [],
    exclude_binaries=True,
    name='dump_layers',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='dump_layers',
)
