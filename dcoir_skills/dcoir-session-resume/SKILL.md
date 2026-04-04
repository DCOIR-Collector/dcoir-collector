---
name: dcoir-session-resume
description: resume the africom_soc_ir / dcoir workspace from the current authoritative control plane. use when the user asks where are we, resume, resume where we left off, what is current, what changed, or get me back on track in the africom_soc_ir or dcoir workspace, including a custom gpt that uses a github-primary bootstrap and actions. before trusting supporting continuity surfaces, consume the shared drift gate through dcoir-source-authority-auditor so stale or contradictory current-state signals do not produce a normal resume summary.
---

Resume the AFRICOM_SOC_IR / DCOIR workspace from the current authoritative control plane.

## Workspace gate
Proceed only when the current chat, project, or custom GPT is operating as the AFRICOM_SOC_IR / DCOIR workspace.

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
3. Then GitHub control plane in repository `malwaredevil/dcoir-collector`.

## Core workflow
1. Read the current manifest file first. Expected current path: `project_sources/CP-01_DCOIR_Version_Manifest.txt`.
2. Read the current change log second. Expected current path: `project_sources/CP-02_DCOIR_Change_Log.txt`.
3. Invoke `dcoir-source-authority-auditor` as the explicit drift gate before trusting supporting continuity surfaces such as `LOG-03`, `LOG-05`, `LOG-01_DCOIR_Todo_Log.txt`, `LOG-01_DCOIR_Todo_Index.txt`, and `todo/01_Active_Now.txt`.
4. If the drift gate returns `hard_stop_conflict`, stop and report the exact conflict plainly instead of producing a normal resume summary.
5. If the drift gate returns `proceed_bounded`, continue only with bounded claims and say exactly which active surfaces were unavailable.
6. If the drift gate returns `clear_to_proceed`, continue into the normal resume summary.
7. Use only files or patterns marked current in the manifest as authoritative governed GitHub readable sources.
8. Use the current todo structure and current session handoff brief only as supporting context after the drift gate clears or bounds the path.
9. If the manifest, change log, or workspace state conflict, stop and report the conflict plainly.

## Required rules
- Treat the current AFRICOM_SOC_IR / DCOIR workspace as the operational workspace, not the historical archive.
- Treat the first available bootstrap anchor plus the current manifest plus the current change log as the default control plane.
- Treat GitHub repository `malwaredevil/dcoir-collector` as the sole working source for readable governed text.
- Treat uploaded bootstrap files and local workspace files as anchors or supporting assets, not as a second editable readable text repository.
- Do not decide authority.
- Do not promote files.
- Do not rewrite content.
- Do not infer missing files.
- Do not treat non-current versions as authoritative unless the user explicitly asks for rollback reference or history.
- Do not reimplement a weaker duplicate of the current-state drift logic inside this skill.
- Do not let a superficially familiar work line override an explicit `hard_stop_conflict` result from the drift gate.

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
