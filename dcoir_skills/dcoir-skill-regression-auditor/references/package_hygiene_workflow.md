# Package Hygiene Workflow

## Purpose
Use this workflow to stop runtime residue such as `__pycache__/`, `*.pyc`, and `.DS_Store` from leaking into delivered DCOIR skill packages.

## Default pattern
1. Prevent bytecode creation where practical.
2. Clean the skill tree before packaging.
3. Fail the regression or packaging check if residue still remains.

## Prevention step
When running Python directly inside a skill folder, prefer one of these patterns when practical:
- `PYTHONDONTWRITEBYTECODE=1 python ...`
- `python -B ...`

This reduces repeated `__pycache__/` creation during local tests.

## Cleanup step
Run:
- `python scripts/clean_skill_runtime_residue.py --clean <skill-folder>`

This should remove at least:
- `__pycache__/`
- `*.pyc`
- `.DS_Store`

## Verification step
Run:
- `python scripts/clean_skill_runtime_residue.py --check <skill-folder>`

The check must fail if any residue remains.

## Packaging rule
Do not package or hand back an updated skill zip until the cleanup step and the post-clean verification step both succeed.

## Repo hygiene support
When the governed repo can carry ignore rules safely, keep `dcoir_skills/.gitignore` aligned so common runtime residue is not reintroduced through local working-copy noise.
