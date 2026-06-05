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
    echo Reached battles limit. Restarting Drake.py in 2 seconds...
    timeout /t 2
    echo.
    goto loop
)

pause
