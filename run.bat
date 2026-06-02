@echo off
:: Check for Administrator privileges
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo Requesting administrative privileges...
    powershell -Command "Start-Process -FilePath '%0' -Verb RunAs"
    exit /b
)

:: Change directory to the folder containing this batch file
cd /d "%~dp0"

echo Running Drake.py...
set PYTHONIOENCODING=utf-8
py -3.12-32 Drake.py

pause
