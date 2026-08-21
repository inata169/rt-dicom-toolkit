# Legacy Project Overview

This file is retained for compatibility with historical links. For current
installation, usage, safety, and development guidance, use the canonical
[`README.md`](README.md).

RT DICOM Toolkit provides desktop and command-line tools for anonymizing and
validating radiotherapy DICOM. It includes configurable anonymization profiles,
consistent UID replacement, private-tag handling, directory-structure
preservation, validation reports, and DICOM template synchronization.
The supported runtime is Python 3.10 or later.

The package is organized into these modules:

- `rt_dicom_toolkit/anonymizer`: anonymization core and profiles;
- `rt_dicom_toolkit/validator`: comparison, validation, and reports;
- `rt_dicom_toolkit/template`: template synchronization;
- `rt_dicom_toolkit/gui`: desktop interfaces; and
- `rt_dicom_toolkit/utils`: file, DICOM, logging, and plotting utilities.

Requirements, commands, and repository safety rules have changed since this
legacy overview was created. Do not follow old installation snippets copied from
earlier versions. Use the canonical README and
[`docs/user_manual.md`](docs/user_manual.md).

This project is available under the [MIT License](LICENSE).
