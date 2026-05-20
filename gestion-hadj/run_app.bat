@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo [INFO] Environnement virtuel non detecte. Utilisation de python systeme.
    python main.py
) else (
    ".venv\Scripts\python.exe" main.py
)

endlocal
