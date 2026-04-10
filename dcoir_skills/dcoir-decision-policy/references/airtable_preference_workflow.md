# Airtable Preference Workflow

## Purpose
Use Airtable as the durable working-state surface for operator preferences and decision overlays that should survive across DCOIR sessions before or alongside later GitHub promotion.

GitHub remains the readable promoted surface for durable project-facing rules that should ship with the skill or helper memory.

## Airtable surface
- Base: AFRICOM SOC IR / DCOIR Airtable base
- Table name: `Operator Preferences`
- Table id: `tblnxZ3eLPT3W38wl`

## Current field ids
- `preference_key` -> `fld98q4UIZsPdPN7s`
- `preference_statement` -> `fldPJYR8l2121YWnU`
- `effective_behavior` -> `fldrn5iy2nP2Cl4O8`
- `status` -> `fld3RX6mX2PxuQ4IP`
- `scope` -> `fldBi5KTUOiEWZtKK`
- `source_session_id` -> `fld7Rft4ETD9YEhWd`
- `source_checkpoint_id` -> `fldfczItHTqUBD8Uz`
- `source_idea_id` -> `fldM4hPeocI2HBD7B`
- `last_confirmed_text` -> `fldUfJqMMZgXsQHEA`
- `notes` -> `fldNyvY56RV3t2rZg`

## Role separation
- Airtable is the primary durable working-state surface for operator preference capture, candidate tracking, and cross-session lookup.
- `references/operator_intent_matrix.md` remains the approved repo-readable durable overlay surface for broad decision defaults that should ship with the skill.
- `references/decision_learning_log.json` remains the situational or pending-learning GitHub surface when a rule should stay reviewable before being treated as approved durable policy.
- `dcoir_skill_memory/dcoir-decision-policy/decision_policy_memory.md` remains the helper-readable GitHub continuity surface for snapshots, delivery-friction notes, campaign posture, and promotion context.

## Read workflow
1. When a current decision branch may be affected by operator preference, read `Operator Preferences` before falling back to generic defaults.
2. Apply rows only when:
   - `status` is `implemented`, and
   - `scope` is `DCOIR workspace` or `both`, and
   - the row materially matches the current branch.
3. Treat `candidate` rows as review context, not as silent durable overrides.
4. If Airtable and approved GitHub durable overlays conflict, surface the conflict and ask whether to replace, narrow, or keep both with scoped conditions.

## Write workflow
1. When the operator states a new preference directly, or answers a targeted decision question clearly enough to create a reusable rule, upsert an Airtable row immediately.
2. Use a stable `preference_key` when practical.
3. Set:
   - `status = implemented` for clear durable rules already being applied,
   - `status = candidate` for still-bounded or still-reviewable cases.
4. Fill source fields when known so later GitHub promotion has provenance.
5. Update `last_confirmed_text` whenever the preference is re-stated, materially refined, or reused successfully.

## Promotion workflow
At the next safe GitHub flush point, evaluate Airtable-held implemented preferences for repo promotion.

Preferred GitHub promotion targets:
- broad durable defaults -> `references/operator_intent_matrix.md`
- situational but still useful carry-forward context -> `references/decision_learning_log.json`
- helper-memory continuity, delivery posture, or campaign notes -> `dcoir_skill_memory/dcoir-decision-policy/decision_policy_memory.md`

Do not treat Airtable as control-plane authority.
Do not silently rewrite approved GitHub durable rules when the Airtable entry conflicts with the current matrix.

## Default scope rules
- `DCOIR workspace`: use for project-specific branching, packaging, testing, repo-update, campaign, documentation, and workflow preferences.
- `both`: use when the preference clearly affects both DCOIR work and broader chat behavior.
- `general chat`: preserve in Airtable for continuity, but do not automatically elevate it into project-governed GitHub files unless it materially affects DCOIR behavior too.

## Recommended sync behavior
- Keep Airtable as the faster durable capture surface.
- Keep GitHub as the promoted readable policy surface.
- After GitHub promotion, keep the Airtable row and record the promotion note in `notes` instead of deleting the row.
