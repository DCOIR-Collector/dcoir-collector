# run-collector-runtime-package-validation

Reusable DCOIR GitHub Actions composite action for issue #209 collector runtime package validation.

## Contract

- Callers keep triggers, permissions, secrets, artifact names, and report paths visible in the entry or reusable workflow.
- This action owns repeated mechanical runtime package validation step logic only.
- The action runs `project_sources/collector/tools/validate_dcoir_collector_runtime_package.py` against the checked-out repository and writes validation artifacts to the caller-provided output directory.
- The action must not directly reference `secrets.*` or mutate repository content.
- Compensating evidence is provided by caller-visible step names, explicit inputs, validator stdout, generated validation files, uploaded artifacts, or the caller workflow report section.

## Maintenance

Change this module when the shared collector runtime package validation mechanic changes, then run the workflow maintenance audit and applicable caller workflows.
