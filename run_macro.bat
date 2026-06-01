@echo off
:: Check for admin rights
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo Requesting Administrator privileges...
    powershell -Command "Start-Process -Verb RunAs -FilePath '%~f0'"
    exit /b
)

:: Elevated code runs below
cd /d "%~dp0"
chcp 65001 > nul
set PYTHONIOENCODING=utf-8
"C:\Users\rd\Documents\exploration\test\python-32\python.exe" "Drake.py"
pause
