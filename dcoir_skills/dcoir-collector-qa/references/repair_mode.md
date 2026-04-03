# Repair mode

Use repair mode only when the user explicitly asks for code fixes, documentation refresh, or a validated patch.

## Required inputs
- current authoritative collector and harness sources
- current audit result
- known failing lane or bounded defect statement
- any environment limits that affect execution

## Repair loop
1. restate the bounded defect and the exact changed targets
2. identify whether the change is code, documentation, or both
3. generate a repair plan before claiming the patch is safe
4. apply the smallest change that addresses the defect
5. refresh maintenance code blocks and any targeted in-code documentation affected by the change
6. rerun the motivating failure lane
7. rerun at least one known-good control lane
8. emit the updated report with exact changed files, exact validation lanes, and any remaining unresolved gaps

## Documentation-refresh rules
- add file-level comment-based help when a primary entry point lacks it and that absence materially hurts maintenance
- add function-level help for externally-invoked, output-contract-critical, or high-friction functions
- prefer terse, durable wording over verbose narrative comments
- never leave documentation describing stale runtime filenames, stale harness commands, or stale output markers

## Stop conditions
- stop if the defect cannot be reproduced or bounded well enough to patch safely
- stop if the required changed set would exceed the requested scope without explicit approval
- stop if validation evidence is missing after the patch
- stop if code or documentation drift remains unresolved in the exact area that was changed
