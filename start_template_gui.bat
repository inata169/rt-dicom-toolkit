@echo off
set PYTHONUTF8=1
set PYTHONPATH=%~dp0
python -m rt_dicom_toolkit.gui.template_gui
pause
