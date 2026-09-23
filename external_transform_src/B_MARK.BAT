@REM [MARK] 書込レイヤに点(1,1)を作図(小さい範囲選択の目印用)
@REM PowerShell版(exe版/python版がセキュリティソフトにブロックされる環境向けの代替)
REM #jww
REM #h0
REM #e
@echo off
if not exist "%~dp0layerdump" mkdir "%~dp0layerdump"
set "LOG=%~dp0layerdump\log_MARK.txt"
set "TRACE=%~dp0layerdump\trace.txt"
echo [MARK] %TIME% enter >> "%TRACE%"
echo [bat] %TIME% mark_point.ps1 起動前 > "%LOG%"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0mark_point.ps1" >> "%LOG%" 2>&1
echo [bat] %TIME% mark_point.ps1 終了後 >> "%LOG%"
echo [MARK] %TIME% exit >> "%TRACE%"
