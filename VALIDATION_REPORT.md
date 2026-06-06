# Supercharge bundle validation report

## `$ python3 scripts/validate-codeql-security-workflow.py`

Exit code: `0`

```text
PASS: CodeQL workflow config validation completed successfully.

```

## `$ python3 project_sources/github_actions/tools/build_workflow_inventory.py --check`

Exit code: `0`

```text
Workflow inventory check passed for 31 workflow files.

```

## `$ python3 project_sources/github_actions/tools/check_workflow_action_versions.py`

Exit code: `0`

```text
Workflow action maintenance audit passed for 61 workflow files and 15 composite action files.

```

## `$ python3 project_sources/github_actions/tools/check_workflow_modularization_contracts.py`

Exit code: `0`

```text
Workflow modularization contract audit passed for 31 workflow files and 31 contracts.

```

## `$ python3 project_sources/github_actions/tools/audit_reusable_contracts.py`

Exit code: `0`

```text
Reusable/composite contract audit passed: 31 primary workflows, 30 reusable workflow definitions, 31 local reusable workflow calls, 15 local action definitions, 109 local action calls (108 from workflows, 1 from composite actions).

```
