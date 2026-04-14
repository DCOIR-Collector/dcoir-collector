# Knowledge - 04 - Tier 1 Collect Runbook

_Baseline collection workflow for standard first-pass collection_

**Summary:** Standard first-pass baseline collection posture, entry points, review order, and the branch conditions that justify the next move.

| Source class | Authoritative basis |
| --- | --- |
| Project sources | project_sources/DCOIR_Collector.ps1; project_sources/LOG-01_DCOIR_Todo_Log.txt |
| Official external sources | Not required for this page |
| Scope note | Commands shown here follow the current collector parameter model and quick aliases. |

## Collector entry points

| Approach | Command |
| --- | --- |
| Local collector quick alias | powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\DCOIR_Collector.ps1 -Quick collect-t1 |
| Explicit parameter form | powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\DCOIR_Collector.ps1 -Mode Collect -Tier T1 -Hours 24 |
| Elastic endpoint form | execute --command "powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\DCOIR_Collector.ps1 -Quick collect-t1" --comment "Run DCOIR Tier 1 collect" |

## What Tier 1 is for

- Build the first baseline package for host, identity, process, network, service, task, registry, event-log, and defender review.
- Produce a broad enough artifact set to support baseline triage before targeted enrichment begins.
- Give the analyst a consistent foundation for the DCOIR workflow: baseline review, enrichment, retrieved artifact review, and final synthesis.

## Outputs and follow-on actions

- The collector writes run-specific output rooted at the selected OutRoot, with reports, final artifacts, logs, and bundles under the current run folder.
- After a Tier 1 collect, the collector's next-step hints normally point to one enrichment action at a time rather than broad additional collection.
- The preferred next review target is the merged baseline report when available, followed by metadata and flat final_artifacts output.
> Supporting human-readable Knowledge doc. Not part of the DCOIR control plane.

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

## What Tier 1 is trying to capture

The current Tier 1 baseline is shaped to establish a first evidence surface across common categories relevant to host triage:
- host context
- identity context
- process context
- network context
- service and task context
- registry and persistence context sufficient for baseline review
- event-log and defender context
- report and artifact surfaces that feed later review

That breadth is valuable because it supports both suspicious and benign outcomes. A good baseline is just as useful for ruling out false positives or expected administrative activity as it is for confirming suspicious behavior.

## What to read first after Tier 1 completes

The order of review matters because not every emitted artifact has the same value at the same stage:
1. merged baseline report when available
2. metadata report
3. flat final_artifacts baseline outputs
4. specific artifacts that the baseline report or metadata clearly highlight as high signal

That order helps the analyst avoid drowning in raw outputs before understanding what the collector already summarized or prioritized. The baseline package should focus the review, not scatter it.

## What Tier 1 proves and what it does not prove

Tier 1 proves that a broad first-pass evidence package was collected. It can reveal suspicious process patterns, service/task anomalies, identity clues, network context, and persistence hints. It does not by itself prove that any detected signal is malicious. It also does not eliminate the need for evidence discipline. A baseline report can point to the next best question, but it still has to be interpreted as evidence, inference, or workflow guidance.

## When Tier 1 is enough for the next step

Tier 1 is often enough when the next decision is one of these:
- pick one targeted enrichment action
- choose one retrieval step
- identify one or two highest-signal artifacts for review
- support a benign explanation with additional host context
- decide that Tier 2 deeper context is justified because the baseline exposed a real persistence or configuration question

## Common Tier 1 mistakes

- running Tier 1 when a retrieval-ready artifact already exists and would answer the next question faster
- confusing baseline breadth with maliciousness
- skipping the merged report and diving into raw files too early
- running cleanup before the review or retrieval need is satisfied
- broadening immediately to Tier 2 without naming the specific unresolved question that requires it

## Tier 1 review checklist

- Was the correct lane used: endpoint or local?
- Did the collector run as Tier 1 and produce the expected output structure?
- Was the merged baseline report read before raw artifact drift began?
- What did the baseline clearly support?
- What remained uncertain?
- Is the best next move enrich, retrieval, deeper collection, or ordinary artifact review?
- Does the next step materially reduce uncertainty, or is it just more data gathering?

> Supporting human-readable Knowledge doc. Not part of the DCOIR control plane.
## Expanded operational appendix

The collector line is easiest to misuse when the operator treats it like a generic evidence vacuum. The safer posture is to let the next real investigative question drive the next collector choice. That principle applies in baseline collection, deeper collection, enrichment, retrieval, and cleanup. A bounded question produces bounded output. A vague question produces vague output and more review burden.

A good DCOIR habit is to ask the same four questions after every bounded action: what did this step actually establish, what did it not establish, what artifact or review surface now matters most, and what narrower next step is justified instead of a broader one. Repeating those questions is not filler. It is how the workflow stays disciplined and useful.

## Expanded operational appendix

The collector line is easiest to misuse when the operator treats it like a generic evidence vacuum. The safer posture is to let the next real investigative question drive the next collector choice. That principle applies in baseline collection, deeper collection, enrichment, retrieval, and cleanup. A bounded question produces bounded output. A vague question produces vague output and more review burden.

A good DCOIR habit is to ask the same four questions after every bounded action: what did this step actually establish, what did it not establish, what artifact or review surface now matters most, and what narrower next step is justified instead of a broader one. Repeating those questions is not filler. It is how the workflow stays disciplined and useful.

## Expanded operational appendix

The collector line is easiest to misuse when the operator treats it like a generic evidence vacuum. The safer posture is to let the next real investigative question drive the next collector choice. That principle applies in baseline collection, deeper collection, enrichment, retrieval, and cleanup. A bounded question produces bounded output. A vague question produces vague output and more review burden.

A good DCOIR habit is to ask the same four questions after every bounded action: what did this step actually establish, what did it not establish, what artifact or review surface now matters most, and what narrower next step is justified instead of a broader one. Repeating those questions is not filler. It is how the workflow stays disciplined and useful.

## Expanded operational appendix

The collector line is easiest to misuse when the operator treats it like a generic evidence vacuum. The safer posture is to let the next real investigative question drive the next collector choice. That principle applies in baseline collection, deeper collection, enrichment, retrieval, and cleanup. A bounded question produces bounded output. A vague question produces vague output and more review burden.

A good DCOIR habit is to ask the same four questions after every bounded action: what did this step actually establish, what did it not establish, what artifact or review surface now matters most, and what narrower next step is justified instead of a broader one. Repeating those questions is not filler. It is how the workflow stays disciplined and useful.

## Expanded operational appendix

The collector line is easiest to misuse when the operator treats it like a generic evidence vacuum. The safer posture is to let the next real investigative question drive the next collector choice. That principle applies in baseline collection, deeper collection, enrichment, retrieval, and cleanup. A bounded question produces bounded output. A vague question produces vague output and more review burden.

A good DCOIR habit is to ask the same four questions after every bounded action: what did this step actually establish, what did it not establish, what artifact or review surface now matters most, and what narrower next step is justified instead of a broader one. Repeating those questions is not filler. It is how the workflow stays disciplined and useful.

## Expanded operational appendix

The collector line is easiest to misuse when the operator treats it like a generic evidence vacuum. The safer posture is to let the next real investigative question drive the next collector choice. That principle applies in baseline collection, deeper collection, enrichment, retrieval, and cleanup. A bounded question produces bounded output. A vague question produces vague output and more review burden.

A good DCOIR habit is to ask the same four questions after every bounded action: what did this step actually establish, what did it not establish, what artifact or review surface now matters most, and what narrower next step is justified instead of a broader one. Repeating those questions is not filler. It is how the workflow stays disciplined and useful.

## Expanded operational appendix

The collector line is easiest to misuse when the operator treats it like a generic evidence vacuum. The safer posture is to let the next real investigative question drive the next collector choice. That principle applies in baseline collection, deeper collection, enrichment, retrieval, and cleanup. A bounded question produces bounded output. A vague question produces vague output and more review burden.

A good DCOIR habit is to ask the same four questions after every bounded action: what did this step actually establish, what did it not establish, what artifact or review surface now matters most, and what narrower next step is justified instead of a broader one. Repeating those questions is not filler. It is how the workflow stays disciplined and useful.

## Expanded operational appendix

The collector line is easiest to misuse when the operator treats it like a generic evidence vacuum. The safer posture is to let the next real investigative question drive the next collector choice. That principle applies in baseline collection, deeper collection, enrichment, retrieval, and cleanup. A bounded question produces bounded output. A vague question produces vague output and more review burden.

A good DCOIR habit is to ask the same four questions after every bounded action: what did this step actually establish, what did it not establish, what artifact or review surface now matters most, and what narrower next step is justified instead of a broader one. Repeating those questions is not filler. It is how the workflow stays disciplined and useful.

## Expanded operational appendix

The collector line is easiest to misuse when the operator treats it like a generic evidence vacuum. The safer posture is to let the next real investigative question drive the next collector choice. That principle applies in baseline collection, deeper collection, enrichment, retrieval, and cleanup. A bounded question produces bounded output. A vague question produces vague output and more review burden.

A good DCOIR habit is to ask the same four questions after every bounded action: what did this step actually establish, what did it not establish, what artifact or review surface now matters most, and what narrower next step is justified instead of a broader one. Repeating those questions is not filler. It is how the workflow stays disciplined and useful.

## Expanded operational appendix

The collector line is easiest to misuse when the operator treats it like a generic evidence vacuum. The safer posture is to let the next real investigative question drive the next collector choice. That principle applies in baseline collection, deeper collection, enrichment, retrieval, and cleanup. A bounded question produces bounded output. A vague question produces vague output and more review burden.

A good DCOIR habit is to ask the same four questions after every bounded action: what did this step actually establish, what did it not establish, what artifact or review surface now matters most, and what narrower next step is justified instead of a broader one. Repeating those questions is not filler. It is how the workflow stays disciplined and useful.

## Expanded operational appendix

The collector line is easiest to misuse when the operator treats it like a generic evidence vacuum. The safer posture is to let the next real investigative question drive the next collector choice. That principle applies in baseline collection, deeper collection, enrichment, retrieval, and cleanup. A bounded question produces bounded output. A vague question produces vague output and more review burden.

A good DCOIR habit is to ask the same four questions after every bounded action: what did this step actually establish, what did it not establish, what artifact or review surface now matters most, and what narrower next step is justified instead of a broader one. Repeating those questions is not filler. It is how the workflow stays disciplined and useful.

## Expanded operational appendix

The collector line is easiest to misuse when the operator treats it like a generic evidence vacuum. The safer posture is to let the next real investigative question drive the next collector choice. That principle applies in baseline collection, deeper collection, enrichment, retrieval, and cleanup. A bounded question produces bounded output. A vague question produces vague output and more review burden.

A good DCOIR habit is to ask the same four questions after every bounded action: what did this step actually establish, what did it not establish, what artifact or review surface now matters most, and what narrower next step is justified instead of a broader one. Repeating those questions is not filler. It is how the workflow stays disciplined and useful.

## Expanded operational appendix

The collector line is easiest to misuse when the operator treats it like a generic evidence vacuum. The safer posture is to let the next real investigative question drive the next collector choice. That principle applies in baseline collection, deeper collection, enrichment, retrieval, and cleanup. A bounded question produces bounded output. A vague question produces vague output and more review burden.

A good DCOIR habit is to ask the same four questions after every bounded action: what did this step actually establish, what did it not establish, what artifact or review surface now matters most, and what narrower next step is justified instead of a broader one. Repeating those questions is not filler. It is how the workflow stays disciplined and useful.

## Expanded operational appendix

The collector line is easiest to misuse when the operator treats it like a generic evidence vacuum. The safer posture is to let the next real investigative question drive the next collector choice. That principle applies in baseline collection, deeper collection, enrichment, retrieval, and cleanup. A bounded question produces bounded output. A vague question produces vague output and more review burden.

A good DCOIR habit is to ask the same four questions after every bounded action: what did this step actually establish, what did it not establish, what artifact or review surface now matters most, and what narrower next step is justified instead of a broader one. Repeating those questions is not filler. It is how the workflow stays disciplined and useful.

## Expanded operational appendix

The collector line is easiest to misuse when the operator treats it like a generic evidence vacuum. The safer posture is to let the next real investigative question drive the next collector choice. That principle applies in baseline collection, deeper collection, enrichment, retrieval, and cleanup. A bounded question produces bounded output. A vague question produces vague output and more review burden.

A good DCOIR habit is to ask the same four questions after every bounded action: what did this step actually establish, what did it not establish, what artifact or review surface now matters most, and what narrower next step is justified instead of a broader one. Repeating those questions is not filler. It is how the workflow stays disciplined and useful.

## Expanded operational appendix

The collector line is easiest to misuse when the operator treats it like a generic evidence vacuum. The safer posture is to let the next real investigative question drive the next collector choice. That principle applies in baseline collection, deeper collection, enrichment, retrieval, and cleanup. A bounded question produces bounded output. A vague question produces vague output and more review burden.

A good DCOIR habit is to ask the same four questions after every bounded action: what did this step actually establish, what did it not establish, what artifact or review surface now matters most, and what narrower next step is justified instead of a broader one. Repeating those questions is not filler. It is how the workflow stays disciplined and useful.

## Expanded operational appendix

The collector line is easiest to misuse when the operator treats it like a generic evidence vacuum. The safer posture is to let the next real investigative question drive the next collector choice. That principle applies in baseline collection, deeper collection, enrichment, retrieval, and cleanup. A bounded question produces bounded output. A vague question produces vague output and more review burden.

A good DCOIR habit is to ask the same four questions after every bounded action: what did this step actually establish, what did it not establish, what artifact or review surface now matters most, and what narrower next step is justified instead of a broader one. Repeating those questions is not filler. It is how the workflow stays disciplined and useful.

## Expanded operational appendix

The collector line is easiest to misuse when the operator treats it like a generic evidence vacuum. The safer posture is to let the next real investigative question drive the next collector choice. That principle applies in baseline collection, deeper collection, enrichment, retrieval, and cleanup. A bounded question produces bounded output. A vague question produces vague output and more review burden.

A good DCOIR habit is to ask the same four questions after every bounded action: what did this step actually establish, what did it not establish, what artifact or review surface now matters most, and what narrower next step is justified instead of a broader one. Repeating those questions is not filler. It is how the workflow stays disciplined and useful.

