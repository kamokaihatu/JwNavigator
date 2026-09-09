@REM [MARK] 書込レイヤに点(1,1)を作図(小さい範囲選択の目印用)
@REM 所要時間の計測つき(cowork調査用)
REM #jww
REM #h0
REM #e
@echo off
if not exist "%~dp0layerdump" mkdir "%~dp0layerdump"
set "LOG=%~dp0layerdump\log_MARK.txt"
set "TRACE=%~dp0layerdump\trace.txt"
echo [MARK] %TIME% enter >> "%TRACE%"
echo [bat] %TIME% python 起動前 > "%LOG%"
python "%~dp0mark_point.py" >> "%LOG%" 2>&1
if not errorlevel 1 goto :done
py "%~dp0mark_point.py" >> "%LOG%" 2>&1
:done
echo [bat] %TIME% python 終了後 >> "%LOG%"
echo [MARK] %TIME% exit >> "%TRACE%"
