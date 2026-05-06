$ErrorActionPreference = 'Stop'
$runId = 'exec-20260506-session-closeout-001'
$now = (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')
$base = [Environment]::GetEnvironmentVariable('DCOIR_AIRTABLE_BASE_ID','Machine')
$token = [Environment]::GetEnvironmentVariable('DCOIR_AIRTABLE_TOKEN','Machine')
if ([string]::IsNullOrWhiteSpace($base)) { throw 'missing DCOIR_AIRTABLE_BASE_ID' }
if ([string]::IsNullOrWhiteSpace($token)) { throw 'missing DCOIR_AIRTABLE_TOKEN' }
$headers = @{ Authorization = "Bearer $token"; 'Content-Type' = 'application/json' }
function At($method, $uri, $body = $null) {
  if ($null -eq $body) { return Invoke-RestMethod -Method $method -Uri $uri -Headers $headers }
  return Invoke-RestMethod -Method $method -Uri $uri -Headers $headers -Body ($body | ConvertTo-Json -Depth 40)
}
$schema = At GET "https://api.airtable.com/v0/meta/bases/$base/tables"
function Tid($name) { foreach ($t in $schema.tables) { if ($t.name -eq $name) { return [string]$t.id } }; throw "missing table $name" }
function FindOne($tableId, $field, $value) {
  $safe = $value.Replace("'", "\\'")
  $formula = [uri]::EscapeDataString("{$field} = '$safe'")
  $r = At GET "https://api.airtable.com/v0/$base/$tableId?filterByFormula=$formula&maxRecords=1"
  if ($r.records.Count -gt 0) { return $r.records[0] }
  return $null
}
function Upsert($tableId, $keyField, $keyValue, $fields) {
  $uri = "https://api.airtable.com/v0/$base/$tableId"
  $existing = FindOne $tableId $keyField $keyValue
  if ($null -eq $existing) { At POST $uri @{ records = @(@{ fields = $fields }); typecast = $true } | Out-Null; return 'created' }
  At PATCH $uri @{ records = @(@{ id = $existing.id; fields = $fields }); typecast = $true } | Out-Null
  return 'updated'
}
$chk = Tid 'Session Checkpoints'
$pref = Tid 'Operator Preferences'
$evid = Tid 'Validation Evidence'
$checkpointId = 'CHK-DCOIR-AIRTABLE-CLEANUP-CLOSEOUT-20260506-CHATGPT-EXEC-TOOLPATH-WBS09'
$state = 'Session closed correctly through Airtable-backed checkpoint. Active cleanup branch should resume at WBS08-01. WBS09 is planned scope for existing data standardization/migration after enforcement assurance gates.'
$constraints = 'Use Airtable connector for normal admin actions; use chatgpt-exec or GitHub workflows for bulk Airtable ETL/mass writes. Do not classify connector/workflow errors as safety until request shape, stale SHA, paths, JSON, field names, typos, script syntax, and logs are checked. Do not use manual download/Desktop bundle. Do not mark WBS tasks complete without evidence.'
$resume = 'Resume AFRICOM_SOC_IR / DCOIR at PLAN-AIRTABLE-CLEANUP-RESTRUCTURE. Re-anchor Airtable-first, read CONTROL-STARTUP-AIRTABLE-FIRST, Queue Control, active Plans, Operator Preferences, Session Checkpoints, and GitHub closeout note chatgpt_staging/notes/session_closeout_20260506_chatgpt_exec_toolpath_wbs09.md. First finish idiot-proofing chatgpt-exec operator_tools execution across PowerShell/Python/future tools using GitHub connector or chatgpt-apply-in, then return to active Airtable cleanup at WBS08-01. WBS09 planned data-standardization scope must be verified/inserted as needed. Use Gmail notifications from notifications@github.com as workflow failure signal.'
Upsert $chk 'checkpoint_id' $checkpointId @{ checkpoint_id = $checkpointId; session_id = 'DCOIR-AIRTABLE-CLEANUP-EXECUTION-20260506'; state_summary = $state; current_focus = 'Closeout complete; next session starts with chatgpt-exec tool_path hardening, then WBS08-01.'; decisions_constraints = $constraints; next_recommended_move = 'Verify and patch chatgpt-exec tool_path/multi-language operator_tools support, then resume WBS08-01 enforcement assurance with evidence gates.'; resume_prompt = $resume; checkpoint_at = $now; trigger = 'closeout'; checkpoint_status = 'active' } | Out-Null
Upsert $pref 'preference_key' 'PREF-DCOIR-AIRTABLE-CONNECTOR-ADMIN-WORKFLOW-SPLIT' @{ preference_key = 'PREF-DCOIR-AIRTABLE-CONNECTOR-ADMIN-WORKFLOW-SPLIT'; preference_statement = 'Use Airtable connector for regular DCOIR admin actions; use chatgpt-exec or GitHub workflows for bulk Airtable mutations and ETL.'; effective_behavior = 'For checkpoint rows, preferences, plan/queue notes, small status updates, and verification readbacks, use the Airtable connector when available. For massive jobs, bulk inserts/updates, destructive campaigns, and existing-data standardization, use chatgpt-exec or governed GitHub workflow lanes to avoid repeated per-record approvals.'; source_session_id = 'DCOIR-AIRTABLE-CLEANUP-EXECUTION-20260506'; last_confirmed_text = $now; notes = 'Captured at session closeout after operator clarified Airtable connector is not off the table; only massive Airtable jobs should avoid repeated connector approvals.'; status = 'active'; scope = 'workflow' } | Out-Null
Upsert $pref 'preference_key' 'PREF-DCOIR-CHATGPT-EXEC-OPERATOR-TOOLS-MULTILANGUAGE' @{ preference_key = 'PREF-DCOIR-CHATGPT-EXEC-OPERATOR-TOOLS-MULTILANGUAGE'; preference_statement = 'chatgpt-exec hardening must support operator_tools execution across PowerShell, Python, current tools, and plausible future tool languages.'; effective_behavior = 'When adding tool_path or similar execution support, preserve inline command compatibility, keep script_path compatibility, allow governed operator_tools paths, support .ps1 and .py now, design the allowlist to extend to future executable tool types, and validate with workflow report plus readback before operational use.'; source_session_id = 'DCOIR-AIRTABLE-CLEANUP-EXECUTION-20260506'; last_confirmed_text = $now; notes = 'Captured from operator correction before closeout.'; status = 'active'; scope = 'workflow' } | Out-Null
Upsert $evid 'evidence_key' 'EVID-DCOIR-SESSION-CLOSEOUT-20260506-CHATGPT-EXEC-WBS09' @{ evidence_key = 'EVID-DCOIR-SESSION-CLOSEOUT-20260506-CHATGPT-EXEC-WBS09'; validation_case_key = 'DCOIR-SESSION-CLOSEOUT'; work_item_key = 'PLAN-AIRTABLE-CLEANUP-RESTRUCTURE'; evidence_summary = 'Airtable closeout checkpoint and durable preferences written by chatgpt-exec because the direct Airtable connector resource was unavailable in-session. Resume from checkpoint CHK-DCOIR-AIRTABLE-CLEANUP-CLOSEOUT-20260506-CHATGPT-EXEC-TOOLPATH-WBS09.'; source_locator = $runId; result = 'pass' } | Out-Null
Write-Host "closeout checkpoint written: $checkpointId"
