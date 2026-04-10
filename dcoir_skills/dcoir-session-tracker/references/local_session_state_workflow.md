# DCOIR Session Tracker Local Cache Workflow

## Purpose
Use a real local `session_state.json` file only as a transient cache, export surface, or render buffer for Airtable-first durable working state.

## Default local cache file
- `/mnt/data/dcoir_session_tracker/session_state.json`

## Primary scripts
- `scripts/session_state_store.py`
- `scripts/render_session_state.py`

## Core rules
- Airtable is the primary durable working-state surface for this skill.
- The local JSON file is optional and should be treated as a cache or deterministic render helper, not as the durable continuity source.
- At the beginning of each new session that uses this skill, prefer Airtable-backed resume state first.
- If code execution and file writing are available, run `scripts/session_state_store.py ensure-state` to prove whether a local cache is already present.
- A missing local cache does not, by itself, prove durable state was lost.
- If a local cache is initialized because no pre-existing file was present, surface that plainly.

## Inspection output requirements
A valid local-cache presence report should surface:
- absolute path
- filename
- file size in bytes
- modified time
- sha256 checksum
- item counts when known

## Truth rules
- Do not claim a real local `session_state.json` cache exists until inspection proves it.
- Do not treat a newly initialized local cache file as evidence that an earlier interval remained file-backed.
- Do not block Airtable-first capture only because the local cache is missing.
