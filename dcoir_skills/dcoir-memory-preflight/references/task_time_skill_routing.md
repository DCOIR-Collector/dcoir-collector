# Task-Time Skill Routing for dcoir-memory-preflight

Purpose: make DCOIR skills fire before relevant work, not only during startup, while `dcoir-memory-preflight` owns continuity, checkpointing, closeout, handoff, and active branch recovery.

Use compact task-time routing whenever a DCOIR task may involve authority, schema, queue/branch state, helper-memory, operator preferences, local configuration, reusable tools, packaging, validation, execution lane choice, checkpointing, closeout, or handoff.

Routing priorities:
1. Preserve continuity first. If branch, task, blocker, milestone, starter prompt, handoff, closeout, remember/capture, or carry-forward state matters, `dcoir-memory-preflight` owns checkpoint-need detection, checkpoint-ready payload preparation, and Airtable Session Checkpoint writes when allowed.
2. Protect Airtable structure next: if table/field ids, select options, linked-record dependencies, cleanup, migration, deletion, or schema-sensitive writes matter, route to `dcoir-airtable-schema-cache` and live schema readback.
3. Resolve decisions/gates: if branch choice, authority drift, approval, grouped delivery, proceed/ask/stop, persistence, or operator preference matters, route to `dcoir-decision-policy`.
4. Protect local configuration: if generated code or commands reference environment/config names, route to `dcoir-local-config-registry-maintainer`.
5. Use the right lane: if local Git/GitHub Desktop/operator_tools/reusable scripts matter, route to `dcoir-github-desktop-lane-advisor`.
6. Package only when required: if deliverables or skill/repo zips matter, route to `dcoir-repo-packager`.
7. Validate before readiness: if readiness, regression, post-change proof, or evidence matters, route to `dcoir-validation-orchestrator`.

Hard rule: when in doubt, perform a compact routing check instead of skipping a potentially relevant skill.

## Non-compete checkpoint routing
Only one helper writes or prepares the active Session Checkpoint for a turn. `dcoir-memory-preflight` is the checkpoint owner for DCOIR unless a future source-authority decision explicitly assigns a different writer and updates the governing project/Airtable/source surfaces first.
