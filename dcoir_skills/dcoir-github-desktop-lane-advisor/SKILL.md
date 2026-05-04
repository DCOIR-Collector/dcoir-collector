---
name: dcoir-github-desktop-lane-advisor
description: advise and maintain reusable africom_soc_ir / dcoir operator-side github desktop lane tools. use when the operator has a local git/github desktop problem, needs a targeted or text-only repo snapshot, needs a reusable powershell helper, asks which local helper tool to run, wants a tool captured instead of one-off chat code, needs github actions orchestrator launcher guidance, or needs operator_tools/github_desktop_lane repo files and airtable operator tools registry kept aligned.
---

<!-- skill-marker: updated-skill|20260504T181500Z|cache-scope-narrowing-stale-reference-scrub|source-update|dcoir-github-desktop-lane-advisor|SKILL.md -->

<!-- skill-marker: updated-skill|20260504T171500Z|airtable-local-cache-contract|source-update|dcoir-github-desktop-lane-advisor|SKILL.md -->
<!-- skill-marker: updated-skill|20260503T165000Z|blocked-action-recovery-ladder|source-update|dcoir-github-desktop-lane-advisor|SKILL.md -->
<!-- skill-marker: updated-skill|20260501T115800Z|operator-tools-module-split|source-update|dcoir-github-desktop-lane-advisor|SKILL.md -->
# DCOIR GitHub Desktop Lane Advisor

## Project gate
Use this skill only inside AFRICOM_SOC_IR / DCOIR work. Treat Airtable as live operational authority for queue and registry state. Treat the GitHub repo as source of truth for tool code.

## Purpose
Select, explain, and maintain reusable operator-side helper tools for the GitHub Desktop/manual repo-update lane.

The skill does not passively monitor a folder and does not execute local PowerShell tools on the operator workstation. It inspects the current Airtable registry and repo catalog when invoked, recommends the right tool, generates launcher commands, and helps create or update durable tools when a reusable pattern appears.

## Authority model
- Airtable `Operator Tools Registry` is the live discovery index for reusable local helper tools.
- GitHub repo folder `operator_tools/github_desktop_lane/` is the source of truth for tool code, README, sample manifests, and repo-side catalog files.
- Airtable `Admin Registry` and helper-memory tables carry skill-state and cross-skill routing notes.
- The operator executes tools locally in PowerShell and uploads logs, JSON, or ZIP outputs.
- ChatGPT may create a GitHub Desktop bundle or use an approved GitHub lane to update repo-side tool files.

## Preflight coexistence
`dcoir-memory-preflight` remains the broad pre-execution and post-blocker routing layer. This skill is narrower.

When a task involves local GitHub Desktop friction, local git state, snapshots, manual repo-update bundles, reusable operator scripts, GitHub Actions orchestration launchers, or repeated PowerShell helper generation:
1. Let preflight identify the task family and reusable-tool opportunity.
2. Use this skill to read the Operator Tools Registry and repo catalog.
3. Recommend an existing tool or create a durable tool candidate.
4. Record durable tool changes in Airtable and repo files so preflight can discover them later without skill repackaging.

Do not hard-code every future tool into this skill. Read the registry and repo catalog dynamically.

## Required Airtable and repo reads
Before recommending or creating a tool, read:
- `Operator Tools Registry` for matching active tools.
- `operator_tools/github_desktop_lane/tool_catalog.json` for repo-side catalog details when GitHub readback is needed.
- `operator_tools/github_desktop_lane/README.md` when operator instructions or module architecture matter.
- `Work Items` if task ordering or plan state matters.
- `Admin Registry` if skill-state or installed-skill awareness matters.
- `dcoir-memory-preflight` only when a blocker signature or reusable lesson needs cross-skill routing.

Use non-display reads by default. Show Airtable grids only when the operator asks, when verification materially benefits from a grid, or when visible Airtable display is already approved by current project guidance.


## Blocked-action recovery ladder
When a direct GitHub/API/connector repo update is blocked, partially blocked, or unverified, do not accept the block and move on. Use this bounded ladder:
1. Direct connector write first when safe and supported.
2. Retry once with corrected bounded inputs, or use the nearest equivalent connector operation, when the failure is a stale SHA, path mismatch, transient API issue, or simple argument mistake.
3. Switch to the staged ChatGPT apply-in/GitHub Actions lane when direct write is blocked by connector safety, write-shape limits, unsupported multi-file changes, or unreliable verification, and when the workflow supports the target path.
4. Switch to a GitHub Desktop/manual repo-update bundle when staged apply-in is unavailable, unsafe, blocked, or unverified.
5. For manual repo-update bundles, include only affected repo-relative files with no wrapper root and no meta/instruction files. Put suggested commit summaries in chat/Airtable only.
6. Preserve failure logs/reports and update Airtable whenever a lane fails. Verify success by GitHub readback, workflow report, logs, or file fetch before closing the task.

## Module-first and harness limits
Shared behavior belongs in modules/tools, not wrapper workarounds.

Wrappers/harnesses may collect parameters, create reviewed JSON/config, tee/log command output, and invoke the real engine/module/tool. They must not own workaround logic, process execution frameworks, dispatch/monitor logic, packaging/cleanup behavior, validation gates, recovery semantics, or durable business logic.

Temporary wrapper-side diagnostic shims are allowed only to isolate a failure. Replace them with a module/tool fix before promotion.

Current validated reusable modules under `operator_tools/github_desktop_lane/modules/`:
- `Dcoir.Git`: Machine/System env lookup, placeholder rejection, UTF-8 logging, git executable discovery, native argument quoting, logged git execution, branch checks, clean-tree checks, fetch, fast-forward pull, and ahead/behind analysis.
- `Dcoir.Snapshot`: repo-relative path safety, safe names, path normalization, under-root checks, text-file filtering, binary sniffing, targeted staging, and UTF-8 logging.
- `Dcoir.RepoPatch`: repo patch path safety, payload-root resolution, allowed target roots, hashing, and UTF-8 logging.
- `Dcoir.Actions`, `Dcoir.GitHub`, `Dcoir.Packaging`, and `Dcoir.Common`: Actions orchestration, GitHub CLI/API, packaging, and shared baseline support.

## Tool selection workflow
1. Classify the operator problem:
   - git diagnostic
   - safe pre-pull recovery
   - targeted snapshot ZIP
   - text-only repo snapshot ZIP
   - repo patch/apply
   - ChatGPT-friendly ZIP packaging
   - GitHub Actions orchestrator
   - Actions smoke harness
   - fail-fast mode ladder harness
   - validation/log capture
   - new reusable tool candidate
2. Search `Operator Tools Registry` by trigger terms and tool family.
3. If one active tool fits, provide:
   - tool name
   - why it fits
   - safety preconditions
   - exact PowerShell launcher
   - expected output file to upload
   - stop conditions
4. If no tool fits, propose a new reusable tool only when the pattern is likely to recur.
5. Keep destructive actions out of generated commands unless explicitly approved. Never suggest `git stash pop`, `git reset --hard`, `git clean`, or deletion without a purpose-specific safety explanation and explicit operator intent.

## Tool creation or maintenance workflow
When creating or updating a durable tool:
1. Define the tool contract first: purpose, inputs, outputs, safety preconditions, expected log/ZIP location, and failure modes.
2. Prefer adding shared logic to an existing module, or create a module when a function/pattern is used by two or more tools.
3. Add or update repo files under `operator_tools/github_desktop_lane/`.
4. Add or update `operator_tools/github_desktop_lane/tool_catalog.json`.
5. Add or update README usage.
6. Add or update the Airtable `Operator Tools Registry` row.
7. Choose the delivery lane using the blocked-action recovery ladder: direct connector write, then staged apply-in if supported, then GitHub Desktop/manual bundle if automation is blocked or unverified.
8. Ask the operator to run the tool locally only after the repo update is applied.
9. Record validation evidence before promotion.

## Repo folder contract
Expected repo surface:
```text
operator_tools/github_desktop_lane/
  README.md
  tool_catalog.json
  modules/
    Dcoir.Common/
    Dcoir.Git/
    Dcoir.GitHub/
    Dcoir.Packaging/
    Dcoir.Actions/
    Dcoir.Snapshot/
    Dcoir.RepoPatch/
    DcoirActionsOrchestrator/
  scripts/
    Get-DcoirGitConflictDiagnostic.ps1
    Invoke-DcoirSafePrePullApply.ps1
    New-DcoirTargetedSnapshot.ps1
    New-DcoirTextOnlyRepoSnapshot.ps1
    Invoke-DcoirRepoPatchApply.ps1
    New-DcoirChatGPTFriendlyZip.ps1
    Invoke-DcoirActionsWorkflowOrchestrator.ps1
    Invoke-DcoirActionsValidationSmoke.ps1
    Invoke-DcoirActionsModeLadder.ps1
  manifests/
    docs_impl_snapshot.sample.json
    repo_patch_apply.sample.json
    actions_workflow_orchestrator.dispatch.sample.json
    actions_workflow_orchestrator.watch.sample.json
```

## Airtable local cache contract
Routine cache scope is intentionally narrow: cache only the high-call tables named as routine in the contract; use live Airtable reads for conditional tables.

This skill is Airtable-backed only for the high-call routine tables named in `references/airtable_cache_contract.md`. Read that contract before relying on cached helper-memory, routing, preference, validation, packaging, or configuration-name state.

On every explicit DCOIR re-anchor/startup recovery/resume-first recovery, refresh or recreate only the routine caches named in the contract. If a routine cache is missing, unreadable, stale, or inconsistent with live schema/table identity, refresh before use. Tables listed as conditional/live-read are not routine caches; read them from live Airtable only when the active task requires them. After this skill writes to a routine cached table, refresh the cache and verify the contract-defined freshness indicator. Local cache is advisory only; live Airtable remains authority for writes, deletes, migrations, and dependency-sensitive decisions.

## Output contract
For tool recommendations, respond with:
1. Selected tool
2. Why this tool
3. Safety checks
4. PowerShell launcher
5. Expected upload/output
6. Stop conditions

For blocked GitHub/repo update recovery, respond with:
1. Failed lane and evidence
2. Bounded retry or alternate lane chosen
3. Next lane in the ladder
4. Verification evidence required
5. Airtable state updated

For new tool candidates, respond with:
1. Reusable pattern
2. Proposed tool/module contract
3. Repo files to create/update
4. Airtable registry row fields
5. Delivery lane
6. Validation step
