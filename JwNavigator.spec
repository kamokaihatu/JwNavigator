# -*- mode: python ; coding: utf-8 -*-
# 👑 icons/*.pyはwidgets/toolbar.pyがimportlib.import_moduleで動的import
# しているだけで静的importが無いため、PyInstallerの依存解析では自動検出
# されない。collect_submodules("icons")で明示的にexe内へ同梱する。
# （utils/palette_config.pyのlist_icon_modules()側はsys.frozen判定で
# sys._MEIPASS配下のicons/*.pyをglobする分岐を用意済み。当初pkgutilで
# 試したが凍結パッケージの__path__は仮想パスで機能しなかったため撤回した）
from PyInstaller.utils.hooks import collect_submodules

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    # 👑 icons/*.pyはhiddenimportsでexe内に実行可能な形で同梱されるが、
    # それだけだとutils/palette_config.pyのlist_icon_modules()が
    # 「一覧を取得する」ためにファイルとして走査できない（凍結パッケージの
    # __path__は仮想パスで実ファイルが存在しないため、実測でpkgutil.
    # iter_modules()が常に空を返すことを確認、2026-08-31）。同じ内容を
    # datasとしても実体コピーし、sys._MEIPASS配下から通常のglobで
    # 一覧取得できるようにする。
    datas=[('icons', 'icons'), ('data/app_icon.ico', 'data'), ('data/starter_presets', 'data/starter_presets')],
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
    icon=['data/app_icon.ico'],
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
