# Knowledge - 10 - AI Prompt and Agent Design

_The current prompt-pack, Gemini workflow, and supporting design-artifact posture_

**Summary:** Current DCOIR prompt-pack and Gemini design posture, with emphasis on stored-source runtime maintenance, routing-rich descriptions, explicit instructions, truthful grounding boundaries, and exact operator-facing behavior.

| Source class | Authoritative basis |
| --- | --- |
| Project sources | project_sources/PP-01_System_Prompt_v1_0_1.txt; project_sources/PP-02_Output_Schema_v1_0_0.txt; project_sources/PP-03_Baseline_Triage_Prompt_v1_0_0.txt; project_sources/PP-04_Enrichment_Review_Prompt_v0_1_1.txt; project_sources/PP-05_Retrieved_Artifact_Review_Prompt_v0_1_1.txt; project_sources/PP-06_Final_Case_Synthesis_Prompt_v0_1_1.txt; project_sources/PP-07_Agent_Guardrails_v1_0_0.txt; project_sources/PP-08_Combined_Analyst_Facing_Master_Prompt_v1_0_0.txt; project_sources/PP-09_Gemini_Enterprise_Agent_Designer_Generator_Workflow_v1_0_0.txt; project_sources/PP-10_Gemini_Enterprise_Agent_Designer_Bounded_Design_Artifact_v0_1_1.txt |
| Official external sources | Not required for this page |
| Scope note | This page is project-grounded; it does not redefine the schema or the prompt sources. |

## Current design posture

The current DCOIR Gemini design posture is explicit, verbose, stored-source based, and operationally durable. Important runtime behavior should live in the maintained source tree rather than in a one-off generation wave that never gets promoted back into the editable runtime. Predictability, routing quality, command-lane discipline, evidence-first reasoning, and explicit next-step guidance are the higher values.

## Description-field writing

The Description field is routing-critical. A good Description should do more than name a role. It should help the runtime decide what class of work belongs to the agent, what inputs matter most, what outputs the agent owns, what branches it should not take, and when it should be selected instead of a sibling agent.

## Instructions-field writing

Instructions should preserve runtime behavior in enough detail that the final agent does not have to guess. High-quality instructions on this line should preserve startup behavior, branch order, evidence discipline, command-lane separation, error handling, guardrails against overstatement, stop conditions, output expectations, tool-use boundaries, and memory or context behavior when relevant.

## Grounding-lane honesty

Gemini-facing design should distinguish clearly among:
- broader public Google Search grounding
- enterprise web grounding that is still public-web grounded but constrained by the enterprise surface
- enterprise or internal retrieval grounded in uploaded files, configured first-party stores, connectors, or a sanctioned search bridge

Do not let prompt text collapse those lanes into one vague statement such as "I searched everything" or "I checked enterprise sources" when the active runtime surface only had public web grounding or uploaded files.

## Internal-knowledge honesty when connectors are absent

When live enterprise connectors are absent, the safe and truthful internal-knowledge path is the material the operator uploaded or any other retrieval surface that is actually configured. Prompt text should say that plainly. Desired enterprise retrieval behavior cannot be achieved by wording alone when the runtime still lacks the underlying retrieval path.

## Action-state honesty

A strong Gemini design distinguishes among:
- requested action
- planned action
- executed action
- returned result
- bounded inability or unsupported action

Do not let final text blur those states. The runtime should not narrate a search, lookup, or handoff as completed unless the surfaced answer includes the actual support for that action.

## Structured-output caution

When exact output-contract compliance matters, prefer a smaller and more enforceable structure over a large expressive schema that is hard for the runtime to satisfy reliably. Over-complex structures, deep nesting, bloated enums, and large optional-property sets can reduce reliability and increase malformed-output risk.

## Comparative references and what they are for

Comparative-reference agent markdowns preserve the approved field-writing style for density, specificity, and instruction explicitness. They are not there to replace DCOIR behavior. They remind the maintainer what good runtime text looks like when the goal is predictable delegation and explicit operator-safe behavior.

## Stored-source compile model

The default operator-facing Gemini bundle should be compiled from the stored runtime source tree. Once a redesign or rewrite is accepted, the accepted text belongs back in the stored-source tree so future packaging can be compile-based, repeatable, and reviewable.

## Anti-patterns to reject

- treating generated markdown artifacts as the default runtime shipment surface when a stored-source compile tree exists
- using PP-09 or PP-10 as substitutes for actual runtime field text
- thinning agent runtime files during packaging
- letting Description become a short slogan instead of a routing-rich field
- letting Instructions collapse into brief reminders for complex behavior
- claiming enterprise retrieval, enterprise search, or grounded completion without the actual active support surface
- using over-complex output schemas when a smaller exact contract is sufficient

## Relationship to manual validation

Manual validation should live in the dynamic testing lane while source truth remains in GitHub. Airtable `Validation Test Cases` is the standard manual-testing surface for tracking what was run, what failed, and what needs follow-up. The maintained runtime files and attachment files should still be edited in the repo.

> Supporting human-readable Knowledge doc. Not part of the DCOIR control plane.
