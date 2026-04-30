# Knowledge - 10 - AI Prompt and Agent Design

_DCOIR prompt-pack and Gemini agent design boundaries_

**Summary:** Use this page to distinguish prompt-pack authority, stored-source Gemini runtime files, grounding limits, and agent-routing expectations.

---

## Runtime source model

Gemini agent behavior must come from maintained source files in the repo, not one-off generated text that is never promoted back.

Current source classes:

- prompt-pack files define analyst-facing reasoning and output behavior;
- Gemini bundle source defines agent files and runtime attachments;
- knowledge docs provide supporting context;
- generated artifacts are delivery outputs, not editing authority.

---

## Agent field responsibilities

| Field | Purpose |
| --- | --- |
| Description | Routing: when this agent should be selected and what it owns |
| Instructions | Behavior: what the agent must do, avoid, and output |
| Attachments | Context: stable reference material for workflow, collector behavior, and interpretation |

A short slogan is not enough for routing. Excessive repetition is also not useful.

---

## Grounding honesty

Gemini output must distinguish:

- public web search;
- uploaded/attached files;
- configured connector or enterprise retrieval;
- unsupported or unavailable retrieval.

Do not claim internal or enterprise lookup happened unless the runtime actually used an available retrieval surface.

---

## Action-state honesty

Keep these separate:

- requested action;
- planned action;
- executed action;
- returned result;
- unsupported action.

Do not describe a search, lookup, validation, or handoff as completed unless it actually returned usable evidence or output.

---

## Output contracts

Prefer enforceable output structures over large schemas that are hard to satisfy. When exact formatting matters, keep required fields clear and avoid large optional structures unless they are necessary.

---

## Anti-patterns

- treating design docs as runtime agent files;
- thinning agent instructions until routing becomes vague;
- repeating the same rule in multiple words to create artificial verbosity;
- claiming unavailable search or connector access;
- allowing generated bundle output to drift from stored source;
- changing attachments without updating the manifest and attachment map.

---

## Manual validation alignment

Use Airtable `Validation Test Cases` for dynamic manual test state. Keep durable source changes in GitHub.

---

> Supporting human-readable Knowledge doc. Not part of the DCOIR control plane.
