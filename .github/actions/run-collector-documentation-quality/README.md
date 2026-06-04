# run-collector-documentation-quality

Reusable DCOIR GitHub Actions composite action for issue #194 workflow modularization.

## Contract

- Callers keep triggers, permissions, secrets, artifact names, and report paths visible in the entry or reusable workflow.
- This action owns repeated mechanical documentation-quality step logic only.
- The action assembles `project_sources/collector/harness/run_DCOIR_Tests.generated.ps1` from checked-in harness parts before running the documentation audit, so clean-checkout callers retain harness documentation coverage.
- The action must not directly reference `secrets.*` or mutate repository content.
- Compensating evidence is provided by caller-visible step names, explicit inputs, assembler output, stdout markers, generated files, uploaded artifacts, or the caller workflow report section.

## Maintenance

Change this module when the shared mechanic changes, then run the workflow maintenance audit and applicable caller workflows.
