# Knowledge - Core - Enrichment Actions

_One-action-at-a-time enrichment and retrieval-oriented follow-up_

**Summary:** Use enrichment after baseline or artifact review identifies one bounded follow-up question. Enrichment is serialized so the reason for each action remains clear.

---

## Enrichment rule

Run one enrichment action at a time.

Each action should answer a specific question such as:

- What process, connection, service, task, registry path, log, or file needs more evidence?
- Is the next step review, retrieval, another related enrichment, or stop?

Do not stack unrelated actions into one session.

---

## Session lifecycle

| Phase | Purpose |
| --- | --- |
| Start | Begin a new bounded enrichment session |
| Add | Add one closely related action to the same session |
| Finalize | Close and package the session |
| Cleanup | Remove runtime/output material only after evidence is safe |

Finalize and cleanup are not interchangeable.

---

## Action groups

| Group | Examples | Use when |
| --- | --- | --- |
| Network | TCP refresh | connection context is the missing evidence |
| Logs | text or raw log export | event evidence is needed |
| Tool-backed checks | sigcheck, listdlls, accesschk, strings, streams | a bundled utility answers the host-state question |
| Retrieval | file, script, task XML, service binary, WMI-referenced file | a specific artifact needs review |

Use official Sysinternals documentation only when exact bundled-tool behavior affects interpretation.

---

## Retrieval preference

Prefer retrieval when the collector or prior review already identified a specific evidence carrier. Retrieval is usually better than another broad collection when the question is about one known file, script, task, service binary, or configuration artifact.

---

## Before enrichment

Confirm:

- the prior finding that justifies enrichment;
- the action family that maps to the question;
- whether an existing artifact should be retrieved first;
- whether the current session should be extended or finalized;
- whether cleanup would remove still-needed evidence.

---

## Output interpretation

An enrichment result may provide:

- evidence;
- workflow state;
- candidate paths for retrieval;
- reasons to stop.

It is not automatically a final verdict.

---

## Common mistakes

- running multiple unrelated enrichments in one session;
- starting a new session when the current one should be extended;
- extending a session that should be finalized;
- cleaning up before outputs are reviewed;
- inventing action flags not exposed by the collector.

---

## Cross-reference boundaries

- Use this page for enrichment and retrieval workflow.
- Use Knowledge - Collector - Feature and Output Contract Reference for collector feature and output-contract facts.
- Use Knowledge - Core - Artifact Review Guide for artifact review order after enrichment produces or references evidence carriers.

---

> Supporting human-readable Knowledge doc. Not part of the DCOIR control plane.
