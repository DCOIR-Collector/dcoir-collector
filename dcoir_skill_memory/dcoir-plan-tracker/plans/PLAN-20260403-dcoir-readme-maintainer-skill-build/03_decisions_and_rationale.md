# Decisions And Rationale

## 2026-04-03 - README-maintainer need confirmed
- Decision
  - Treat the `dcoir-readme-maintainer` skill as still grounded in the current project working line.
- Rationale
  - The documentation lane still explicitly tracks a dedicated README-maintainer skill as a current candidate for root and folder README maintenance.
  - The session handoff still records the README-maintainer idea as preserved project follow-on work.

## 2026-04-03 - Plan preview before GitHub upload
- Decision
  - For future `dcoir-plan-tracker` usage, show the proposed decomposed plan to the user before first uploading the plan structure to GitHub unless the user explicitly waives preview.
- Rationale
  - The user wants a discussion opportunity before durable tracker writes land.
  - This should reduce avoidable tracker churn and improve early task decomposition quality.
- Persistence note
  - Treat this as an approved working rule for the current conversation and as a future skill-update requirement.

## 2026-04-03 - Prefer grouped GitHub transactions when possible
- Decision
  - Prefer staging content in-session and then using as few GitHub operations as possible, ideally one grouped transaction for related changes.
- Rationale
  - The user wants fewer piecemeal file creates and a more memory-first or buffer-first workflow.
- Current limitation note
  - The connector surface clearly exposes low-level git-object functions for grouped writes, but safe use still depends on recovering all required base repo state. Until that lane is fully reliable in-chat, direct new-file creates may still be used for bounded scaffold creation.

## 2026-04-03 - Explore session-local write buffers
- Decision
  - Treat session-local accumulation and later grouped GitHub flushes as a valid design line for `dcoir-plan-tracker`, `dcoir-session-tracker`, `dcoir-decision-policy`, and `dcoir-memory-preflight`.
- Rationale
  - This could reduce GitHub write churn while preserving richer working context during a session.
- Constraint
  - Session-local state is not cross-session durable unless written to GitHub or exported into a handoff artifact.
