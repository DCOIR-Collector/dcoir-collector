# Operator Intent Learning

Use this file when the current matrix does not fully answer a decision point and one targeted question to the operator is required.

## Purpose

Convert a missing preference into the smallest possible question, then convert the answer into a reusable rule.

## Learning loop

1. Identify the exact branch that is unresolved.
2. Ask one focused question that resolves that branch only.
3. Read the operator's answer literally first.
4. Infer the broader rule only if the answer clearly supports it.
5. Separate durable preference from one-off case fact.
6. Apply the derived rule immediately within the current conversation.
7. If the rule is durable, emit a policy update candidate for future persistence.

## Question-writing rules

The question must:
- resolve one branch only
- avoid offering a broad menu unless necessary
- avoid repeating context the operator already provided
- avoid asking about style preferences that do not materially matter
- prefer defaults plus one confirmation branch when helpful

Good pattern:
- "For structural multi-file changes, should I default to a full-refresh bundle unless you say otherwise?"
- "Since the remaining similar skills are already known, should I treat this as one coordinated campaign instead of more onesy-twosey pushes?"

Bad pattern:
- "How do you want me to handle packaging, validation, naming, promotion, and testing in general?"

## Derivation rules

Map the answer into one of these classes:
- durable preference: likely to apply again across tasks
- workflow rule: process step or sequencing preference
- packaging rule: repo vs update, release scope, bundle default
- validation rule: required test depth or evidence threshold
- evidence/confidence rule: how strongly to word conclusions under partial evidence
- campaign or delivery-friction rule: whether to batch similar work instead of trickling it
- one-off case fact: only for the current task or artifact

## Safe generalization test

Generalize the answer only when all are true:
- the answer is phrased as a rule, default, or repeated preference
- the answer is not obviously tied to one specific file or incident only
- carrying the rule forward would reduce future clarification without changing authority improperly

If any test fails, keep it as a one-off case fact.

## Current-chat persistence

Within the current conversation:
- treat a derived durable rule as an authoritative operator overlay
- prefer the new operator overlay over the default matrix when they conflict
- mention the learned rule only when it materially affects the path chosen

## Cross-chat persistence

A learned rule does not persist automatically across future conversations unless the skill or a current project-readable policy file is actually updated.

When persistence is needed:
1. emit a policy update candidate
2. update the skill or project file
3. repackage or refresh the artifact carrying the rule

## Output pattern after learning

After the operator answers, summarize the learning result in this shape:
- Derived rule: <one sentence>
- Scope: <current chat only | candidate for durable policy update>
- Effect on current task: <one sentence>
