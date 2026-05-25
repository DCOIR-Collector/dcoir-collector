# Knowledge - Core - Tier 1 Collect Runbook

_Baseline collection workflow for first-pass host evidence_

**Summary:** Use Tier 1 when a host needs a broad first-pass evidence package before enrichment, retrieval, or deeper collection.

---

## When to use Tier 1

Use Tier 1 when:

- current alert or telemetry evidence is insufficient;
- the host needs a baseline evidence package;
- no narrower enrich or retrieval action is already clearly better;
- outputs can be preserved long enough for review or retrieval.

Do not run Tier 1 only because the collector is available.

---

## Entry points

| Lane | Command |
| --- | --- |
| Local quick alias | `powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\DCOIR_Collector.ps1 -Quick collect-t1` |
| Local explicit form | `powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\DCOIR_Collector.ps1 -Mode Collect -Tier T1 -Hours 24` |
| Elastic endpoint form | `execute --command "powershell.exe -NoProfile -ExecutionPolicy Bypass -File "".\DCOIR_Collector.ps1"" -Quick collect-t1" --comment "Run DCOIR Tier 1 collect"` |

For optional EXE usage, use Knowledge - Collector - EXE Usage and Runtime Behavior.

---

## Before running

Confirm:

- the investigative question;
- endpoint vs local lane;
- staged runtime state;
- output preservation needs;
- whether existing artifacts should be reviewed or retrieved first.

---

## What Tier 1 produces

Tier 1 is intended to collect first-pass evidence around:

- host and identity context;
- processes and services;
- scheduled tasks;
- registry and persistence clues;
- network context;
- event-log and Defender-relevant surfaces;
- package metadata and retrieval guidance.

Tier 1 produces evidence for triage. It does not prove maliciousness by itself.

---

## Review order

Read outputs in this order:

1. merged baseline report, when present;
2. metadata report;
3. final artifact list or flat output directory;
4. specific high-signal artifacts referenced by the reports.

Avoid jumping into raw files before reading the summary surfaces.

---

## Repeated runs

Before rerunning Tier 1:

- identify what the prior run did not answer;
- check whether the needed artifact already exists;
- verify staged runtime state;
- re-stage when runtime state is uncertain;
- avoid cleanup until evidence is safe.

---

## Targeted follow-through

Tier 1 may justify targeted follow-up, enrichment, retrieval, or Tier 2. Targeted mode narrows intent and output emphasis, but exact filtering must be validated for the specific lane before it is claimed.

---

## Large-output boundary

Synthetic chunking reconstruction is validated for the regression fixture. Do not assume every real large Tier 1 output will be automatically chunked unless that exact live behavior has been validated.

A very large monolithic output should be handled as an implementation or retrieval/review planning boundary, not automatically as a failure.

---

## Common mistakes

- running Tier 1 when retrieval would answer the question;
- treating baseline breadth as proof of compromise;
- skipping the merged report;
- cleaning up before retrieval or review;
- jumping to Tier 2 without naming the unresolved question;
- assuming all large real outputs are chunked.

---

## Completion checklist

- Correct lane used?
- Tier 1 output structure present?
- Baseline report reviewed?
- Key artifacts identified?
- Next move selected: review, retrieval, enrich, Tier 2, or stop?

---

## Cross-reference boundaries

- Use this page for Tier 1 procedure.
- Use Knowledge - Collector - Feature and Output Contract Reference for collector feature families, parameter reference, and output contract.
- Use Knowledge - Collector - EXE Usage and Runtime Behavior for optional EXE command form and EXE-specific interpretation.

---

> Supporting human-readable Knowledge doc. Not part of the DCOIR control plane.
