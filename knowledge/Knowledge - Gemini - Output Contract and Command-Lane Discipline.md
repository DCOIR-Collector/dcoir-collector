# Knowledge - Gemini - Output Contract and Command-Lane Discipline

_Gemini final structure, decision states, and command-lane separation_

**Summary:** Describes the current Gemini output and command-lane contract so attachment-based retrieval can explain the behavior. The enforcing rules live in the Prime/Sub-Agent instruction source, not in this knowledge attachment.

---

## Attachment boundary

This page is reference material for retrieval and operator understanding. It is not a hidden instruction channel and does not override Prime Agent or Sub-Agent instruction source.

Use this page to explain the output contract and command-lane model when it is retrieved as evidence. Do not treat this attachment as the authority that enforces response format, tool use, reasoning visibility, or runtime behavior.

---

## Decision states

The current instruction-owned decision-state vocabulary is:

- Continue
- Benign
- Malicious
- Unresolved due to evidence gaps

A final state is supported only when reviewed evidence supports it; the instruction source owns enforcement of that rule.

---

## Continue response structure

When the instruction source requires the full continue structure, the expected section order is:

1. BLUF
2. FACTS AND SOURCES
3. ANALYSIS
4. SYNTAX VERIFICATION
5. SINGULAR TRIAGE COMMAND
6. ANALYST SCRATCHPAD

If BLUF is the required first section, the instruction-owned output contract expects no malformed preamble, scaffold text, or internal state block above it.

---

## Singular-command rule

For continue states, the instruction-owned command contract expects one copy-paste-ready command or query unless a multi-step exception is necessary and explicitly justified.

Alternate command drafts or repeated command sections are output-contract defects.

---

## Command lanes

| Lane | Correct rendering |
| --- | --- |
| Elastic native response action | Native response-action syntax |
| Elastic shell execution | `execute --command "powershell.exe ..." --comment "..."` |
| Local workstation | Direct PowerShell command |

Native Elastic response actions should remain native, and local workstation commands should not be presented as endpoint response-console guidance without the response-action wrapper.

---

## Grounding honesty

The instruction-owned grounding contract distinguishes:

- public web grounding;
- uploaded or attached files;
- connector-backed retrieval;
- unsupported or unavailable lookup.

A search, lookup, retrieval, validation, or handoff claim is supported only when the action actually ran and produced usable support.

---

## Action-state honesty

The instruction-owned action-state contract keeps these states separate:

- requested action;
- planned action;
- executed action;
- returned result;
- bounded inability.

---

## No internal scaffold leakage

The instruction-owned output hygiene contract treats these as internal material, not analyst-facing content:

- planner payloads;
- routing state;
- readiness objects;
- hidden diagnostics;
- YAML or JSON control scaffolding;
- transfer or handoff narration.

The analyst-facing answer is expected to read as one clean final response, not an internal work trace.

---

## Single-draft rule

The instruction-owned output contract expects exactly one final analyst-facing draft.

The following are output-contract defects:

- duplicate final sections;
- repeated near-identical section pairs;
- alternate drafts;
- malformed preamble text before the first required section.

If overlapping branch drafts exist internally, the instruction source expects them to be reconciled silently into one final compliant version.

---

## Related pages

- Use this page as reference material for Gemini user-visible response and command-lane discipline.
- Use Knowledge - Collector - Feature and Output Contract Reference for collector output-contract details.
- Use Knowledge - Core - Elastic Quick Start for Elastic endpoint quick-start command examples.

---

> Supporting human-readable Knowledge doc. Not part of the DCOIR control plane.