@echo off
REM ============================================================================
REM  MWA2 - First-time setup / environment check
REM  Python is BUNDLED (system\python) - nothing to install there. This checks the
REM  one external requirement (.NET runtime, for the PPeX asset server) and tells
REM  you what to do if it's missing.
REM ============================================================================
setlocal
cd /d "%~dp0"
echo ============================================================
echo   MWA2 - setup check
echo ============================================================
echo.
echo [1/2] Python (bundled in system\python) ...
"%~dp0system\python\python.exe" --version
if %errorlevel% neq 0 (
    echo   ERROR: bundled Python did not run. The package may be incomplete.
) else (
    echo   OK - no separate Python install needed.
)
echo.
echo [2/2] .NET runtime (needed by the shared PPeX asset server) ...
where dotnet >nul 2>&1
if %errorlevel%==0 (
    echo   OK - dotnet found:
    dotnet --version
) else (
    echo   MISSING - 'dotnet' is not on PATH.
    echo   Install the .NET Runtime ^(3.1 or newer^) from:
    echo       https://dotnet.microsoft.com/download
    echo   then run this again.
)
echo.
echo ============================================================
echo   Done. Start the game with  Play.bat
echo ============================================================
echo.
pause
endlocal
