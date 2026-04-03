---
artifact_type: dcoir-decision-policy-memory
schema_version: 1
project: AFRICOM_SOC_IR / DCOIR
exported_at_utc: 2026-04-03T21:35:00Z
authority_basis:
  - Project Instructions v15
  - project_sources/CP-01_DCOIR_Version_Manifest.txt
  - project_sources/CP-02_DCOIR_Change_Log.txt
---

# DCOIR Decision Policy Memory

## Current focus
GitHub-backed decision-memory continuity for DCOIR helper skills

## Approved overlay snapshot
- **single bundle for multi-skill updates** (status: approved; source: operator_intent_matrix)
  - rule: prefer one zip bundle containing the full update set and concise replacement instructions
  - why: minimize operator downloads and manual update burden
  - next_action: keep applying this default for multi-skill updates
- **operator chooses repo update lane** (status: approved; source: operator_intent_matrix)
  - rule: when repo updates could be done either in chat or through GitHub Desktop or another operator-managed lane, ask which lane the operator wants before shifting the work
  - why: the operator may not always be on a machine where GitHub Desktop is available and wants explicit control over whether the update stays in chat
  - next_action: apply this before suggesting or shifting to any operator-managed repo-update path
- **github existing-file recovery comes before limitation claims** (status: approved; source: operator_intent_matrix)
  - rule: for GitHub-family existing-file or grouped existing-file friction, re-anchor and apply GH-PROC-007 plus GH-PROC-001 or GH-PROC-006, then GH-PROC-005, before writing durable limitation or connector-failure claims
  - why: avoid turning assistant procedure-recovery failure or execution-discipline failure into a false permanent record about capability boundaries
  - next_action: use this as the default recovery order for GitHub-family write friction
- **aggregate known downstream github follow-on updates** (status: approved; source: operator_intent_matrix)
  - rule: when multiple downstream GitHub control-plane, continuity, task-memory, or helper-memory updates are already known, collect them into one bounded grouped transaction instead of serial one-off commits or repeated best-next-move nudges
  - why: reduce churn, preserve grouped intent, and avoid forcing the operator through repeated tiny repo updates
  - next_action: treat this as the default posture unless an unresolved dependency requires an intermediate commit

## Pending or situational learning
- **GitHub-backed helper-memory rollout sequencing** (status: in_progress; source: current_chat)
  - rule: prefer converting the highest-value helper skills before starting new net-new super-skill work
  - why: establish a stable GitHub-primary foundation first
  - next_action: reassess after operator verifies the manual skill updates

## Delivery and update preferences
- bundle multi-file skill updates into one zip when that lane is chosen
- keep helper memory in dcoir_skill_memory/ and separate from governed project files
- ask before shifting repo updates to GitHub Desktop or another operator-managed lane
- for existing-file GitHub recovery, use canonical GitHub task memory before writing any capability-boundary explanation
- when multiple downstream GitHub updates are already known, batch them into one grouped update

## Next actions
- keep the decision memory file current after durable preference or sequencing changes
- re-read this file before future packaging-handoff decisions and repo-update lane decisions

## Provenance notes
- Initialized during the five-skill GitHub-memory rollout.
- Expanded on 2026-04-03 after the operator clarified that repo-update lane choice must stay under explicit operator control.
- Expanded again on 2026-04-03 after recovery of the validated low-level git-object lane for existing-file updates.
- Expanded again on 2026-04-03 after the operator required batching known downstream GitHub follow-on updates into one grouped change set.
