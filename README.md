# Radiotherapy DICOM Anonymization and Validation Toolkit

A toolkit for anonymizing and validating radiotherapy (RT) DICOM files. It
supports privacy-conscious research and multi-institutional data-sharing
workflows, but its output alone does not guarantee complete de-identification,
legal compliance, or clinical suitability.

## Features

![GUI screenshot](docs/images/gui_screenshot.png)

### Anonymizer

- **Modern GUI:** A CustomTkinter interface with dark-mode support.
- **Full and partial profiles:** Select an anonymization level appropriate to the
  workflow.
- **Consistent relationships:** Preserve Study/Series relationships while
  replacing UIDs consistently, or generate new UIDs.
- **Private-tag handling:** Recursively remove private tags, including tags in
  nested sequences.
- **Robust output:** Add standard file-meta information when saving non-standard
  DICOM input.

### Validator

- Compare DICOM tags before and after anonymization.
- Detect potentially remaining protected health information (PHI).
- Check that expected structural information is preserved.
- Generate detailed JSON and text validation reports.

## Quick start

### Launch the GUI

Double-click `start_gui.bat` from the repository root, or run:

```powershell
python -m rt_dicom_toolkit
```

### Use the command line

```powershell
# Anonymize a directory
python -m rt_dicom_toolkit --input ./DICOM --output ./OUT --private remove

# Validate anonymized output against the original directory
python -m rt_dicom_toolkit validate --original ./DICOM --anonymized ./OUT
```

Use only synthetic data for development and testing. Never commit real-patient
DICOM, anonymized derivatives, reports, logs, or screenshots.

## Project structure

```text
rt-dicom-toolkit/
|-- rt_dicom_toolkit/
|   |-- anonymizer/        # Anonymization core
|   |-- gui/               # Desktop interfaces
|   |-- template/          # DICOM template synchronization
|   `-- validator/         # Validation and reports
|-- tests/                 # Pytest suite using synthetic data
|-- changes/               # OpenSpec change management
|-- docs/                  # Manuals and installation guides
|-- tools/                 # Offline and validation utilities
|-- AGENTS.md              # AI contributor entry point
`-- AI_AGENT_RULES.md       # AI development and safety policy
```

## Installation

### Requirements

- Python 3.10 or later
- Windows 10/11 is the primary desktop target

### Install dependencies

For a development installation, install the dependencies declared by the
project:

```powershell
python -m pip install -r rt_dicom_toolkit/requirements.txt
python -m pip install -e .
```

For a network-isolated Windows installation, see
[`docs/windows_offline_installation.md`](docs/windows_offline_installation.md).

## Testing

```powershell
python -m pytest -q -p no:cacheprovider tests
python tools/offline_smoke_test.py
```

The smoke test creates synthetic DICOM at runtime and removes it afterward.

## Development process

This project uses AI-assisted development within explicit safety and review
boundaries:

- Read [`AGENTS.md`](AGENTS.md) and [`AI_AGENT_RULES.md`](AI_AGENT_RULES.md)
  before making changes.
- Manage new capabilities and public-behavior changes through OpenSpec files in
  `changes/`.
- Work in small, single-purpose pull requests.
- A human reviews and merges pull requests; AI agents do not merge them.

## License

This project is available under the [MIT License](LICENSE).
