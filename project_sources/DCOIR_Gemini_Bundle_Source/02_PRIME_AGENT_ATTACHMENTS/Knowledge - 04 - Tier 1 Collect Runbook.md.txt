# Knowledge - 04 - Tier 1 Collect Runbook

_Baseline collection workflow for standard first-pass collection_

**Summary:** Standard first-pass baseline collection posture, entry points, review order, and the branch conditions that justify the next move, with bounded guidance for repeated collect-style runs, honest targeted follow-through expectations, and the current large-output chunking boundary.

| Source class | Authoritative basis |
| --- | --- |
| Project sources | project_sources/DCOIR_Collector.ps1; project_sources/DOC-01_AFRICOM_SOC_IR_Project_Setup_and_Workflow.txt; project_sources/LOG-70_DCOIR_Infrastructure_First_Reprioritization_Closeout_2026-04-17.txt; project_sources/LOG-63_DCOIR_Chunking_Reconstruction_Hotfix_2026-04-09.txt |
| Official external sources | Not required for this page |
| Scope note | Commands shown here follow the current collector parameter model, current runtime filename, and current lane-separation rules. |

## Collector entry points

| Approach | Command |
| --- | --- |
| Local collector quick alias | powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\DCOIR_Collector.ps1 -Quick collect-t1 |
| Explicit parameter form | powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\DCOIR_Collector.ps1 -Mode Collect -Tier T1 -Hours 24 |
| Elastic endpoint form | execute --command "powershell.exe -NoProfile -ExecutionPolicy Bypass -File "".\DCOIR_Collector.ps1"" -Quick collect-t1" --comment "Run DCOIR Tier 1 collect" |

## What Tier 1 is for

- Build the first baseline package for host, identity, process, network, service, task, registry, event-log, and defender review.
- Produce a broad enough artifact set to support baseline triage before targeted enrichment begins.
- Give the analyst a consistent foundation for the DCOIR workflow: baseline review, enrichment, retrieved artifact review, and final synthesis.

## Tier 1 collection posture

Tier 1 is the standard first-pass host collection because it is broad enough to support meaningful baseline review without immediately jumping into deeper persistence or highly specific follow-up branches. It should be treated as the normal entry point when the host needs a starting evidence package and the operator does not yet know which narrow artifact family will matter most.

The point of Tier 1 is not to prove compromise by itself. The point is to stage the first broad evidence package that lets the analyst ask better questions afterward. A well-run Tier 1 collection narrows uncertainty, exposes likely next review targets, and makes later enrich or retrieval choices less speculative.

## Before the first baseline run

A disciplined Tier 1 run starts with a short reasoning step:
- what question is driving host collection
- why telemetry or current alert evidence is not enough
- whether the host is already in a state where a narrower enrich action would be better than a baseline
- whether the endpoint or local lane is being used
- whether the operator will need to preserve the outputs for immediate artifact review or later retrieval

Tier 1 is the default broad lane, but it is still a deliberate choice. Running it merely because collection exists leads to oversized output and weak review discipline.

## Repeated collect-style runs

Repeated Tier 1 or other collect-style runs should be treated as a fresh staging decision, not a reflexive rerun.

Before rerunning:
- confirm whether the needed artifact already exists and should be reviewed or retrieved instead
- confirm that the endpoint or local test layout still has the expected collector runtime staged
- re-stage the collector package when the current staged state is uncertain or no longer matches the run you are about to perform
- state the exact new question the rerun is supposed to answer

The safe lesson is simple: do not assume a prior staged ZIP or prior run state remains the right baseline for a new collect-style action.

## What to read first after Tier 1 completes

The order of review matters because not every emitted artifact has the same value at the same stage:
1. merged baseline report when available
2. metadata report
3. flat `final_artifacts` baseline outputs
4. specific artifacts that the baseline report or metadata clearly highlight as high signal

That order helps the analyst avoid drowning in raw outputs before understanding what the collector already summarized or prioritized. The baseline package should focus the review, not scatter it.

## Large-output chunking boundary

Current governed source and hotfix history do **not** support the claim that every large real-world Tier 1 output is chunked by default.

What is currently proven:
- the synthetic chunking regression lane was repaired so reconstruction of the synthetic oversized validation fixture is deterministic
- chunk manifests and reconstruction metadata are therefore proven for that synthetic validation path

What is **not** currently proven:
- that every oversized real baseline report or large real final artifact will be chunked automatically in live runs
- that a monolithic real output necessarily means the collector failed rather than exposing a current implementation boundary

Operational takeaway:
- treat a very large monolithic real output as a current limitation that may require retrieval/review planning rather than assuming the chunking feature silently failed
- if exact real-output chunking becomes required, treat that as a new collector implementation task rather than as already-delivered behavior

## What Tier 1 proves and what it does not prove

Tier 1 proves that a broad first-pass evidence package was collected. It can reveal suspicious process patterns, service/task anomalies, identity clues, network context, and persistence hints. It does not by itself prove that any detected signal is malicious. It also does not eliminate the need for evidence discipline. A baseline report can point to the next best question, but it still has to be interpreted as evidence, inference, or workflow guidance.

## Targeted follow-through boundary

Tier 1 often leads to a targeted next step, but that should be described honestly.

Current live findings indicate that targeted follow-through should be treated as a narrower guidance, scope, and prioritization step unless the specific lane has been proven to implement exact filtering semantics for the requested subset. In practice that means:
- use targeted follow-through to narrow the next action intentionally
- do not imply that every targeted branch is already a mathematically exact subset of the baseline package
- when a later step depends on exact start/end or exact artifact-family filtering, verify that capability directly instead of assuming it from the word `targeted`

## Common Tier 1 mistakes

- running Tier 1 when a retrieval-ready artifact already exists and would answer the next question faster
- confusing baseline breadth with maliciousness
- skipping the merged report and diving into raw files too early
- running cleanup before the review or retrieval need is satisfied
- broadening immediately to Tier 2 without naming the specific unresolved question that requires it
- rerunning collection without re-checking staged runtime state or clarifying why the earlier run was insufficient
- assuming real oversized outputs must already chunk because the synthetic validation lane chunks

## Tier 1 review checklist

- Was the correct lane used: endpoint or local?
- Did the collector run as Tier 1 and produce the expected output structure?
- Was the merged baseline report read before raw artifact drift began?
- What did the baseline clearly support?
- What remained uncertain?
- Is the best next move enrich, retrieval, deeper collection, or ordinary artifact review?
- Does the next step materially reduce uncertainty, or is it just more data gathering?

> Supporting human-readable Knowledge doc. Not part of the DCOIR control plane.
