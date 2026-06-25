# run-duplicate-function-check

Reusable DCOIR GitHub Actions composite action for cross-file duplicate PowerShell function definition detection in collector source.

## Contract

- Callers keep triggers, permissions, artifact names, retention, and workflow claims visible in the entry or reusable workflow.
- This action owns the repeated mechanical step for parsing all collector PS1 source files with the PowerShell AST and detecting function names defined in more than one file.
- The action fails the step when duplicate function definitions are found (`fail-on-duplicates` input, default `true`), printing each duplicate name, the files that define it, and the load-order winner.
- The action must not upload artifacts, enable code scanning, generate SARIF, use `pull_request_target`, reference `secrets.*`, or mutate repository history.
- Compensating evidence is provided by caller-visible step names, explicit inputs, stdout duplicate report listing file paths and line numbers, and the caller workflow conclusion.

## Maintenance

Change this module when the collector source discovery logic or duplicate detection AST traversal changes, then run local validation and applicable workflow readback.
