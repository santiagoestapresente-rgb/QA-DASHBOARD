@echo off
cd /d "%~dp0\.."
echo.
echo DiDi CX Dashboard v2  -  http://127.0.0.1:8000
echo Leave this window open. Close it to stop the server.
echo First time only, if import fails:
echo   python -m pip install -r dashboard_v2\backend\requirements.txt
echo.
C:\Users\PC\AppData\Local\Programs\Python\Python311\python.exe -m uvicorn dashboard_v2.backend.main:app --reload --port 8000
