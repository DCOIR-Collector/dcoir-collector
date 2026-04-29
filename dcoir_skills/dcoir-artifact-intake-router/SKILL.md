---
name: dcoir-artifact-intake-router
description: classify and route uploaded africom_soc_ir / dcoir artifacts using bounded manifest-first inspection before expensive extraction or reading; use for archives, github actions artifacts, repo bundles, skill packages, collector output, prompt-pack files, evidence bundles, or unknown mixed uploads.
---
<!-- skill-marker: updated-skill|20260429T171500Z|airtable-operational-schema-alignment|source-update|dcoir-artifact-intake-router|SKILL.md -->

# DCOIR Artifact Intake Router

## Airtable operational schema alignment
Airtable cutover and skill cutover are complete. Use the current Airtable schema as live operational authority, not historical migration or cleanup plans.

Use `references/airtable_operational_schema_contract.md` for durable rules covering:
- current live authority tables
- idea-to-work-item-to-plan promotion
- Delete Queue deletion requests and dependency order
- DCOIR Lifecycle Ledger readback/history events
- Local Configuration Registry secret-safe configuration references

Do not assume retired or absent tables exist. In particular, do not require `Plan Tasks`, `Plan Checkpoints`, `Skill State Registry`, `Schema Registry`, `Tracking Registry`, `Repo File Coverage Detail`, or `Retained Repo Manifest` unless live Airtable schema readback proves the table exists for the current task.

## Airtable-first startup authority
- For normal AFRICOM_SOC_IR / DCOIR startup, resume, current-state reporting, administrative control, queue selection, active-plan recovery, helper-memory lookup, or operator-preference recovery, use Airtable-first authority.
- Required order: Project Instructions; CP-00 only as a bootstrap pointer when present; Airtable `Governance Control Plane` row `CONTROL-STARTUP-AIRTABLE-FIRST`; Airtable `Session Checkpoints`; Airtable `Queue Control`; Airtable `Work Items`; active Airtable `Plans` and `Work Items for task execution`; Airtable `Operator Preferences`; then skill-specific Airtable memory tables when relevant.
- Do not fetch GitHub `CP-01` or `CP-02` during normal startup when the Airtable startup-control row is available and current.
- Read GitHub CP files only for repository-source tasks: source-file role resolution, packaging or release bundles, prompt/collector source inspection, promoted-history comparison, or explicit operator request.
- Treat older final-cleanup references as historical unless live Airtable authority says they remain active.

## Required project gate
This skill is for the AFRICOM_SOC_IR / DCOIR project only.
Before proceeding, verify that the current task is inside the AFRICOM_SOC_IR / DCOIR project context and concerns a DCOIR upload, archive, artifact, evidence bundle, repo bundle, skill package, collector output, Gemini file, prompt-pack file, or GitHub Actions output.
If the project context is not present, do not proceed.

## Purpose
Use this skill to prevent slow, timeout-prone upload handling.
The skill routes artifacts by using a manifest-first approach before any deep unzip, recursive grep, Python parsing, or bulk file reading.

The goal is to answer: what is this upload, what should be inspected first, what should be skipped for now, which DCOIR helper skill should take over, and what stop conditions apply?

## Core intake rule
Never begin by fully extracting and reading every file in an archive.
Always start with the cheapest safe manifest:
1. archive type and size
2. top-level folder names
3. file count estimate
4. largest files
5. extension histogram
6. likely artifact class
7. capped shortlist of files to inspect

Only inspect deeper after producing a narrow read plan.

## Artifact classes
Classify the upload into one primary class and optional secondary classes:

- `github-actions-artifact`: workflow logs, CI job outputs, junit files, pytest results, coverage reports, build logs, step summaries, or downloaded GitHub Actions artifacts.
- `repo-snapshot`: repository working tree, source tree, or full project export.
- `repo-update-bundle`: patch-style bundle intended for GitHub Desktop or repo replacement.
- `skill-package`: one or more ChatGPT skill folders or skill ZIPs containing `SKILL.md`.
- `collector-output`: DCOIR collector output, endpoint collection, retrieved artifact, transcript, or triage bundle.
- `gemini-or-prompt-pack`: Gemini parent/sub-agent instructions, modular prompt-pack files, combined prompt drafts, or routing instructions.
- `evidence-bundle`: alert triage evidence, logs, endpoint artifacts, event exports, or enrichment material.
- `unknown-mixed`: mixed or unclear upload requiring bounded classification before routing.

## Manifest-first workflow
1. Identify uploaded file names and obvious file types.
2. If the upload is an archive, list archive contents without extracting the whole tree when the environment supports it.
3. Generate the smallest useful manifest using `scripts/build_artifact_manifest.py` when local archive access is available.
4. Identify high-value files by name and size. Prioritize names containing: `fail`, `failure`, `error`, `stderr`, `summary`, `junit`, `pytest`, `test-results`, `coverage`, `sarif`, `workflow`, `action`, `collector`, `gemini`, `prompt`, `SKILL.md`, `manifest`, `readme`.
5. Cap deep inspection unless the operator explicitly asks for full extraction.
6. Produce an intake verdict before downstream analysis.

## GitHub Actions artifact playbook
For GitHub Actions logs or artifact ZIPs:
- Prefer file listing, job/step summaries, junit/xml reports, pytest output, failure logs, stderr logs, SARIF, and workflow summary files first.
- Do not recursively grep the entire extracted tree as the first move.
- Do not read generated dependency folders, caches, build outputs, virtual environments, or binary artifacts unless the manifest shows they are directly relevant.
- If failure files are found, inspect a small bounded excerpt around error/failure markers.
- If no failure files are found, inspect the shortest summary and the newest/smallest log-like files first.

## Routing matrix
After classification, route to the most specific helper:

- GitHub Actions artifact, test logs, validation outputs: route to `dcoir-validation-orchestrator`, `dcoir-skill-regression-auditor`, or `dcoir-collector-qa` depending on content.
- Skill package or skill source: route to `skill-creator`, then `dcoir-skill-regression-auditor`, then `dcoir-parity-verifier` when parity/source follow-through is needed.
- Repo snapshot or repo-update bundle: route to `dcoir-source-authority-auditor`, `dcoir-change-impact-analyzer`, or `dcoir-repo-packager` depending on whether the task is review, impact, or packaging.
- Collector output or endpoint artifacts: route to `dcoir-collector-qa`, `dcoir-operator-workflow-hardener`, or `dcoir-large-file-intake-manager`.
- Gemini/prompt-pack files: route to `dcoir-prompt-pack-assembler`, `dcoir-validation-orchestrator`, or `dcoir-live-test-remediation-planner`.
- Triage/evidence bundles: route to `dcoir-triage-to-collector-escalation-designer` or `dcoir-large-file-intake-manager`.
- Unknown mixed archive: stay in this skill until classification is safe, then route.

## Stop conditions
Stop and report clearly when any of these are true:
- archive is too large or too deep to inspect safely within the current environment
- manifest indicates multiple unrelated artifact classes and no safe primary route can be inferred
- archive appears to contain secrets, credentials, private keys, tokens, or highly sensitive unrelated material
- expected DCOIR project context is missing
- the task requires current Airtable authority and Airtable access is unavailable
- repo replacement, final cleanup, or deletion logic appears in scope but live authority says that lane is closed or unclear

## Intake verdict format
Return this short verdict before deeper work:

```text
Artifact intake verdict
- Primary class:
- Secondary classes:
- Manifest basis:
- Files inspected:
- Files intentionally skipped:
- Timeout risk:
- Recommended downstream helper:
- Stop conditions:
- Safe next move:
```

## Bounded read defaults
Use these defaults unless the operator gives stricter limits:
- list up to 250 manifest rows in chat
- inspect no more than 10 candidate files in the first pass
- read no more than 64 KiB per text file in the first pass
- show largest 20 files and top 20 extensions
- summarize skipped directories and skipped binary/generated content

## Output handling
- Be explicit about what was inspected versus skipped.
- Prefer one safe next move over a long menu.
- Do not claim complete analysis when only the manifest or a bounded subset was inspected.
- Keep command-lane separation clear: local workstation/test instructions must not be mixed with Elastic Defend response-action instructions.

## Script
Use `scripts/build_artifact_manifest.py` for local archive/file manifest generation when available.

Example:
```bash
python scripts/build_artifact_manifest.py /mnt/data/upload.zip --output /mnt/data/artifact_manifest.json --max-rows 250
```
