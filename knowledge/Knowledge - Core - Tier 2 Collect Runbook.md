# Knowledge - Core - Tier 2 Collect Runbook

_Deeper collection workflow for persistence, configuration, and follow-on context after Tier 1_

**Summary:** Use Tier 2 only when Tier 1 or current evidence leaves a specific unresolved question that needs deeper host context. Tier 2 is not a generic “do more” button.

---

## What Tier 2 is for

Tier 2 exists for the moment when Tier 1 has already done its job and the next question is now more specific.

Examples:

- Is this persistence-looking surface merely present, or does it need deeper host context?
- Which registry or WMI persistence details matter enough to justify artifact retrieval?
- Do deeper configuration surfaces support or weaken the leading theory?

Use Tier 2 to answer a deeper question that has already been named.
Do not use it as a substitute for reviewing Tier 1 properly.

---

## When to use Tier 2

Use Tier 2 when:

- Tier 1 exposed persistence, service, task, registry, WMI, identity, firewall, share, or session questions;
- the next question needs deeper host configuration context;
- retrieval or a single enrichment action is not already the narrower answer;
- broader context is still required before choosing the next retrieval or enrichment move.

Do not use Tier 2 as a generic escalation path just because Tier 1 produced a lot of output.

---

## Entry points

| Lane | Command |
| --- | --- |
| Local quick alias | `powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\DCOIR_Collector.ps1 -Quick collect-t2` |
| Local explicit form | `powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\DCOIR_Collector.ps1 -Mode Collect -Tier T2 -Hours 72` |
| Bounded validation form | `powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\DCOIR_Collector.ps1 -Mode Collect -Tier T2 -Hours 1 -MaxEvents 100` |
| Elastic endpoint form | `execute --command "powershell.exe -NoProfile -ExecutionPolicy Bypass -File "".\DCOIR_Collector.ps1"" -Quick collect-t2" --comment "Run DCOIR Tier 2 collect"` |

For optional EXE usage, use `Knowledge - Collector - EXE Usage and Runtime Behavior`.
For the broader source-backed contract, use `Knowledge - Collector - Feature and Output Contract Reference`.

---

## Bounded Tier 2 validation shape

The maintained regression harness uses a runner-safe Tier 2 shape: `-Tier T2 -Hours 1 -MaxEvents 100`.

That validation shape proves three operator-relevant facts when FullRegression passes:

- the collector accepts the Tier 2 path without relying on an unbounded time window;
- collection metadata records `Tier=T2`, `Hours=1`, and `MaxEvents=100`;
- the bundle contains the Tier 2 deep-check artifacts under `TIER2_DEEP_CHECKS`, including IFEO, Winlogon, LSA, WMI persistence, network share/session, and firewall profile outputs.

For live operations, choose a wider `-Hours` value only when the case needs it. Keep `-MaxEvents` bounded when event volume or upload budget matters.

---

## What Tier 2 adds

Tier 2 adds deeper context around:

- registry persistence, including IFEO, Winlogon, and LSA-related paths;
- WMI subscription and persistence surfaces;
- network share and session context;
- firewall profile context;
- a longer time horizon than Tier 1.

Think of Tier 2 as the deeper context layer that helps explain suspicious host state after the first broad pass.

---

## Before running

Confirm:

- the exact Tier 1 or alert finding that justifies deeper collection;
- which deeper evidence class is expected to answer the question;
- whether retrieval or enrichment would answer it faster;
- whether targeted follow-up would now be narrower than another broad collect run;
- the correct execution lane;
- output preservation needs.

If you cannot name the unresolved question, Tier 2 is probably not the right next move yet.

---

## What Tier 2 actually gives the operator

Tier 2 is still a collect-mode run, so many of the same operator-visible surfaces still matter:

- `STATUS`
- `RUN_ID`
- `METADATA_REPORT_PATH` including `Tier`, `Hours`, and `MaxEvents` values
- `ANALYST_OVERVIEW_PATH`
- `UPLOAD_SUMMARY_PATH`
- `ATTACHMENT_BUDGET_MANIFEST_PATH`
- optional `UPLOAD_SAFE_CHUNK_MANIFEST_PATH` when oversized full-fidelity text artifacts were chunked
- `COLLECTION_SCOPE_PATH`
- `SECURITY_HIGH_SIGNAL_SUMMARY_PATH`
- `EXECUTION_CONTEXT_PATH`
- `PARALLELISM_ASSESSMENT_PATH`
- `COLLECT_BUNDLE_PATH`
- `NEXT_GET_FILE`
- `CLEANUP_COMMAND`
- `DELETE_SCRIPT_COMMAND`

Even in Tier 2, do not skip the orientation surfaces just because the run is “deeper.”

---

## How to read Tier 2 output

Read Tier 2 as deeper context, not as automatic escalation or proof.

Ask:

- Which deeper surface produced a meaningful signal?
- Did it support or weaken the leading explanation?
- Does it justify retrieval, enrichment, targeted follow-up, broader artifact review, or stopping?
- Is the finding evidence of use, or only evidence that a mechanism exists?

Tier 2 becomes useful when it narrows the next move, not when it simply adds volume.

---

## Practical first review order for Tier 2

Use this order for the current build:

1. `ANALYST_OVERVIEW_PATH`
2. `UPLOAD_SUMMARY_PATH`
3. `METADATA_REPORT_PATH`
4. `ATTACHMENT_BUDGET_MANIFEST_PATH`
5. optional `UPLOAD_SAFE_CHUNK_MANIFEST_PATH` when full-fidelity text chunks are present
6. `COLLECTION_SCOPE_PATH`
7. `SECURITY_HIGH_SIGNAL_SUMMARY_PATH`
8. Tier 2 deep-check artifacts under `TIER2_DEEP_CHECKS` when present: IFEO, Winlogon, LSA, WMI persistence, network share/session, and firewall profile outputs
9. upload-safe full-fidelity chunks only when the summary is insufficient
10. broader local output only after the deeper question is more clearly framed

If the run was launched to answer a narrow persistence or WMI question, prioritize the artifacts that most directly support that question instead of reading all deeper output uniformly.

---

## When Tier 2 should lead to retrieval or enrichment

Tier 2 should often end by identifying one narrower next move.

Common patterns:

- suspicious service path found -> retrieve service binary
- suspicious scheduled task action found -> retrieve task XML or referenced script/binary
- suspicious WMI persistence reference found -> retrieve the referenced file
- suspicious registry/config surface found -> choose the narrow enrich or retrieval action that best answers the next question

Tier 2 is often the bridge between broad baseline context and a specific evidence carrier.

---

## Common Tier 2 mistakes

- running Tier 2 before reading Tier 1 properly;
- treating persistence-capable configuration as proof of malicious use;
- using Tier 2 when one specific artifact should simply be retrieved;
- using Tier 2 as a substitute for naming the unresolved question;
- cleaning up before reviewing deeper outputs and preserving needed evidence;
- widening the review before the highest-value deeper surface is read.

---

## Completion checklist

- Driving finding named?
- Deeper evidence class identified?
- Analyst overview and orientation surfaces reviewed first?
- Tier 2 output reviewed against the specific question?
- Next move selected: retrieval, enrich, targeted follow-up, broader review, stop, or additional collection?

---

## Cross-reference boundaries

- Use this page for Tier 2 procedure and deeper-question framing.
- Use `Knowledge - Collector - Feature and Output Contract Reference` for the source-backed collector contract.
- Use `Knowledge - Core - Artifact Review Guide` for review order and evidence-carrier priority.
- Use `Knowledge - Collector - EXE Usage and Runtime Behavior` only when EXE-specific wrapper interpretation matters.

---

> Supporting human-readable Knowledge doc. Not part of the DCOIR control plane.
