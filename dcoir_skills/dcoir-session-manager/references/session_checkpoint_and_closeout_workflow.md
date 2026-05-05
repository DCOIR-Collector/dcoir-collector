# Session Checkpoint and Closeout Workflow

Purpose: restore automatic continuity behavior formerly split across `dcoir-session-resume` and `dcoir-session-tracker`. Use this workflow during DCOIR startup, resume, re-anchor, milestone capture, blocker recovery, handoff, and closeout.

## Trigger checklist
Create or prepare a Session Checkpoint when any of these occur:
- startup/resume/re-anchor establishes or changes active branch state;
- one or two bounded tasks complete;
- task, plan, lane, or source-authority branch changes;
- blocker appears, changes, or resolves;
- before GitHub writes, GitHub Desktop bundles, skill packages, or workflow execution where session state matters;
- operator says remember, capture, checkpoint, park this, carry this forward, do not forget, handoff, close out, resume later, or equivalent wording;
- starter prompt is generated for a next session;
- local/session cache state is stale, missing, reinitialized, or uncertain.

## Required checkpoint payload
Preserve enough state to resume without chat memory:
- checkpoint_id and session_id when known;
- session mode and current focus;
- active plan, active work item, queue branch, and execution lane;
- completed work and verification evidence;
- pending work and next recommended move;
- blockers, conflicts, unresolved approval gates, and assumptions;
- operator preferences/corrections learned this session;
- artifacts, packages, repo paths, Airtable rows, skills, caches, and parity surfaces changed or needing verification;
- starter prompt or resume prompt when closing/handoff.

## Write/readback rule
Prefer a live Airtable Session Checkpoint write. If Airtable writes are blocked or forbidden, emit a checkpoint-ready payload in chat and label it non-durable. After a successful write, verify by readback and refresh the local Session Checkpoints cache when file access exists.

## Closeout rule
A closeout response without either a durable Session Checkpoint or a non-durable checkpoint payload is incomplete. Do not provide only a chat summary unless the operator explicitly says not to checkpoint.
