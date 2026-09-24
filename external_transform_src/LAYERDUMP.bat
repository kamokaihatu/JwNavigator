@REM JwNavi
@REM layer state dump (all 16 groups x 16 layers)
REM #jww
REM #h1
REM #g1
REM #gn
REM #e
@echo off
if not exist "%~dp0layerdump" mkdir "%~dp0layerdump"
python "%~dp0dump_layers.py" DUMP > "%~dp0layerdump\log_DUMP.txt" 2>&1
if not errorlevel 1 goto :done
py "%~dp0dump_layers.py" DUMP >> "%~dp0layerdump\log_DUMP.txt" 2>&1
:done
