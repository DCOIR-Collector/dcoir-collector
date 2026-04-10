# DCOIR Plan Tracker Local Plan-State Cache Workflow

## Purpose
Use a real local `plan_state.json` file only as a transient cache, export surface, or render mirror for Airtable-first durable plan state.

## Per-plan local cache file
- `PLAN-YYYYMMDD-short-slug/plan_state.json`

## Primary scripts
- `scripts/ensure_plan_state.py`
- `scripts/init_plan.py`
- `scripts/add_task.py`
- `scripts/update_plan_state.py`

## Core commands
At the beginning of each new session that uses a local plan cache, run the local plan-state preflight only after Airtable-backed durable state is understood:
```bash
python scripts/ensure_plan_state.py /path/to/PLAN-YYYYMMDD-short-slug
```

Initialize a brand-new local plan cache folder when none exists yet and deterministic local rendering is needed:
```bash
python scripts/init_plan.py --slug example-slug --title "Example title" --objective "Example objective" --output-root /mnt/data/dcoir_plan_tracker
```

## Presence and absence rules
- Airtable is the primary durable execution-state surface for this skill.
- `ensure_plan_state.py` is the cache-proof step for local plan folders, not the source of durable truth.
- When `plan_state.json` already exists, the preflight should report that the cache file is present and inspectable.
- When a brand-new local plan cache is being created, `init_plan.py` should say plainly that a new local cache file was initialized.
- If a local plan cache is expected but `plan_state.json` is missing, surface that explicitly, but distinguish cache absence from durable-state loss when Airtable remains current.
- Do not block Airtable-first plan capture only because a local cache is absent.

## Inspection output requirements
A valid local plan-cache presence report should surface:
- absolute path
- filename
- file size in bytes
- modified time
- sha256 checksum
- plan id when known
- active task id when known
- task count when known

## Truth rules
- Do not claim a real local `plan_state.json` cache exists until the preflight proves it.
- Do not treat a newly initialized local cache file as evidence that an earlier missing interval remained file-backed.
- Do not silently continue by pretending local continuity survived when a cache was missing; say so plainly while still using Airtable as the durable state source.
