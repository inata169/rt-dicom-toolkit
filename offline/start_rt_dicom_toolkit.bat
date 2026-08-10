@echo off
setlocal EnableExtensions DisableDelayedExpansion
chcp 65001 >nul 2>&1
cd /d "%~dp0"
set "PYTHONHOME="
set "PYTHONPATH="
set "PYTHONUTF8=1"

if not exist "%~dp0.venv\Scripts\pythonw.exe" (
  echo ERROR: Dedicated virtual environment was not found. 1>&2
  echo Run install_offline.bat first. 1>&2
  pause
  exit /b 1
)

start "RT DICOM Toolkit" "%~dp0.venv\Scripts\pythonw.exe" -m rt_dicom_toolkit
exit /b 0
