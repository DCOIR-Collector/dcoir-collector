# Knowledge - 05 - Tier 2 Collect Runbook

_Deeper collection workflow for persistence and configuration context_

**Summary:** Use Tier 2 only when Tier 1 or current evidence leaves a specific unresolved question that requires deeper host context.

---

## When to use Tier 2

Use Tier 2 when:

- Tier 1 exposed persistence, service, task, registry, WMI, identity, firewall, share, or session questions;
- the next question needs deeper host configuration context;
- retrieval or a single enrichment action is not already the narrower answer.

Do not use Tier 2 as a generic “do more” button.

---

## Entry points

| Lane | Command |
| --- | --- |
| Local quick alias | `powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\DCOIR_Collector.ps1 -Quick collect-t2` |
| Local explicit form | `powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\DCOIR_Collector.ps1 -Mode Collect -Tier T2 -Hours 72` |
| Elastic endpoint form | `execute --command "powershell.exe -NoProfile -ExecutionPolicy Bypass -File "".\DCOIR_Collector.ps1"" -Quick collect-t2" --comment "Run DCOIR Tier 2 collect"` |

For optional EXE usage, use Knowledge 16.

---

## What Tier 2 adds

Tier 2 adds deeper context around:

- registry persistence, including IFEO, Winlogon, and LSA-related paths;
- WMI subscription and persistence surfaces;
- network share and session context;
- firewall profile context;
- longer time horizon than Tier 1.

---

## Before running

Confirm:

- the exact Tier 1 or alert finding that justifies deeper collection;
- which deeper evidence class is expected to answer the question;
- whether retrieval or enrichment would answer it faster;
- endpoint vs local lane;
- output preservation needs.

---

## How to read Tier 2 output

Read Tier 2 as deeper context, not automatic escalation.

Ask:

- Which deeper surface produced a meaningful signal?
- Did it support or weaken the leading explanation?
- Does it justify retrieval, enrichment, artifact review, or stopping?
- Is the finding evidence of use, or only evidence that a mechanism exists?

---

## Common Tier 2 mistakes

- running Tier 2 before reading Tier 1;
- treating persistence-capable configuration as proof of malicious use;
- running broader collection when one artifact should be retrieved;
- cleaning up before reviewing deeper outputs;
- failing to name the unresolved question.

---

## Completion checklist

- Driving finding named?
- Deeper evidence class identified?
- Output reviewed against the question?
- Next move selected: retrieval, enrichment, review, stop, or additional collection?

---

> Supporting human-readable Knowledge doc. Not part of the DCOIR control plane.
