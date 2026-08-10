@echo off
setlocal EnableExtensions DisableDelayedExpansion
chcp 65001 >nul 2>&1
cd /d "%~dp0"
set "PYTHONUTF8=1"
set "MPLBACKEND=Agg"

if not exist "%~dp0.venv\Scripts\python.exe" (
  echo ERROR: Dedicated virtual environment was not found. 1>&2
  echo Run install_offline.bat first. 1>&2
  exit /b 1
)

"%~dp0.venv\Scripts\python.exe" "%~dp0tools\offline_smoke_test.py"
exit /b %ERRORLEVEL%
