---
name: dcoir-session-resume
description: resume the africom_soc_ir / dcoir workspace from the current airtable-first operational authority model and current queue state.
---
<!-- skill-marker: updated-skill|20260429T171500Z|airtable-operational-schema-alignment|source-update|dcoir-session-resume|SKILL.md -->

# DCOIR Session Resume

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



Resume the AFRICOM_SOC_IR / DCOIR workspace from the current Airtable-first authority model.

## Workspace gate
Proceed only when the current chat, project, or custom GPT is operating as the AFRICOM_SOC_IR / DCOIR workspace.

## Default first-turn bootstrap use
On the first substantive AFRICOM_SOC_IR / DCOIR turn of every new session, invoke this skill before other substantive project work even if the operator did not explicitly ask to resume.

Use this first-turn bootstrap path to:
- re-anchor to the current control plane
- consume the explicit drift gate before trusting supporting continuity surfaces
- establish the current governed state that later skills and workflow choices should inherit
- hand off immediately into the required startup chain instead of leaving Airtable carry-forward state unread

Required startup chain after this skill clears the control plane:
1. `dcoir-memory-preflight`
2. `dcoir-session-tracker` Airtable leftover scan
3. conditional `dcoir-plan-tracker` Airtable active-plan scan when open plan state exists

## Operator preference readback
During session-start bootstrap, read Airtable table `Operator Preferences` after the control plane is re-anchored and before handing off to the rest of the startup chain.

For that readback:
- prefer active implemented preferences scoped to `DCOIR workspace` or `both`
- surface only the few operator preferences that materially affect response style, workflow branching, or execution posture for the current session
- treat those surfaced preferences as current session defaults unless the operator overrides them in the live branch
- do not render Airtable UI just to prove the preference read happened
- do not use `display_records_for_table` during startup or re-anchor preference reads; prefer silent Airtable reads such as `search_records` or equivalent non-display retrieval
- if a visible Airtable view would help, ask the operator first instead of showing it automatically
- when no relevant active operator preference is found, say that plainly and continue with the normal startup chain

## Three-division governance table awareness
During session-start bootstrap and any resume/current-state report, consult Airtable `CONTROL-STARTUP-AIRTABLE-FIRST`, Queue Control, Work Items, active Plans, Work Items for task execution, Session Checkpoints, Operator Preferences, and relevant governance/registry tables before selecting the next work lane. Do not fetch GitHub `CP-01`/`CP-02` for normal startup when Airtable startup authority is present.

Use silent Airtable reads only for these tables unless the operator explicitly asks to display them:
- `Governance Control Plane`: current GitHub / Airtable / ChatGPT Project authority model and startup-chain expectations
- `Repo Surface Registry`: major repo surfaces, their authority status, keep/delete state, replacement surface, and owning division
- `Admin Registry skill-state rows`: installed and governed `dcoir-*` skills, startup relevance, invocation priority, parity status, and maintenance state
- `Repo File Classification Detail`: optional supporting file-level evidence for cleanup or repo-shrink decisions; do not treat it as control-plane authority

Startup use rules:
- Use `Governance Control Plane` to confirm the three-division model when the operator asks where project authority lives or when a branch may change repo/Airtable/Project boundaries.
- Use `Admin Registry skill-state rows` to improve skill awareness before claiming no helper skill exists for a task family.
- Use `Repo Surface Registry` before recommending repo cleanup, deletion, surface movement, or GitHub-versus-Airtable boundary changes.
- Do not let `Repo File Classification Detail` override GitHub source authority; use it only as snapshot-derived supporting evidence.
- Continue to treat Airtable `Queue Control`, `Work Items`, and active `Plans` as the live queue authority.


## Airtable todo authority
Treat Airtable `Queue Control`, Airtable `Work Items`, and active Airtable `Plans` as the sole live todo authority for ordinary queue priority, resume order, branch supersession, and active-versus-parked decisions.

Use GitHub for:
- the control plane
- governed readable source
- promoted history and important decisions

Do not use GitHub todo files as the live queue authority once Airtable queue-control state exists.

## Resume-status fast path
When the current request is a simple current-state, resume-status, or "where are we" check, use the governed GitHub readable-text fast path first.

Default fast path order:
1. `dcoir_skills/project_discovery_contract.json` when present
2. Airtable `CONTROL-STARTUP-AIRTABLE-FIRST` and live Airtable state
3. GitHub manifest/change log only for repository-source fallback
4. the current supporting continuity surfaces resolved from the control plane and drift gate

For this resume-status fast path:
- prefer governed GitHub readable-text fetches only
- keep Airtable reads silent by default and do not render Airtable UI during resume-status or startup work
- do not use `display_records_for_table` during resume-status or startup work; prefer `search_records` or other non-display Airtable reads
- if a visible Airtable view might materially help, ask the operator first instead of displaying it automatically
- do not consider repo clone, archive download, raw web fetch, container execution, or local script execution before trying the governed GitHub connector path
- escalate to alternate acquisition or execution lanes only when the GitHub connector cannot retrieve the required governed readable files or the drift gate cannot be resolved from fetched text alone

## Strong trigger phrases
- `where are we`
- `resume`
- `resume where we left off`
- `what is current`
- `what changed`
- `get me back on track`

## First-anchor rule
Use the first available bootstrap anchor in this order:
1. AFRICOM_SOC_IR / DCOIR workspace instructions if present.
2. Uploaded bootstrap pointer such as `CP-00_DCOIR_Airtable_First_Bootstrap.txt` if present; treat it as a pointer only.
3. Airtable `Governance Control Plane` row `CONTROL-STARTUP-AIRTABLE-FIRST` when present.
4. Airtable live state tables: `Session Checkpoints`, `Queue Control`, `Work Items`, active `Plans`, `Work Items for task execution`, and `Operator Preferences`.
5. GitHub repository `malwaredevil/dcoir-collector` only when the immediate task requires governed source/readback, promoted-history comparison, packaging, or explicit repo cleanup/source-role review.

## Core workflow
1. Determine whether the current use is `session_start_bootstrap` or an explicit user resume request.
2. Read Airtable `Governance Control Plane` row `CONTROL-STARTUP-AIRTABLE-FIRST`, then live `Session Checkpoints`, `Queue Control`, `Work Items`, active `Plans`, `Work Items for task execution`, and `Operator Preferences` for startup/resume state.
3. Read `dcoir_skills/project_discovery_contract.json` and GitHub `CP-01`/`CP-02` only when the resume request requires governed source/readback, promoted-history comparison, packaging, or explicit repo cleanup/source-role review.
4. Invoke `dcoir-source-authority-auditor` as a drift gate only when source-authority, repo cleanup, skill-source governance, or promoted-history comparison is in scope. For ordinary startup/resume, use Airtable live authority first and report missing GitHub CP files as non-blocking if Airtable replacement rows exist.
6. If the drift gate returns `hard_stop_conflict`, stop and report the exact conflict plainly instead of producing a normal resume summary.
7. If the drift gate returns `proceed_bounded`, continue only with bounded claims and say exactly which active surfaces were unavailable.
8. If the drift gate returns `clear_to_proceed`, continue into the normal resume summary.
9. Use only Airtable live records as queue/resume authority unless the task explicitly requires governed GitHub source content.
10. Use GitHub todo files and old current-state narratives only as promoted history or comparison support after Airtable authority is established.
11. If Airtable startup authority conflicts with an older GitHub CP/current-state narrative, prefer Airtable for live queue/startup and report the GitHub surface as promoted-history drift unless the source task explicitly requires a hard-stop comparison.
12. For `session_start_bootstrap` and explicit resume-status requests, use the Airtable-first resume-status fast path by default.
13. For `session_start_bootstrap`, invoke `dcoir-memory-preflight` immediately after Airtable startup authority is re-anchored.
14. After `dcoir-memory-preflight`, invoke `dcoir-session-tracker` to scan Airtable durable leftovers, open idea-capture items, and buffered promotion candidates that are not yet durably represented in governed GitHub sources.
15. After the session-tracker leftover scan, invoke `dcoir-plan-tracker` only when open or active Airtable-backed plan state exists, or when the leftover scan indicates unfinished plan work.
16. Read the active Airtable `Queue Control` row when it exists using silent Airtable retrieval only.
17. Read active Airtable `Work Items` rows and active Airtable `Plans` rows needed to resolve the current live queue branch using silent Airtable retrieval only.
18. During startup or re-anchor, do not use `display_records_for_table`; prefer `search_records` or other non-display Airtable reads.
19. If a visible Airtable view would help, ask the operator first instead of displaying it automatically.
20. Treat Airtable queue state as the live source for ordinary next-work-item priority and treat older GitHub todo files only as retired history or migration surfaces.
21. Surface startup leftovers as carry-forward context, but distinguish clearly between governed GitHub source/promoted-history context and Airtable durable working-state leftovers.
22. When the current workflow favors grouped manual updates or grouped skill-install waves, prefer grouped ready follow-up prompts over one-skill-at-a-time prompts.

## Required rules
- Treat the first substantive session turn as a mandatory resume bootstrap point for this workspace unless the request is clearly outside DCOIR scope.
- Treat `dcoir-memory-preflight`, `dcoir-session-tracker`, and conditional `dcoir-plan-tracker` recovery as part of the same startup chain instead of optional later conveniences.
- Treat the current AFRICOM_SOC_IR / DCOIR workspace as the operational workspace, not the historical archive.
- Treat Project Instructions plus CP-00 pointer plus Airtable `CONTROL-STARTUP-AIRTABLE-FIRST` plus live Airtable state as the default startup authority. Treat GitHub manifest/change log only as repository-source fallback or promoted history when explicitly in scope.
- Treat the repository named in `dcoir_skills/project_discovery_contract.json` as the sole working source for readable governed text when that contract is present.
- Treat Airtable `Queue Control`, `Work Items`, and active `Plans` as the sole live todo authority for queue order and resume priority.
- Treat GitHub todo files as retired live-queue surfaces once the Airtable queue-control record exists.
- Fall back to `malwaredevil/dcoir-collector` only when the governed discovery contract is unavailable.
- Treat uploaded bootstrap files and local workspace files as anchors or supporting assets, not as a second editable readable text repository.
- Do not decide authority.
- Do not promote files.
- Do not rewrite content.
- Do not infer missing files.
- Do not treat non-current versions as authoritative unless the operator explicitly asks for rollback reference or history.
- Do not reimplement a weaker duplicate of the current-state drift logic inside this skill.
- Do not let a superficially familiar work line override an explicit `hard_stop_conflict` result from the drift gate.
- Do not evaluate alternate acquisition lanes before trying the governed GitHub connector path for resume-only status work.
- Do not broaden a simple resume-status request into clone, container, archive-download, raw-web, or local-script work unless the primary governed readable-text lane actually fails or cannot resolve the drift gate.
- Do not skip the Airtable leftover recovery steps just because the governed resume summary already looks stable; carry-forward state must still be checked.
- Do not render Airtable UI during startup or re-anchor unless the operator explicitly asked for it or explicitly approved it after being asked.
- Do not use `display_records_for_table` during startup or re-anchor.
- Treat “ask before showing Airtable” as the only override path for visible Airtable displays during startup or re-anchor.

## Output contract
Return sections in this exact order:
1. Current stable baseline
2. Current governed GitHub readable sources
3. Current supporting GitHub assets
4. Current governance/control-plane state
5. Current validated status
6. Current next planned work item
7. Refresh watchlist
8. Recommended next move
9. Ready follow-up prompts

See `references/resume_output_contract.md` for the exact section intent and compact-output rules.

## Output behavior
- Default to plain English, short sentences, and state-first wording.
- Keep startup replies concise unless there is a real conflict, blocker, or materially important drift.
- When Airtable queue-control state exists, let it set the current next planned work item before older GitHub handoff text.
- When startup leftovers exist, summarize them briefly in the current next planned work item, refresh watchlist, or recommended next move rather than silently dropping them.
- Give one recommended next move only.
- Prefer 2 short ready follow-up prompts by default, not a broad menu.
- Use plain-language prompts, not internal tool syntax.
- Include packaging prompts only when relevant.
- Prefer grouped prompts when the current workflow favors batched manual updates or grouped skill-install waves.
- Prefer the next most useful artifact or action, not a broad menu.
- When the path is bounded, say which active surfaces were unavailable.
- When the path hard-stops, do not continue into the normal nine-section resume summary.

## Airtable testing surface default
When the resumed work is collector testing, Gemini testing, live evaluation, or validation-status follow-through, treat Airtable table `Validation Test Cases` as the default durable manual-testing surface after the normal resume/bootstrap chain completes.

For those testing branches:
- open the Airtable testing catalog early instead of reconstructing the test plan from chat continuity alone
- prefer the active rows relevant to the current build or artifact
- surface that table as the starting testing plan before proposing new ad hoc test steps
- preserve repo and control-plane authority for executable source, packaging, workflows, and governed readable docs
