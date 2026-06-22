@echo off
cd /d "%~dp0"
C:\Users\chris\projects\venv\Scripts\streamlit run ui.py --server.port 8510 --server.headless false
pause
