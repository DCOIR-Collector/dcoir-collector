# Knowledge - 06 - Enrichment Actions

_Quick-alias enrichment map and tool-backed actions_

**Summary:** The current stable collector supports a one-action-at-a-time enrichment model. The quick aliases make those actions easier to launch consistently.

| Source class | Authoritative basis |
| --- | --- |
| Project sources | project_sources/DCOIR_Collector.ps1; project_sources/run_DCOIR_Tests.ps1 |
| Official external sources | Microsoft Learn / Sysinternals tool pages |
| Scope note | Current quick aliases cover TCP, log text, raw log export, tool-backed checks, and several retrieval actions. |

## One-action-at-a-time model

- Use enrich-start-* to begin a new enrichment session.
- Use enrich-add-* to add another action to an existing enrichment session.
- Use enrich-finalize to close and bundle the current enrichment session.
- Use cleanup only after the current run output is no longer needed.

## Current quick-action groups

| Group | Examples | Backing capability |
| --- | --- | --- |
| Network | enrich-start-tcp, enrich-add-tcp | Tcpvcon refresh |
| Log review | enrich-start-logtext, enrich-start-lograw | Filtered event text or raw EVTX export |
| Tool-backed checks | sigcheck, listdlls, access-file, access-service, access-reg, strings, streams | Sysinternals console tools |
| Retrieval actions | pull-file, pull-script, pull-task, pull-service, pull-wmi-file | Targeted file or config staging for analyst review |

## Current Sysinternals bundle detected in DCOIR_Collector.zip

- AccessChk
- Autoruns/Autorunsc
- Handle
- ListDLLs
- PipeList
- PsList
- Sigcheck
- Streams
- Strings
- TCPView/Tcpvcon

## Operator reminders

- Do not invent flags that the collector source does not expose.
- Use official Sysinternals documentation when interpreting a bundled tool's exact switch behavior.
- Keep local workstation commands separate from Elastic response-console commands.
> Supporting human-readable Knowledge doc. Not part of the DCOIR control plane.
