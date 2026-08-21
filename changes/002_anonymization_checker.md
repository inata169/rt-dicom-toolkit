# Proposal: Implement an Anonymization Checker (CLI and GUI)

- Status: ✅ APPROVED
- Author: Antigravity
- Date: 2026-04-30

## 1. Background and objective

Strengthen the ability to verify whether DICOM output is actually anonymized.
The existing validator required a paired comparison with the original data and
depended on a GUI. Address these needs:

1. scan one anonymized directory for remaining personal information;
2. provide fast CLI validation with Markdown, JSON, and text reports; and
3. keep the checker lightweight and standalone.

## 2. Changes

- `check_anonymization.py`: CLI checker with standalone scan and paired
  comparison modes.
- `check_anonymization_gui.py`: modern CustomTkinter wrapper.
- `start_checker_gui.bat`: GUI launcher.
- `DICOM_LOGS/`: automatically created report directory.

## 3. Impact and risks

- The tools are standalone files at the repository root and do not modify the
  existing `rt_dicom_toolkit` package.
- They depend on `pydicom` and `customtkinter`.

## 4. Validation plan

- Run scan and paired comparison against the then-approved test directory and
  confirm normal completion.
- Scan the original test directory and confirm expected warnings.
- Keep all existing unit and integration tests passing under pytest.

> Historical note: this validation record predates the repository's current
> synthetic-data-only development rule. Future validation must not use or search
> for the historical path named in the original proposal.
