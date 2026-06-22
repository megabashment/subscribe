@echo off
cd /d "%~dp0"
start "SubScribe API" cmd /k "C:\Users\chris\projects\venv\Scripts\uvicorn api.server:app --port 8511 --reload"
start "SubScribe UI" cmd /k "cd /d "%~dp0frontend" && npm run dev"
