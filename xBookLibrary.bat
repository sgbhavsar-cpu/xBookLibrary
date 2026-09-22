@echo off
title xBookLibrary v1.2.9.22
cd /d "%~dp0"

echo =========================================================
echo   Starting xBookLibrary v1.2.9.22...
echo   Calibre-Compatible AI Book Library Platform
echo =========================================================

if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" run_xBookLibrary.py
) else (
    uv run python run_xBookLibrary.py
)

pause
