# Proposal: Windows 10 Offline Installation Package

- Status: ✅ APPROVED
- Author: Codex (Developer Agent)
- Date: 2026-08-10

## 1. Background and objective

Allow RT DICOM Toolkit to be installed on an offline Windows 10 x64 computer
from USB storage. On an online computer, collect the official CPython installer,
Windows wheels, and repository application in one ZIP. On the offline computer,
install into a dedicated virtual environment without external communication.

The design follows an approach previously validated by a related project while
using the dependencies and launch procedures specific to this repository.

## 2. Investigation

### 2.1 Supported Python range

- `setup.py` originally declared `python_requires=">=3.6"`.
- The root README required Python 3.10 or later while the legacy
  `docs/readme.md` stated 3.6 or later.
- No syntax newer than Python 3.10 was found in runtime code.
- `matplotlib 3.10.3` requires Python 3.10 or later, making 3.10 the effective
  minimum for current dependencies.
- The fixed Windows offline target is **CPython 3.12.10 64-bit**.
- All nine tests present at investigation time passed on CPython 3.12.10 x64.

### 2.2 Runtime dependencies

Imports, `setup.py`, requirement files, the README, and the active environment
were compared.

- Core: `pydicom`, `numpy`, `pandas`, `matplotlib`
- Standard GUI: `customtkinter`
- `customtkinter` dependencies: `darkdetect`, `packaging`
- Transitive `matplotlib` and `pandas` dependencies: `contourpy`, `cycler`,
  `fonttools`, `kiwisolver`, `pillow`, `pyparsing`, `python-dateutil`, `six`,
  `pytz`, and `tzdata`

At investigation time, `setup.py` and `rt_dicom_toolkit/requirements.txt` did
not include `customtkinter`; only the README's manual installation command did.
That inconsistency had to be resolved.

The directly tested versions were:

- `pydicom==2.4.4`
- `numpy==1.26.4`
- `pandas==2.3.1`
- `matplotlib==3.10.3`
- `customtkinter==5.2.2`
- `darkdetect==0.8.0`

The offline lock also pins every resolved transitive dependency exactly.

## 3. Changes

### 3.1 Dependencies and package metadata

- Align the `setup.py` Python minimum with 3.10 and add the standard GUI's
  direct `customtkinter` dependency.
- Align runtime requirements with current code.
- Add a fully pinned CPython 3.12 / Windows x64 requirement file.

### 3.2 Online bundle construction

Add a PowerShell script that:

1. confirms Windows, CPython 3.12, and a 64-bit process;
2. downloads the CPython 3.12.10 x64 installer from python.org;
3. verifies its Authenticode signature and signer;
4. downloads only CPython 3.12 `win_amd64` wheels from PyPI;
5. builds the repository application wheel;
6. creates a SHA-256 manifest for Python, every wheel, and installation,
   startup, and smoke-test files; and
7. creates the USB-transfer ZIP under `dist/`.

Build the application payload from Git-tracked files and exclude `DICOM/`,
`DICOM_LOGS/`, `.git/`, virtual environments, and caches so patient data and
local artifacts cannot enter the bundle.

### 3.3 Offline installation and launch

- `install_offline.bat`
  - Verify the bundle SHA-256 manifest.
  - If CPython 3.12.10 x64 is unavailable, install the bundled Python silently
    into a dedicated local runtime. Use an existing compatible Python only to
    create the dedicated environment.
  - Create a bundle-local `.venv`.
  - Set `PIP_NO_INDEX=1` and `PIP_CONFIG_FILE=nul`, and use `--isolated`,
    `--no-index`, and `--find-links` so installation can use only bundled
    wheels.
  - Run `pip check` and import checks.
- `start_rt_dicom_toolkit.bat`
  - Launch the GUI only with the dedicated `.venv` `pythonw.exe`.
- `smoke_test.bat`
  - Run the synthetic-DICOM smoke test with the dedicated `.venv`.

Instructions require copying and extracting the bundle to a writable local
folder rather than running it directly from USB storage.

### 3.4 Synthetic-DICOM smoke test

Create minimal synthetic DICOM in a temporary directory at runtime, without any
patient-derived data, and verify:

- anonymization processes Patient Name, Patient ID, UIDs, and private tags as
  expected and produces standard DICOM that can be read again;
- validation compares before and after data and observes changed key tags plus
  preserved structure and Pixel Data;
- the Universal Template synchronizes selected patient and geometry data and
  creates a new SOP Instance UID; and
- `tkinter`, `customtkinter`, and the matplotlib Tk backend can be imported.

### 3.5 Documentation

Document online bundle construction, USB transfer, offline installation,
launch, smoke testing, logs, reinstallation, and common troubleshooting.

## 4. Impact and risks

- Adding `customtkinter` aligns package installation with standard GUI use and
  does not change core processing logic.
- The target is Windows 10 x64. Windows 32-bit and ARM64 are out of scope.
- The bundle is fixed to the CPython 3.12 ABI so it can reuse the same wheels.
  Normal source use continues to support Python 3.10 or later.
- The Python installation must include Tcl/Tk for the GUI.
- Authenticode validation assumes a healthy Windows certificate store on the
  online construction computer.
- The bundled SHA-256 manifest detects transfer corruption. Bundle authenticity
  requires comparing the ZIP hash with a value published through a separate
  channel.
- Historical untracked DICOM directories were explicitly excluded and not
  inspected.
- Unrelated user changes were preserved.

## 5. Validation plan

1. Rerun the existing nine tests on CPython 3.12.10 x64.
2. Automatically test dependency definitions, wheel pins, offline batch flags,
   and patient-data exclusions.
3. Run the synthetic-DICOM smoke test in the normal environment.
4. Build a real bundle ZIP and confirm every file is an allowed bundled item or
   wheel and every SHA-256 matches.
5. Extract into a new local folder and validate installation without network
   dependencies.
6. Run `pip check`, the smoke test, and GUI import from the dedicated `.venv`.

Automated tests do not drive the GUI. The launch batch and GUI imports are
automatic; final display is a Windows 10 offline-machine checklist item.

## 6. Implementation and validation results

- Date: 2026-08-10
- All 17 pytest tests passed on CPython 3.12.10 x64.
- The official Python 3.12.10 x64 installer had a `Valid` Authenticode signature
  from the Python Software Foundation.
- The bundle contained 17 pinned dependency wheels and one application wheel.
- SHA-256 verification passed for all 59 ZIP payload files.
- With HTTP, HTTPS, ALL proxy, and pip index settings redirected to unreachable
  `127.0.0.1:9`, creation of the dedicated `.venv`, isolated no-index
  installation, `pip check`, and the synthetic-DICOM smoke test all passed.
- Environments with a missing `python.exe` or a replaced non-Python executable
  were detected and recreated. Existing data integrity and same-version package
  repair were confirmed by SHA-256 checks.
- The dedicated environment used 64-bit Python 3.12.10 and imported the
  application from that environment's `site-packages`.
- A user confirmed installation, startup, and normal GUI use on a physically
  disconnected Windows 10 computer.

Generated artifact record:

```text
dist/rt-dicom-toolkit-offline-win64-1.0.0.zip
source commit: 898e2d8adc3060764041fb6814cd59597cac594d
SHA-256: bb4912e2286ed60ed1ade7aee9a86b00f09b4beeb5dbe3df7d86ad71eca8e642
```
