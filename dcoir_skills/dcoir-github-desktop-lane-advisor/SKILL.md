---
name: dcoir-github-desktop-lane-advisor
description: advise and maintain reusable africom_soc_ir / dcoir operator-side github desktop lane tools. use when the operator has a local git/github desktop problem, needs a targeted snapshot zip, needs a reusable powershell helper, asks which local helper tool to run, wants a tool captured instead of one-off chat code, or needs the operator_tools/github_desktop_lane repo folder and airtable operator tools registry kept aligned.
---

# DCOIR GitHub Desktop Lane Advisor

## Project gate
Use this skill only inside AFRICOM_SOC_IR / DCOIR work. Treat Airtable as live operational authority for queue and registry state. Treat the GitHub repo as the source of truth for tool code.

## Purpose
Select, explain, and maintain reusable operator-side helper tools for the GitHub Desktop/manual repo-update lane.

The skill does not passively monitor a folder and does not execute local PowerShell tools. It inspects the current Airtable registry and repo catalog when invoked, recommends the right tool, generates the launcher command, and helps create or update durable tools when a reusable pattern appears.

## Authority model
- Airtable `Operator Tools Registry` is the live discovery index for reusable local helper tools.
- GitHub repo folder `operator_tools/github_desktop_lane/` is the source of truth for tool code, README, sample manifests, and repo-side catalog files.
- Airtable `Admin Registry` and relevant helper-memory tables carry skill-state and cross-skill routing notes.
- The operator executes tools locally in PowerShell and uploads logs or ZIP outputs.
- ChatGPT may create a GitHub Desktop bundle or use an approved GitHub lane to update repo-side tool files.

## Preflight coexistence
`dcoir-memory-preflight` remains the broad pre-execution and post-blocker routing layer. This skill is narrower.

When a task involves local GitHub Desktop friction, local git state, targeted snapshots, manual repo-update bundles, reusable operator scripts, or repeated PowerShell helper generation:
1. Let preflight identify the task family and reusable-tool opportunity.
2. Use this skill to read the Operator Tools Registry and repo catalog.
3. Recommend an existing tool or create a durable tool candidate.
4. Record durable tool changes in Airtable and repo files so preflight can discover them later without skill repackaging.

Do not hard-code every future tool into this skill. Read the registry and repo catalog dynamically.

## Required Airtable reads
Before recommending or creating a tool, read:
- `Operator Tools Registry` for matching active tools.
- `Work Items` if task ordering or plan state matters.
- `Admin Registry` if skill-state or installed-skill awareness matters.
- `dcoir-memory-preflight` only when a blocker signature or reusable lesson needs cross-skill routing.

Use non-display reads by default. Do not show Airtable grids unless the operator asks.

## Tool selection workflow
1. Classify the operator problem:
   - git diagnostic
   - safe pre-pull recovery
   - targeted snapshot ZIP
   - bundle-builder manifest generation
   - validation/log capture
   - new reusable tool candidate
2. Search `Operator Tools Registry` by trigger terms and tool family.
3. If one active tool fits, provide:
   - tool name
   - why it fits
   - safety preconditions
   - exact launcher command
   - expected output file to upload
4. If no tool fits, propose a new reusable tool only when the pattern is likely to recur.
5. Keep destructive actions out of generated commands unless explicitly approved. Never suggest `git stash pop`, `git reset --hard`, `git clean`, or deletion without a purpose-specific safety explanation and explicit operator intent.

## Tool creation workflow
When creating a new durable tool:
1. Define the tool contract first: purpose, inputs, outputs, safety preconditions, expected log/ZIP location, and failure modes.
2. Add or update repo files under `operator_tools/github_desktop_lane/`.
3. Add or update `operator_tools/github_desktop_lane/tool_catalog.json`.
4. Add or update README usage.
5. Add or update an Airtable `Operator Tools Registry` row.
6. Provide a GitHub Desktop bundle unless an approved direct GitHub write lane is active.
7. Ask the operator to run the tool locally only after the repo update is applied.

## Repo folder contract
Expected repo surface:
```text
operator_tools/github_desktop_lane/
  README.md
  tool_catalog.json
  scripts/
    Get-DcoirGitConflictDiagnostic.ps1
    Invoke-DcoirSafePrePullApply.ps1
    New-DcoirTargetedSnapshot.ps1
  manifests/
    docs_impl_snapshot.sample.json
```

The folder should stay outside validate-on-push monitored paths unless a future plan explicitly adds a lightweight validation lane for operator tools.

## Output contract
For tool recommendations, respond with:
1. Selected tool
2. Why this tool
3. Safety checks
4. PowerShell launcher
5. Expected upload/output
6. Stop conditions

For new tool candidates, respond with:
1. Reusable pattern
2. Proposed tool contract
3. Repo files to create/update
4. Airtable registry row fields
5. Delivery lane
6. Validation step
