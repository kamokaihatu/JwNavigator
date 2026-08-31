# -*- mode: python ; coding: utf-8 -*-
# 👑 usage_logger.pyはJwNavigator本体とは無関係に単体配布する想定
# （Pythonを持たない同僚に「これだけ実行しておいて」と渡す用途）。
# 小さなtkinterウィンドウ＋「終了して保存」ボタンで完結するため、
# 黒いコンソール窓は不要（console=False）。

a = Analysis(
    ['tools/usage_logger.py'],
    # 👑 tools/usage_logger.pyはリポジトリルート直下のutils/を
    # `from utils import ...`で参照する（スクリプト自身の実行時
    # sys.path.insert()と同じ意図）。PyInstallerの静的解析はエントリ
    # スクリプト自身のディレクトリ（tools/）基準で探索してしまい
    # utils/を見つけられなかった（実測: ModuleNotFoundError: 'utils'）
    # ため、リポジトリルートを明示的にpathexへ追加する。
    pathex=['.'],
    binaries=[],
    # 👑 単体配布（同僚に1ファイルだけ渡す想定）のため、コマンド一覧の
    # 元になるdata/commands_master.csvを同梱する。command_master.pyの
    # _resolve_csv_path()はexe横にdata/が無ければsys._MEIPASSからこの
    # 同梱コピーを読みに行くフォールバックを持つ。
    datas=[('data/commands_master.csv', 'data')],
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
    name='JwNavigator_UsageLogger',
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
# 👑 onefile（単一exe）はWindowsのApplication Control policyに
# ブロックされることを実測で確認（2026-08-31、この開発機で再現）。
# JwNavigator.exe同様、フォルダ形式（onedir）にすることで回避する。
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='JwNavigator_UsageLogger',
)
