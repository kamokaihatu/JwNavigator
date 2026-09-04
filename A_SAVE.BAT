@REM [A] ƒŒƒCƒ„ó‘Ô‚ð•Û‘¶
@REM ‘O”ÍˆÍ¨Shift+V ‚ÅŠm’è
REM #jww
REM #h1
REM #g1
REM #gn
REM #e
@echo off
if not exist "%~dp0layerdump" mkdir "%~dp0layerdump"
python "%~dp0dump_layers.py" A > "%~dp0layerdump\log_A.txt" 2>&1
if not errorlevel 1 goto :done
py "%~dp0dump_layers.py" A >> "%~dp0layerdump\log_A.txt" 2>&1
:done
