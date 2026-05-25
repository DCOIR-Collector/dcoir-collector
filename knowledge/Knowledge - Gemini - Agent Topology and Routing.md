# Knowledge - Gemini - Agent Topology and Routing

_Gemini prime-agent and sub-agent routing model_

**Summary:** The current Gemini topology is one prime agent plus eleven specialist sub-agents. The prime routes work; specialists own bounded lanes.

---

## Prime-agent role

The prime agent owns:

- startup and intake posture;
- branch selection;
- specialist routing;
- evidence-first discipline;
- final response coordination.

The prime should not duplicate every specialist's job.

---

## Sub-agent ownership

| Agent | Owns |
| --- | --- |
| 01 Session Readiness and Intake | startup, intake boundaries, readiness |
| 02 Environment and Coverage Mapper | visibility, evidence surfaces, coverage assumptions |
| 03 Alert Family Classifier | alert-family classification and benign-technology differentiation |
| 04 Evidence and Provenance Analyst | source labels, proof boundaries, provenance |
| 05 Query Planner and Syntax Guard | one best query/command and syntax correctness |
| 06 Collector Execution and Bundle Workflow Orchestrator | collector justification, execution lane, retrieval, cleanup, and collection sequencing |
| 07 Collector Artifact Interpreter | collector output meaning and artifact priority |
| 08 IOC Parsing and Public Enrichment Planner | indicator parsing and bounded public enrichment |
| 09 Targeted Collection Designer | narrow evidence-gap reduction and targeted collection design |
| 10 Output Contract Guard | final structure, decision state, and output consistency |
| 11 USB Violations Report Composer | weekly USB violations report validation, SNOW-prefix classification, NIPR/SIPR split handling, and exact plaintext email block drafting |

---

## Routing rules

- Stay in triage when current evidence can answer the question.
- Use collector-aware agents only when collection, enrichment, retrieval, or artifact interpretation is actually in scope.
- Use IOC enrichment only for evidence-grounded indicators.
- Use targeted collection when a narrow evidence gap exists.
- Use final-output enforcement only after the evidence path is clear.
- Use the USB Violations Report Composer only when the operator explicitly asks to prepare, validate, draft, or convert weekly USB violations report material.

---

## Grounding boundary

Routing text must not imply that a search, connector lookup, retrieval action, collector run, or USB report dataset parsing happened unless that action was actually available and performed.

---

## Related pages

- Use this page for agent topology and routing summary.
- Use Knowledge - Gemini - Output Contract and Command-Lane Discipline for response-structure and command-lane behavior.

---

> Supporting human-readable Knowledge doc. Not part of the DCOIR control plane.
