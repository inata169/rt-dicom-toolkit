# Proposal: Translate the project interface and documentation to English

- Status: ✅ APPROVED
- Author: Codex (Developer Agent)
- Date: 2026-08-21

## 1. Background and objective

The repository currently mixes Japanese and English across its documentation,
OpenSpec history, CLI output, logs, reports, Python scripts, and desktop GUIs.
The requested outcome is an English-language repository and product interface
that can be reviewed and used without Japanese-language knowledge.

This change will translate tracked human-readable text to English while
preserving DICOM semantics, anonymization behavior, UID handling, file formats,
and processing logic. It will also rename the root `readme.md` to the canonical
`README.md` filename.

## 2. Scope

### 2.1 Documentation and governance

- Rename `readme.md` to `README.md` and update repository references.
- Translate the root README, duplicate/legacy readmes, user manuals, installation
  guides, validation records, handover notes, and task notes.
- Translate `AI_AGENT_RULES.md` and `AGENTS.md` without weakening any safety,
  permission, DICOM, OpenSpec, bounded-loop, or pull-request stopping rule.
- Translate `changes/_template.md` and every existing OpenSpec document under
  `changes/`. Preserve their identifiers, approval state, acceptance history,
  and technical meaning.
- Replace the README GUI screenshot with an English-interface screenshot that
  contains only synthetic example paths and no patient, institution, or
  personal-computer-specific information.

### 2.2 Application, scripts, and GUIs

- Translate user-visible CLI descriptions, option help, status messages,
  warnings, errors, logs, reports, chart labels, and generated text.
- Translate all labels, buttons, tabs, dialogs, status text, logs, plots, and
  tooltips in the CustomTkinter and Tkinter GUIs.
- Translate user-visible text in top-level scripts, support scripts, and legacy
  scripts under `data/`.
- Translate Japanese comments and docstrings in maintained Python source and
  tests so tracked source text is consistently English.
- Translate Japanese programmatic output keys that are exposed in summaries or
  serialized reports to stable English names, then update every in-repository
  consumer and test. This is a public output-contract change; no Japanese alias
  will be retained because the requested result is English-only output.

### 2.3 Explicitly preserved behavior

- Do not change DICOM keywords, tag numbers, Value Representations, SOP classes,
  UIDs, coordinate systems, geometry, units, dose values, transfer syntax, or
  file-meta behavior.
- Do not change which tags are removed, retained, replaced, validated, or
  recursively traversed.
- Do not change anonymization thresholds, validation thresholds, matching logic,
  directory traversal, output placement, or offline installation behavior.
- Do not add internationalization frameworks, runtime language selection, large
  dependencies, or background services in this change.
- Use only synthetic DICOM data for automated and manual validation.

## 3. Implementation plan

- [x] Translate governance documents and all OpenSpec files, preserving meaning
      and status.
- [x] Translate README/manual/install/validation/handover/task documentation and
      complete the `README.md` case-sensitive rename.
- [x] Translate package CLI, log, report, exception, comment, and docstring text.
- [x] Translate all maintained GUI text and plot labels.
- [x] Translate top-level, support, and legacy script text.
- [x] Update affected tests and add focused assertions for English CLI/report/UI
      text where practical without coupling tests to full layouts.
- [x] Replace the README screenshot with a safe English screenshot.
- [x] Run the focused and full validation listed below.
- [x] Confirm no Japanese text remains in tracked Markdown, Python, PowerShell,
      batch, or plain-text files unless an exception is documented and approved.

The implementation may be split into small reviewable commits, but it remains
one English-localization change. No unrelated refactor or feature work is in
scope.

## 4. Requirements and scenarios

### Requirement 1: English documentation

All maintained project documentation and OpenSpec content shall be readable in
English while retaining its original technical and approval meaning.

#### Scenario: Repository entry point

- **Given** a user opens the repository root
- **When** the hosting platform resolves the conventional README
- **Then** `README.md` exists, `readme.md` does not exist, and the rendered
  document and screenshot use English text.

#### Scenario: Historical OpenSpec review

- **Given** a reviewer opens any file under `changes/`
- **When** they inspect its requirements, status, and recorded outcome
- **Then** the content is English and no identifier, status, acceptance result,
  or historical technical decision has changed.

### Requirement 2: English product interface

All user-visible text emitted by maintained CLIs, GUIs, reports, plots, and
scripts shall be English.

#### Scenario: CLI help and execution

- **Given** a user invokes a supported command with `--help` or runs it against
  synthetic input
- **Then** descriptions, option help, progress, warnings, errors, and summaries
  are English.

#### Scenario: Desktop GUI

- **Given** a user launches any maintained GUI
- **Then** window titles, labels, controls, dialogs, status text, log text, tabs,
  and charts are English at supported window sizes.

#### Scenario: Generated validation report

- **Given** a validation run over synthetic DICOM
- **When** the text or structured summary is generated
- **Then** headings, messages, and exposed keys are English while calculated
  values and pass/fail thresholds remain unchanged.

### Requirement 3: Behavioral preservation

Translation shall not alter DICOM processing or safety behavior.

#### Scenario: Existing automated behavior

- **Given** the translated implementation and the existing synthetic test suite
- **When** compilation, tests, and the offline smoke test run
- **Then** they pass without using real patient data, and any test update is
  limited to translated text or translated output keys.

## 5. Impact and risks

- English summary/report keys can break external consumers that depend on the
  current Japanese keys. This is intentional but must be called out in the
  README and completion report as a public output-contract change.
- Long English GUI strings can cause clipping or layout regressions. Each GUI
  requires launch and visual inspection at its default size.
- Historical OpenSpec translation can accidentally alter the meaning or status
  of an approved change. Reviews must compare identifiers, status fields,
  acceptance criteria, and recorded results before and after translation.
- A repository-wide mechanical replacement can modify DICOM literals or logic.
  Translation must be reviewed file by file, and DICOM behavior must be covered
  by the existing tests and synthetic smoke test.
- The current README screenshot contains Japanese labels and local absolute
  paths. It must not remain in the completed English documentation.

## 6. Validation plan

Focused checks:

```text
python -m rt_dicom_toolkit --help
python -m rt_dicom_toolkit validate --help
python -m rt_dicom_toolkit template --help
python check_anonymization.py --help
```

Repository checks:

```text
python -m compileall rt_dicom_toolkit
python -m pytest -q -p no:cacheprovider tests
python tools/offline_smoke_test.py
rg --pcre2 "[\p{Hiragana}\p{Katakana}\p{Han}]" -g "*.md" -g "*.py" -g "*.ps1" -g "*.bat" -g "*.txt"
git diff --check
git diff --stat
git status --short
```

The Japanese-text scan must return no matches, or every remaining match must be
listed with a specific approved reason. GUI validation shall use no patient
data and shall record which windows were visually inspected. Full Windows
offline installation validation is required only if executable installer logic
changes; translation-only batch/PowerShell changes require syntax and focused
message-path review.

## 7. Approval boundary

Implementation of runtime, script, GUI, report-key, or historical OpenSpec
translations must not begin until a human changes this proposal's status to
`✅ APPROVED`. Approval covers English-only presentation and the documented
English output-key migration; it does not authorize any DICOM semantic,
anonymization, clinical, privacy, or protected-data change.

## 8. Implementation and validation record

Implementation completed on 2026-08-21 using synthetic DICOM only.

- The root entry point is exactly `README.md`; lowercase `readme.md` is absent.
- Governance, documentation, OpenSpec history, runtime output, reports, scripts,
  tests, and maintained GUI text are English.
- The README screenshot shows the English main GUI with synthetic example paths.
- The main anonymizer, Tk anonymizer, validator, template engine, and
  anonymization checker GUIs were visually inspected at their default sizes.
- The validator close button was manually accepted by the user; closing the
  window now terminates its Python process and returns to PowerShell.
- English serialized-summary keys and the English validation-report heading are
  asserted by the synthetic offline smoke test.
- CLI help checks passed for the toolkit, validator, template engine, and
  anonymization checker.
- `python -m compileall` completed successfully.
- Pytest result: 15 passed, 2 skipped. The skips require an optional historical
  integration fixture and do not indicate a localization regression.
- The offline synthetic DICOM smoke test passed.
- The repository Japanese-text scan returned no matches outside temporary local
  tooling, which is removed after validation.
- `git diff --check` and the case-sensitive README filename check passed.
