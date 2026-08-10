@echo off
setlocal EnableExtensions DisableDelayedExpansion
chcp 65001 >nul 2>&1
cd /d "%~dp0"

set "BUNDLE_ROOT=%~dp0"
set "RTDT_BUNDLE_ROOT=%~dp0"
set "PYTHON_INSTALLER=%BUNDLE_ROOT%python\python-3.12.10-amd64.exe"
set "PRIVATE_PYTHON=%BUNDLE_ROOT%.runtime\python.exe"
set "VENV_PYTHON=%BUNDLE_ROOT%.venv\Scripts\python.exe"
set "BASE_PYTHON="
set "WHEELHOUSE=%BUNDLE_ROOT%wheelhouse"
set "TRUSTED_POWERSHELL=%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe"
set "PIP_NO_INDEX=1"
set "PIP_CONFIG_FILE=NUL"
set "PIP_DISABLE_PIP_VERSION_CHECK=1"
set "PYTHONUTF8=1"

echo RT DICOM Toolkit offline installer
echo.
echo This folder must be copied from USB to a writable local-disk folder.
echo No internet connection is used by this installer.
echo.

if not exist "%BUNDLE_ROOT%SHA256SUMS.txt" (
  echo ERROR: SHA256SUMS.txt is missing. 1>&2
  exit /b 1
)
if not exist "%TRUSTED_POWERSHELL%" (
  echo ERROR: Windows PowerShell was not found in the system directory. 1>&2
  exit /b 1
)

echo [1/6] Verifying bundle SHA-256 checksums...
"%TRUSTED_POWERSHELL%" -NoLogo -NoProfile -NonInteractive -ExecutionPolicy Bypass -Command ^
  "$ErrorActionPreference='Stop';$root=[IO.Path]::GetFullPath($env:RTDT_BUNDLE_ROOT);$prefix=$root.TrimEnd([IO.Path]::DirectorySeparatorChar)+[IO.Path]::DirectorySeparatorChar;$inventory=[Collections.Generic.HashSet[string]]::new([StringComparer]::OrdinalIgnoreCase);$lines=Get-Content -LiteralPath (Join-Path $root 'SHA256SUMS.txt') -Encoding UTF8;foreach($line in $lines){if([string]::IsNullOrWhiteSpace($line)){continue};if($line -notmatch '^([0-9a-f]{64}) \*(.+)$'){throw ('Invalid checksum line: '+$line)};$expected=$matches[1];$relative=$matches[2].Replace('/',[IO.Path]::DirectorySeparatorChar);if([IO.Path]::IsPathRooted($relative)-or $relative.Contains(':')){throw ('Unsafe checksum path: '+$relative)};$full=[IO.Path]::GetFullPath((Join-Path $root $relative));if(-not $full.StartsWith($prefix,[StringComparison]::OrdinalIgnoreCase)){throw ('Checksum path escapes bundle: '+$relative)};$key=$full.Substring($prefix.Length).Replace([IO.Path]::DirectorySeparatorChar,'/');if(-not $inventory.Add($key)){throw ('Duplicate checksum path: '+$key)};if(-not [IO.File]::Exists($full)){throw ('Missing bundle file: '+$key)};$actualHash=(Get-FileHash -LiteralPath $full -Algorithm SHA256).Hash.ToLowerInvariant();if($actualHash -ne $expected){throw ('SHA-256 mismatch: '+$key)}};if($inventory.Count -eq 0){throw 'Checksum inventory is empty'};$payload=@(Get-ChildItem -LiteralPath $root -Force|Where-Object{$_.Name -notin @('.venv','.runtime','SHA256SUMS.txt')}|ForEach-Object{if($_.PSIsContainer){Get-ChildItem -LiteralPath $_.FullName -Recurse -Force -File}else{$_}});foreach($file in $payload){$key=$file.FullName.Substring($prefix.Length).Replace([IO.Path]::DirectorySeparatorChar,'/');if(-not $inventory.Contains($key)){throw ('Unexpected bundle file: '+$key)}};if($payload.Count -ne $inventory.Count){throw ('Bundle inventory count mismatch: expected '+$inventory.Count+', found '+$payload.Count)};Write-Host ('Verified '+$inventory.Count+' files and rejected unlisted payloads.')"
if errorlevel 1 (
  echo ERROR: Bundle verification failed. 1>&2
  exit /b 1
)

if not exist "%PYTHON_INSTALLER%" (
  echo ERROR: Bundled Python installer is missing. 1>&2
  exit /b 1
)

call :select_python "%PRIVATE_PYTHON%"
call :select_python "%LocalAppData%\Programs\Python\Python312\python.exe"
call :select_python "%ProgramFiles%\Python312\python.exe"

if not defined BASE_PYTHON (
  echo [2/6] Installing bundled CPython 3.12.10 runtime...
  "%PYTHON_INSTALLER%" /quiet InstallAllUsers=0 TargetDir="%BUNDLE_ROOT%.runtime" Include_launcher=0 Include_test=0 Include_doc=0 Shortcuts=0 AssociateFiles=0 PrependPath=0 Include_tcltk=1 Include_pip=1
  if errorlevel 1 (
    echo ERROR: Bundled Python installation failed. 1>&2
    exit /b 1
  )
  call :select_python "%PRIVATE_PYTHON%"
  call :select_python "%LocalAppData%\Programs\Python\Python312\python.exe"
  call :select_python "%ProgramFiles%\Python312\python.exe"
) else (
  echo [2/6] Using compatible CPython 3.12.10 x64: %BASE_PYTHON%
)

if not defined BASE_PYTHON (
  echo ERROR: CPython 3.12.10 x64 is unavailable after installation. 1>&2
  exit /b 1
)

if not exist "%VENV_PYTHON%" (
  echo [3/6] Creating dedicated virtual environment...
  "%BASE_PYTHON%" -m venv "%BUNDLE_ROOT%.venv"
  if errorlevel 1 (
    echo ERROR: Virtual environment creation failed. 1>&2
    exit /b 1
  )
) else (
  echo [3/6] Dedicated virtual environment already exists.
)

echo [4/6] Installing only from the bundled wheelhouse...
"%VENV_PYTHON%" -m pip install --no-index --find-links "%WHEELHOUSE%" --only-binary=:all: --upgrade --force-reinstall rt-dicom-toolkit==1.0.0
if errorlevel 1 (
  echo ERROR: Offline wheel installation failed. 1>&2
  exit /b 1
)

echo [5/6] Checking installed dependencies...
"%VENV_PYTHON%" -m pip check
if errorlevel 1 (
  echo ERROR: pip check failed. 1>&2
  exit /b 1
)

echo [6/6] Running synthetic-DICOM smoke test...
call "%BUNDLE_ROOT%smoke_test.bat"
if errorlevel 1 (
  echo ERROR: Smoke test failed. 1>&2
  exit /b 1
)

echo.
echo Installation and smoke test completed successfully.
echo Start the application with start_rt_dicom_toolkit.bat.
exit /b 0

:select_python
if defined BASE_PYTHON exit /b 0
if not exist "%~1" exit /b 0
"%~1" -c "import struct,sys,tkinter; raise SystemExit(0 if sys.version_info[:3] == (3,12,10) and struct.calcsize('P')*8 == 64 else 1)" >nul 2>&1
if not errorlevel 1 set "BASE_PYTHON=%~1"
exit /b 0
