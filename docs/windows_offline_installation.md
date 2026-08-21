# Windows 10 Offline Installation

This procedure installs RT DICOM Toolkit on a Windows 10 x64 computer without
internet access by using USB storage. Do not use patient-derived DICOM for
installation validation. The bundled smoke test generates synthetic DICOM at
runtime.

## Target environment

- Online computer: Windows 10/11 x64, PowerShell 5.1 or later, CPython 3.12 x64,
  and pip.
- Offline computer: Windows 10 x64.
- Bundled Python: CPython 3.12.10 x64.
- Installation location: a dedicated `.venv` inside the locally extracted
  bundle.

Windows 32-bit, Windows ARM64, and non-Windows systems are outside this bundle's
scope.

## 1. Build the ZIP on an online computer

Open PowerShell at the repository root. Use a reviewed commit or working tree
and confirm that no real-patient DICOM is tracked.

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\prepare_offline_bundle.ps1
```

The build Python needs `pip`, `setuptools`, and `wheel`. If they are missing,
install them on the online computer and retry:

```powershell
python -m pip install --upgrade pip setuptools wheel
```

Add `-Force` only when intentionally replacing an existing ZIP with the same
name:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\prepare_offline_bundle.ps1 -Force
```

Output:

```text
dist\rt-dicom-toolkit-offline-win64-0.0.0.zip
```

The script:

1. verifies that the build interpreter is CPython 3.12 x64;
2. downloads the Python 3.12.10 x64 installer from python.org;
3. verifies the Python installer's Authenticode signature and signer;
4. downloads only pinned Windows x64 wheels from PyPI;
5. builds the RT DICOM Toolkit wheel;
6. creates SHA-256 entries for runtime source, batch files, documentation,
   wheels, and Python; and
7. creates a ZIP suitable for USB transfer.

Record the displayed ZIP SHA-256 somewhere separate from the USB device. The
bundled `SHA256SUMS.txt` detects transfer corruption. Authenticating the ZIP
itself requires comparison with the separately recorded hash.

## 2. Copy the bundle to USB storage

Copy this file:

```text
dist\rt-dicom-toolkit-offline-win64-0.0.0.zip
```

When practical, verify the copied ZIP:

```powershell
Get-FileHash .\rt-dicom-toolkit-offline-win64-0.0.0.zip -Algorithm SHA256
```

Patient DICOM and local `DICOM/` or `DICOM_LOGS/` directories are not included.

## 3. Install on the offline computer

1. Copy the ZIP from USB storage to an empty writable folder on a local disk.
2. Extract it into that folder. Do not install directly from USB storage.
3. Double-click `install_offline.bat` in the extracted folder.

Administrator permission is normally unnecessary. The installer:

- validates every bundled file against `SHA256SUMS.txt`;
- checks for CPython 3.12.10 x64 and installs the bundled runtime under
  `.runtime` when no compatible Python is available;
- creates the dedicated `.venv`;
- installs dependencies and the application only from `wheelhouse`;
- runs `pip check`; and
- runs the synthetic-DICOM smoke test.

pip always receives these network-blocking settings:

```text
PIP_NO_INDEX=1
PIP_CONFIG_FILE=nul
--no-index
--find-links <bundled-wheelhouse>
--only-binary=:all:
```

The offline installation therefore does not contact PyPI or another package
index.

## 4. Launch the application

Double-click `start_rt_dicom_toolkit.bat`. It launches the GUI with the
dedicated `.venv\Scripts\pythonw.exe` and does not use the system PATH. If an
existing compatible Python created the environment, launch still uses the
dedicated virtual environment.

Before processing operational DICOM, review the governing data-handling policy,
anonymization requirements, output location, and access permissions. A passing
smoke test does not guarantee anonymization quality for every vendor, modality,
or local workflow.

## 5. Rerun the smoke test

Double-click `smoke_test.bat`. Success prints:

```text
SMOKE TEST PASSED: anonymizer, validator, template engine, and GUI imports
```

The test creates minimal synthetic CT DICOM in a temporary folder and checks:

- output creation and standard-DICOM readback;
- Patient Name, Patient ID, SOP Instance UID, and private-tag processing;
- Pixel Data preservation;
- comparison and validation-report generation;
- Universal Template patient/geometry synchronization and UID generation; and
- imports of `tkinter`, CustomTkinter, and the matplotlib Tk backend.

Temporary test data is removed when the test finishes.

## 6. Troubleshooting

### SHA-256 mismatch

Extraction, USB transfer, or a file modification may have corrupted the bundle.
Stop installation and recopy the original ZIP from the online computer. Never
disable integrity validation to continue.

### Python installation failed

Confirm that the extraction folder is writable, free disk space is sufficient,
and Windows is x64. Use a local disk rather than USB or a network drive.

### Offline wheel installation failed

Confirm that no file under `wheelhouse` was modified or deleted. Do not manually
install these wheels into a Python version other than 3.12.

### The GUI does not appear

Run `smoke_test.bat` first. If it succeeds but no window appears, inspect Windows
Event Viewer, security-product blocking, and whether Windows restored the GUI
outside the visible desktop.

## 7. Reinstall or remove

Running `install_offline.bat` again in the same extracted directory verifies and
updates the environment from bundled wheels. Default input, output, log, and
report locations are in the extracted directory's `data` folder, separate from
the virtual environment.

Data created inside a legacy virtual environment is moved to the extracted
directory's `data`. If that destination already exists, it is moved to
`data\legacy-venv-data`. If the backup destination also exists, installation
stops instead of deleting data.

For a completely clean reinstall or removal, first close every toolkit window
and move the extracted `data` directory to an approved secure location if it
must be retained. If `.runtime\python.exe` exists, the bundle installed a
private Python runtime that is also registered with Windows. Open **Windows
Settings > Apps > Apps & features** and uninstall the **Python 3.12.10 (64-bit)**
entry associated with this bundle before deleting files. If `.runtime` does not
exist, do not remove the compatible Python installation that was already on the
computer.

Finally, remove only the verified extracted bundle folder. For a reinstall,
extract the original ZIP into a new writable local-disk folder. Output folders
selected outside the bundle are not removed by this process.
