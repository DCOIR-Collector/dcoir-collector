---
artifact_type: dcoir-decision-policy-memory
schema_version: 1
project: AFRICOM_SOC_IR / DCOIR
exported_at_utc: 2026-04-10T18:05:00Z
authority_basis:
  - Project Instructions v17
  - project_sources/CP-01_DCOIR_Version_Manifest.txt
  - project_sources/CP-02_DCOIR_Change_Log.txt
---

# DCOIR Decision Policy Memory

## Current focus
Airtable-first durable preference continuity for DCOIR decision-policy state with GitHub-readable promoted overlays and helper-memory follow-through.

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
- **airtable-first durable preference surface** (status: approved; source: operator_intent_matrix)
  - rule: use Airtable `Operator Preferences` as the durable working-state preference surface, consult it before generic defaults when a branch is preference-sensitive, and promote matured DCOIR-facing rules into GitHub-readable policy at the next safe grouped flush point
  - why: the operator explicitly wants durable preference continuity that does not depend only on recollection or direct skill-file edits
  - next_action: keep Airtable and GitHub preference surfaces aligned and surface conflicts instead of silently choosing one
- **concise operator-facing responses by default** (status: approved; source: operator_intent_matrix)
  - rule: default to concise operator-facing responses unless extra detail materially improves continuity, validation, or maintenance quality
  - why: the operator prefers shorter direct answers by default while still preserving the richer continuity path when it actually matters
  - next_action: apply this in future DCOIR chat reporting while preserving detailed underlying artifacts when needed
- **offer near-equivalent alternatives when the main path is not ideal** (status: approved; source: operator_intent_matrix)
  - rule: when a requested or candidate path is workable but not ideal, surface the best bounded path and one or more near-equivalent alternatives when that materially helps the operator choose without expanding into a broad unfocused menu
  - why: the operator explicitly wants alternatives that reach the same or a very similar result instead of a single-path recommendation only
  - next_action: keep applying this in future decision branches where tradeoffs matter

## Pending or situational learning
- **GitHub-backed helper-memory rollout sequencing** (status: in_progress; source: current_chat)
  - rule: prefer converting the highest-value helper skills before starting new net-new super-skill work
  - why: establish a stable GitHub-primary foundation first
  - next_action: reassess after operator verifies the manual skill updates

## Airtable durable preference surface
- Airtable table: `Operator Preferences` (`tblnxZ3eLPT3W38wl`)
- Role: durable working-state preference capture, candidate tracking, cross-session lookup, and provenance before or alongside later GitHub promotion
- Current posture: seeded with standing general preferences plus the repo-side decision-policy overlays mirrored from `operator_intent_matrix.md` and this helper-memory file
- GitHub promotion rule: treat Airtable as working state and GitHub as promoted readable state; do not silently rewrite approved GitHub durable rules when the two differ

## Delivery and update preferences
- bundle multi-file skill updates into one zip when that lane is chosen
- keep helper memory in `dcoir_skill_memory/` and separate from governed project files
- ask before shifting repo updates to GitHub Desktop or another operator-managed lane
- for existing-file GitHub recovery, use canonical GitHub task memory before writing any capability-boundary explanation
- when multiple downstream GitHub updates are already known, batch them into one grouped update
- use Airtable `Operator Preferences` as the faster durable capture surface and promote matured DCOIR-facing rules into GitHub-readable policy later
- default to concise operator-facing responses unless extra detail materially improves continuity, validation, or maintenance quality
- when a requested or candidate path is not ideal, include one or more near-equivalent alternatives when useful

## Next actions
- keep the Airtable preference table and the GitHub-readable decision-policy surfaces aligned after material preference changes
- re-read Airtable `Operator Preferences`, `references/operator_intent_matrix.md`, and this file before future packaging-handoff, repo-update lane, or preference-sensitive branching decisions
- preserve conflicts explicitly when Airtable working state and GitHub approved durable overlays diverge until the operator resolves the conflict or the next grouped promotion is complete

## Provenance notes
- Initialized during the five-skill GitHub-memory rollout.
- Expanded on 2026-04-03 after the operator clarified that repo-update lane choice must stay under explicit operator control.
- Expanded again on 2026-04-03 after recovery of the validated low-level git-object lane for existing-file updates.
- Expanded again on 2026-04-03 after the operator required batching known downstream GitHub follow-on updates into one grouped change set.
- Expanded on 2026-04-10 after the operator required `dcoir-decision-policy` to use the Airtable-backed Operator Preferences surface alongside the GitHub repo, mirroring repo-side overlays into Airtable durable working state and promoting matured DCOIR-facing rules back into the authoritative GitHub-readable surfaces at the next safe grouped flush point.
