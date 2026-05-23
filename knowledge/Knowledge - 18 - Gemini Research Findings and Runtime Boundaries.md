# Knowledge - 18 - Gemini Research Findings and Runtime Boundaries

_Governed summary of post-research Gemini design findings that affect DCOIR prompt source, runtime claims, and validation posture_

**Summary:** Use this page when changing Gemini prime-agent or sub-agent source, output-contract wording, grounding claims, or runtime-validation expectations. It condenses the highest-value findings from the final Gemini research reference set so those findings do not remain trapped in a legacy Airtable export.

---

## Why this page exists

The final Gemini research set showed that several important behaviors should not be treated as intuition or product folklore:

- grounded answers must stay tied to returned evidence;
- progress or planner text is not proof of execution;
- retrieval misses can come from indexing, extraction, connector, or scope limits rather than planner quality alone;
- structured-output guarantees differ across Gemini Enterprise, Agent Designer, Vertex/API, and ADK or Agent Engine paths;
- observability and execution proof belong more to runtime receipts and logs than to UI assumptions.

This page is the governed human-readable capture of those findings.

---

## Core design rules

### 1. Narrate only from returned evidence

Do not claim a search, tool use, grounding step, enterprise lookup, workflow action, or validation event happened unless the current path returned usable evidence for it.

Keep these separate:

- requested action
- planned action
- executed action
- returned result
- bounded inability

Progress wording is allowed only when it is visibly provisional and not disguised as completion.

### 2. Use staged execution wording

The strongest documented anti-fabrication pattern is:

1. decide whether grounding or a tool is needed
2. execute it
3. narrate only from the returned result

Do not let hidden planner state, status text, or draft scaffolding become analyst-facing proof.

### 3. Preserve bounded grounded-source claims

Scope grounded claims to the source family that actually supported them.

Possible grounded families include:

- uploaded or attached files
- connector-backed enterprise retrieval
- public web grounding
- custom search or configured enterprise data stores
- returned runtime tool results

Do not collapse these into a vague claim that "Gemini searched everything" or "enterprise data was checked" unless the actual configured lane returned evidence.

### 4. Treat misses as bounded, not magical

A no-result or weak-result outcome can come from:

- over-narrow query shape
- field mismatch
- index mismatch
- connector limits
- searchable-text extraction limits
- file-size or indexing limits
- source absence
- retention or timing limits
- unsupported or unavailable grounding

A retrieval miss is not safely attributable to planner quality alone and is not proof of benignity, maliciousness, stealth, or absence.

### 5. Keep output contracts realistic for the runtime surface

Do not over-promise schema-locked output on Gemini Enterprise or Agent Designer web surfaces just because stronger structured-output controls exist on Vertex or API paths.

Where schema-native constraints are truly supported, prefer them over duplicating the same schema contract in prompt prose.

Where they are not supported, rely on prompt-source rules plus runtime validation and readback.

### 6. Prefer runtime receipts over UI assumptions

For execution proof and observability, prefer:

- sessions
- events
- tool-call traces
- invocation IDs
- runtime logs
- downstream resource logs

Treat preview, partial, or UI-only observability as bounded evidence rather than complete proof.

---

## Prime-agent and sub-agent implications

These findings should shape Gemini source work in the following ways:

- prime-agent source should explicitly forbid fake completion narration and unsupported groundedness claims
- query-planning and output-contract layers should preserve one exact next action and one final rendered answer
- zero-result guidance should distinguish planner failure from source-lane or indexing limits
- output-contract layers should preserve no-internal-scaffold leakage and no duplicate final drafts
- runtime-facing validation should fail fabricated groundedness, fake action completion, duplicate drafts, or malformed preamble spillover

---

## Validation implications

Gemini validation should check for at least:

- exact final structure when required
- one-command pacing
- no internal scaffold leakage
- no duplicate final drafts or duplicate final sections
- no malformed preamble before the first required section
- no fake completion narration
- bounded source-family wording
- bounded zero-result wording
- support evidence present when grounded or executed behavior is claimed

---

## Current caution boundaries

These research findings do not mean every Gemini runtime path has the same guarantees.

Be careful about:

- assuming enterprise web or no-code agent session semantics equal Agent Engine sessions
- assuming Model Armor or other enterprise-console safety settings automatically protect registered ADK runtime paths
- assuming preview observability surfaces are complete or stable
- assuming structured-output guarantees are equally strong across enterprise web, Agent Designer, Vertex, and ADK surfaces

---

## Use this page when

Consult this page before changing:

- prime-agent response rules
- sub-agent topology or responsibilities
- output-contract wording
- search or grounding truthfulness wording
- no-result interpretation behavior
- runtime validation expectations
- execution-proof or observability claims

---

> Governed knowledge page derived from the final Gemini research reference set. Use with source readback and runtime validation; do not treat it as proof that every Gemini surface behaves identically.
