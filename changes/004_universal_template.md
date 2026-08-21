# Proposal: 004 Implement a Universal DICOM Template

- Status: ✅ APPROVED
- Author: Antigravity
- Date: 2026-04-30

## 1. Background and objective

### Original problem

When converting PHITS output to DICOM such as RTDOSE, the structure of the
source clinical DICOM can vary by manufacturer and export settings. Conversion
scripts that depend on a particular tag structure may fail, and generated DICOM
may not display correctly in a viewer.

### Solution

Adopt a Universal Template strategy. Start with a prepared, standard, clean
DICOM template and inject selected geometry, such as coordinates and
resolution, plus requested patient information from a source DICOM. A stable
output structure improves system reliability.

## 2. Changes

### 2.1 Add `rt_dicom_toolkit/template/`

- `engine.py`: core template operations.
  - Implement `DICOMTemplateEngine`.
  - `inject_tags(template_path, source_tags_dict)`: inject selected tags.
  - `sync_geometry(template_path, source_dicom_path)`: synchronize geometry.
- `tags.py`: define standard synchronization lists.
  - `GEOMETRY_TAGS`: `ImagePositionPatient`, `PixelSpacing`, `Rows`, `Columns`,
    and related tags.
  - `PATIENT_TAGS`: `PatientName`, `PatientID`, `StudyInstanceUID`, and related
    tags.

### 2.2 Extend the CLI

- Add a `--template` option.
- Add a `template-base` command or equivalent sub-option.

### 2.3 Extend the GUI

- Add a control for selecting the template DICOM file.

## 3. Impact and risks

- Existing anonymization behavior is unaffected because the template feature is
  an independent tool or mode.
- If template and source modalities differ, for example CT and RTDOSE, manual
  tag adjustment may be required. The initial implementation emits a warning.

## 4. Validation plan

### 4.1 Unit tests

- Confirm selected values are injected into the template.
- Confirm coordinates, spacing, and other geometry match the synthetic source.

### 4.2 Integration tests

The original plan referenced a local DICOM sample and operational parameters.
Under the current repository rules, equivalent validation must use synthetic
DICOM only. Generate a new DICOM, scan it with the checker, and confirm its
geometry is internally consistent without making a clinical-validity claim.
