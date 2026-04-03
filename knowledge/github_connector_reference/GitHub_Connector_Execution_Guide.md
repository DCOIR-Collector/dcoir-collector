# GitHub Connector Execution Guide

Purpose
- This guide explains how the DCOIR project should use the GitHub connector reference pack in practice.
- It is the human-oriented companion to `github_connector_information.json`.

Chosen format strategy
- Use `github_connector_information.json` as the canonical machine-readable **distilled** snapshot.
- Use this guide as the human-facing companion distilled from the uploaded TXT view and the current DCOIR GitHub workflow.
- Do not maintain two large raw reference files unless there is a later proven reason to keep both.

Recommended operating sequence
1. Re-anchor to Project Instructions.
2. Read CP-01, then CP-02.
3. Run GitHub task-memory preflight when the task family is GitHub-heavy or likely to hit a known procedure.
4. Classify the job:
   - read and inspect
   - create a new file
   - update an existing file
   - grouped multi-file change
   - delete or cleanup
   - issue or pull-request interaction
   - branch, tree, commit, or ref work
5. Open `github_connector_information.json` and identify the smallest candidate function set.
6. Compare required inputs and expected outputs before choosing the lane.
7. Prefer the validated low-level git-object transaction lane for existing-file updates and grouped changes, even if other connector functions appear simpler.
8. After any write action, verify the final repo state by readback.

How the reference pack should help
- reduce avoidable guesswork about function names and parameters
- speed up function selection for repo work
- improve consistency when the operator asks for step-by-step GitHub guidance
- make it easier to promote proven connector patterns into task memory

What this guide should not do
- It should not override the live connector tool surface.
- It should not replace canonical GitHub task-memory procedures.
- It should not be treated as proof that every listed function is the best choice for a given DCOIR task.

High-value promotion targets
- common function families worth mapping into durable procedures:
  - repo readback and verification
  - new file create
  - existing file overwrite
  - grouped tree or commit or ref change sets
  - issue or PR comment and review workflows
  - branch-safe planning patterns

DCOIR-specific workflow reminders
- For existing-file repo updates, prefer the validated git-object lane and post-write verification already documented in GitHub task memory.
- For grouped related repo changes, prefer one bounded transaction over one-file-at-a-time churn.
- For operator training, optional ChatGPT Codex tasks should be offered as step-by-step, click-by-click learning exercises, starting basic before advanced.
- All project-specific helper skills must retain the `dcoir-` prefix.

Next maintenance step
- Mine the governed connector snapshot for the most reusable DCOIR GitHub execution patterns and promote them into canonical task memory and operator-facing GitHub procedure guidance.
