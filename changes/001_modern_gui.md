# OpenSpec: Introduce a Modern CustomTkinter GUI

- Status: ✅ APPROVED
- Author: Antigravity
- Date: 2026-04-28

## 1. Background and objective

`rt_dicom_toolkit` originally operated through a command-line interface. That
can be a barrier for non-engineering users, including healthcare professionals.
Introduce an intuitive modern GUI so users can select input and output
directories, change settings, and monitor progress on screen. Use
`customtkinter` to provide a lightweight Python interface with built-in dark
mode support.

## 2. Changes

1. Add `customtkinter` as a project dependency.
2. Create `rt_dicom_toolkit/gui/` with these components:
   - `main_window.py`: path selection, setting toggles, start button, progress
     bar, and log display;
   - `app.py`: application startup and thread management.
3. Update the entry point so `python -m rt_dicom_toolkit` without arguments
   launches the GUI, while arguments continue to select CLI behavior.
4. Add a callback or signal mechanism so `RTDicomAnonymizer` can report progress
   and log messages to the GUI.

## 3. Impact and risks

- The GUI dependency increases installation and packaged-build size.
- Anonymization performs substantial I/O and must run outside the main GUI
  thread to keep the window responsive.
- Keep the core independent from the GUI so both CLI and GUI callers can use it
  safely.

## 4. Validation plan

1. Select folders in the GUI, start processing, and confirm normal completion.
2. Process many files and confirm the progress bar updates while the window
   remains responsive and movable.
3. Run the existing pytest suite to confirm that CLI and core behavior remain
   backward compatible.
