@echo off
setlocal
cd /d "%~dp0"

if exist ".venv\Scripts\python.exe" (
    set PYTHON_EXE=.venv\Scripts\python.exe
) else (
    set PYTHON_EXE=python
)

echo [INFO] Installation/verif de pyinstaller...
%PYTHON_EXE% -m pip install pyinstaller

echo [INFO] Build executable en cours...
%PYTHON_EXE% -m PyInstaller ^
  --noconfirm ^
  --windowed ^
  --name GestionHadj ^
  --add-data "assets;assets" ^
  --add-data "data;data" ^
  main.py

echo [OK] Build termine. Voir dossier dist\GestionHadj\
endlocal
