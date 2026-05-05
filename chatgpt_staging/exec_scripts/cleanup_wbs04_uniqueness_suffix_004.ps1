$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$RunId = 'exec-20260505-wbs04-uniqueness-suffix-004'
$NowUtc = (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')
$RepoRoot = if ($env:GITHUB_WORKSPACE) { $env:GITHUB_WORKSPACE } else { (Get-Location).Path }
$DownloadsDir = [Environment]::GetEnvironmentVariable('DCOIR_DOWNLOADS_DIR','Machine')
if ([string]::IsNullOrWhiteSpace($DownloadsDir)) { $DownloadsDir = Join-Path $RepoRoot 'chatgpt_staging/tmp_exec_outputs' }
$OutDir = Join-Path $DownloadsDir $RunId
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null
$JsonPath = Join-Path $OutDir 'wbs04_uniqueness_suffix.json'
$MdPath = Join-Path $OutDir 'wbs04_uniqueness_suffix.md'
function EnvReq([string]$Name){$v=[Environment]::GetEnvironmentVariable($Name,'Process');if([string]::IsNullOrWhiteSpace($v)){$v=[Environment]::GetEnvironmentVariable($Name,'User')};if([string]::IsNullOrWhiteSpace($v)){$v=[Environment]::GetEnvironmentVariable($Name,'Machine')};if([string]::IsNullOrWhiteSpace($v)){throw "Missing $Name"};return $v}
$BaseId=EnvReq 'DCOIR_AIRTABLE_BASE_ID';$Token=EnvReq 'DCOIR_AIRTABLE_TOKEN';$Headers=@{Authorization="Bearer $Token";'Content-Type'='application/json'}
function At([string]$Method,[string]$Uri,[object]$Body=$null){if($null -eq $Body){return Invoke-RestMethod -Method $Method -Uri $Uri -Headers $Headers};return Invoke-RestMethod -Method $Method -Uri $Uri -Headers $Headers -Body ($Body|ConvertTo-Json -Depth 30)}
function Patch([string]$TableId,[string]$RecordId,[hashtable]$Fields){$uri='https://api.airtable.com/v0/{0}/{1}' -f $BaseId,$TableId;At PATCH $uri @{records=@(@{id=$RecordId;fields=$Fields});typecast=$true}|Out-Null}
function Find([string]$TableId,[string]$FieldName,[string]$Value){$safe=$Value.Replace("'","\\'");$enc=[uri]::EscapeDataString("{$FieldName} = '$safe'");$uri='https://api.airtable.com/v0/{0}/{1}?filterByFormula={2}&maxRecords=1' -f $BaseId,$TableId,$enc;$r=At GET $uri;if($r.records.Count -gt 0){return $r.records[0]};return $null}
function Upsert([string]$TableId,[string]$FieldName,[string]$Value,[hashtable]$Fields){$uri='https://api.airtable.com/v0/{0}/{1}' -f $BaseId,$TableId;$e=Find $TableId $FieldName $Value;if($null -eq $e){At POST $uri @{records=@(@{fields=$Fields});typecast=$true}|Out-Null}else{At PATCH $uri @{records=@(@{id=$e.id;fields=$Fields});typecast=$true}|Out-Null}}
function IdLike([string]$n){if($n -eq 'config_name'){return $true};if($n -match '(?i)(^|[_ /-])(id|key)(s)?($|[_ /-])'){return $true};if($n -match '(?i)(signature|record[_ ]id|source_record_id|target_record_id|parent_.*key|canonical_parent_)'){return $true};if($n -match '(?i)^(source_|target_|parent_)'){return $true};return $false}
$Schema=At GET ('https://api.airtable.com/v0/meta/bases/{0}/tables' -f $BaseId)
$Tables=@{};foreach($t in $Schema.tables){$Tables[$t.name]=$t.id}
foreach($need in @('DCOIR Cleanup WBS','Plans','Queue Control','Validation Evidence')){if(-not $Tables.ContainsKey($need)){throw "Missing table $need"}}
$Rows=@()
foreach($t in ($Schema.tables|Sort-Object name)){
  $idNames=@($t.fields|Where-Object{IdLike $_.name}|ForEach-Object{$_.name})
  $lineage=@($idNames|Where-Object{$_ -match '(?i)^(source_|target_|parent_|canonical_parent_)|record_id$|target_record_id|source_record_id'})
  $canonical=@($idNames|Where-Object{$_ -match '(?i)(_key$| key$|^key$|config_name|_entry_id$| id$|_id$|Item ID|Test ID)'})
  $suffix = if($lineage.Count -gt 0){$lineage -join ', '} elseif($canonical.Count -gt 1){($canonical|Select-Object -Skip 1|Select-Object -First 3) -join ', '} else {'Airtable record id as last-resort collision suffix only'}
  $collision = if($lineage.Count -gt 0){'low if lineage source is populated'} elseif($canonical.Count -gt 0){'medium; verify canonical key uniqueness before formula rollout'} else {'high until a canonical key is introduced or record-id fallback is accepted'}
  $Rows += [pscustomobject]@{table_name=$t.name;table_id=$t.id;existing_identity_fields=$idNames;uniqueness_suffix=$suffix;collision_note=$collision;implementation_gate='planning only; no schema mutation'}
}
[pscustomobject]@{run_id=$RunId;observed_at_utc=$NowUtc;table_count=$Schema.tables.Count;uniqueness_suffix_design=$Rows}|ConvertTo-Json -Depth 20|Set-Content $JsonPath -Encoding UTF8
$md=@('# WBS04 uniqueness suffix design','',('Run: {0}' -f $RunId),'')
foreach($r in $Rows){$md += ('## {0}' -f $r.table_name);$md += ('suffix: {0}' -f $r.uniqueness_suffix);$md += ('collision_note: {0}' -f $r.collision_note);$md += ''}
$md|Set-Content $MdPath -Encoding UTF8
$Evidence04='WBS04-04 completed by '+$RunId+'. Uniqueness suffix options and collision notes defined for '+$Rows.Count+' tables. Artifact files: wbs04_uniqueness_suffix.json and wbs04_uniqueness_suffix.md.'
Patch $Tables['DCOIR Cleanup WBS'] 'recucvUq3rj7M1uDA' @{state='complete';validation_notes=$Evidence04}
Patch $Tables['DCOIR Cleanup WBS'] 'rectmzGHTi4CfATLx' @{state='active';validation_notes=('Activated by '+$RunId+' after WBS04-04 completion. Next: define dedupe signatures.')}
Patch $Tables['Plans'] 'recoLHyurY4OZx3K8' @{active_task_id='CLEANUP-WBS-04';active_task_title='Calculated ID and Dedupe Signature Design';active_plan_task_id='CLEANUP-WBS-04-05';exact_resume_goal='Resume at CLEANUP-WBS-04-05 in WBS order.';next_recommended_action='Continue with CLEANUP-WBS-04-05: Define dedupe signatures.';last_updated_text=$NowUtc;plan_state='active'}
Patch $Tables['Queue Control'] 'recW8cAlClYFEVhjF' @{branch_summary='Active branch: PLAN-AIRTABLE-CLEANUP-RESTRUCTURE / CLEANUP-WBS-04.';branch_decision='WBS04-04 complete; WBS04-05 active.';resume_rule='Resume cleanup plan at CLEANUP-WBS-04-05 unless live Airtable state changes.';next_revalidation_trigger='After WBS04-05 dedupe signatures are complete.';last_confirmed_text=$NowUtc}
Upsert $Tables['Validation Evidence'] 'evidence_key' 'EVID-CLEANUP-WBS-04-04-UNIQUENESS-SUFFIX-20260505' @{evidence_key='EVID-CLEANUP-WBS-04-04-UNIQUENESS-SUFFIX-20260505';validation_case_key='CLEANUP-WBS-04-04';work_item_key='CLEANUP-WBS-04-04';evidence_summary=$Evidence04;source_locator=$RunId}
Write-Host ('[{0}] success: WBS04-04 complete; WBS04-05 active.' -f $RunId)
