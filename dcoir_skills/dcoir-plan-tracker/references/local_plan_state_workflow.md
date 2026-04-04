# DCOIR Plan Tracker Local Plan-State Workflow

## Purpose
Use a real local `plan_state.json` file as the machine-readable working mirror for a local plan folder when deterministic local plan rendering or pre-GitHub review is needed.

## Per-plan local file
- `PLAN-YYYYMMDD-short-slug/plan_state.json`

## Primary scripts
- `scripts/ensure_plan_state.py`
- `scripts/init_plan.py`
- `scripts/add_task.py`
- `scripts/update_plan_state.py`

## Core commands
At the beginning of each new session that uses a local plan folder, run the local plan-state preflight first:
```bash
python scripts/ensure_plan_state.py /path/to/PLAN-YYYYMMDD-short-slug
```

Initialize a brand-new local plan folder when none exists yet:
```bash
python scripts/init_plan.py --slug example-slug --title "Example title" --objective "Example objective" --output-root /mnt/data/dcoir_plan_tracker
```

## Presence and absence rules
- `ensure_plan_state.py` is the required first substantive local-state command at the beginning of each new session that uses a local plan folder.
- When `plan_state.json` already exists, the preflight must report that the file is present and inspectable.
- When a brand-new local plan folder is being created, `init_plan.py` should say plainly that a new local plan-state file was initialized.
- If a plan folder is expected to exist but `plan_state.json` is missing, do not silently pretend continuity remained file-backed.
- A missing `plan_state.json` for an existing local plan folder must produce an explicit absence warning before other local plan mutations continue.

## Inspection output requirements
A valid local plan-state presence report should surface:
- absolute path
- filename
- file size in bytes
- modified time
- sha256 checksum
- plan id when known
- active task id when known
- task count when known

## Truth rules
- Do not claim a real local `plan_state.json` file exists until the preflight proves it.
- Do not treat a newly initialized local plan-state file as evidence that an earlier missing interval remained file-backed.
- Do not silently continue local plan mutations when a pre-existing plan folder is missing its `plan_state.json` file.
