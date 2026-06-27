@echo off
REM ============================================================================
REM  MWA2 - Create Characters
REM  Opens the AA2 character editor with the shared PPeX asset server running
REM  (bodies/faces live in the PPeX archives, so the editor needs it). Bundled
REM  Python; self-elevates like Play.bat.
REM ============================================================================

net session >nul 2>&1
if %errorlevel% neq 0 (
    echo Requesting administrator rights ...
    powershell -Command "Start-Process -FilePath '%~f0' -Verb RunAs"
    exit /b
)

cd /d "%~dp0"
"%~dp0system\python\python.exe" "%~dp0system\app\run_edit.py"
echo.
echo [editor closed] - press any key to close.
pause >nul
