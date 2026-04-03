# Import and merge rules

## Purpose
Use these rules when the operator uploads a prior exported markdown tracker artifact.

## Merge order
1. Current control plane
2. Current conversation items
3. Imported markdown session state
4. Current Project todo/handoff context when relevant

## Why this order
The imported markdown is durable session context, but it is not authoritative control-plane truth.

## Merge behavior
- Deduplicate by meaning, not only by exact text.
- Prefer the most specific recent wording.
- Preserve imported IDs if the imported item clearly matches a current item.
- Preserve provenance notes from both sides when useful.
- Do not silently reopen items marked done unless the operator explicitly reopens them or new evidence clearly does so.
- If an imported item is already promoted into current Project files, mark the session copy as resolved or promoted instead of keeping two active copies.

## Conflict behavior
If the imported artifact says something that conflicts with the current control plane:
- keep the item visible
- move it to `blocked_or_needs_authority`
- explain the conflict plainly
- do not treat the imported item as authoritative
