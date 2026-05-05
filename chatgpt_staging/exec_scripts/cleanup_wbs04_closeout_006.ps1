$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$RunId = 'exec-20260505-wbs04-closeout-006'
$NowUtc = (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')
$RepoRoot = if ($env:GITHUB_WORKSPACE) { $env:GITHUB_WORKSPACE } else { (Get-Location).Path }
$DownloadsDir = [Environment]::GetEnvironmentVariable('DCOIR_DOWNLOADS_DIR','Machine')
if ([string]::IsNullOrWhiteSpace($DownloadsDir)) { $DownloadsDir = Join-Path $RepoRoot 'chatgpt_staging/tmp_exec_outputs' }
$OutDir = Join-Path $DownloadsDir $RunId
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null
$JsonPath = Join-Path $OutDir 'wbs04_closeout.json'
$MdPath = Join-Path $OutDir 'wbs04_closeout.md'
function EnvReq([string]$Name){$v=[Environment]::GetEnvironmentVariable($Name,'Process');if([string]::IsNullOrWhiteSpace($v)){$v=[Environment]::GetEnvironmentVariable($Name,'User')};if([string]::IsNullOrWhiteSpace($v)){$v=[Environment]::GetEnvironmentVariable($Name,'Machine')};if([string]::IsNullOrWhiteSpace($v)){throw "Missing $Name"};return $v}
$BaseId=EnvReq 'DCOIR_AIRTABLE_BASE_ID';$Token=EnvReq 'DCOIR_AIRTABLE_TOKEN';$Headers=@{Authorization="Bearer $Token";'Content-Type'='application/json'}
function At([string]$Method,[string]$Uri,[object]$Body=$null){if($null -eq $Body){return Invoke-RestMethod -Method $Method -Uri $Uri -Headers $Headers};return Invoke-RestMethod -Method $Method -Uri $Uri -Headers $Headers -Body ($Body|ConvertTo-Json -Depth 30)}
function Patch([string]$TableId,[string]$RecordId,[hashtable]$Fields){$uri='https://api.airtable.com/v0/{0}/{1}' -f $BaseId,$TableId;At PATCH $uri @{records=@(@{id=$RecordId;fields=$Fields});typecast=$true}|Out-Null}
function Find([string]$TableId,[string]$FieldName,[string]$Value){$safe=$Value.Replace("'","\\'");$enc=[uri]::EscapeDataString("{$FieldName} = '$safe'");$uri='https://api.airtable.com/v0/{0}/{1}?filterByFormula={2}&maxRecords=1' -f $BaseId,$TableId,$enc;$r=At GET $uri;if($r.records.Count -gt 0){return $r.records[0]};return $null}
function Upsert([string]$TableId,[string]$FieldName,[string]$Value,[hashtable]$Fields){$uri='https://api.airtable.com/v0/{0}/{1}' -f $BaseId,$TableId;$e=Find $TableId $FieldName $Value;if($null -eq $e){At POST $uri @{records=@(@{fields=$Fields});typecast=$true}|Out-Null}else{At PATCH $uri @{records=@(@{id=$e.id;fields=$Fields});typecast=$true}|Out-Null}}
$Schema=At GET ('https://api.airtable.com/v0/meta/bases/{0}/tables' -f $BaseId)
$Tables=@{};foreach($t in $Schema.tables){$Tables[$t.name]=$t.id}
foreach($need in @('DCOIR Cleanup WBS','Plans','Queue Control','Validation Evidence','Session Checkpoints')){if(-not $Tables.ContainsKey($need)){throw "Missing table $need"}}
$Children=@(
  @{key='CLEANUP-WBS-04-01';title='List ID-related fields';status='complete';evidence='45 ID/key/signature-like fields across 21 tables'},
  @{key='CLEANUP-WBS-04-02';title='Define table-specific ID components';status='complete';evidence='table-specific identity components carried into slug source design'},
  @{key='CLEANUP-WBS-04-03';title='Define canonical slug sources';status='complete';evidence='canonical slug sources for 21 tables'},
  @{key='CLEANUP-WBS-04-04';title='Define uniqueness suffix options';status='complete';evidence='suffix strategies and collision notes for 21 tables'},
  @{key='CLEANUP-WBS-04-05';title='Define dedupe signatures';status='complete';evidence='dedupe signature proposals for 21 tables'}
)
$Closeout='WBS04 closed by '+$RunId+'. ID and dedupe recommendations are ready: inventory, table-specific ID components, slug sources, uniqueness suffixes, and dedupe signatures completed with evidence. No schema changes or merges were performed.'
[pscustomobject]@{run_id=$RunId;observed_at_utc=$NowUtc;wbs='CLEANUP-WBS-04';state='complete';children=$Children;next='CLEANUP-WBS-05'}|ConvertTo-Json -Depth 10|Set-Content $JsonPath -Encoding UTF8
@('# WBS04 closeout','',('Run: {0}' -f $RunId),'', $Closeout,'','Next: CLEANUP-WBS-05 Controlled Vocabulary and Taxonomy Design / CLEANUP-WBS-05-01 Inventory select fields.')|Set-Content $MdPath -Encoding UTF8
Patch $Tables['DCOIR Cleanup WBS'] 'recXK5TmBzuRhYEJ3' @{state='complete';validation_notes=$Closeout}
Patch $Tables['DCOIR Cleanup WBS'] 'recDtAA48oO71h9xd' @{state='complete';validation_notes=$Closeout}
Patch $Tables['DCOIR Cleanup WBS'] 'recRXwQCCSAAwGd51' @{state='active';validation_notes=('Activated by '+$RunId+' after WBS04 closeout. Begin controlled vocabulary/taxonomy design.')}
Patch $Tables['DCOIR Cleanup WBS'] 'recaq7c5Qa6K00ehv' @{state='active';validation_notes=('Activated by '+$RunId+'. Next: inventory select fields and options from live Airtable schema.')}
Patch $Tables['Plans'] 'recoLHyurY4OZx3K8' @{active_task_id='CLEANUP-WBS-05';active_task_title='Controlled Vocabulary and Taxonomy Design';active_plan_task_id='CLEANUP-WBS-05-01';exact_resume_goal='Resume at CLEANUP-WBS-05-01 in WBS order. WBS04 is complete.';next_recommended_action='Continue with CLEANUP-WBS-05-01: Inventory select fields.';last_updated_text=$NowUtc;plan_state='active'}
Patch $Tables['Queue Control'] 'recW8cAlClYFEVhjF' @{branch_summary='Active branch: PLAN-AIRTABLE-CLEANUP-RESTRUCTURE / CLEANUP-WBS-05 Controlled Vocabulary and Taxonomy Design.';branch_decision='WBS04 closed; WBS05 activated in WBS order.';resume_rule='Resume cleanup plan at CLEANUP-WBS-05-01 unless live Airtable state changes.';next_revalidation_trigger='After WBS05-01 select-field inventory is complete.';last_confirmed_text=$NowUtc}
Upsert $Tables['Validation Evidence'] 'evidence_key' 'EVID-CLEANUP-WBS-04-CLOSEOUT-20260505' @{evidence_key='EVID-CLEANUP-WBS-04-CLOSEOUT-20260505';validation_case_key='CLEANUP-WBS-04-06';work_item_key='CLEANUP-WBS-04';evidence_summary=$Closeout;source_locator=$RunId}
Upsert $Tables['Session Checkpoints'] 'checkpoint_id' 'CHK-DCOIR-AIRTABLE-CLEANUP-WBS04-CLOSEOUT-20260505' @{checkpoint_id='CHK-DCOIR-AIRTABLE-CLEANUP-WBS04-CLOSEOUT-20260505';session_id='DCOIR-AIRTABLE-CLEANUP-EXECUTION-20260505';state_summary='WBS04 complete; WBS05 active.';current_focus='CLEANUP-WBS-05-01 Inventory select fields';decisions_constraints='Continue chatgpt-exec-first with workflow polling; no status-only chat stops.';next_recommended_move='Run/select-field inventory for WBS05-01.';resume_prompt='Resume PLAN-AIRTABLE-CLEANUP-RESTRUCTURE at CLEANUP-WBS-05-01.';checkpoint_at=$NowUtc;trigger='milestone';checkpoint_status='active'}
Write-Host ('[{0}] success: WBS04 closed; WBS05-01 active.' -f $RunId)
