---
artifact_type: dcoir-decision-policy-memory
schema_version: 1
project: AFRICOM_SOC_IR / DCOIR
exported_at_utc: 2026-03-30T12:29:55Z
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

## Pending or situational learning
- **GitHub-backed helper-memory rollout sequencing** (status: in_progress; source: current_chat)
  - rule: prefer converting the highest-value helper skills before starting new net-new super-skill work
  - why: establish a stable GitHub-primary foundation first
  - next_action: reassess after operator verifies the manual skill updates

## Delivery and update preferences
- bundle multi-file skill updates into one zip
- keep helper memory in dcoir_skill_memory/ and separate from governed project files

## Next actions
- keep the decision memory file current after durable preference or sequencing changes
- re-read this file before future packaging-handoff decisions

## Provenance notes
- Initialized during the five-skill GitHub-memory rollout.
