# Hard Stop Conditions

Stop and ask or report conflict when any of these are true:

1. The task-required authority surface is missing or inconsistent. For startup/admin/live-queue work, Airtable `CONTROL-STARTUP-AIRTABLE-FIRST` and live Airtable state are sufficient; missing GitHub CP files are not a blocker unless repository-source work requires them.
2. The task would require treating a non-current file as authoritative.
3. The requested result would change the released file set in materially different ways depending on an unresolved operator choice.
4. The task requires a safety-sensitive action or a claim of verification that cannot be supported.
5. The workspace has drifted beyond the known mapping or skill logic and continuing would require inventing filenames, folders, or authority.
6. The operator explicitly reserved the decision for themselves.
7. The request conflicts with Project Instructions or the current control plane.

## Conflict-report format

When a hard stop is triggered, report:
- the exact role, file, or rule that conflicts
- why the conflict blocks a safe or authoritative choice
- the single best next move needed to unblock the work

## Non-blocking issues

Do not stop for these alone:
- historical files still present beside current ones
- missing stylistic preference that does not affect authority
- incomplete evidence when a bounded assessment is still possible
- multiple equivalent implementation paths with the same authoritative outcome
