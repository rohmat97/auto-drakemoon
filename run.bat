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

:loop
echo Running Drake.py...
set PYTHONIOENCODING=utf-8
py -3.12-32 Drake.py

:: Check if the Python script requested a restart (exit code 5)
if %errorlevel% equ 5 (
    echo.
    echo Reached 5 battles limit. Restarting Drake.py in a new console in 5 seconds...
    timeout /t 5
    start run.bat
    exit
)

pause
