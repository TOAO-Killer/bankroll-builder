@echo off
cd /d "%~dp0"
set PYTHONPATH=%~dp0scripts;%PYTHONPATH%
"C:\Users\marcu\AppData\Local\Programs\Python\Python312\python.exe" -m bankroll capital dashboard --host 127.0.0.1 --port 8080
