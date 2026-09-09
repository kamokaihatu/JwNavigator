@REM [A] レイヤ状態を保存
@REM 全選択方式(所要時間の計測つき・ブロック/曲線/寸法図形/ソリッド除外で高速化を試験中)
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
echo [bat] %TIME% python 起動前 > "%LOG%"
python "%~dp0dump_layers.py" A >> "%LOG%" 2>&1
if not errorlevel 1 goto :done
py "%~dp0dump_layers.py" A >> "%LOG%" 2>&1
:done
echo [bat] %TIME% python 終了後 >> "%LOG%"
echo [SAVE] %TIME% exit >> "%TRACE%"
