# DCOIR Write Gate Contract

## Plain English summary
The Write Gate is a safety check before a DCOIR Airtable or governance change runs. It answers: do we know exactly what will change, why it is allowed, how we prove it worked, and how we stop if something is wrong?

## Gate results
- PASS: safe to proceed in the selected lane, if any separate approval is already present.
- CONDITIONAL_PASS: almost ready, but a named condition must be fixed first.
- FAIL: not safe as written; repair the missing or bad evidence.
- STOP_ESCALATE: stop for operator decision or authority/safety repair.

## Required evidence
A complete gate review needs:
1. exact target identity
2. one action type
3. authority basis
4. payload or record identity
5. live schema evidence when Airtable fields/options matter
6. duplicate and dependency checks
7. approval scope
8. execution lane
9. readback plan
10. evidence destination
11. failure or rollback plan
12. hard-stop review

## Duplicate search rules
Search exact stable keys first. Then search primary title, aliases, and source locators. Search related governance surfaces when the concept may appear in more than one table. Classify matches as current, historical, retired, candidate, scaffold, or residue.

## Schema rules
Use live Airtable schema for schema-sensitive work. Confirm table id, field id, field type, select choices, linked-record targets, defaults if relied on, and filter/search fields. Cache is only a helper.

## Hard stops
Stop for missing approval on high-risk work, authority conflict, live schema contradiction, unresolved dependencies, secret exposure, wrong source surface, or any case where proceeding could make state drift worse.

## Reporting format
Use this compact format:

```text
Gate result: PASS | CONDITIONAL_PASS | FAIL | STOP_ESCALATE
Plain English: <one or two sentences>
Missing or risky: <short list>
Next safe action: <single next step>
```
