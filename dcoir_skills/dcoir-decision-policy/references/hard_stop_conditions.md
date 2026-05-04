# Hard Stop Conditions

Stop and ask or report conflict when any of these are true:

1. The task-required authority surface is missing or inconsistent. For startup/admin/live-queue work, Airtable `CONTROL-STARTUP-AIRTABLE-FIRST` and live Airtable state are sufficient; missing GitHub CP files are not a blocker unless repository-source work requires them.
2. The task would require treating a non-current file as authoritative.
3. The requested result would change the released file set in materially different ways depending on an unresolved operator choice.
4. The task requires a safety-sensitive action or a claim of verification that cannot be supported.
5. The workspace has drifted beyond the known mapping or skill logic and continuing would require inventing filenames, folders, or authority.
6. The operator explicitly reserved the decision for themselves.
7. The request conflicts with Project Instructions or the current control plane.
8. A task assumes a retired or absent Airtable table, field, registry, helper-memory surface, or repo file exists without current live schema/readback proof.
9. A task treats GitHub CP/todo/promoted-history files as live queue authority after the Airtable-first control plane is current.
10. A repo cleanup, helper-skill retirement, source rewrite, destructive delete, or schema write has unresolved dependency order, missing approval evidence, or missing readback verification.

## Source-authority and drift gate

This section preserves the hard-stop and authority-drift behavior formerly handled by a retired source-authority helper. Use it from `dcoir-decision-policy` whenever source authority, live-state alignment, or cleanup safety could materially affect the outcome.

### Audit outcomes

Use one of these outcomes when source authority is in doubt:

- `clear_to_proceed`: the control plane resolves; task-required authority surfaces are present; current repo source/readback is available when needed; no current-vs-historical conflict is found.
- `proceed_bounded`: the control plane is clear but evidence is partial; no contradiction is proven; the answer or action must state which surfaces were unavailable or inferred.
- `hard_stop_conflict`: an authority surface required for the task is missing, stale, contradictory, or unsafe to infer.

### Drift families

Classify authority drift using these families when reporting conflicts:

- `startup_authority_conflict`: Project Instructions, CP-00, Governance Control Plane, or live Airtable state disagree about startup/live queue rules.
- `schema_assumption_drift`: a table, field, select option, linked-record path, or helper-memory table is assumed without live schema readback.
- `github_promoted_history_drift`: GitHub CP/todo/promoted history is treated as live queue authority when Airtable is live authority.
- `skill_instruction_drift`: installed or source skill instructions reference retired tables, old cutover language, deleted helpers, or obsolete workflows.
- `project_attachment_drift`: Project attachment wording conflicts with the current operational model.
- `repo_surface_drift`: repo keep/delete/source-role classification is unclear or conflicts with Repo Surface Registry.
- `delete_queue_dependency_drift`: deletion order, approval, or verification path is unclear.
- `helper_memory_drift`: helper memory appears split between old GitHub memory and Airtable helper-memory tables.
- `connector_failure_drift`: a connector failure causes unsupported fallback assumptions.

Severity levels:

- `info`: note only; no immediate workflow risk.
- `warning`: could cause extra roundtrips or mild confusion.
- `high`: could cause wrong source choice, duplicated tasks, bad package, or stale skill behavior.
- `critical`: could cause destructive delete, schema write, source overwrite, or hard authority conflict.

### Authority report fields

When reporting an authority hard stop, include only the fields needed to unblock the work:

- audit outcome
- authoritative basis used
- exact drift or conflict
- affected active surfaces
- expected authority versus observed conflicting or missing source
- drift family and severity
- smallest remediation set
- whether the fix requires a skill update, Airtable data update, GitHub source update, table deletion, or operator decision
- single best next move

## Conflict-report format

When a hard stop is triggered, report:
- the exact role, file, table, record, or rule that conflicts
- why the conflict blocks a safe or authoritative choice
- the single best next move needed to unblock the work

## Non-blocking issues

Do not stop for these alone:
- historical files still present beside current ones
- missing GitHub CP files during startup/admin/live-queue work when Airtable startup authority and live state are current
- missing stylistic preference that does not affect authority
- incomplete evidence when a bounded assessment is still possible
- multiple equivalent implementation paths with the same authoritative outcome
- a retired source folder or helper-memory table that has already been replaced and archived with readback evidence
