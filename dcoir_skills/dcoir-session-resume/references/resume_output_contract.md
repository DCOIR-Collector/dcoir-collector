# Resume Output Contract

Use this file when the skill needs exact formatting guidance or needs to choose the best ready follow-up prompts.

## Fixed section order
Always return sections in this order:
1. Current stable baseline
2. Current governed GitHub readable sources
3. Current supporting GitHub assets
4. Current governance/control-plane state
5. Current validated status
6. Current next planned work item
7. Refresh watchlist
8. Recommended next move
9. Ready follow-up prompts

## Compact default form
For ordinary startup or resume-status replies:
- use the fixed section order, but keep each section to one short sentence or bullet unless a conflict or blocker genuinely needs more detail
- prefer short bold labels or other compact formatting over large markdown headers when the operator did not ask for a formal report
- keep the whole resume output compact and plain English by default
- do not display Airtable UI during re-anchor unless the operator asked for it or the visual surface materially changes understanding
- do not dump raw Airtable field names, internal state labels, or long file inventories into the operator-facing summary

## Section intent
### Current stable baseline
Name the current stable collector, current GitHub-readable harness sources, and current modular prompt-pack or AI-workflow sources only when those details are materially useful to the current branch.

### Current governed GitHub readable sources
Summarize the current governed GitHub readable source set from the manifest in one short line unless the operator explicitly asked for a deeper file inventory.

### Current supporting GitHub assets
List supporting assets separately from authoritative readable source files, but keep this section brief. If nothing materially changed, say so plainly.

### Current governance/control-plane state
State that the default control plane is workspace instructions plus current manifest plus current change log. State that GitHub is the sole readable working source and Airtable is the live queue authority.

### Current validated status
Give a concise summary of the latest validated or promoted state from the current authoritative files.

### Current next planned work item
Report the live next planned item from Airtable queue state when it exists, not from retired GitHub todo surfaces.

### Refresh watchlist
Say whether any dependent artifacts likely need refresh before the next promotion. Keep it to one short line when the watchlist is quiet.

### Recommended next move
Give one best next action only.

### Ready follow-up prompts
Give 2 short prompts by default. Use 3 to 4 only when the operator explicitly wants options or the branch truly needs them.

If the operator has already given a direct next-step instruction, keep this section minimal or say that no extra follow-up prompt set is needed.

## Prompt-selection rules
- Always include one prompt to continue the next planned work item when prompts are useful.
- Include packaging prompts only when relevant.
- When the current workflow favors batched manual updates or batched skill-install waves, prefer grouped follow-up prompts over one-skill-at-a-time prompts.
- Do not exceed 4 prompts.
- Keep prompts plain-language and state-aware.
- Do not emit internal tool syntax.
