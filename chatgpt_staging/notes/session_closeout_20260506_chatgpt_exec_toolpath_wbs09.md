# DCOIR session closeout - 2026-05-06

Resume branch: PLAN-AIRTABLE-CLEANUP-RESTRUCTURE.

Current active plan lane should remain WBS08 until verified complete. WBS09 is a planned insertion for existing data standardization and migration execution after enforcement assurance gates.

Important operator preferences and corrections captured in-session:
- Prefer chatgpt-exec and governed GitHub workflow lanes over manual bundles and direct connector fallbacks.
- Do not ask operator to manually trigger proven workflows.
- Check Gmail notifications from notifications@github.com for chatgpt-exec failure notices while debugging workflow runs.
- Before blaming connector safety, inspect request shape, stale SHA, path, JSON, field names, typo/misspelling, script syntax, and workflow logs.
- Before marking any WBS task complete, verify the work was actually done against concrete evidence.
- Existing Airtable data must be transformed to new standards, not only planned or described.

Verified facts:
- chatgpt-exec workflow itself is proven and healthy.
- The harness has current script_path support for chatgpt_staging/exec_scripts/*.ps1 and has the empty CommandSanitized catch-path fix in main readback.
- The chatgpt-exec workflow YAML still triggers from chatgpt_staging/exec_requests/*.json and allows workflow_dispatch request_path.
- Current harness readback still restricts script_path to chatgpt_staging/exec_scripts/*.ps1 only. Need future hardening for tool_path and multi-language tools.

Unfinished work:
1. Finish idiot-proofing chatgpt-exec tool execution for operator_tools across languages.
   - Must account for PowerShell, Python, cmd/bat, shell, and future languages.
   - Best target: add a governed request field such as tool_path plus optional tool_args, with path allowlist for operator_tools and chatgpt_staging exec scripts.
   - Do not break existing inline command requests.
   - Keep script_path compatibility.
   - Add validation docs or preflight script so malformed requests fail with committed diagnostic report.
2. Retry the tool_path hardening patch using current SHA/readback first. Last attempt failed due stale SHA on chatgpt_staging/exec_scripts/probe_exec_write_20260506.ps1.
3. After tool-path hardening, resume real work:
   - verify WBS09 rows in Airtable;
   - complete or insert missing WBS09 children if needed;
   - keep active branch at WBS08-01 until WBS08 is actually complete with evidence;
   - resume enforcement assurance model, then data standardization WBS.

Important caution:
- Do not use a manual GitHub Desktop bundle. The operator cannot download/use one. Use GitHub connector and chatgpt-exec/chatgpt-apply-in workflows only.

Suggested new-session starter:
Resume AFRICOM_SOC_IR / DCOIR. Re-anchor Airtable-first. Read this closeout note, Queue Control, active Plans, Operator Preferences, current chatgpt-exec harness, workflow YAML, and latest Gmail chatgpt-exec failures. First finish idiot-proofing chatgpt-exec operator_tools execution across PowerShell/Python/future tools using GitHub connector or chatgpt-apply-in, then return to active Airtable cleanup plan at WBS08-01 and WBS09 planned data-standardization insertion. Do not mark tasks complete without evidence.
