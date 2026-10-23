@echo off
title Smart Expense Tracker & AI Financial Advisor
cd /d "%~dp0"
echo ==========================================================
echo   Smart Expense Tracker ^& AI Financial Advisor
echo ==========================================================
echo.
echo Activating virtual environment...
if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
) else (
    echo [!] Virtual environment not found. Using system python.
)

echo Starting application server...
echo Local URL:   http://localhost:5000
echo Mobile/LAN:  http://0.0.0.0:5000
echo.
python run.py
pause
