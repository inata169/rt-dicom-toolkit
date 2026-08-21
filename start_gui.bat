@echo off
setlocal EnableExtensions DisableDelayedExpansion
cd /d "%~dp0"
set "PYTHONUTF8=1"
set "VENV_PYTHON=%~dp0.venv\Scripts\python.exe"

if not exist "%VENV_PYTHON%" (
  echo ERROR: The development virtual environment was not found.
  echo.
  echo From PowerShell in this repository, run:
  echo   python -m venv .venv
  echo   .\.venv\Scripts\python.exe -m pip install --upgrade pip setuptools wheel
  echo   .\.venv\Scripts\python.exe -m pip install -r .\rt_dicom_toolkit\requirements.txt
  echo   .\.venv\Scripts\python.exe -m pip install -e .
  echo.
  pause
  exit /b 1
)

"%VENV_PYTHON%" -m rt_dicom_toolkit
set "EXIT_CODE=%ERRORLEVEL%"
if not "%EXIT_CODE%"=="0" (
  echo.
  echo ERROR: RT DICOM Toolkit exited with code %EXIT_CODE%.
  pause
)
exit /b %EXIT_CODE%
