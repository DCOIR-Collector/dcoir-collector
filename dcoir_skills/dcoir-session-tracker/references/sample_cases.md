# Sample cases

## Case 1: durable packaging preference
Input:
- "From now on when you provide me with a zip bundle, name it with the prefix YYYYMMDDTHHMMSSZ_."

Expected handling:
- capture one `durable_preference_candidate`
- normalized rule: prefix delivered zip bundles with `YYYYMMDDTHHMMSSZ_`
- if this implies a gap in `dcoir-decision-policy`, also capture a linked `candidate_log01` or `follow_on_validation` item to patch and regress that skill

## Case 2: must-not-forget Gemini guidance
Input:
- "You must capitalize on the 500,000 character limits for the description and instruction fields ..."
- "Description is used internally by ADK for automatic delegation and routing across agents"
- "The more detailed the instructions, the better the agent can understand its role and how to use its tools effectively. Be explicit about error handling if needed."

Expected handling:
- capture as a high-importance item, normally `session_only` plus `candidate_log01` if the operator wants later governed promotion
- preserve the exact wording or a tightly faithful summary
- mark it as a Gemini follow-on requirement, not as already-promoted Project truth unless it is actually promoted later

## Case 3: collector QA / V&V skill idea
Input:
- "it would be awesome if we could create a skill that would test the collector's ps1"
- operator wants QA, V&V, repeatable clean-room testing, and regression discipline

Expected handling:
- capture one `new_skill_idea`
- capture one linked `follow_on_validation` item
- tie to collector readable source, harness mirrors, and any preserved test failures

## Case 4: imported session-state markdown
Input:
- uploaded prior `YYYYMMDDTHHMMSSZ_dcoir_session_state.md`

Expected handling:
- merge rather than replace
- preserve imported provenance
- deduplicate overlapping items with current chat and Project logs
- report current open items and one best next move

## Case 5: governed push is about to happen
Input:
- "the repo batch is ready" or "I’m about to do the GitHub Desktop push"

Expected handling:
- inspect the local state file
- derive a pre-push review bundle
- surface staged governed updates and staged todo actions
- say plainly what will land in the same grouped push and what will remain local
- stage post-push cleanup so the next step after confirmation is explicit
