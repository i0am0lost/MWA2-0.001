@echo off
REM ============================================================================
REM  MWA2 - Memory Tool
REM  Inspect / tune the per-playthrough SSOT memory (the cross-world brain) without
REM  grinding the game. No admin needed. Bundled Python.
REM
REM  Examples:
REM    "Memory Tool.bat"                          overview of every character
REM    "Memory Tool.bat" show "Kuroda Katsuki"    detail + resolver reasoning
REM    "Memory Tool.bat" set "Kuroda Katsuki" climax 40    force a counter
REM    "Memory Tool.bat" resolve                  re-resolve + push the char_state flag
REM ============================================================================

cd /d "%~dp0"
if "%~1"=="" (
    "%~dp0system\python\python.exe" "%~dp0system\app\debug_tool.py"
    echo.
    echo Tip: "Memory Tool.bat" show "Name"  ^|  set "Name" metric value  ^|  resolve
    echo.
    pause
) else (
    "%~dp0system\python\python.exe" "%~dp0system\app\debug_tool.py" %*
)
