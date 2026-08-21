# AI Contributor Entry Point

Read `AI_AGENT_RULES.md` in full before inspecting or changing this repository.
It is the provider-neutral safety, permission, and iteration policy for Codex,
Claude Code, Antigravity, and other coding agents.

`rt-dicom-toolkit` supports radiotherapy DICOM anonymization, validation,
template synchronization, and offline installation. Do not treat it as a
guarantee of complete de-identification, legal compliance, clinical suitability,
patient QA, or device or vendor certification. Follow, in order: the current
human-approved task, approved OpenSpec changes, documented behavior and safety
boundaries, and tests. Preserve evidence and report conflicts instead of
guessing.

## Starting work

Confirm the repository root, branch, status, recent history, remote, and tags.
Read only files relevant to the task, preserve unrelated user changes, and make
the smallest diff on a feature branch. Do not commit or push directly to `main`.

Never add real-patient DICOM, UIDs, images, metadata, anonymized output,
validation reports, logs, screenshots, or derivatives to the repository. Use
synthetic data for development and CI. Do not discover, connect to, or execute
against patient data or an external DICOM environment on an agent's initiative.

When asking the primary user a question, state the evidence first, make one safe
proposal, and make the question answerable with `yes` or `no`. Do not bundle
independent decisions or permissions.

## OpenSpec and loops

For a new capability or a change to public behavior, architecture, dependencies,
or data-handling boundaries, create an OpenSpec from `changes/_template.md`
before implementation and wait for a human to mark it `✅ APPROVED`. A bug fix
that restores documented behavior and a documentation-only correction do not
require a proposal.

Use the inner loop only for safe failures caused by the current diff. Change,
run focused validation, inspect the result and diff, and apply the smallest fix
within the attempt and stopping limits in `AI_AGENT_RULES.md`. Return
specification, DICOM meaning, anonymization boundaries, clinical decisions, real
data, external execution, destructive operations, permission expansion, and
scope changes to the outer human loop.

Codex acts as the Developer Agent by default, implementing and validating small
changes against approved requirements. Return requirement redefinition,
complex design choices, and hard-to-isolate failures to a human or Architect
Agent instead of expanding scope. Prefer reproducible Windows 10/11 and Ubuntu
24 procedures and staged execution suitable for low-specification computers.

## Stopping and handoff

Stop expanding the work when the human-approved acceptance criteria are met and
required checks pass. Only a concrete merge-blocking defect in the current diff
justifies one minimal additional correction round on the same branch and pull
request. Do not create another issue, branch, pull request, OpenSpec change, or
automation for refactors, optional coverage, future work, or style suggestions
unless a human requests it. An agent does not merge.

Run focused checks followed by all applicable public checks:

```text
python -m compileall rt_dicom_toolkit
python -m pytest -q -p no:cacheprovider tests
python tools/offline_smoke_test.py
git diff --check
git diff --stat
git status --short
```

For documentation-only changes, run at least `git diff --check`, reference
checks, `git diff --stat`, and `git status --short`, and state why runtime tests
were omitted. A completion report must list changed files, exact commands and
results, unrun checks and reasons, unresolved items, and branch plus commit or
pull-request identifiers when created. It must state whether runtime behavior,
the public specification, DICOM meaning, or protected data changed.
