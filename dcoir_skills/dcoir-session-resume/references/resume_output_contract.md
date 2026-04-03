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

## Section intent
### Current stable baseline
Name the current stable collector, current GitHub-readable harness sources, and current modular prompt-pack or AI-workflow sources when the authoritative files provide them.

### Current governed GitHub readable sources
Summarize the current governed GitHub readable source set from the manifest.

### Current supporting GitHub assets
List supporting assets separately from authoritative readable source files.

### Current governance/control-plane state
State that the default control plane is workspace instructions plus current manifest plus current change log.
State that GitHub is the sole readable working source and that GPT knowledge is bootstrap/runtime anchor only when the custom GPT model is in use.

### Current validated status
Give a concise summary of the latest validated or promoted state from the current authoritative files.

### Current next planned work item
Report the next planned item from the current authoritative files.

### Refresh watchlist
Say whether any dependent artifacts likely need refresh before the next promotion.

### Recommended next move
Give one best next action only.

### Ready follow-up prompts
Give 2 to 4 short prompts that the user can paste next.

## Prompt-selection rules
- Always include one prompt to continue the next planned work item.
- Include packaging prompts only when relevant.
- Do not exceed 4 prompts.
- Keep prompts plain-language and state-aware.
- Do not emit internal tool syntax.
