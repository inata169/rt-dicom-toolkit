# Windows 10 Offline Installation Validation Record (2026-08-10)

## Target

- Repository: `inata169/rt-dicom-toolkit`
- Bundle: `rt-dicom-toolkit-offline-win64-1.0.0.zip`
- Source commit: `898e2d8adc3060764041fb6814cd59597cac594d`
- Bundle SHA-256:
  `bb4912e2286ed60ed1ade7aee9a86b00f09b4beeb5dbe3df7d86ad71eca8e642`
- Python: CPython 3.12.10 x64
- OS: Windows 10 x64

## Automated validation

Bundle construction ran with invalid paths in `PYTHONHOME` and `PYTHONPATH` and
with `PIP_REQUIRE_VIRTUALENV=1`. This confirmed that producer Python,
dependency retrieval, and application-wheel construction were isolated from an
inherited environment.

In the development environment, all external destinations were redirected to
unreachable `127.0.0.1:9`, and `PIP_FIND_LINKS`, `PIP_INDEX_URL`, and
`PIP_EXTRA_INDEX_URL` were set to unreachable URLs before running the extracted
`install_offline.bat`. Invalid `PYTHONHOME` and `PYTHONPATH` values additionally
tested batch-file environment isolation.

| Check | Result |
|---|---|
| Python installer Authenticode signature | PASS, Python Software Foundation |
| SHA-256 for 59 ZIP payload files | PASS |
| 17 pinned dependency wheels plus one application wheel | PASS |
| Dedicated `.venv` creation | PASS |
| `--isolated --no-index` wheel installation | PASS |
| Preserve data and recreate `.venv` with missing `python.exe` | PASS |
| Detect and recreate `.venv` containing a non-Python replacement executable | PASS |
| Preserve legacy `.venv` data with matching SHA-256 | PASS |
| Force reinstall after same-version application-file corruption | PASS |
| `pip check` | PASS |
| Synthetic-DICOM anonymization | PASS |
| Before/after validation | PASS |
| Universal Template synchronization | PASS |
| GUI dependency imports | PASS |
| pytest | 17 passed |

The smoke test used only minimal synthetic CT DICOM generated at runtime and
deleted at completion. It did not use real-patient data.

## Offline Windows 10 machine check

On 2026-08-10, the user reported:

- successful GUI installation on a Windows 10 computer with no internet
  connection;
- successful launch from the dedicated environment; and
- successful normal GUI operation.

The exact Windows build number was not collected in this record.

## Conclusion

The validated bundle supported USB transfer, installation on an offline Windows
10 x64 computer, execution in a dedicated virtual environment, and use of its
primary functions.

After changing bundle contents or dependency pins, update the ZIP SHA-256 and
repeat `install_offline.bat`, `pip check`, the synthetic-DICOM smoke test, and a
visual GUI launch check.
