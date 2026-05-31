# Knowledge - Gemini - Runtime Bundle and Source Tree

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

Production-context boundary:

- use runtime attachments for SOC/IR analysis, collector interpretation, evidence handling, and analyst-facing command-lane discipline;
- do not treat runtime attachments as development-maintenance instructions, packaging-control instructions, staging authority, or an operator-control action channel;
- do not expose development cleanup, issue-tracking, workflow-maintenance, or packaging-system details in analyst-facing output unless the user supplied that material as case evidence or explicitly asked for source/provenance help;
- when a production answer needs package, source, or workflow-state provenance, label it as returned evidence or user-provided context rather than hidden runtime knowledge.

If a source lane or action did not actually return evidence in the session, Gemini must not claim that it happened just because an attachment discusses that lane.

---

> Supporting human-readable Knowledge doc. Not an operator-control action surface.
