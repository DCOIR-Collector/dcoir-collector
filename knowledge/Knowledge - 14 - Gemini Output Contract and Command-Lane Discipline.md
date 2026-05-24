# Knowledge - 14 - Gemini Output Contract and Command-Lane Discipline

_Gemini final structure, decision states, and command-lane separation_

**Summary:** Use this page to keep Gemini responses honest about decision state, executed actions, grounding, and endpoint-versus-local commands.

---

## Decision states

Allowed states:

- Continue
- Benign
- Malicious
- Unresolved due to evidence gaps

Do not use a final state before reviewed evidence supports it.

---

## Continue response structure

Continue-state responses should preserve this order when the full structure is required:

1. BLUF
2. FACTS AND SOURCES
3. ANALYSIS
4. SYNTAX VERIFICATION
5. SINGULAR TRIAGE COMMAND
6. ANALYST SCRATCHPAD

If BLUF is the required first section, no malformed preamble, scaffold text, or internal state block may appear above it.

---

## Singular-command rule

For continue states, provide one copy-paste-ready command or query unless a multi-step exception is necessary and explicitly justified.

Do not emit alternate command drafts or repeated command sections.

---

## Command lanes

| Lane | Correct rendering |
| --- | --- |
| Elastic native response action | Native response-action syntax |
| Elastic shell execution | `execute --command "powershell.exe ..." --comment "..."` |
| Local workstation | Direct PowerShell command |

Do not wrap native Elastic response actions in shell syntax for visual consistency. Do not paste local commands into endpoint guidance without the response-action wrapper.

---

## Grounding honesty

Gemini must distinguish:

- public web grounding;
- uploaded or attached files;
- connector-backed retrieval;
- unsupported or unavailable lookup.

Do not claim a search, lookup, retrieval, validation, or handoff happened unless the action actually ran and produced usable support.

---

## Action-state honesty

Keep these separate:

- requested action;
- planned action;
- executed action;
- returned result;
- bounded inability.

---

## No internal scaffold leakage

Do not leak:

- planner payloads;
- routing state;
- readiness objects;
- hidden diagnostics;
- YAML or JSON control scaffolding;
- transfer or handoff narration.

The analyst-facing answer should read as one clean final response, not an internal work trace.

---

## Single-draft rule

Gemini should emit exactly one final analyst-facing draft.

Do not emit:

- duplicate final sections;
- repeated near-identical section pairs;
- alternate drafts;
- malformed preamble text before the first required section.

If overlapping branch drafts exist internally, reconcile them silently and return only the final compliant version.

---

## Related pages

- Use this page for Gemini user-visible response and command-lane discipline.
- Use Knowledge 17 for collector output-contract details.
- Use Knowledge 02 for Elastic endpoint quick-start command examples.

---

> Supporting human-readable Knowledge doc. Not part of the DCOIR control plane.
