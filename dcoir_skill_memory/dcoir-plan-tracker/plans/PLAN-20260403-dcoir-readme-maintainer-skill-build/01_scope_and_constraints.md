# Scope And Constraints

Objective
- Build a dedicated `dcoir-readme-maintainer` helper skill for root and folder README maintenance after confirming the need is still grounded in the current DCOIR working line.

Authority basis
- Project Instructions
- `project_sources/CP-01_DCOIR_Version_Manifest.txt`
- `project_sources/CP-02_DCOIR_Change_Log.txt`
- `project_sources/todo/03_Documentation_And_Knowledge_Lane.txt`
- `project_sources/LOG-03_DCOIR_Session_Handoff_Brief.txt`

In scope
- validate that the README-maintainer need is still current
- define the skill boundary for root README, folder README, navigation guidance, and cross-link upkeep
- draft the skill specification and then package-ready contents

Out of scope for this plan phase
- broad README rewrites across the repo before the skill exists
- broad documentation architecture work not directly needed for the README-maintainer skill
- source-hosting rollout for all `dcoir-*` skills

Constraints
- GitHub remains the durable readable source of truth
- current tracker writes should preserve continuity-rich markdown plus machine-readable state
- user-visible milestone signaling should remain concise
- grouped GitHub transactions are preferred when safe and fully supported by the connector lane

Stop conditions
- authority conflict between current control-plane files
- README-maintainer need no longer appears in current governed docs or handoff surfaces
- GitHub write lane becomes unsafe for tracker continuity updates
