# Knowledge - Collector - Feature and Output Contract Reference

_Source-grounded collector anchor page for modes, quick aliases, targeted collection, enrichment, output surfaces, and runtime contract_

**Summary:** Use this page as the main operator reference when you only have `DCOIR_Collector.ps1` and `DCOIR_Collector.zip` and need to understand what the collector can do, which entry path to choose, what outputs to expect, and what the current implementation does not guarantee.

---

## Operator starting point

This page is written for the operator who did not build the collector.

Start here when you need to answer questions like:

- What are the real top-level modes?
- When should I use Tier 1 versus Tier 2?
- Which quick alias already matches what I want to do?
- When should I use targeted collection instead of baseline collection?
- What does enrichment really do in practice?
- Which outputs should I look at first?
- What does the collector guarantee, and what does it not guarantee?

This page is the collector anchor page.
Dependent runbooks should align to this page rather than restating partial copies of the source contract.

---

## Collector mental model

The collector is not one generic "collect more" button.
It has three different top-level operating modes:

| Mode | Purpose | Typical operator question |
| --- | --- | --- |
| `Collect` | Create a baseline or targeted host evidence package | What broad or scoped host evidence should I collect now? |
| `Enrich` | Run one bounded follow-up action tied to an evidence question | What specific process, path, service, task, log, or file needs deeper follow-up? |
| `Cleanup` | Remove runtime/output material after evidence is safe | Have I already retrieved or preserved what I need? |

The safest general pattern is:

1. collect only what matches the current question;
2. review summary surfaces before raw volume;
3. enrich only when one bounded follow-up question exists;
4. retrieve specific evidence carriers when a known artifact matters more than another broad run;
5. clean up only after evidence is safe.

---

## Top-level modes

| Mode | What it does | Important boundary |
| --- | --- | --- |
| `Collect` | Builds the run structure, stages the runtime ZIP, expands tools, collects baseline artifacts, writes reports/manifests, and bundles the result | Collection breadth does not prove maliciousness by itself |
| `Enrich` | Reuses the existing run state and appends one bounded follow-up action into an enrichment session | Enrichment is for narrower follow-up, not a second baseline pass |
| `Cleanup` | Removes the run root and consumed package state | Cleanup is not the same as retrieval and should happen only after evidence is safe |

---

## Tier model

| Tier | Purpose | Normal use |
| --- | --- | --- |
| `T1` | First-pass baseline collection | Start here when you need a broad but still triage-oriented evidence package |
| `T2` | Deeper persistence and configuration context | Use only when Tier 1 or current evidence leaves a specific unresolved deeper question |

Tier selection is a depth decision, not a confidence decision.
Use T2 because a named question needs deeper persistence/configuration context, not because T1 feels incomplete in the abstract.

---

## Entry styles actually supported

| Entry style | Use when | Example |
| --- | --- | --- |
| Explicit parameters | You want the clearest source-aligned invocation | `-Mode Collect -Tier T1 -Hours 24` |
| `-Quick` shortcut | The collector already exposes a matching common path | `-Quick collect-t1` |
| `-ShowHelp` | You need the collector’s built-in operator help | `-ShowHelp` |
| `-ShowVersion` | You need to prove runtime/build identity before a stateful step | `-ShowVersion` |

---

## Common parameters

| Parameter | Purpose | Notes |
| --- | --- | --- |
| `-Mode` | Select `Collect`, `Enrich`, or `Cleanup` | Top-level execution selector |
| `-Tier` | Select `T1` or `T2` | Used for collect depth |
| `-Hours` | Set the lookback window | Still relevant even when targeted mode is used |
| `-OutRoot` | Select the output root | Used to locate run state, reports, artifacts, bundles, and cleanup target |
| `-PackageName` | Select the runtime ZIP name | Defaults to `DCOIR_Collector.zip` |
| `-RunId` | Reuse or target a specific run state | Usually auto-created for collect |
| `-Quick` | Use a supported shortcut | See the source-grounded quick alias list below |
| `-ShowHelp` | Print help | Can also route through help quick aliases |
| `-ShowVersion` | Print version/build identity | Use before stateful validation or package-movement questions |

---

## Quick aliases accepted by source

These are the quick aliases currently accepted by the collector quick resolver. Some are
also highlighted in the help surface as common operator shortcuts, but this table is the
source-backed complete quick set. Operators and Gemini should not invent commands outside
this supported set.

### Collect quick aliases

| Quick alias | Purpose |
| --- | --- |
| `collect-t1` | Run Tier 1 collect |
| `collect-t2` | Run Tier 2 collect |
| `collect-targeted-popup` | Start a targeted popup-oriented collection path |
| `collect-targeted-script` | Start a targeted script-execution-oriented collection path |

### Enrich quick aliases

Each `enrich-start-*` alias starts a new enrich session for that action. The matching
`enrich-add-*` alias adds the same action to the currently open session or to the explicit
non-finalized session supplied with `-EnrichSessionId`.

| Quick alias family | Action | Required target |
| --- | --- | --- |
| `enrich-start-tcp`, `enrich-add-tcp` | Refresh TCP connection evidence | None |
| `enrich-start-logtext`, `enrich-add-logtext` | Export event log text | Optional `-Target <log name>`; defaults to Security |
| `enrich-start-lograw`, `enrich-add-lograw` | Export raw EVTX log data | Optional `-Target <log name>`; defaults to Security |
| `enrich-start-sigcheck`, `enrich-add-sigcheck` | Run signature/hash review for a path | `-Target <path>` |
| `enrich-start-listdlls`, `enrich-add-listdlls` | Review loaded modules for a PID | `-Target <pid>` |
| `enrich-start-access-file`, `enrich-add-access-file` | Run access-check review for a file path | `-Target <path>` |
| `enrich-start-access-service`, `enrich-add-access-service` | Run access-check review for a service | `-Target <service name>` |
| `enrich-start-access-reg`, `enrich-add-access-reg` | Run access-check review for a registry path | `-Target <registry path>` |
| `enrich-start-strings`, `enrich-add-strings` | Extract strings from a path | `-Target <path>` |
| `enrich-start-streams`, `enrich-add-streams` | Check alternate data streams for a path | `-Target <path>` |
| `enrich-start-pull-file`, `enrich-add-pull-file` | Retrieve a suspicious file | `-Target <path>` |
| `enrich-start-pull-script`, `enrich-add-pull-script` | Retrieve a suspicious script or config file | `-Target <path>` |
| `enrich-start-pull-task`, `enrich-add-pull-task` | Retrieve scheduled task XML | `-Target <task path>` |
| `enrich-start-pull-service`, `enrich-add-pull-service` | Retrieve a service binary | `-Target <service name>` |
| `enrich-start-pull-wmi-file`, `enrich-add-pull-wmi-file` | Retrieve a file referenced by WMI persistence evidence | `-Target <path>` |
| `enrich-finalize` | Finalize and bundle the current open enrich session, or the explicit non-finalized session supplied with `-EnrichSessionId` | None unless finalizing an explicit session |

### Cleanup and help quick aliases

| Quick alias | Purpose |
| --- | --- |
| `cleanup` | Run cleanup |
| `help` | Print general help |
| `help-collect` | Print collect-specific contextual help |
| `help-enrich` | Print enrich-specific contextual help |
| `help-cleanup` | Print cleanup-specific contextual help |
| `help-targeted` | Print targeted-collection-specific contextual help |
| `help-version` | Print version/build guidance |

---

## Targeted collection contract

Use targeted collection when the question is narrower than a generic baseline and you have specific context such as a time window, user report, focal process, focal path, or focal indicator.

### Targeted parameters

| Parameter | Purpose |
| --- | --- |
| `-Targeted` | Enable targeted collection posture |
| `-TargetProfile` | Choose the targeted profile |
| `-WindowStart` | Set explicit requested start time |
| `-WindowEnd` | Set explicit requested end time |
| `-IncludeArtifactCategory` | Prefer specific artifact families |
| `-FocusProcess` | Name a focal process |
| `-FocusPath` | Name a focal path |
| `-FocusIndicator` | Name a focal indicator |
| `-FocusIndicatorType` | Clarify indicator type |
| `-UserReport` | Preserve the user/analyst problem statement |

Exact event-window filtering is source-backed for event-log text and raw EVTX lanes that route through the explicit event-window helpers. Targeted mode still does not mean every artifact family is exact-window filtered; use the scope and plan surfaces to identify the requested boundary and event-log artifacts to verify the filtered evidence carrier.

### Targeted profiles actually exposed by source

| Profile | Intended use |
| --- | --- |
| `Generic` | Narrow the request without a more specific profile fit |
| `PopupWindow` | Follow a user-reported popup or likely GUI-launching event |
| `ScriptExecution` | Follow suspicious script or command execution |
| `PersistenceFollowUp` | Follow a persistence-oriented lead |
| `NetworkOnly` | Follow a primarily network-oriented lead |
| `ProcessAndPowerShell` | Follow a process-plus-PowerShell execution lead |

### Current implementation boundary

The current source is explicit about a boundary that operators must understand:

- targeted mode narrows analyst guidance, collection scope intent, artifact prioritization, and recommended next actions;
- it does **not** yet rewrite every baseline collection helper into exact start/end timestamp filtering across all artifact families.

That means targeted mode is still valuable and real, but it should not be described as universal exact filtering unless a narrower claim is backed by source and validation for that specific path.

---

## Enrichment session contract

Enrichment is session-based, not just action-based.
The collector keeps bounded follow-up work grouped into one session until the operator finalizes it.

### Session behavior actually visible in source

| Behavior | Meaning |
| --- | --- |
| Create new session | `enrich-start` style paths create a fresh session |
| Reuse current open session | `enrich-add` style paths append to the current open session when appropriate |
| Reuse by explicit id | Operators can target an existing session with `-EnrichSessionId` |
| Finalize session | Creates a bundle and closes the active non-finalized session |
| Reject finalized requested session | Explicit `-EnrichSessionId` cannot append to a session already finalized |
| Reject finalize without open session | `enrich-finalize` without `-EnrichSessionId` requires an existing open session |

### Session controls

| Parameter | Purpose |
| --- | --- |
| `-EnrichSessionId` | Continue or target a specific session |
| `-NewEnrichSession` | Force a new session |
| `-FinalizeEnrichSession` | Finalize the current or targeted session |
| `-Action` | Select the enrich action |

### Important session rule

The source-backed behavioral contract is:

- `enrich-start` creates a new session;
- `enrich-add` reuses the current open session unless explicitly overridden;
- `enrich-finalize` finalizes the current open session;
- `enrich-finalize -EnrichSessionId <id>` finalizes that specific non-finalized session;
- a finalized session cannot be appended to;
- a finalize-only call with no open session is rejected instead of creating an empty bundle.

Use one session for closely related follow-up.
Do not mix unrelated questions into one enrich session just because the session is open.

---

## Enrichment actions actually exposed by source

### Review-style enrich actions

These answer analyst-review questions without primarily staging a new retrieval artifact.

| Action | Typical use |
| --- | --- |
| `SigcheckPath` | Review signer, hashes, and version data for a suspicious path |
| `ListDllsPid` | Review loaded modules for a suspicious process |
| `AccessChkFile` | Review effective access for a file or directory |
| `AccessChkService` | Review effective access for a service |
| `AccessChkReg` | Review effective access for a registry location |
| `StringsPath` | Extract readable strings from a suspicious file |
| `StreamsPath` | Review alternate data streams |
| `TcpvconRefresh` | Refresh TCP view for network review |
| `LogText` | Export text-form event review data |

### Retrieval-style enrich actions

These stage or export a concrete evidence carrier for analyst pickup.

| Action | Typical use |
| --- | --- |
| `LogRaw` | Export raw EVTX for workstation review |
| `PullSuspiciousFile` | Stage a suspicious file for retrieval |
| `PullScriptOrConfig` | Stage a script or config file for retrieval |
| `PullTaskXml` | Export a scheduled task XML definition |
| `PullServiceBinary` | Stage the binary referenced by a service |
| `PullWmiReferencedFile` | Stage a file referenced by suspicious WMI persistence |

### Action-specific parameter families visible in source

| Parameter family | Common actions |
| --- | --- |
| `-Path` | file, script, config, task-name-as-path, WMI-referenced file |
| `-TargetPid` | process-centric review |
| `-ServiceName` | service review or service-binary retrieval |
| `-RegistryPath` | registry access review |
| `-LogName` | text or raw log export |
| `-EventId` | narrower log selection |
| `-MaxEvents` | bounded event count |

The exact best action should be chosen from the question you are trying to answer, not from the broadest available action.

---

## Runtime/package contract visible to operators

### PS1-first delivery contract

The current governed runtime contract is PS1-first.
Operators should treat the PowerShell runtime as the primary supported delivery path unless an explicit future promotion decision changes that contract.

### Retained runtime ZIP

The governed retained runtime ZIP is `DCOIR_Collector.zip`.
It is part of the current packaging/runtime model and should not be mentally replaced with an imagined newer source of truth.

### Transport-safe delivery rule

The packaging manifest and packaging pipeline docs make clear that the delivery artifact uses transport-safe `.txt` suffixes for script entries inside the delivery package.
That matters when handling packaged contents and when reasoning about how the runtime is delivered.

### Optional EXE lane

The optional EXE exists, but it is additive.
It does not replace the PS1-first collector delivery contract.
Use the EXE page for wrapper-specific interpretation, not as a reason to blur the primary runtime contract.

---

## Collect output contract

A successful collect run emits more than one useful surface.
Operators should not reduce it to “one big bundle” or “one report.”

### Core collect status surfaces visible in source

| Surface | Why it matters |
| --- | --- |
| `STATUS` | Tells you whether the run succeeded, partially succeeded, or failed |
| `RUN_ID` | Anchors later enrich, retrieval, and cleanup work |
| `COLLECTOR_VERSION` | Confirms runtime version |
| `COLLECTOR_BUILD_IDENTITY` | Confirms runtime/build identity |

### Core collect report and context surfaces visible in source

| Surface | Why it matters |
| --- | --- |
| `METADATA_REPORT_PATH` | High-level run metadata and state |
| `EXECUTION_CONTEXT_PATH` | Elevation, identity, host, and runtime context |
| `SECURITY_AUDIT_POLICY_PATH` | Audit-policy visibility context |
| `AUDIT_POLICY_ACCESS_STATUS` | Signals whether the audit-policy surface was accessible as expected |
| `SECURITY_FILTERED_PATH` | Security-focused filtered output surface |
| `SECURITY_HIGH_SIGNAL_SUMMARY_PATH` | High-signal triage surface |
| `IS_ELEVATED` | Matters for visibility and interpretation |
| `NETSTAT_OWNER_AWARE_STATUS` | Explains whether owner-aware netstat succeeded |
| optional `NETSTAT_PID_ONLY_PATH` | Supplemental path when owner-aware capture cannot be used |

### Analyst-first collect guidance surfaces visible in source

| Surface | Why it matters |
| --- | --- |
| `ANALYST_OVERVIEW_PATH` | Source-backed analyst-first entry surface |
| `UPLOAD_SUMMARY_PATH` | Tells you what is recommended for upload/review first |
| `ATTACHMENT_BUDGET_MANIFEST_PATH` | Records the recommended upload set against environment budget |
| optional `UPLOAD_SAFE_CHUNK_MANIFEST_PATH` | Lists upload-safe chunk companions for oversized real text artifacts |
| `COLLECTION_SCOPE_PATH` | Documents the current collect scope |
| `PARALLELISM_ASSESSMENT_PATH` | Explains bounded runtime parallelism posture |
| optional `TARGETED_COLLECTION_PLAN_PATH` | Gives targeted analyst guidance when targeted mode is used |
| optional `PARALLEL_EXECUTION_PROOF_PATH` | Supports validation of bounded runtime overlap/proof surfaces |

### Bundle and handoff surfaces visible in source

| Surface | Why it matters |
| --- | --- |
| `COLLECT_BUNDLE_PATH` | Points to the collect bundle |
| `NEXT_GET_FILE` | Retrieval handoff |
| `CLEANUP_COMMAND` | Cleanup handoff |
| `DELETE_SCRIPT_COMMAND` | Response-action-safe script removal handoff |
| `GEMINI_UPLOAD_GUIDANCE` | Upload-priority guidance from the collector itself |

### Optional collect surfaces visible in source

| Surface | Why it matters |
| --- | --- |
| `DEFAULT_GEMINI_UPLOAD_SET_STATUS` | Shows whether the default upload set fits the expected budget |
| optional `UPLOAD_SAFE_CHUNK_MANIFEST_PATH` | Production chunk manifest for oversized real human-readable artifacts such as full-fidelity event text |
| optional `SYNTHETIC_OVERSIZE_SOURCE_PATH` | Validation-specific oversized-artifact surface |
| optional `CHUNK_MANIFEST_PATH` | Validation-specific chunking surface |
| `MaxEvents` in collection metadata | Confirms the bounded event-count setting used by collect-mode event surfaces |
| repeated `COLLECTOR_ERROR=` lines | Preserve bounded degraded-run facts without hiding them |

### Practical operator review order

For current source behavior, the safest first-pass review order is:

1. `ANALYST_OVERVIEW_PATH`
2. `UPLOAD_SUMMARY_PATH`
3. `METADATA_REPORT_PATH`
4. `ATTACHMENT_BUDGET_MANIFEST_PATH`
5. optional `UPLOAD_SAFE_CHUNK_MANIFEST_PATH` when the upload summary reports oversized full-fidelity text chunks
6. `COLLECTION_SCOPE_PATH`
7. `SECURITY_HIGH_SIGNAL_SUMMARY_PATH`
8. representative high-signal artifacts referenced by those surfaces
9. upload-safe full-fidelity chunks only when the high-signal summary is not enough
10. bundle retrieval or deeper local review after the first-pass question is clearer

Do not assume a merged baseline report is the primary review surface in the current build.

---

## Enrich output contract

A successful enrich run also emits more than one meaningful surface.

| Surface | Why it matters |
| --- | --- |
| `STATUS` | Success / partial / error |
| `RUN_ID` | Anchors back to the collect run |
| `COLLECTOR_VERSION` | Runtime identity |
| `COLLECTOR_BUILD_IDENTITY` | Build identity |
| `ENRICH_SESSION_ID` | Session anchor |
| `SESSION_RESOLUTION_MODE` | Tells you whether the session was created, reused, or explicitly targeted |
| `ENRICH_REPORT_PATH` | Session summary/report surface |
| optional `ACTION_ARTIFACT_PATH` | Per-action artifact surface when an action ran |
| optional `STAGED_PATH` | Retrieval-ready staged artifact |
| `SESSION_STATUS` | Whether the session remains open or has been finalized |
| optional `ENRICH_BUNDLE_PATH` | Finalized enrich bundle |
| `NEXT_GET_FILE` | Retrieval handoff when finalized |
| `DELETE_SCRIPT_COMMAND` | Script-removal handoff |

A finalize-only enrich path is a normal success path only when there is an open session or a valid non-finalized `-EnrichSessionId`.
When the operator runs `enrich-finalize` without a new action, current source emits the session report and finalization surfaces without `ACTION_ARTIFACT_PATH`; if there is no open or requested non-finalized session, the collector rejects the command instead of producing an empty bundle.

Review-style enrich actions often answer the next question directly.
Retrieval-style enrich actions often exist to hand you the next evidence carrier to inspect offline.

---

## Cleanup contract

Cleanup exists to remove run/output material after evidence is safe.
It is not a retrieval step, and it should not be used as a substitute for deciding what matters first.

Source-backed cleanup guidance also makes clear that cleanup does not remove the uploaded collector script unless the explicit delete-script command is used.
If collect fails before `state.json` is saved, cleanup has a bounded missing-state fallback: plain latest cleanup removes only timestamp-style latest `DCOIR_*` orphans under the selected `OutRoot` plus the configured package file, while custom `-RunId` no-state roots require cleanup with that explicit `-RunId`. The collector reports `MISSING_STATE_ORPHAN_CLEANED` or `NO_TARGET_FOUND` instead of requiring broad manual temp-folder cleanup.

Practical operator rule:

- retrieve first when retrieval is still needed;
- review first when review is still needed;
- clean up only after the evidence you care about is preserved.

---

## Current limitations and uncertainty boundaries

The current source and governed docs support these bounded statements:

- targeted mode is real and source-backed, but not a universal exact-time filtering guarantee across all artifact families;
- enrichment is a bounded follow-up mechanism, not a replacement for baseline collection;
- collect outputs include multiple analyst-first guidance surfaces, not just one report or one bundle;
- the optional EXE lane exists, but the supported delivery contract remains PS1-first;
- passing code/help coverage checks does not by itself prove operator-usable documentation depth.

Avoid stronger claims than the source currently supports.

---

## Cross-reference boundaries

- Use this page as the collector anchor page.
- Use `knowledge/Knowledge - Core - Tier 1 Collect Runbook.md` for T1 procedure and decision framing.
- Use `knowledge/Knowledge - Core - Tier 2 Collect Runbook.md` for T2 procedure and decision framing.
- Use `knowledge/Knowledge - Core - Enrichment Actions.md` for enrichment workflow guidance.
- Use `knowledge/Knowledge - Core - Artifact Review Guide.md` for evidence-review order and upload priority.
- Use `knowledge/Knowledge - Collector - EXE Usage and Runtime Behavior.md` for EXE-specific interpretation only.

---

> Supporting human-readable Knowledge doc. Not part of the DCOIR control plane.