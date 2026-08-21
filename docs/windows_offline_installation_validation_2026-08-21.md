# Windows 11 Offline Bundle Validation Record (2026-08-21)

## Target

- Repository: `inata169/rt-dicom-toolkit`
- Release: `v0.0.0`
- Bundle: `rt-dicom-toolkit-offline-win64-0.0.0.zip`
- Source commit: `be7875d5b66534b9c10f7c41835df57d9b0977ac`
- Bundle SHA-256:
  `53d675175609e68799285292e0a2aa207d7341650dd46814a57e9dc1fe5d860c`
- OS: Windows 11 x64, upgraded from Windows 10
- Installation location: a writable local-disk folder

## Artifact origins and license review

- The CPython installer was downloaded by the bundle builder from
  `https://www.python.org/ftp/python/3.12.10/python-3.12.10-amd64.exe`.
  Its Authenticode signature was valid and identified the Python Software
  Foundation. CPython is distributed under the Python Software Foundation
  License Version 2.
- The 17 third-party wheels were downloaded from the official
  `https://pypi.org/simple` index using the exact versions in
  [`../requirements/offline-win64-py312.txt`](../requirements/offline-win64-py312.txt).
  The license labels below were reviewed from each bundled wheel's
  `.dist-info/LICENSE*` files and `METADATA`. Bundled third-party notices remain
  inside the respective wheels.
- The application wheel was built locally from the source commit recorded
  above and is covered by the repository's [MIT License](../LICENSE).

| Bundled package | Version | Reviewed license |
|---|---:|---|
| contourpy | 1.3.3 | BSD-3-Clause |
| customtkinter | 5.2.2 | MIT |
| cycler | 0.12.1 | BSD-3-Clause |
| darkdetect | 0.8.0 | BSD-3-Clause |
| fonttools | 4.59.0 | MIT; bundled external notices |
| kiwisolver | 1.4.8 | BSD-3-Clause |
| matplotlib | 3.10.3 | Matplotlib License |
| numpy | 1.26.4 | BSD-3-Clause; bundled third-party notices |
| packaging | 25.0 | Apache-2.0 or BSD-2-Clause |
| pandas | 2.3.1 | BSD-3-Clause |
| pillow | 12.0.0 | MIT-CMU |
| pydicom | 2.4.4 | MIT |
| pyparsing | 3.2.3 | MIT |
| python-dateutil | 2.9.0.post0 | Apache-2.0 or BSD-3-Clause |
| pytz | 2025.2 | MIT |
| six | 1.17.0 | MIT |
| tzdata | 2025.2 | Apache-2.0 |
| rt-dicom-toolkit | 0.0.0 | MIT |

## Human-observed validation

A human completed `install_offline.bat` for the `v0.0.0` bundle on the Windows
11 computer and launched the RT DICOM Anonymizer GUI. The installer reports
success only after running the bundled
[`offline_smoke_test.py`](../tools/offline_smoke_test.py), which creates a
minimal project-authored synthetic CT DICOM at runtime, exercises anonymization,
validation, and template synchronization, and removes the synthetic files at
completion.

The human also observed a separate anonymization run reporting
`Processing complete` and producing output, a text log, and a JSON summary.
Because the provenance of that separately selected input was not independently
captured in this repository, the run is recorded only as a supplementary
observation and is not used as formal DICOM-validation evidence. No input path,
metadata, or DICOM content from that run is recorded here.

The admissible evidence therefore confirms bundle installation, the bundled
synthetic-DICOM smoke test, and application launch on that Windows 11 x64
computer. It does not record a disconnected network test, every toolkit GUI, or
the newly documented removal procedure.
