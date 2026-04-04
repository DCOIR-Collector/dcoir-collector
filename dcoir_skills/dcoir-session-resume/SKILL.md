---
name: dcoir-session-resume
description: resume the africom_soc_ir / dcoir workspace from the current authoritative control plane. use at the first substantive turn of every new africom_soc_ir or dcoir session as the mandatory bootstrap resume step, even when the user did not explicitly ask to resume, and also use when the user asks where are we, resume, resume where we left off, what is current, what changed, or get me back on track. before trusting supporting continuity surfaces, consume the shared drift gate through dcoir-source-authority-auditor so stale or contradictory current-state signals do not produce a normal resume summary.
---

Resume the AFRICOM_SOC_IR / DCOIR workspace from the current authoritative control plane.

## Workspace gate
Proceed only when the current chat, project, or custom GPT is operating as the AFRICOM_SOC_IR / DCOIR workspace.

## Default first-turn bootstrap use
On the first substantive AFRICOM_SOC_IR / DCOIR turn of every new session, invoke this skill before other substantive project work even if the user did not explicitly ask to resume.

Use this first-turn bootstrap path to:
- re-anchor to the current control plane
- consume the explicit drift gate before trusting supporting continuity surfaces
- establish the current governed state that later skills and workflow choices should inherit

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

## Required rules
- Treat the first substantive session turn as a mandatory resume bootstrap point for this workspace unless the request is clearly outside DCOIR scope.
- Treat the current AFRICOM_SOC_IR / DCOIR workspace as the operational workspace, not the historical archive.
- Treat the first available bootstrap anchor plus the current manifest plus the current change log as the default control plane.
- Treat the repository named in `dcoir_skills/project_discovery_contract.json` as the sole working source for readable governed text when that contract is present.
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
- Give one recommended next move only.
- Then give 2 to 4 short ready follow-up prompts.
- Use plain-language prompts, not internal tool syntax.
- Include packaging prompts only when relevant to the current state.
- Prefer the next most useful artifact or action, not a broad menu.
- When the path is bounded, say which active surfaces were unavailable.
- When the path hard-stops, do not continue into the normal nine-section resume summary.

See `references/resume_output_contract.md` for the exact section intent and prompt rules.
