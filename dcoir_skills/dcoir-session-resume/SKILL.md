---
name: dcoir-session-resume
description: resume the africom_soc_ir / dcoir workspace from the current authoritative control plane. use at the first substantive turn of every new africom_soc_ir or dcoir session to re-anchor to the current state, then continue the required startup chain through dcoir-memory-preflight, dcoir-session-tracker airtable leftover recovery, and conditional dcoir-plan-tracker active-plan recovery. also use when the operator asks where are we, resume, what is current, what changed, or get me back on track. prefer the governed github readable-text fast path for simple current-state checks and use grouped, state-aware follow-up prompts when the current workflow favors batched manual updates or skill-install waves.
---

# DCOIR Session Resume

<!-- skill-marker: updated-skill|20260415T154500Z|dcoir-session-resume|SKILL.md|R02 -->

Resume the AFRICOM_SOC_IR / DCOIR workspace from the current authoritative control plane.

## Workspace gate
Proceed only when the current chat, project, or custom GPT is operating as the AFRICOM_SOC_IR / DCOIR workspace.


## Operator preference readback
During session-start bootstrap, read Airtable table `Operator Preferences` after the control plane is re-anchored and before handing off to the rest of the startup chain.

For that readback:
- prefer active implemented preferences scoped to `DCOIR workspace` or `both`
- surface only the few operator preferences that materially affect response style, workflow branching, or execution posture for the current session
- treat those surfaced preferences as current session defaults unless the operator overrides them in the live branch
- when no relevant active operator preference is found, say that plainly and continue with the normal startup chain

## Airtable todo authority
Treat Airtable `Queue Control`, Airtable `Work Items`, and active Airtable `Plans` as the sole live todo authority for ordinary queue priority, resume order, branch supersession, and active-versus-parked decisions.

Use GitHub for:
- the control plane
- governed readable source
- promoted history and important decisions

Do not use GitHub todo files as the live queue authority once Airtable queue-control state exists.

<!-- skill-marker: updated-skill|20260415T135556Z|dcoir-session-resume|SKILL.md|R01 -->


## Operator preference readback

During session-start bootstrap, read Airtable table `Operator Preferences` after the control plane is re-anchored and before handing off to the rest of the startup chain.

For that readback:
- prefer active implemented preferences scoped to `DCOIR workspace` or `both`
- surface only the few operator preferences that materially affect response style, workflow branching, or execution posture for the current session
- treat those surfaced preferences as current session defaults unless the operator overrides them in the live branch
- when no relevant active operator preference is found, say that plainly and continue with the normal startup chain


## Default first-turn bootstrap use
On the first substantive AFRICOM_SOC_IR / DCOIR turn of every new session, invoke this skill before other substantive project work even if the user did not explicitly ask to resume.

Use this first-turn bootstrap path to:
- re-anchor to the current control plane
- consume the explicit drift gate before trusting supporting continuity surfaces
- establish the current governed state that later skills and workflow choices should inherit
- hand off immediately into the required startup chain instead of leaving Airtable carry-forward state unread

Required startup chain after this skill clears the control plane:
1. `dcoir-memory-preflight`
2. `dcoir-session-tracker` Airtable leftover scan
3. conditional `dcoir-plan-tracker` Airtable active-plan scan when open plan state exists

## Resume-status fast path
When the current request is a simple current-state, resume-status, or "where are we" check, use the governed GitHub readable-text fast path first.

Default fast path order:
1. `dcoir_skills/project_discovery_contract.json` when present
2. the current manifest
3. the current change log
4. the current supporting continuity surfaces resolved from the control plane and drift gate

For this resume-status fast path:
- prefer governed GitHub readable-text fetches only
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
2. Uploaded bootstrap pointer such as `CP-00_DCOIR_GitHub_Primary_Bootstrap.txt` if present.
3. Then GitHub control plane in the repository named in `dcoir_skills/project_discovery_contract.json` when that contract is present.
4. If no governed discovery contract is available, fall back to repository `malwaredevil/dcoir-collector`.

## Core workflow
1. Determine whether the current use is `session_start_bootstrap` or an explicit user resume request.
2. Read `dcoir_skills/project_discovery_contract.json` when it is present and use it to resolve the current manifest path, change-log path, supporting continuity surfaces, and repository name.
3. Read the current manifest file first. Expected current path remains `project_sources/CP-01_DCOIR_Version_Manifest.txt` when no better contract-driven path is available.
4. Read the current change log second. Expected current path remains `project_sources/CP-02_DCOIR_Change_Log.txt` when no better contract-driven path is available.
5. Invoke `dcoir-source-authority-auditor` as the explicit drift gate before trusting the supporting continuity surfaces resolved from the current discovery contract or the current default active-surface set.
6. If the drift gate returns `hard_stop_conflict`, stop and report the exact conflict plainly instead of producing a normal resume summary.
7. If the drift gate returns `proceed_bounded`, continue only with bounded claims and say exactly which active surfaces were unavailable.
8. If the drift gate returns `clear_to_proceed`, continue into the normal resume summary.
9. Use only files or patterns marked current in the manifest as authoritative governed GitHub readable sources.
10. Use the current todo structure and current session handoff brief only as supporting context after the drift gate clears or bounds the path.
11. If the manifest, change log, or workspace state conflict, stop and report the conflict plainly.
12. For `session_start_bootstrap` and explicit resume-status requests, use the resume-status fast path by default unless the current task already shows that the primary GitHub readable-text lane cannot resolve the state.
13. For `session_start_bootstrap`, invoke `dcoir-memory-preflight` immediately after the control plane is re-anchored.
14. After `dcoir-memory-preflight`, invoke `dcoir-session-tracker` to scan Airtable durable leftovers, open idea-capture items, and buffered promotion candidates that are not yet durably represented in governed GitHub sources.
15. After the session-tracker leftover scan, invoke `dcoir-plan-tracker` only when open or active Airtable-backed plan state exists, or when the leftover scan indicates unfinished plan work.
16. Read the active Airtable `Queue Control` row when it exists.
17. Read active Airtable `Work Items` rows and active Airtable `Plans` rows needed to resolve the current live queue branch.
18. Treat Airtable queue state as the live source for ordinary next-work-item priority and treat older GitHub todo files only as retired history or migration surfaces.
19. Surface startup leftovers as carry-forward context, but distinguish clearly between governed GitHub authority and Airtable durable working-state leftovers.
20. When the current workflow favors grouped manual updates or grouped skill-install waves, prefer grouped ready follow-up prompts over one-skill-at-a-time prompts.

## Required rules
- Treat the first substantive session turn as a mandatory resume bootstrap point for this workspace unless the request is clearly outside DCOIR scope.
- Treat `dcoir-memory-preflight`, `dcoir-session-tracker`, and conditional `dcoir-plan-tracker` recovery as part of the same startup chain instead of optional later conveniences.
- Treat the current AFRICOM_SOC_IR / DCOIR workspace as the operational workspace, not the historical archive.
- Treat the first available bootstrap anchor plus the current manifest plus the current change log as the default control plane.
- Treat the repository named in `dcoir_skills/project_discovery_contract.json` as the sole working source for readable governed text when that contract is present.
- Treat Airtable `Queue Control`, `Work Items`, and active `Plans` as the sole live todo authority for queue order and resume priority.
- Treat GitHub todo files as retired live-queue surfaces once the Airtable queue-control record exists.
- Fall back to `malwaredevil/dcoir-collector` only when the governed discovery contract is unavailable.
- Treat uploaded bootstrap files and local workspace files as anchors or supporting assets, not as a second editable readable text repository.
- Do not decide authority.
- Do not promote files.
- Do not rewrite content.
- Do not infer missing files.
- Do not treat non-current versions as authoritative unless the user explicitly asks for rollback reference or history.
- Do not reimplement a weaker duplicate of the current-state drift logic inside this skill.
- Do not let a superficially familiar work line override an explicit `hard_stop_conflict` result from the drift gate.
- Do not evaluate alternate acquisition lanes before trying the governed GitHub connector path for resume-only status work.
- Do not broaden a simple resume-status request into clone, container, archive-download, raw-web, or local-script work unless the primary governed readable-text lane actually fails or cannot resolve the drift gate.
- Do not skip the Airtable leftover recovery steps just because the governed resume summary already looks stable; carry-forward state must still be checked.

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

## Output behavior
- Keep the response concise and state-first.
- When Airtable queue-control state exists, let it set the current next planned work item before older GitHub handoff text.
- When startup leftovers exist, summarize them briefly in the current next planned work item, refresh watchlist, or recommended next move rather than silently dropping them.
- Give one recommended next move only.
- Then give 2 to 4 short ready follow-up prompts.
- Use plain-language prompts, not internal tool syntax.
- Include packaging prompts only when relevant to the current state.
- Prefer grouped prompts when the current workflow favors batched manual updates or grouped skill-install waves.
- Prefer the next most useful artifact or action, not a broad menu.
- When the path is bounded, say which active surfaces were unavailable.
- When the path hard-stops, do not continue into the normal nine-section resume summary.

See `references/resume_output_contract.md` for the exact section intent and prompt rules.

## Airtable testing surface default

When the resumed work is collector testing, Gemini testing, live evaluation, or validation-status follow-through, treat Airtable table `Validation Test Cases` as the default durable manual-testing surface after the normal resume/bootstrap chain completes.

For those testing branches:
- open the Airtable testing catalog early instead of reconstructing the test plan from chat continuity alone
- prefer the active rows relevant to the current build or artifact
- surface that table as the starting testing plan before proposing new ad hoc test steps
- preserve repo and control-plane authority for executable source, packaging, workflows, and governed readable docs
