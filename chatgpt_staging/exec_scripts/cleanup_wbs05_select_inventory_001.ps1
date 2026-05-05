$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$RunId = 'exec-20260505-wbs05-select-inventory-001'
$NowUtc = (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')
$RepoRoot = if ($env:GITHUB_WORKSPACE) { $env:GITHUB_WORKSPACE } else { (Get-Location).Path }
$DownloadsDir = [Environment]::GetEnvironmentVariable('DCOIR_DOWNLOADS_DIR','Machine')
if ([string]::IsNullOrWhiteSpace($DownloadsDir)) { $DownloadsDir = Join-Path $RepoRoot 'chatgpt_staging/tmp_exec_outputs' }
$OutDir = Join-Path $DownloadsDir $RunId
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null
$JsonPath = Join-Path $OutDir 'wbs05_select_inventory.json'
$MdPath = Join-Path $OutDir 'wbs05_select_inventory.md'
function EnvReq([string]$Name){$v=[Environment]::GetEnvironmentVariable($Name,'Process');if([string]::IsNullOrWhiteSpace($v)){$v=[Environment]::GetEnvironmentVariable($Name,'User')};if([string]::IsNullOrWhiteSpace($v)){$v=[Environment]::GetEnvironmentVariable($Name,'Machine')};if([string]::IsNullOrWhiteSpace($v)){throw "Missing $Name"};return $v}
$BaseId=EnvReq 'DCOIR_AIRTABLE_BASE_ID';$Token=EnvReq 'DCOIR_AIRTABLE_TOKEN';$Headers=@{Authorization="Bearer $Token";'Content-Type'='application/json'}
function At([string]$Method,[string]$Uri,[object]$Body=$null){if($null -eq $Body){return Invoke-RestMethod -Method $Method -Uri $Uri -Headers $Headers};return Invoke-RestMethod -Method $Method -Uri $Uri -Headers $Headers -Body ($Body|ConvertTo-Json -Depth 30)}
function Patch([string]$TableId,[string]$RecordId,[hashtable]$Fields){$uri='https://api.airtable.com/v0/{0}/{1}' -f $BaseId,$TableId;At PATCH $uri @{records=@(@{id=$RecordId;fields=$Fields});typecast=$true}|Out-Null}
function Find([string]$TableId,[string]$FieldName,[string]$Value){$safe=$Value.Replace("'","\\'");$enc=[uri]::EscapeDataString("{$FieldName} = '$safe'");$uri='https://api.airtable.com/v0/{0}/{1}?filterByFormula={2}&maxRecords=1' -f $BaseId,$TableId,$enc;$r=At GET $uri;if($r.records.Count -gt 0){return $r.records[0]};return $null}
function Upsert([string]$TableId,[string]$FieldName,[string]$Value,[hashtable]$Fields){$uri='https://api.airtable.com/v0/{0}/{1}' -f $BaseId,$TableId;$e=Find $TableId $FieldName $Value;if($null -eq $e){At POST $uri @{records=@(@{fields=$Fields});typecast=$true}|Out-Null}else{At PATCH $uri @{records=@(@{id=$e.id;fields=$Fields});typecast=$true}|Out-Null}}
$Schema=At GET ('https://api.airtable.com/v0/meta/bases/{0}/tables' -f $BaseId)
$Tables=@{};foreach($t in $Schema.tables){$Tables[$t.name]=$t.id}
foreach($need in @('DCOIR Cleanup WBS','Plans','Queue Control','Validation Evidence')){if(-not $Tables.ContainsKey($need)){throw "Missing table $need"}}
$Rows=@()
foreach($t in ($Schema.tables|Sort-Object name)){
 foreach($f in ($t.fields|Sort-Object name)){
  if($f.type -in @('singleSelect','multipleSelects')){
    $choices=@()
    if($null -ne $f.options -and $null -ne $f.options.choices){foreach($c in $f.options.choices){$choices += [pscustomobject]@{name=$c.name;color=$c.color}}}
    $Rows += [pscustomobject]@{table_name=$t.name;table_id=$t.id;field_name=$f.name;field_id=$f.id;field_type=$f.type;choice_count=$choices.Count;choices=$choices}
  }
 }
}
[pscustomobject]@{run_id=$RunId;observed_at_utc=$NowUtc;table_count=$Schema.tables.Count;select_field_count=$Rows.Count;select_inventory=$Rows}|ConvertTo-Json -Depth 30|Set-Content $JsonPath -Encoding UTF8
$md=@('# WBS05 select field inventory','',('Run: {0}' -f $RunId),('Select/multi-select fields: {0}' -f $Rows.Count),'')
foreach($g in ($Rows|Group-Object table_name|Sort-Object Name)){$md += ('## {0}' -f $g.Name);foreach($r in ($g.Group|Sort-Object field_name)){$md += ('- {0} [{1}] choices={2}' -f $r.field_name,$r.field_type,$r.choice_count)};$md += ''}
$md|Set-Content $MdPath -Encoding UTF8
$Evidence='WBS05-01 completed by '+$RunId+'. Inventoried '+$Rows.Count+' single-select/multi-select fields across '+$Schema.tables.Count+' tables. Artifact files: wbs05_select_inventory.json and wbs05_select_inventory.md.'
Patch $Tables['DCOIR Cleanup WBS'] 'recRXwQCCSAAwGd51' @{state='active';validation_notes='Parent WBS05 active; child taxonomy tasks are being executed in order.'}
Patch $Tables['DCOIR Cleanup WBS'] 'recaq7c5Qa6K00ehv' @{state='complete';validation_notes=$Evidence}
Patch $Tables['DCOIR Cleanup WBS'] 'recXlbXcXgHhU1oWV' @{state='active';validation_notes=('Activated by '+$RunId+' after WBS05-01 completion. Next: classify authoritative single-selects.')}
Patch $Tables['Plans'] 'recoLHyurY4OZx3K8' @{active_task_id='CLEANUP-WBS-05';active_task_title='Controlled Vocabulary and Taxonomy Design';active_plan_task_id='CLEANUP-WBS-05-02';exact_resume_goal='Resume at CLEANUP-WBS-05-02 in WBS order.';next_recommended_action='Continue with CLEANUP-WBS-05-02: Classify authoritative single-selects.';last_updated_text=$NowUtc;plan_state='active'}
Patch $Tables['Queue Control'] 'recW8cAlClYFEVhjF' @{branch_summary='Active branch: PLAN-AIRTABLE-CLEANUP-RESTRUCTURE / CLEANUP-WBS-05.';branch_decision='WBS05-01 complete; WBS05-02 active.';resume_rule='Resume cleanup plan at CLEANUP-WBS-05-02 unless live Airtable state changes.';next_revalidation_trigger='After WBS05-02 authoritative single-select classification is complete.';last_confirmed_text=$NowUtc}
Upsert $Tables['Validation Evidence'] 'evidence_key' 'EVID-CLEANUP-WBS-05-01-SELECT-INVENTORY-20260505' @{evidence_key='EVID-CLEANUP-WBS-05-01-SELECT-INVENTORY-20260505';validation_case_key='CLEANUP-WBS-05-01';work_item_key='CLEANUP-WBS-05-01';evidence_summary=$Evidence;source_locator=$RunId}
Write-Host ('[{0}] success: WBS05-01 complete; WBS05-02 active.' -f $RunId)
