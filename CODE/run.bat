@echo off
REM Clinical Documentation Assistant - Windows Batch File
REM This script starts the Flask web application

echo ============================================================
echo Clinical Documentation Assistant - Web Version
echo ============================================================
echo.
echo Installing dependencies...
pip install -r requirements.txt -q

echo.
echo Starting Flask server...
echo.
echo Open your browser to: http://localhost:5000
echo.
echo Press Ctrl+C to stop the server
echo ============================================================
echo.

python APP_WEB_IMPROVED.py

pause
