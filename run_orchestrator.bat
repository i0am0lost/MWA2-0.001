@echo off
REM ============================================================================
REM  AA2 Jail Orchestrator - self-elevating launcher
REM  Runs the orchestrator as Administrator so BlockInput works (the user's mouse
REM  is frozen during jail's ~3s click sequence, so a stray move can't divert it).
REM  Double-click this; accept the UAC prompt.
REM ============================================================================

REM Already elevated? (net session only succeeds as admin)
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo Requesting administrator rights ...
    powershell -Command "Start-Process -FilePath '%~f0' -Verb RunAs"
    exit /b
)

cd /d "%~dp0"
set "PY=python"
if not exist "%PY%" set "PY=py"
"%PY%" "%~dp0orchestrator.py"
echo.
echo [orchestrator exited] - press any key to close.
pause >nul
