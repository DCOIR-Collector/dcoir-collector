# Knowledge - Core - Enrichment Actions

_One-bounded-question-at-a-time enrichment and retrieval-oriented follow-up_

**Summary:** Use enrichment after baseline or artifact review identifies one bounded follow-up question. Enrichment is session-based and intentionally narrow so the reason for each action remains clear.

---

## What enrichment is for

Enrichment exists for the moment when broad collection has already identified the next question.

Examples:

- Which DLLs were loaded by this suspicious process?
- Is this file signed and what hash does it have?
- Which strings does this script or binary expose?
- Should I export the raw EVTX instead of relying on text-form event output?
- Should I stage this task XML, service binary, or referenced script for offline review?

Enrichment should answer one bounded follow-up question at a time.
It is not a second baseline collection path.

---

## Enrichment rule

Run one enrichment action at a time.

Each action should answer a specific question such as:

- What process, connection, service, task, registry path, log, or file needs more evidence?
- Is the next step review, retrieval, another related enrichment, or stop?

Do not stack unrelated actions into one session.
A session is for one investigative thread, not for every open question on the host.

---

## Session lifecycle

The collector's enrich behavior is session-based.
That matters for operator use because one session can remain open across closely related actions.

| Phase | Purpose |
| --- | --- |
| Start | Begin a new bounded enrichment session |
| Add | Add one closely related action to the same session |
| Finalize | Close and package the session |
| Cleanup | Remove runtime/output material only after evidence is safe |

Finalize and cleanup are not interchangeable.

### Source-backed session behavior

The current source supports these bounded statements:

- `enrich-start` style paths create a new session;
- `enrich-add` style paths reuse the current open session unless explicitly overridden;
- explicit session targeting can be done with `-EnrichSessionId`;
- a finalized requested session cannot be appended to;
- `enrich-finalize` finalizes the current open session or a valid non-finalized requested session and produces a bundle;
- `enrich-finalize` without an open or requested non-finalized session is rejected instead of creating an empty bundle.

---

## Session controls

| Parameter | Purpose |
| --- | --- |
| `-EnrichSessionId` | Continue or target a specific existing session |
| `-NewEnrichSession` | Force a new session |
| `-FinalizeEnrichSession` | Finalize the current or targeted session |
| `-Action` | Choose the enrich action |

Use one session for one closely related investigative thread.
Do not create a new session when the current open one already owns the question, and do not keep extending a session when it is time to finalize and review.

---

## Review-style versus retrieval-style enrichment

This distinction matters for interpretation.

| Action type | Purpose |
| --- | --- |
| Review-style action | Produce an action artifact that helps answer the next question directly |
| Retrieval-style action | Stage or export a concrete evidence carrier for offline review |

Do not flatten these into one review model.
Some enrich actions primarily answer the question in place.
Others primarily hand you the next file or EVTX to retrieve.

---

## Review-style enrich actions actually exposed by source

| Action | Typical use |
| --- | --- |
| `SigcheckPath` | Review signer, hashes, and version data for a suspicious path |
| `ListDllsPid` | Review loaded modules for a suspicious process |
| `AccessChkFile` | Review effective access for a file or directory |
| `AccessChkService` | Review effective access for a service |
| `AccessChkReg` | Review effective access for a registry path |
| `StringsPath` | Extract readable strings from a suspicious file |
| `StreamsPath` | Review alternate data streams |
| `TcpvconRefresh` | Refresh command-line TCP view for network review |
| `LogText` | Export text-form event evidence |

### Typical parameter families for review-style actions

| Parameter family | Common actions |
| --- | --- |
| `-Path` | signature, strings, streams, file review |
| `-TargetPid` | loaded-module review |
| `-ServiceName` | service access review |
| `-RegistryPath` | registry access review |
| `-LogName` | log text export |
| `-EventId` | narrower event selection |
| `-MaxEvents` | bounded event count |

---

## Retrieval-style enrich actions actually exposed by source

| Action | Typical use |
| --- | --- |
| `LogRaw` | Export raw EVTX for workstation review |
| `PullSuspiciousFile` | Stage a suspicious file for retrieval |
| `PullScriptOrConfig` | Stage a script or config file for retrieval |
| `PullTaskXml` | Export scheduled task XML |
| `PullServiceBinary` | Stage the binary referenced by a service |
| `PullWmiReferencedFile` | Stage a file referenced by suspicious WMI persistence |

### Typical parameter families for retrieval-style actions

| Parameter family | Common actions |
| --- | --- |
| `-Path` | suspicious file, script/config, task-name-as-path, WMI-referenced file |
| `-ServiceName` | service-binary retrieval |
| `-LogName` | raw EVTX export |
| `-EventId` | narrower event selection |
| `-Hours` | time window for event export |

Prefer retrieval when the decisive next evidence carrier is already known.
If you already know the suspicious file, script, service binary, or task definition you need, retrieval is often better than another broader collection step.

---

## Quick aliases accepted by source

Quick aliases are the safest way to avoid unsupported command shapes when one of the source-backed paths matches the question. Each `enrich-start-*` alias starts a new enrich session for that action. The matching `enrich-add-*` alias adds the same action to the currently open session or to the explicit non-finalized session supplied with `-EnrichSessionId`.

For quick aliases that need a value, pass the value with `-Target`. The collector maps that target into the action-specific parameter family. Use explicit `-Mode Enrich -Action ...` parameters when you need to set more specific fields such as `-EventId`, `-MaxEvents`, `-WindowStart`, or `-WindowEnd`.

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

### Common quick-alias examples

| Question | Example command shape |
| --- | --- |
| Start a TCP follow-up session | `powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\DCOIR_Collector.ps1 -Quick enrich-start-tcp` |
| Add log-text review to the open session | `powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\DCOIR_Collector.ps1 -Quick enrich-add-logtext -Target Security` |
| Start file signature review | `powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\DCOIR_Collector.ps1 -Quick enrich-start-sigcheck -Target C:\Path\To\File.exe` |
| Stage a service binary for retrieval | `powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\DCOIR_Collector.ps1 -Quick enrich-start-pull-service -Target SuspiciousService` |
| Finalize the current open session | `powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\DCOIR_Collector.ps1 -Quick enrich-finalize` |

These matter because operators and Gemini should prefer supported quick paths instead of inventing unsupported command shapes.

---

## Before enrichment

Confirm:

- the prior finding that justifies enrichment;
- the narrow question the enrich action is supposed to answer;
- whether the best next step is review-style or retrieval-style;
- whether an existing artifact should be retrieved first;
- whether the current session should be extended or finalized;
- whether cleanup would remove still-needed evidence.

A good enrich action begins from a specific question, not a desire to "look deeper" in general.

---

## What enrich output actually gives the operator

Important enrich output surfaces visible in current source include:

- `STATUS`
- `RUN_ID`
- `COLLECTOR_VERSION`
- `COLLECTOR_BUILD_IDENTITY`
- `ENRICH_SESSION_ID`
- `SESSION_RESOLUTION_MODE`
- `ENRICH_REPORT_PATH`
- optional `ACTION_ARTIFACT_PATH` when an enrich action ran
- optional `STAGED_PATH`
- `SESSION_STATUS`
- optional `ENRICH_BUNDLE_PATH`
- `NEXT_GET_FILE` when finalized
- `DELETE_SCRIPT_COMMAND`

A finalize-only path is still a normal enrich outcome when it closes an existing open session or a valid non-finalized requested session.
When the operator runs `enrich-finalize` without a new action, the current source emits the session report and finalization surfaces without `ACTION_ARTIFACT_PATH`; if no open or requested non-finalized session exists, the collector rejects the command so operators do not receive an empty finalized bundle.

### Practical enrich review order

1. `ENRICH_REPORT_PATH`
2. optional `ACTION_ARTIFACT_PATH` when an action ran
3. `SESSION_RESOLUTION_MODE`
4. `SESSION_STATUS`
5. optional `STAGED_PATH` when retrieval occurred
6. optional `ENRICH_BUNDLE_PATH` after finalization

Review-style actions often answer the next question in the action artifact.
Retrieval-style actions often exist to give you the next evidence carrier to inspect offline.

---

## Output interpretation

An enrichment result may provide:

- direct evidence;
- session/workflow state;
- a candidate path for retrieval;
- a reason to stop;
- a reason to run one more closely related bounded action in the same session.

It is not automatically a final verdict.

---

## Retrieval preference

Prefer retrieval when the collector or prior review already identified a specific evidence carrier.

Retrieval is usually better than another broad collection when the question is about:

- one known file;
- one known script or config;
- one task definition;
- one service binary;
- one raw event-log export for workstation review.

---

## Common mistakes

- running multiple unrelated enrichments in one session;
- starting a new session when the current one should be extended;
- extending a session that should be finalized;
- trying to append to a session that has already been finalized;
- treating a rejected finalize-without-open command as a collector failure instead of a guardrail;
- using enrichment when retrieval is already the narrower answer;
- cleaning up before outputs are reviewed or retrieved;
- inventing action flags not exposed by the collector;
- treating retrieval-style and review-style actions as if they behave the same way.

---

## Cross-reference boundaries

- Use this page for enrichment workflow, session behavior, action families, and enrich-output interpretation.
- Use `Knowledge - Collector - Feature and Output Contract Reference` for the source-backed collector anchor contract.
- Use `Knowledge - Core - Artifact Review Guide` for review order after enrichment surfaces or staged evidence are produced.
- Use `Knowledge - Collector - EXE Usage and Runtime Behavior` only when EXE-specific wrapper interpretation matters.

---

> Supporting human-readable Knowledge doc. Not part of the DCOIR control plane.
