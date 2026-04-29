---
name: dcoir-parity-verifier
description: verify governed dcoir skill source, installed skill packages, and parity manifests for africom_soc_ir / dcoir helper-skill maintenance.
---
<!-- skill-marker: updated-skill|20260429T171500Z|airtable-operational-schema-alignment|source-update|dcoir-parity-verifier|SKILL.md -->

# DCOIR Parity Verifier

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
- Read GitHub CP files only for repository-source tasks: source-file role resolution, packaging or release bundles, prompt/collector source inspection, promoted-history comparison, explicit repo cleanup/source-role review, or explicit operator request.
- Treat any older instruction that says to read `CP-01` and `CP-02` first as superseded for startup, resume, queue, administrative-control, helper-memory, and operator-preference branches. If a source task still requires those files and they are absent, use Airtable `Governance Control Plane`, `Repo Surface Registry`, `Repo Surface Registry supporting evidence`, `Repo Surface Registry retained-state evidence`, and active plan state before stopping.



## Required project gate
This skill is for the AFRICOM_SOC_IR / DCOIR project only.
Before proceeding, verify that the current task is actually inside the AFRICOM_SOC_IR / DCOIR project context and grounded in the current Airtable-first authority model or current governed GitHub source working line.
If the current AFRICOM_SOC_IR / DCOIR project context is not present, do not proceed.

## Purpose
Use this skill to make governed skill-source parity checks repeatable and less manual.
The canonical machine-readable parity surface is `dcoir_skills/skill_parity_manifest.json`.
The human-readable companion surface is `dcoir_skills/skill_parity_summary.md`.

Prefer a normalized tree hash and per-file `sha256` values as the primary parity evidence.
Treat zip hash as a secondary package or install check only.
Treat runtime residue in packaged skill zips such as `__pycache__/` and `*.pyc` as an explicit package-cleanliness failure signal even when the normalized tree hash still matches after exclusions.

## Core workflows

### 1. Refresh governed parity surfaces
Use when the governed repo-side skill source changed.
1. Re-anchor to Project Instructions, CP-00 as a pointer, and Airtable `CONTROL-STARTUP-AIRTABLE-FIRST`; read GitHub `CP-01`/`CP-02` only for repository-source tasks.
2. Read `references/manifest_schema.md`, `references/hash_policy.md`, and `references/verification_workflow.md` when needed.
3. Resolve the current project label, governed repository naming, and skill prefix from `dcoir_skills/project_discovery_contract.json` when those assumptions matter.
4. Build or refresh `dcoir_skills/skill_parity_manifest.json` from the governed skill-source root.
4. Render `dcoir_skills/skill_parity_summary.md` from the manifest.
5. If install zips were built, record their zip hashes too.
6. Treat the manifest as canonical and the summary as generated.

### 2. Verify installed skill package against governed source
Use when the operator wants to know whether the installed skill package still matches the governed repo source.
1. Load the canonical manifest.
2. Hash the installed skill tree, extracted install zip, or both.
3. Compare per-file hashes first.
4. Compare normalized tree hash second.
5. Report zip hash only as a secondary package check.
7. Treat missing expected markers as pending install or readback confirmation until the edited installed files are confirmed, not as automatic governed-source drift.
8. Run a package-cleanliness check on the zip contents and call out runtime residue such as `__pycache__/`, `*.pyc`, or equivalent packaging contamination explicitly.
9. Call out missing files, extra files, hash mismatches, marker-confirmation gaps, and contamination separately.

### 3. Bootstrap or rebaseline parity inventory
Use when the parity surface does not exist yet or when the project needs a controlled rebaseline.
1. Say whether the baseline is coming from repo source, installed-skill tree, or a mixed bootstrap.
2. Do not silently label an installed-skill bootstrap as a repo-verified source baseline.
3. Mark bootstrap status plainly when full repo-side rebaseline still remains.

## No brittle hard-coding rule
Do not hard-code the expected file list for a skill when the current skill tree can be discovered directly.
Prefer:
- reading the current skill tree from the current source root
- reading the canonical parity manifest
- reading current control-plane files

Hard-code only the canonical surface names that are part of the governed contract for this skill, such as:
- `dcoir_skills/skill_parity_manifest.json`
- `dcoir_skills/skill_parity_summary.md`

## Scripts
Use these scripts:
- `scripts/build_skill_parity_manifest.py`
- `scripts/render_skill_parity_summary.py`
- `scripts/verify_skill_parity.py`

### Commands
Build or refresh manifest:
```bash
python scripts/build_skill_parity_manifest.py --skills-root /mnt/data/dcoir_skills --output /mnt/data/skill_parity_manifest.json --zip-dir /mnt/data/skill_zips --contract /mnt/data/dcoir_skills/project_discovery_contract.json --baseline-origin repo_source
```

Render summary:
```bash
python scripts/render_skill_parity_summary.py --manifest /mnt/data/skill_parity_manifest.json --output /mnt/data/skill_parity_summary.md
```

Verify source tree and install zips:
```bash
python scripts/verify_skill_parity.py --manifest /mnt/data/skill_parity_manifest.json --skills-root /mnt/data/dcoir_skills --zip-dir /mnt/data/skill_zips --output-md /mnt/data/skill_parity_verification.md --output-json /mnt/data/skill_parity_verification.json
```

## Output contract
Return these sections in order:
1. Baseline type
2. Manifest status
3. Verified skills
4. Mismatches or gaps
5. Required governed updates
6. Best next move

## References
Read when needed:
- `references/manifest_schema.md`
- `references/hash_policy.md`
- `references/verification_workflow.md`
