# setup-python-runtime

Reusable DCOIR GitHub Actions composite action for issue #194 workflow modularization.

## Contract

- Callers keep triggers, permissions, secrets, artifact names, and report paths visible in the entry or reusable workflow.
- This action owns repeated mechanical step logic only.
- Compensating evidence is provided by caller-visible step names, explicit inputs, stdout markers, generated files, uploaded artifacts, or the caller workflow report section.

## Maintenance

Change this module when the shared mechanic changes, then run the workflow maintenance audit and applicable caller workflows.
