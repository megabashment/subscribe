@echo off
cd /d "%~dp0"
C:\Users\chris\projects\venv\Scripts\uvicorn api.server:app --port 8511 --reload
pause
