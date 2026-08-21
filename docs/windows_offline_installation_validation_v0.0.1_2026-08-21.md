# Windows 11 Offline Bundle Validation Record for v0.0.1 (2026-08-21)

## Target

- Repository: `inata169/rt-dicom-toolkit`
- Release: `v0.0.1`
- Bundle: `rt-dicom-toolkit-offline-win64-0.0.1.zip`
- Source commit: `113172ae9118d191ea7a160cbed176f87f44256d`
- Bundle SHA-256:
  `565f3e47c2815930c30cb8062b1d39578a6047c55265d21317644cb1a4f23c01`
- OS: Windows 11 x64, upgraded from Windows 10
- Installation location: a temporary writable local-disk folder

The pinned third-party dependency set and license review are unchanged from the
[`v0.0.0` Windows 11 validation record](windows_offline_installation_validation_2026-08-21.md).
The application wheel in this bundle reports version `0.0.1` and remains
covered by the repository's [MIT License](../LICENSE).

## Automated validation

The bundle was built from the source commit above with
[`prepare_offline_bundle.ps1`](../tools/prepare_offline_bundle.ps1). The build
reported a valid Python Software Foundation Authenticode signature for the
bundled CPython 3.12.10 x64 installer and created a payload containing 59 files
and 18 wheels, including the application wheel.

The ZIP was then extracted into a new temporary local-disk folder. Running
`install_offline.bat` produced the following results:

- all 59 payload files matched `SHA256SUMS.txt`, and no unlisted payload was
  accepted;
- the installer selected an existing compatible CPython 3.12.10 x64 runtime;
- installation used only the bundled wheelhouse with package-index access
  disabled;
- `pip check` reported no broken requirements;
- the bundled synthetic-DICOM smoke test passed for the anonymizer, validator,
  template engine, and GUI imports; and
- both installed package metadata and runtime `__version__` reported `0.0.1`.

The repository test suite also completed with 19 passed tests and 2 skipped
integration tests. The skipped tests require a local DICOM fixture that is not
stored in Git.

## Human-observed GUI validation

After installation on the Windows 11 x64 computer, a human launched every
available toolkit GUI and confirmed that each window opened successfully and
closed normally with its window **X** button. No traceback or error dialog was
reported. The extracted test folder was then removed.

Because the installer used the computer's existing compatible Python, it did
not create or register a bundle-private `.runtime` installation. Removing the
extracted test folder was therefore sufficient cleanup for this validation.

## Limits of this record

Only project-authored synthetic DICOM was used for automated validation. This
record does not claim validation with patient-derived data, a physically
disconnected network, every possible interactive GUI workflow, clinical use,
or complete de-identification for every vendor and modality. DICOM processing
semantics are unchanged from `v0.0.0`.
