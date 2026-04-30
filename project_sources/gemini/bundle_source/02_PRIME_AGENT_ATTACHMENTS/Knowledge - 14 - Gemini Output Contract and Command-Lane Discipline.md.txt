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

---

## Singular-command rule

For continue states, provide one copy-paste-ready command or query unless a multi-step exception is necessary and explicitly justified.

---

## Command lanes

| Lane | Correct rendering |
| --- | --- |
| Elastic native response action | Native response-action syntax |
| Elastic shell execution | `execute --command "powershell.exe ..." --comment "..."` |
| Local workstation | Direct PowerShell command |
| GitHub Actions | Workflow name and inputs |

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

## Validation expectations

Output-contract validation should check:

- exact final structure;
- one-command pacing;
- command-lane rendering;
- no scaffold leakage;
- grounding/support proof;
- action-state truthfulness.

---

## Cross-reference boundaries

- Use this page for Gemini user-visible response and command-lane discipline.
- Use Knowledge 17 for collector output-contract details.
- Use Knowledge 02 for Elastic endpoint quick-start command examples.
- Use Knowledge 15 for attachment maintenance.

---

> Supporting human-readable Knowledge doc. Not part of the DCOIR control plane.
