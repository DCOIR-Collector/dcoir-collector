# GitHub workflow authority pointer

This folder holds repo-native GitHub workflow support surfaces.

Current authority model:

- The workflow YAML body is the executable source of truth.
- The top comment block in each `.github/workflows/*.yml` file owns workflow-specific execution guidance.
- GitHub is canonical for workflow and source truth.
- Supabase `ircore` is the operational routing, validation, lessons, and active-state surface.
- Legacy Airtable may still exist for migration or historical lookup, but it is not the active default workflow-routing authority.

## Workflow modularization contract

Issue #194 governs the repo-wide GitHub Actions restructuring into deliberate entry workflows, reusable workflows, composite actions, repo-local scripts, and audited contracts.

The foundation surfaces are:

- `workflow_modularization_contracts.json`: the issue #194 contract registry for all existing workflow files, required contract families, migration status, rollback notes, and acceptance evidence.
- `workflow_inventory.json`: generated machine-readable inventory for the current workflow surface.
- `workflow_inventory.md`: generated readable contract matrix for operators and reviewers.
- `tools/build_workflow_inventory.py`: regenerates the JSON and Markdown inventory; use `--check` in CI to fail on stale generated outputs.
- `tools/check_workflow_modularization_contracts.py`: validates that every workflow has a contract entry, required contract families are mapped, reusable workflows avoid generic catch-all posture, composite actions expose compensating evidence, and inventory fields match the registry.

Regenerate the inventory after any workflow, reusable workflow, composite action, report, artifact, or workflow-tooling change:

```bash
python project_sources/github_actions/tools/build_workflow_inventory.py
python project_sources/github_actions/tools/build_workflow_inventory.py --check
python project_sources/github_actions/tools/check_workflow_modularization_contracts.py
```

Entry workflows must keep operator-visible contract surfaces visible: workflow name, triggers, path filters, schedules, dispatch inputs, permissions, concurrency, secret names, artifact names, report path shapes, and central-reporter compatibility. Reusable workflows should be family-specific contract surfaces, composite actions should be mechanical step bundles only, and complex safety/reporting logic should remain script-backed and testable.

This foundation slice introduces non-calling `.github/actions` composite action
scaffolds for repeated mechanical step bundles. Existing workflows do not call
those actions yet. Add callers and any `.github/workflows/reusable-*` workflow
files only in a later behavior-migration slice with explicit input, output,
permission, secret, shell, runner, artifact, report, and readback contracts.

`tools/generate_workflow_inventory.py` is a compatibility wrapper for
`tools/build_workflow_inventory.py`; both names use the same canonical inventory
format.

Recommended local validation after workflow-tooling changes:

```bash
python3 project_sources/github_actions/tools/build_workflow_inventory.py --check
python3 project_sources/github_actions/tools/check_workflow_modularization_contracts.py
python3 project_sources/github_actions/tools/audit_reusable_contracts.py
python3 project_sources/github_actions/tools/check_workflow_consistency_drift.py
python3 project_sources/github_actions/tools/check_workflow_action_versions.py
```
