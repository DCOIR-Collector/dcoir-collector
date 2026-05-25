# Knowledge - Core - Artifact Review Guide

_Evidence-first review of baseline, enrichment, and retrieved artifacts_

**Summary:** Use this page to distinguish workflow wrappers from evidence carriers and to choose the next artifact or action based on what the evidence shows.

---

## Review order

1. Merged baseline report
2. Metadata report
3. Flat `final_artifacts` outputs
4. Enrichment reports and retrieval handoffs
5. Retrieved scripts, configs, task XML, registry exports, EVTX/log excerpts, or service binaries
6. Final synthesis only after evidence review supports it

---

## Wrapper versus evidence carrier

| Artifact type | Role |
| --- | --- |
| Summary or metadata file | Points to context, scope, and next review targets |
| Upload priority or retrieval guidance | Workflow state for what to inspect next |
| Retrieved file, script, task XML, registry export, binary, or log extract | Evidence carrier |

Do not treat a wrapper as a substitute for reviewing the evidence carrier it references.

---

## Review posture

Separate:

- observed evidence;
- inference;
- uncertainty;
- recommended next action.

Do not overstate maliciousness, benignity, completeness, or confidence.

---

## Artifact-specific focus

| Artifact | Focus |
| --- | --- |
| Script or command file | behavior, references, execution context, intent indicators |
| Config or XML | triggers, paths, accounts, timing, referenced binaries/scripts |
| Registry export | path, value, startup/security relevance, policy or persistence meaning |
| Log or EVTX excerpt | event timing, actor, process, host context, correlation limits |
| Binary/service artifact | signer, path, hash, service context, relationship to observed behavior |

---

## Upload priority

When upload limits matter, prefer artifacts most likely to answer the current question:

1. report that identifies the lead finding;
2. evidence carrier referenced by that finding;
3. supporting context needed to interpret the carrier.

Do not upload broad low-value output before high-signal evidence.

---

## Common mistakes

- treating metadata as proof;
- jumping to final synthesis before evidence carriers are reviewed;
- ignoring what an artifact does not prove;
- reading many low-value files before the high-signal file;
- treating artifact volume as severity.

---

## Cross-reference boundaries

- Use this page for evidence review order and upload priority.
- Use Knowledge - Gemini - Output Contract and Command-Lane Discipline for Gemini response and command-lane discipline.
- Use Knowledge - Gemini - Runtime Bundle and Source Tree for Gemini attachment inventory and maintenance.
- Use Knowledge - Collector - Feature and Output Contract Reference for collector output-contract expectations.

---

> Supporting human-readable Knowledge doc. Not part of the DCOIR control plane.
