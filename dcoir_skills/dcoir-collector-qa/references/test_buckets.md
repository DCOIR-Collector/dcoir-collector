# Collector QA test buckets

Use this four-bucket model for every collector QA run.

## 1. Static source checks
Validate the current readable source set before claiming anything about runtime behavior.

Minimum checks:
- current authoritative filenames match the control plane
- runtime alias rules still map readable sources to emitted runtime filenames
- current harness source still points to the expected runtime collector filename
- output-contract markers still exist in the collector source
- known maintenance command blocks still match current sources

## 2. Harness execution checks
Run representative harness lanes only when the environment actually supports them.

Suggested lanes:
- `Core`
- `Retrieval`
- `QuickAliases`
- `FullRegression`

If in-chat execution is not possible, emit exact local instructions instead of guessing.

## 3. Workflow and output-contract checks
Validate the semantics of emitted guidance, not just exit codes.

Important fields to verify when present:
- `STATUS`
- `RUN_ID`
- `SESSION_STATUS`
- `NEXT_GET_FILE`
- `NEXT_OPTIONS`
- `CLEANUP_COMMAND`
- `DELETE_SCRIPT_COMMAND`
- `NEXT_QUICK_COMMANDS`

## 4. Regression replay lanes
Always preserve the known-failure line.

For this skill, the default required preserved lane is:
- Gemini collector transcript execution error for `DCOIR_Collector.ps1`

If the exact failing excerpt is not yet recovered, keep the lane as a placeholder and explicitly say so.
