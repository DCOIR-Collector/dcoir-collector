# Knowledge - 12 - Gemini Runtime Bundle and Source Tree

_Gemini runtime capability and attachment boundaries_

**Summary:** Use this page to remember that Gemini attachments support interpretation and response behavior, but they do not create hidden tools, hidden searches, or connector capability by themselves.

---

## Boundaries

The runtime attachment set can provide:

- stable reference context;
- routing support;
- command-lane interpretation support;
- output-discipline support;
- collector and artifact interpretation support.

The runtime attachment set does not by itself create:

- enterprise search;
- connector-backed retrieval;
- public-web search results;
- command execution;
- hidden background work;
- durable memory;
- proof that an external workflow or tool already ran.

If a source lane or action did not actually return evidence in the session, Gemini must not claim that it happened just because an attachment discusses that lane.

---

> Supporting human-readable Knowledge doc. Not part of the DCOIR control plane.
