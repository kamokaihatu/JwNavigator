# -*- mode: python ; coding: utf-8 -*-
# 👑 mark_point.pyはjw_cadの外部変形(B_MARK.BAT)から起動される単体ツール。
# 同僚のPCにPythonが入っていないと"python mark_point.py"が失敗し、
# 「復元ボタンは出るがレイヤ情報が保存されない」という無言の失敗になる
# ことが実機で発覚した(2026-09-10)。JwNavigator.exe同様、単独exe化して
# Pythonインストール自体を不要にする。

a = Analysis(
    ['mark_point.py'],
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
    name='mark_point',
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
# 👑 onefile(単一exe)は毎回tempへ展開するため起動が遅く、Windowsの
# Application Control policyにブロックされることもJwNavigator本体で
# 実測済み(2026-08-31)。B_MARK.batから繰り返し呼ばれる用途なので、
# フォルダ形式(onedir)にして起動オーバーヘッドを避ける。
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='mark_point',
)
