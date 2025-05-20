@echo off
title 🔒 Starter Nummerplade Sløring v2.5
echo ================================
echo 📦 Tjekker Python...
echo ================================

where python >nul 2>&1
if errorlevel 1 (
    echo ❌ Python er ikke installeret. Hent det her: https://www.python.org/downloads
    pause
    exit /b
)

echo ✅ Python fundet!
echo ================================
echo 📦 Installerer requirements...
echo ================================
pip install -r requirements.txt

echo ================================
echo 🌍 Åbner webside...
echo ================================
start http://127.0.0.1:5000

echo ================================
echo 🚀 Starter Flask server...
echo ================================
python app.py

echo.
pause
