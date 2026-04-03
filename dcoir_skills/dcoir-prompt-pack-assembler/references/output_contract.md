# Output Contract

## Successful run
A successful run must emit:
- `dcoir_combined_master_prompt_draft.txt`
- `dcoir_prompt_pack_assembly_report.txt`

## Draft expectations
The combined draft should:
- declare itself as generated
- state that the modular prompt-pack files remain the source of truth
- list the included source files in order
- include the full source text of each module in canonical order

## Report expectations
The short assembly report should include:
- success or failure status
- stop reason when failed
- current modular prompt-pack files discovered
- ignored approved non-modular prompt-pack entries
- canonical module order used or expected
- exact output paths when successful

## Failure behavior
When the run fails, do not emit a partial combined draft.
A failed run may still emit the short report so the operator can see why the build stopped.
