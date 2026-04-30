@echo off
set PYTHONUTF8=1
python check_anonymization_gui.py
if %ERRORLEVEL% neq 0 pause
