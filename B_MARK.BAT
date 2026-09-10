@REM [MARK] 書込レイヤに点(1,1)を作図(小さい範囲選択の目印用)
@REM 所要時間の計測用(cowork使用)
REM #jww
REM #h0
REM #e
@echo off
if not exist "%~dp0layerdump" mkdir "%~dp0layerdump"
set "LOG=%~dp0layerdump\log_MARK.txt"
set "TRACE=%~dp0layerdump\trace.txt"
echo [MARK] %TIME% enter >> "%TRACE%"
echo [bat] %TIME% mark_point.exe 起動前 > "%LOG%"
"%~dp0mark_point\mark_point.exe" >> "%LOG%" 2>&1
echo [bat] %TIME% mark_point.exe 終了後 >> "%LOG%"
echo [MARK] %TIME% exit >> "%TRACE%"
