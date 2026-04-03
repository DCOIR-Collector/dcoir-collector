# Classification rules

## Purpose
Use these rules to decide where a captured item belongs.

## Buckets

### session_only
Use for reminders, short-term sequencing notes, and current-chat scratch items that do not yet justify governed promotion.

### candidate_log01
Use for future work, queued tasks, deferred patches, or explicit "we still need to do X" items that should likely land in `LOG-01_DCOIR_Todo_Log.txt` if approved.

### candidate_log02
Use for lessons learned, regression findings, design conclusions, or workflow mistakes that should likely land in `LOG-02_DCOIR_Lessons_Learned_Log.txt` if approved.

### candidate_log03
Use for handoff notes that a future worker would need to resume the exact branch cleanly. These usually include current phase, exact stop point, preserved concerns, or next move context.

### durable_preference_candidate
Use for operator statements that sound like a lasting default, especially:
- packaging rules
- bundle naming rules
- delivery friction rules
- validation posture
- documentation depth preferences
- workflow sequencing defaults

### new_skill_idea
Use for proposals to build a new helper skill or materially widen an existing skill.

### follow_on_validation
Use for explicit future testing, QA, V&V, regression, or clean-room revalidation tasks.

### blocked_or_needs_authority
Use when the item cannot safely proceed without control-plane clarification, file refresh, or operator choice.

## Tie-breakers
- If the item is both a task and a durable rule, create two linked entries: one in `durable_preference_candidate` and one in the most relevant task bucket.
- If the item is a new skill idea with explicit testing expectations, create both a `new_skill_idea` entry and a `follow_on_validation` entry.
- If the item is only preserved so it is not forgotten during the current phase, keep it session-local until the operator asks for promotion.
