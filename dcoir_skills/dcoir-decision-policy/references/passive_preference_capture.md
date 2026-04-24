# Passive Preference Capture

Use this file when the operator states a preference, opinion, correction, or process principle without being asked a direct question.

## Purpose

Capture useful operator intent from ordinary statements so the skill can become more like a virtual operator proxy over time.

This mechanism is approval-gated. It may interpret a candidate rule immediately within the current conversation, but it must not persist the rule silently.

## Trigger patterns

Consider passive capture when the operator says things like:
- prefer
- do not
- always
- never
- no need to
- keep it simple
- default to
- avoid
- I want
- I do not want
- should
- should not
- when possible
- unless necessary

These phrases are signals, not automatic persistence.

## Candidate classes

Classify the statement into one of these:
- durable preference candidate
- situational preference candidate
- one-off comment with no policy value

## Durable preference indicators

Prefer the durable class when most of these are true:
- the statement describes a broad working style or default
- the statement would plausibly apply across future tasks
- the statement reduces future clarification cost
- the statement does not depend on one specific file, date, or incident
- the statement is consistent with prior operator behavior

Examples:
- prefer the lowest-friction approach that still preserves control
- do not make me re-upload files unless necessary
- bundle multi-file updates into one zip so I have fewer downloads
- default to the smallest maintainable change
- keep recommendations narrow instead of giving a large menu
- when the remaining similar skills are already known, prefer one bounded coordinated campaign instead of a slow trickle of onesy-twosey pushes

## Situational preference indicators

Prefer the situational class when one or more are true:
- the statement is tied to the current release or artifact only
- the statement depends on a temporary project posture
- the statement is useful later in the same conversation but not obviously durable
- promoting it broadly could distort future decisions

Examples:
- for this validation round, test only repo mode first
- keep this package local until we finish the comparison
- use the current change-log wording for this release set
- for this one release, attach the larger reference bundle even though it is not the normal default

## No-policy-value indicators

Do not persist when any of these dominate:
- it is only emotional emphasis with no actionable default
- it restates what the current control plane already requires
- it is too vague to guide a future branch
- it is clearly a one-time reaction without generalizable meaning

## Derivation workflow

1. Quote the observed statement concisely.
2. Infer the narrowest reusable rule that fits the statement.
3. Run the safe generalization test.
4. Classify it as durable, situational, or non-persistent.
5. Apply it immediately in the current chat if relevant.
6. If it affects downloadable outputs, bundle shape, update cadence, campaign scope, or operator update steps, surface the approval block in the same response turn where practical.
7. Surface a short approval block before persistence.

## Safe generalization test

Persist only when all are true:
- the interpreted rule can be stated in one sentence
- the rule would help answer future branch choices
- the rule does not conflict with the control plane or safety
- the rule is not just a paraphrase of a one-off artifact fact

If any test fails, keep it current-chat only.

## Approval block format

When a candidate should be persisted, present it in this shape:
- Observed statement: <one sentence>
- Interpreted rule: <one sentence>
- Class: <durable | situational>
- Persistence target: <operator_intent_matrix.md | decision_learning_log.json>
- Current-task effect: <one sentence>

## Persistence target rules

- durable preference candidate -> `references/operator_intent_matrix.md`
- situational preference candidate -> `references/decision_learning_log.json`
- one-off comment -> no persistence target

## Conflict handling

If the interpreted rule appears to conflict with an approved durable rule:
1. show the old rule
2. show the new interpreted rule
3. ask whether to replace, narrow, or keep both with scoped conditions

Do not overwrite approved durable rules silently.
