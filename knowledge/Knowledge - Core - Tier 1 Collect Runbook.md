# Knowledge - Core - Tier 1 Collect Runbook

_First-pass collection workflow for broad but triage-oriented host evidence_

**Summary:** Use Tier 1 when you need the first broad evidence package for a host, but still want the collector to orient you toward the most useful review surfaces instead of forcing you into raw output immediately.

---

## What Tier 1 is for

Tier 1 is the normal first collect path when:

- current alert or telemetry evidence is not enough by itself;
- you need a baseline host evidence package;
- no narrower enrich or retrieval action is already the clearly better next step;
- the goal is to triage efficiently, not to collect everything possible by default.

Tier 1 is broad, but it is still meant to support decision-making.
It is not proof of maliciousness by itself.

---

## When to use Tier 1

Use Tier 1 when:

- the host needs a first-pass evidence package;
- you need host, process, service, task, registry, network, and event context before choosing a narrower next move;
- the likely next decision is still one of: stop, retrieve, enrich, targeted follow-up, or Tier 2;
- outputs can be preserved long enough for review or retrieval.

Do not run Tier 1 only because the collector is available.
If a known artifact already needs retrieval, retrieval may be the narrower and better next move.

---

## Entry points

| Lane | Command |
| --- | --- |
| Local quick alias | `powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\DCOIR_Collector.ps1 -Quick collect-t1` |
| Local explicit form | `powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\DCOIR_Collector.ps1 -Mode Collect -Tier T1 -Hours 24` |
| Elastic endpoint form | `execute --command "powershell.exe -NoProfile -ExecutionPolicy Bypass -File "".\DCOIR_Collector.ps1"" -Quick collect-t1" --comment "Run DCOIR Tier 1 collect"` |

For optional EXE usage, use `Knowledge - Collector - EXE Usage and Runtime Behavior`.
For the source-backed collector contract, use `Knowledge - Collector - Feature and Output Contract Reference`.

---

## Before running

Confirm:

- the investigative question;
- whether the correct lane is endpoint or local;
- whether the staged runtime state is understood;
- whether there are already outputs or retrieved artifacts that should be reviewed first;
- whether output preservation/retrieval needs are understood before any cleanup later.

A good Tier 1 run starts from a named question, not from vague curiosity.

---

## What Tier 1 is intended to collect

Tier 1 is the first-pass baseline evidence layer around:

- host and identity context;
- process and service state;
- scheduled tasks;
- registry and persistence clues;
- network context;
- event-log and Defender-relevant surfaces;
- package metadata and retrieval guidance.

Tier 1 is designed to support triage.
It gives you enough breadth to choose a narrower next step, not to eliminate all uncertainty in one pass.

---

## What Tier 1 actually gives the operator

A successful Tier 1 run emits more than a bundle.
For current source behavior, the important operator-visible surfaces include:

- `STATUS`
- `RUN_ID`
- `METADATA_REPORT_PATH`
- `ANALYST_OVERVIEW_PATH`
- `UPLOAD_SUMMARY_PATH`
- `ATTACHMENT_BUDGET_MANIFEST_PATH`
- optional `UPLOAD_SAFE_CHUNK_MANIFEST_PATH` when oversized full-fidelity text artifacts were chunked
- `COLLECTION_SCOPE_PATH`
- `SECURITY_HIGH_SIGNAL_SUMMARY_PATH`
- `EXECUTION_CONTEXT_PATH`
- `PARALLELISM_ASSESSMENT_PATH`
- optional `TARGETED_COLLECTION_PLAN_PATH` when targeted mode was used
- `COLLECT_BUNDLE_PATH`
- `NEXT_GET_FILE`
- `CLEANUP_COMMAND`
- `DELETE_SCRIPT_COMMAND`

Treat these as distinct surfaces with different jobs, not as duplicate noise.

---

## First review order for Tier 1

For the current build, use this review order:

1. `ANALYST_OVERVIEW_PATH`
2. `UPLOAD_SUMMARY_PATH`
3. `METADATA_REPORT_PATH`
4. `ATTACHMENT_BUDGET_MANIFEST_PATH`
5. optional `UPLOAD_SAFE_CHUNK_MANIFEST_PATH` when full-fidelity text chunks are present
6. `COLLECTION_SCOPE_PATH`
7. `SECURITY_HIGH_SIGNAL_SUMMARY_PATH`
8. `EXECUTION_CONTEXT_PATH` when elevation/visibility affects interpretation
9. representative high-signal artifacts referenced by the above surfaces
10. upload-safe full-fidelity chunks only when the summary is insufficient
11. broader flat output or the bundle only after the first-pass question is clearer

Avoid jumping directly into raw files before reading the orientation surfaces.

---

## What to decide after Tier 1

Tier 1 should help you choose one of these next moves:

- stop because the current question is answered;
- retrieve a specific evidence carrier;
- run one bounded enrich action;
- run a targeted follow-up collection path;
- escalate to Tier 2 because a specific deeper question remains.

A good Tier 1 outcome is not "more files."
A good Tier 1 outcome is a clearer next move.

---

## Repeated Tier 1 runs

Before rerunning Tier 1:

- identify what the prior run did not answer;
- check whether the needed artifact already exists;
- review whether targeted follow-up or enrichment would now be narrower;
- verify staged runtime state;
- re-stage when runtime state is uncertain;
- avoid cleanup until evidence is safe.

Do not rerun Tier 1 as a reflex when a narrower step would answer the question faster.

---

## Targeted follow-through from Tier 1

Tier 1 can justify targeted follow-up, retrieval, enrichment, or Tier 2.

Important boundary:

- targeted mode is real and useful;
- it narrows guidance, scope intent, artifact prioritization, and recommended next actions;
- it should not be described as universal exact filtering across all artifact families unless that narrower claim is specifically validated.

Use targeted follow-through when the incident is now narrow enough that a profile, time window, user report, process, path, or indicator can focus the next step.

---

## Large-output boundary

The current collector can create upload-safe chunk companions for oversized real human-readable artifacts such as full-fidelity event text, and it reports those companions through `UPLOAD_SAFE_CHUNK_MANIFEST_PATH` when they exist.

Use the chunk manifest when the summary points to a large source artifact that still needs full-fidelity review:

1. read `UPLOAD_SUMMARY_PATH` to see whether chunk companions were recommended;
2. read `UPLOAD_SAFE_CHUNK_MANIFEST_PATH` to identify the original artifact, ordered chunk files, byte counts, and reconstruction metadata;
3. upload or review the ordered chunk companions only when the high-signal summary is not enough;
4. keep the manifest with the chunks so the reviewer can reconstruct or reason about the original artifact.

This production chunking support is not a promise that every possible large artifact family is chunked. A very large monolithic output outside the supported upload-safe chunk paths should still be treated as a retrieval/review planning or implementation-boundary issue, not automatically as a collector failure.

---

## Common mistakes

- running Tier 1 when retrieval would already answer the question;
- treating baseline breadth as proof of compromise;
- ignoring `ANALYST_OVERVIEW_PATH` and `UPLOAD_SUMMARY_PATH`;
- assuming a merged baseline report is still the primary review surface in the current build;
- cleaning up before retrieval or review;
- jumping to Tier 2 without naming the unresolved question;
- ignoring `UPLOAD_SAFE_CHUNK_MANIFEST_PATH` when the collector reports upload-safe chunks for oversized full-fidelity text;
- assuming every possible large artifact family is chunked.

---

## Completion checklist

- Correct lane used?
- Tier 1 run completed with expected status and run id?
- Analyst overview and upload summary reviewed first?
- Key high-signal artifacts identified?
- Narrowest next move selected: stop, review, retrieval, enrich, targeted follow-up, or Tier 2?

---

## Cross-reference boundaries

- Use this page for Tier 1 procedure and decision framing.
- Use `Knowledge - Collector - Feature and Output Contract Reference` for the source-backed collector contract.
- Use `Knowledge - Core - Artifact Review Guide` for evidence-review order and upload priority.
- Use `Knowledge - Collector - EXE Usage and Runtime Behavior` only when EXE-specific wrapper interpretation matters.

---

> Supporting human-readable Knowledge doc. Not part of the DCOIR control plane.
