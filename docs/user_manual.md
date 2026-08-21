# RT DICOM Toolkit User Manual

## Contents

1. [Introduction](#1-introduction)
2. [Anonymizer](#2-anonymizer)
3. [Validator](#3-validator)
4. [Template synchronization](#4-template-synchronization)
5. [Troubleshooting](#5-troubleshooting)
6. [Security and privacy](#6-security-and-privacy)
7. [Reference](#7-reference)

## 1. Introduction

RT DICOM Toolkit provides desktop and command-line workflows for anonymizing
radiotherapy DICOM, comparing original and anonymized files, and synchronizing
selected values into a DICOM template.

The toolkit supports research and education workflows. Its output alone does
not guarantee complete de-identification, compliance with local policy or law,
clinical suitability, patient QA, or vendor certification. A qualified human
must define the applicable data-governance process and review the result.

### 1.1 Components

- `RTDicomAnonymizer`: replaces configured identifying values, processes UIDs,
  and optionally removes private tags.
- `RTDicomValidator`: compares original and anonymized DICOM and generates
  validation summaries and reports.
- `DICOMTemplateEngine`: copies selected patient, geometry, and RT values from a
  source into a template while generating new instance identifiers.
- Desktop GUIs: expose the maintained workflows through CustomTkinter or Tkinter.

### 1.2 Requirements

- Windows 10/11 is the primary desktop target.
- Python 3.10 or later.
- Runtime dependencies from `rt_dicom_toolkit/requirements.txt`.
- Tcl/Tk, which is included by the standard python.org Windows installer.

### 1.3 Installation

```powershell
python -m pip install -r rt_dicom_toolkit/requirements.txt
python -m pip install -e .
```

For a network-isolated Windows x64 computer, follow
[`windows_offline_installation.md`](windows_offline_installation.md).

## 2. Anonymizer

### 2.1 Launch

Launch the main GUI:

```powershell
python -m rt_dicom_toolkit
```

Run the CLI:

```powershell
python -m rt_dicom_toolkit --input SYNTHETIC_INPUT --output OUTPUT_DIRECTORY
```

Use only synthetic data during development and repository validation. An
operational workflow that handles real-patient data must keep input, output,
reports, logs, and screenshots outside the repository.

### 2.2 GUI workflow

1. Select the input directory.
2. Select an output directory outside the input tree.
3. Choose UID handling:
   - `consistent` maps each old UID to one new UID and preserves references;
   - `generate` creates new values according to the selected profile.
4. Choose whether to preserve the source directory structure.
5. Choose whether to remove private tags. Private tags may contain identifying
   information and should normally be removed unless the data-governance process
   explicitly allows them.
6. Start anonymization and monitor progress and log messages.
7. Review the completion summary and validate the output before release or use.

### 2.3 CLI options

Run `python -m rt_dicom_toolkit --help` for the authoritative option list.
The maintained CLI accepts input, output, log, anonymization-level,
private-tag, UID-handling, patient-ID, and directory-structure settings.

Example:

```powershell
python -m rt_dicom_toolkit `
  --input SYNTHETIC_INPUT `
  --output OUTPUT_DIRECTORY `
  --private remove `
  --uid consistent
```

### 2.4 Anonymization profile

The exact profile is defined in `rt_dicom_toolkit/anonymizer/profiles.py`.
Important behaviors include:

- replacing Patient Name and Patient ID;
- replacing or clearing configured birth, address, telephone, physician,
  operator, accession, and institution values;
- mapping Study, Series, SOP Instance, and Frame of Reference UIDs;
- recursively updating mapped UID references inside sequences;
- processing configured RT labels and comments; and
- optionally removing private tags recursively.

Do not treat this summary as a complete list of potentially identifying DICOM
attributes. Review the active profile and local requirements for every data-
sharing workflow.

### 2.5 UID and relationship handling

In consistent mode, the anonymizer first builds an old-to-new mapping for major
UIDs, then applies it to the objects and referenced UI elements. This preserves
relationships such as CT to RTSTRUCT, RTSTRUCT to RTPLAN, and RTPLAN to RTDOSE.

Changing UID behavior can make an RT dataset unusable. Such a change requires a
separate approved OpenSpec and synthetic reference-chain tests.

### 2.6 Patient-ID mapping and logs

The anonymizer may keep an in-memory mapping while processing a directory and
may include a masked mapping in its summary. Treat summaries and logs as
sensitive operational output even after anonymization. Do not commit them.

## 3. Validator

### 3.1 Launch

Run a paired comparison from the package CLI:

```powershell
python -m rt_dicom_toolkit validate `
  --original SYNTHETIC_ORIGINAL `
  --anonymized SYNTHETIC_ANONYMIZED `
  --report REPORT_DIRECTORY
```

Launch the maintained validator GUI directly:

```powershell
python -m rt_dicom_toolkit.gui.validator_gui
```

The standalone checker also supports a directory-only scan and paired
comparison:

```powershell
python check_anonymization.py --help
```

### 3.2 GUI workflow

1. Select the original, anonymized, and report directories.
2. Configure the profile, private-tag, structure, UID, and report-detail checks.
3. Run a directory comparison for file and modality counts if needed.
4. Start validation.
5. Review logs, the summary, charts, and per-tag details.
6. Store reports according to the workflow's access-control policy; do not
   commit operational reports.

### 3.3 Validation categories

The authoritative rules are in `rt_dicom_toolkit/validator/rules.py`.

- Required anonymization tags include configured patient, physician,
  institution, station, and operator values.
- UID checks cover Study, Series, SOP Instance, and Frame of Reference UIDs.
- Structure checks cover selected modality, SOP Class, image encoding, pixel,
  and frame attributes.
- Optional checks cover dates, times, identifiers, image coordinates, and device
  identifiers according to the selected level.
- RT checks cover configured Structure Set, ROI, Dose, and Plan labels.
- Private-tag checks report whether vendor-private content remains.

### 3.4 Interpreting a report

Reports can include total and matched file counts, per-category results, UID
changes, structure preservation, private-tag removal, modality distribution,
and a masked patient-ID mapping.

The current summary uses these display thresholds:

- 95 percent or greater: good;
- 80 to less than 95 percent: review required;
- less than 80 percent: insufficient.

These percentages are application heuristics, not proof of de-identification or
clinical validity. Investigate each failed or skipped tag and apply the governing
privacy policy before using or sharing data.

## 4. Template synchronization

The template workflow copies configured patient, geometry, and RT-specific tags
from a source dataset into a deep copy of a DICOM template. It generates a new
SOP Instance UID and Series Instance UID for the output.

CLI example:

```powershell
python -m rt_dicom_toolkit template `
  --template SYNTHETIC_TEMPLATE.dcm `
  --input SYNTHETIC_SOURCE `
  --output OUTPUT_DIRECTORY
```

Use `--no-patient` or `--no-geometry` to disable those synchronization groups.
Modality mismatches produce a warning and require human review. Template
synchronization does not establish geometric, dosimetric, or clinical validity.

## 5. Troubleshooting

| Symptom | Possible cause | Action |
|---|---|---|
| Output cannot be saved | Missing permission or invalid output path | Select a writable directory outside the repository and input tree. |
| Processing stops on a large dataset | Memory or I/O pressure | Process a smaller synthetic batch during diagnosis and inspect the log. |
| A file is not recognized as DICOM | Damaged or non-standard input | Verify the source independently; do not weaken validation without approval. |
| Few files match during validation | Names or directory structure changed | Run directory comparison and inspect matching diagnostics. |
| Anonymization score is low | Expected tags remain or files did not match | Review per-tag results and the active profile. |
| Charts do not render | Tk or matplotlib backend is unavailable | Verify the installed runtime and Tk dependencies. |
| Offline launch fails | Bundle integrity or `.venv` is invalid | Run the documented offline smoke test and inspect installer output. |

Logs may contain file names, paths, identifiers, or mappings. Keep them outside
Git and restrict access. When reporting a defect, reproduce it with synthetic
data instead of attaching operational logs.

## 6. Security and privacy

- Keep original DICOM, anonymized output, reports, logs, and screenshots outside
  the source repository.
- Prefer isolated, access-controlled storage for operational processing.
- Limit access to any reidentification or patient-ID mapping.
- Validate the anonymized result independently before sharing it.
- Follow the applicable law, ethics approval, data-use agreement, and
  institutional policy.
- Do not infer that preserved RT structure is clinically correct merely because
  it survived anonymization.
- Use synthetic DICOM for software development, tests, examples, and issue
  reproduction.

## 7. Reference

### 7.1 Primary commands

```text
python -m rt_dicom_toolkit --help
python -m rt_dicom_toolkit validate --help
python -m rt_dicom_toolkit template --help
python check_anonymization.py --help
```

### 7.2 External references

- [pydicom documentation](https://pydicom.github.io/)
- [DICOM standard](https://www.dicomstandard.org/)
- [DICOM PS3.15 Security and System Management Profiles](https://dicom.nema.org/medical/dicom/current/output/html/part15.html)
- [AAPM TG-263 report](https://www.aapm.org/pubs/reports/RPT_263.pdf)

### 7.3 Revision history

- Initial Japanese edition: 2025-03-10.
- English repository edition: 2026-08-21 (OpenSpec 006).
