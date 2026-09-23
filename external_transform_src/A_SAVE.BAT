@REM [A] 全レイヤ状態を保存
@REM PowerShell版(exe版/python版がセキュリティソフトにブロックされる環境向けの代替)
REM #jww
REM #h1
REM #ht10
REM #ht20
REM #ht30
REM #ht40
REM #g1
REM #gn
REM #e
@echo off
if not exist "%~dp0layerdump" mkdir "%~dp0layerdump"
set "LOG=%~dp0layerdump\log_A.txt"
set "TRACE=%~dp0layerdump\trace.txt"
echo [SAVE] %TIME% enter >> "%TRACE%"
echo [bat] %TIME% dump_layers.ps1 起動前 > "%LOG%"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0dump_layers.ps1" A >> "%LOG%" 2>&1
echo [bat] %TIME% dump_layers.ps1 終了後 >> "%LOG%"
echo [SAVE] %TIME% exit >> "%TRACE%"
