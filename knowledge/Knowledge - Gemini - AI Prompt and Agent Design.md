# Knowledge - Gemini - AI Prompt and Agent Design

_Gemini runtime design principles for routing, grounding, and output behavior_

**Summary:** Use this page to keep Gemini routing, grounding, action-state honesty, and output behavior clear during live operator use.

---

## Agent field responsibilities

| Field | Purpose |
| --- | --- |
| Description | Routing: when the agent or sub-agent should be used and what it owns |
| Instructions | Behavior: what the agent must do, avoid, and output |
| Attachments | Context: stable reference material that helps the agent interpret evidence and explain next steps |

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
- describing planned or requested actions as completed actions;
- letting routing language become so broad that the wrong specialist branch is chosen.

---

> Supporting human-readable Knowledge doc. Not part of the DCOIR control plane.
