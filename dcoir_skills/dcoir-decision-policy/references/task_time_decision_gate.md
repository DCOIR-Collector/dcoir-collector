# Task-Time Decision Gate for dcoir-decision-policy

Use this reference when a DCOIR task needs a quick proceed/ask/stop decision before execution.

## Frequent-fire rule
Prefer a compact decision gate over skipping decision-policy when the request includes authority, approval, persistence, lane, validation, packaging, cleanup, deletion, schema, source-role, or operator-preference consequences.

## Trigger matrix
- Authority/source drift: use control-plane precedence, report exact conflict, prefer Airtable for live operational state unless source-authority comparison is the task.
- Approval gates: destructive actions, Airtable writes, Delete Queue processing, repo writes, package/release claims, and durable preference persistence require explicit approval unless already approved in the current task.
- Lane choice: pick the safest effective lane among in-session tools, GitHub connector/workflows, GitHub Desktop/manual bundle, reusable operator tools, or manual review.
- Persistence: distinguish session-local buffer, Airtable governance/memory, GitHub source/parity, package artifact, or no persistence.
- Campaign cadence: prefer a bounded coordinated campaign when scope is known and operator approved; otherwise keep changes one skill/task at a time.
- Validation: route readiness/evidence claims to dcoir-validation-orchestrator and checkpoint continuity through dcoir-session-manager.

## Compact output template
Decision gate: <green|yellow|red>. Authority: <basis>. Lane: <chosen lane>. Approval gate: <none|required>. Persistence: <none|session-local|Airtable|GitHub|package>. Companion skills: <names>. Verification/checkpoint: <needed>. Next move: <single action>.

## Hard stops
Stop for authority conflict, missing required approval, unresolved destructive dependency order, unsupported verification claim, final artifact ambiguity, or a reserved operator decision.
