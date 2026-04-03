# Execution modes

## Default mode: hybrid
Use a hybrid mode unless the user explicitly narrows the run.

Hybrid means:
- static analysis always happens
- repeatable local instructions are always produced
- representative checks are executed only when the current environment supports them

## Analysis-only mode
Use when execution is impossible, unsafe, or explicitly out of scope.

Required behavior:
- mark execution-dependent checks as `blocked` or `planned-not-executed`
- emit exact next local steps
- do not overstate confidence

## Local/manual execution mode
Use when the user wants a copyable operator path.

Required behavior:
- use Windows PowerShell 5.1 syntax for local test instructions
- keep command blocks copyable and current
- separate local commands from any Elastic response-action examples

## Patch-validation mode
Use after a collector or harness change.

Required behavior:
- rerun the motivating failing lane
- rerun at least one known-good control lane
- regenerate maintenance command blocks
- update the report so the changed code and changed documentation stay aligned


## Repair mode
Use when the user explicitly asks to fix collector or harness defects rather than only audit them.

Required behavior:
- define the exact changed targets before editing
- keep the patch bounded to the defect-under-test and required maintenance alignment
- refresh targeted maintenance documentation and code blocks in the same pass
- rerun the motivating failure lane and at least one known-good control lane
- report the exact changed files, validation lanes, and remaining gaps

## Maintenance-doc mode
Use when the user wants future-maintenance clarity improved even if functional behavior does not change.

Required behavior:
- prefer file-level comment-based help when absent from entry-point scripts
- add or refresh function-level help only for externally-invoked, high-friction, or output-contract-critical functions
- avoid noisy comment spam that restates obvious code
- keep code comments aligned with current runtime alias rules, emitted markers, and operator sequence expectations
