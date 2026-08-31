# -*- mode: python ; coding: utf-8 -*-
# 👑 icons/*.pyはwidgets/toolbar.pyがimportlib.import_moduleで動的import
# しているだけで静的importが無いため、PyInstallerの依存解析では自動検出
# されない。collect_submodules("icons")で明示的にexe内へ同梱する。
# （utils/palette_config.pyのlist_icon_modules()側はsys.frozen判定で
# pkgutil.iter_modules(icons.__path__)を使う分岐を用意済み）
from PyInstaller.utils.hooks import collect_submodules

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=collect_submodules('icons'),
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
    name='JwNavigator',
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
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='JwNavigator',
)
