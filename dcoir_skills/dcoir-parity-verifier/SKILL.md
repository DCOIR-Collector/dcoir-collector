---
name: dcoir-parity-verifier
description: verify governed dcoir skill source, installed skill packages, and parity manifests for africom_soc_ir / dcoir work. use when chatgpt needs to generate or refresh the canonical skill parity manifest, render the human-readable parity summary, compare installed skills or skill zips against governed repo source, check whether a skill package matches its governed files, or audit parity drift before or after a grouped skill update. use only when working inside the africom_soc_ir / dcoir project context.
---

# DCOIR Parity Verifier

## Required project gate
This skill is for the AFRICOM_SOC_IR / DCOIR project only.
Before proceeding, verify that the current task is actually inside the AFRICOM_SOC_IR / DCOIR project context and grounded in the current project control plane or current project working line.
If the current AFRICOM_SOC_IR / DCOIR project context is not present, do not proceed.

## Purpose
Use this skill to make governed skill-source parity checks repeatable and less manual.
The canonical machine-readable parity surface is `dcoir_skills/skill_parity_manifest.json`.
The human-readable companion surface is `dcoir_skills/skill_parity_summary.md`.

Prefer a normalized tree hash and per-file `sha256` values as the primary parity evidence.
Treat zip hash as a secondary package or install check only.

## Core workflows

### 1. Refresh governed parity surfaces
Use when the governed repo-side skill source changed.
1. Re-anchor to Project Instructions, then CP-01, then CP-02.
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
6. Call out missing files, extra files, and hash mismatches explicitly.

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
