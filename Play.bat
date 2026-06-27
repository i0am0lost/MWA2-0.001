@echo off
REM ============================================================================
REM  MWA2 - Play (Jail Mode)
REM  Starts the two-world orchestrator (school + jail). Self-elevates to admin:
REM  the input is briefly locked during jail's ~3s auto-click sequence so a stray
REM  mouse move can't divert it. Accept the UAC prompt. Python is bundled - no
REM  separate install needed.
REM ============================================================================

net session >nul 2>&1
if %errorlevel% neq 0 (
    echo Requesting administrator rights ...
    powershell -Command "Start-Process -FilePath '%~f0' -Verb RunAs"
    exit /b
)

cd /d "%~dp0"
"%~dp0system\python\python.exe" "%~dp0system\app\orchestrator.py"
echo.
echo [MWA2 exited] - press any key to close.
pause >nul
