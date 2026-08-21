# Documentation Index

The canonical project overview and quick start are in
[`../README.md`](../README.md).

The supported runtime is Python 3.10 or later.

Additional documentation:

- [`user_manual.md`](user_manual.md): application usage and troubleshooting;
- [`windows_offline_installation.md`](windows_offline_installation.md): build
  and use the Windows x64 offline bundle;
- [`windows_offline_installation_validation_2026-08-10.md`](windows_offline_installation_validation_2026-08-10.md):
  recorded Windows 10 validation of the offline workflow;
- [`windows_offline_installation_validation_2026-08-21.md`](windows_offline_installation_validation_2026-08-21.md):
  recorded human-observed Windows 11 installation, launch, and anonymizer
  validation for release `v0.0.0`;
- [`windows_offline_installation_validation_v0.0.1_2026-08-21.md`](windows_offline_installation_validation_v0.0.1_2026-08-21.md):
  recorded automated offline installation and human-observed all-GUI startup
  and shutdown validation for release `v0.0.1` on Windows 11.

Development and safety guidance:

- [`../AGENTS.md`](../AGENTS.md): AI contributor entry point;
- [`../AI_AGENT_RULES.md`](../AI_AGENT_RULES.md): provider-neutral AI safety and
  iteration rules;
- [`../changes/`](../changes/): OpenSpec proposals and implementation records.

Only synthetic DICOM may be used for development and repository validation.
Toolkit output alone does not guarantee complete de-identification, legal
compliance, or clinical suitability.
