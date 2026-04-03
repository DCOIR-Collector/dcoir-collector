# DCOIR Plan Tracker Blocker Promotion Workflow

## Purpose
This reference explains how to decide whether a blocker stays local to the current plan or becomes a broader reusable lesson.

## Always capture locally first
Every meaningful blocker or failed attempt should be captured in the current plan before any promotion decision.

Record:
- what happened
- where it happened
- failure signature
- attempted fixes
- successful mitigation if found
- whether the blocker looks reusable across similar tasks or technologies

## Keep it local when
- the blocker is clearly one-off
- the mitigation is highly situational
- there is not enough evidence to claim reuse
- the lesson does not improve future execution meaningfully

## Create a promotion-ready candidate when
- the same blocker family is likely to recur
- the mitigation changes the recommended execution lane
- the issue reveals a connector or tool boundary worth documenting
- the mitigation should shape canonical task memory, a helper skill, or a governed document

## Promotion targets
A reusable lesson may be promoted into one of these:
- canonical task memory
- governed project documentation
- a helper-skill update
- a future remediation or maintenance task

## Approval posture
Do not silently turn a local blocker lesson into canonical project doctrine.
Surface a bounded promotion candidate and follow the correct governance path.

## Relationship to companion skills
- use `dcoir-memory-preflight` before execution to avoid known blockers
- use `dcoir-decision-policy` for proceed-versus-ask branch choices
- use this workflow after a blocker is encountered or overcome
