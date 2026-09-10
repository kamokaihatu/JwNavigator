@REM [A] レイヤ状態を保存
@REM 全選択せず(所要時間の計測・ブロック/曲線/多角形/ソリッドをログで区別するため)
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
echo [bat] %TIME% dump_layers.exe 起動前 > "%LOG%"
"%~dp0dump_layers\dump_layers.exe" A >> "%LOG%" 2>&1
echo [bat] %TIME% dump_layers.exe 終了後 >> "%LOG%"
echo [SAVE] %TIME% exit >> "%TRACE%"
