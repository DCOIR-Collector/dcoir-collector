$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$RunId = 'exec-20260505-wbs04-dedupe-signatures-005'
$NowUtc = (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')
$RepoRoot = if ($env:GITHUB_WORKSPACE) { $env:GITHUB_WORKSPACE } else { (Get-Location).Path }
$DownloadsDir = [Environment]::GetEnvironmentVariable('DCOIR_DOWNLOADS_DIR','Machine')
if ([string]::IsNullOrWhiteSpace($DownloadsDir)) { $DownloadsDir = Join-Path $RepoRoot 'chatgpt_staging/tmp_exec_outputs' }
$OutDir = Join-Path $DownloadsDir $RunId
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null
$JsonPath = Join-Path $OutDir 'wbs04_dedupe_signatures.json'
$MdPath = Join-Path $OutDir 'wbs04_dedupe_signatures.md'
function EnvReq([string]$Name){$v=[Environment]::GetEnvironmentVariable($Name,'Process');if([string]::IsNullOrWhiteSpace($v)){$v=[Environment]::GetEnvironmentVariable($Name,'User')};if([string]::IsNullOrWhiteSpace($v)){$v=[Environment]::GetEnvironmentVariable($Name,'Machine')};if([string]::IsNullOrWhiteSpace($v)){throw "Missing $Name"};return $v}
$BaseId=EnvReq 'DCOIR_AIRTABLE_BASE_ID';$Token=EnvReq 'DCOIR_AIRTABLE_TOKEN';$Headers=@{Authorization="Bearer $Token";'Content-Type'='application/json'}
function At([string]$Method,[string]$Uri,[object]$Body=$null){if($null -eq $Body){return Invoke-RestMethod -Method $Method -Uri $Uri -Headers $Headers};return Invoke-RestMethod -Method $Method -Uri $Uri -Headers $Headers -Body ($Body|ConvertTo-Json -Depth 30)}
function Patch([string]$TableId,[string]$RecordId,[hashtable]$Fields){$uri='https://api.airtable.com/v0/{0}/{1}' -f $BaseId,$TableId;At PATCH $uri @{records=@(@{id=$RecordId;fields=$Fields});typecast=$true}|Out-Null}
function Find([string]$TableId,[string]$FieldName,[string]$Value){$safe=$Value.Replace("'","\\'");$enc=[uri]::EscapeDataString("{$FieldName} = '$safe'");$uri='https://api.airtable.com/v0/{0}/{1}?filterByFormula={2}&maxRecords=1' -f $BaseId,$TableId,$enc;$r=At GET $uri;if($r.records.Count -gt 0){return $r.records[0]};return $null}
function Upsert([string]$TableId,[string]$FieldName,[string]$Value,[hashtable]$Fields){$uri='https://api.airtable.com/v0/{0}/{1}' -f $BaseId,$TableId;$e=Find $TableId $FieldName $Value;if($null -eq $e){At POST $uri @{records=@(@{fields=$Fields});typecast=$true}|Out-Null}else{At PATCH $uri @{records=@(@{id=$e.id;fields=$Fields});typecast=$true}|Out-Null}}
function IdLike([string]$n){if($n -eq 'config_name'){return $true};if($n -match '(?i)(^|[_ /-])(id|key)(s)?($|[_ /-])'){return $true};if($n -match '(?i)(signature|record[_ ]id|source_record_id|target_record_id|parent_.*key|canonical_parent_)'){return $true};if($n -match '(?i)^(source_|target_|parent_)'){return $true};return $false}
function SlugFields($t){$names=@();foreach($pat in @('title','name','summary','work item','test case','locator','surface','tool','object','control','plan','checkpoint','idea','event','finding','preference','purpose')){foreach($f in $t.fields){if($names.Count -ge 4){break};if($f.name -match ('(?i)'+[regex]::Escape($pat)) -and -not (IdLike $f.name) -and $names -notcontains $f.name){$names += $f.name}}};if($names.Count -eq 0){$p=$t.fields|Where-Object{$_.id -eq $t.primaryFieldId}|Select-Object -First 1;if($p){$names += $p.name}};return @($names)}
$Schema=At GET ('https://api.airtable.com/v0/meta/bases/{0}/tables' -f $BaseId)
$Tables=@{};foreach($t in $Schema.tables){$Tables[$t.name]=$t.id}
foreach($need in @('DCOIR Cleanup WBS','Plans','Queue Control','Validation Evidence')){if(-not $Tables.ContainsKey($need)){throw "Missing table $need"}}
$Rows=@()
foreach($t in ($Schema.tables|Sort-Object name)){
  $slug=SlugFields $t
  $ids=@($t.fields|Where-Object{IdLike $_.name}|ForEach-Object{$_.name})
  $scope=@($ids|Where-Object{$_ -match '(?i)^(source_|target_|parent_|canonical_parent_)|record_id$|target_record_id|source_record_id'}|Select-Object -First 3)
  if($scope.Count -eq 0){$scope=@($ids|Where-Object{$_ -match '(?i)_key$|_id$| id$|config_name|Item ID|Test ID'}|Select-Object -First 2)}
  if($scope.Count -eq 0){$scope=@('record_id_fallback')}
  $formula='hash(normalize('+(($slug)-join ' + ')+') + scope('+(($scope)-join ' + ')+'))'
  $Rows += [pscustomobject]@{table_name=$t.name;table_id=$t.id;signature_sources=$slug;scope_sources=$scope;dedupe_signature_formula=$formula;collision_review='review exact duplicate candidates before any merge/delete';implementation_gate='planning only; no calculated fields created'}
}
[pscustomobject]@{run_id=$RunId;observed_at_utc=$NowUtc;table_count=$Schema.tables.Count;dedupe_signature_design=$Rows}|ConvertTo-Json -Depth 20|Set-Content $JsonPath -Encoding UTF8
$md=@('# WBS04 dedupe signature design','',('Run: {0}' -f $RunId),'')
foreach($r in $Rows){$md += ('## {0}' -f $r.table_name);$md += ('signature_sources: {0}' -f (($r.signature_sources)-join ', '));$md += ('scope_sources: {0}' -f (($r.scope_sources)-join ', '));$md += ('formula: {0}' -f $r.dedupe_signature_formula);$md += ''}
$md|Set-Content $MdPath -Encoding UTF8
$Evidence05='WBS04-05 completed by '+$RunId+'. Dedupe signature proposals defined for '+$Rows.Count+' tables. Artifact files: wbs04_dedupe_signatures.json and wbs04_dedupe_signatures.md.'
Patch $Tables['DCOIR Cleanup WBS'] 'rectmzGHTi4CfATLx' @{state='complete';validation_notes=$Evidence05}
Patch $Tables['DCOIR Cleanup WBS'] 'recXK5TmBzuRhYEJ3' @{state='active';validation_notes=('Activated by '+$RunId+' after WBS04-05 completion. Next: close out ID standard.')}
Patch $Tables['Plans'] 'recoLHyurY4OZx3K8' @{active_task_id='CLEANUP-WBS-04';active_task_title='Calculated ID and Dedupe Signature Design';active_plan_task_id='CLEANUP-WBS-04-06';exact_resume_goal='Resume at CLEANUP-WBS-04-06 in WBS order.';next_recommended_action='Continue with CLEANUP-WBS-04-06: Close out ID standard.';last_updated_text=$NowUtc;plan_state='active'}
Patch $Tables['Queue Control'] 'recW8cAlClYFEVhjF' @{branch_summary='Active branch: PLAN-AIRTABLE-CLEANUP-RESTRUCTURE / CLEANUP-WBS-04.';branch_decision='WBS04-05 complete; WBS04-06 active.';resume_rule='Resume cleanup plan at CLEANUP-WBS-04-06 unless live Airtable state changes.';next_revalidation_trigger='After WBS04-06 closeout is complete.';last_confirmed_text=$NowUtc}
Upsert $Tables['Validation Evidence'] 'evidence_key' 'EVID-CLEANUP-WBS-04-05-DEDUPE-SIGNATURES-20260505' @{evidence_key='EVID-CLEANUP-WBS-04-05-DEDUPE-SIGNATURES-20260505';validation_case_key='CLEANUP-WBS-04-05';work_item_key='CLEANUP-WBS-04-05';evidence_summary=$Evidence05;source_locator=$RunId}
Write-Host ('[{0}] success: WBS04-05 complete; WBS04-06 active.' -f $RunId)
