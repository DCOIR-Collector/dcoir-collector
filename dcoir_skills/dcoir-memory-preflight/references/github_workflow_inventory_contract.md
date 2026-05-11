# GitHub Workflow Inventory Contract

Purpose: define how DCOIR helper skills use Airtable table `GitHub Workflow Inventory` as the routing registry for GitHub Actions workflows.

## Authority boundary
- Airtable `GitHub Workflow Inventory` owns general task-routing guidance for repository workflows.
- `.github/workflows/*.yml` header comments own workflow-specific execution guidance.
- `.github/workflows/*.yml` workflow bodies remain the executable source of truth.
- Adjacent repo docs and status reports are supporting context or historical evidence, not workflow-use source of truth.

## Intended table responsibility
Use the table to answer: which workflow should a future session inspect, run, validate, or avoid for a task family?
Do not store workflow source code, secret values, run logs, full reports, payloads, or duplicated executable instructions in this table.

## Required cache posture
`dcoir-memory-preflight` is the primary cache owner for workflow-routing use. Other skills may consult the cache or live table when their task family requires workflow selection, validation, or lane decisions.

Cache only fields needed for workflow selection and safety routing:
workflow_key, workflow_name, repo_path, workflow_family, status, trigger_family, routing_owner_skill, active, use_when, do_not_use_when, dispatch_inputs_summary, trigger_summary, readback_summary, safety_notes, maintenance_notes, cache_scope, retention_class, updated_at.

Exclude secrets, logs, artifacts, payloads, report bodies, and workflow source code from the cache.

## Creation/readback requirement
Until the Airtable table exists and live schema readback provides a table id, use the table name and field names for approval-packet planning only. After creation, refresh this contract with the table id and field ids if a future strict-cache pass requires field-id pinning.

## Refresh triggers
Refresh the workflow inventory cache when:
- a DCOIR task requires selecting or validating a GitHub Actions workflow;
- workflow files or workflow headers change;
- Airtable workflow inventory rows are created or updated;
- a workflow changes trigger/input/reporting/safety behavior;
- cache is missing, stale, unreadable, or inconsistent with live schema readback.

## Validation
Before claiming workflow inventory readiness, verify:
1. live Airtable schema contains the expected table and fields;
2. all workflow rows exist for current `.github/workflows/*.yml` files;
3. workflow_key values are unique and generated as designed;
4. cache JSON excludes unsafe content and includes only routing fields;
5. changed skills can read or route from the inventory without treating it as workflow execution authority.
