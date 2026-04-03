# Remediation Model

## Purpose
This skill prioritizes what to fix first after DCOIR live testing and defines what must be re-tested before the repaired path is considered ready again.

## Current active remediation themes
Ground planning in the current authoritative workspace, especially the todo log and handoff brief. The present active themes include:
- merged alert-triage-to-collector workflow validation
- operator workflow guidance quality
- collector output interpretation and retrieval guidance
- large-file fallback behavior
- bounded-confidence and scope discipline
- packaging drift from retired collector-name and older knowledge-doc folder assumptions

## Priority intent
Choose the smallest truthful fix that removes the highest operational risk first.

Favor:
- issues that block operators from completing the workflow
- issues that create wrong or unsafe next-step guidance
- issues that could cause incorrect packaging or stale source-of-truth handling
- issues that are likely to recur unless encoded into a skill, prompt, or workflow artifact

## Deep-regression default
After a remediation patch, deep-regress the repaired path before it is considered ready again when the change affects:
- any DCOIR skill
- any script or harness
- bundle generation or packaging rules
- operator command generation or command-lane separation
- collector output interpretation or retrieval logic
- large-file fallback or bounded-confidence behavior

## Output intent
The report should answer:
- what to fix first
- which files or skills are most likely implicated
- what has to be re-tested after the fix
- whether the issue is targeted or structural enough to push toward a full-refresh bundle
