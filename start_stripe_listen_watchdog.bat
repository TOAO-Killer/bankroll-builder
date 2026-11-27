@echo off
cd /d "%~dp0"
set PYTHONPATH=%~dp0scripts;%PYTHONPATH%
"C:\Users\marcu\AppData\Local\Programs\Python\Python312\python.exe" scripts\stripe_listen_watchdog.py --replace
