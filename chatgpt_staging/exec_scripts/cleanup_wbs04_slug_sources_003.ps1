$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$RunId = 'exec-20260505-wbs04-slug-sources-003'
$NowUtc = (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')
$RepoRoot = if ($env:GITHUB_WORKSPACE) { $env:GITHUB_WORKSPACE } else { (Get-Location).Path }
$DownloadsDir = [Environment]::GetEnvironmentVariable('DCOIR_DOWNLOADS_DIR','Machine')
if ([string]::IsNullOrWhiteSpace($DownloadsDir)) { $DownloadsDir = Join-Path $RepoRoot 'chatgpt_staging/tmp_exec_outputs' }
$OutDir = Join-Path $DownloadsDir $RunId
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null
$JsonPath = Join-Path $OutDir 'wbs04_slug_sources.json'
$MdPath = Join-Path $OutDir 'wbs04_slug_sources.md'

function Get-EnvRequired {
  param([string]$Name)
  $v = [Environment]::GetEnvironmentVariable($Name, 'Process')
  if ([string]::IsNullOrWhiteSpace($v)) { $v = [Environment]::GetEnvironmentVariable($Name, 'User') }
  if ([string]::IsNullOrWhiteSpace($v)) { $v = [Environment]::GetEnvironmentVariable($Name, 'Machine') }
  if ([string]::IsNullOrWhiteSpace($v)) { throw "Missing required environment variable: $Name" }
  return $v
}

$BaseId = Get-EnvRequired 'DCOIR_AIRTABLE_BASE_ID'
$Token = Get-EnvRequired 'DCOIR_AIRTABLE_TOKEN'
$Headers = @{ Authorization = "Bearer $Token"; 'Content-Type' = 'application/json' }

function Invoke-At {
  param([string]$Method,[string]$Uri,[object]$Body=$null)
  if ($null -eq $Body) { return Invoke-RestMethod -Method $Method -Uri $Uri -Headers $Headers }
  $json = $Body | ConvertTo-Json -Depth 30
  return Invoke-RestMethod -Method $Method -Uri $Uri -Headers $Headers -Body $json
}
function Patch-At {
  param([string]$TableId,[string]$RecordId,[hashtable]$Fields)
  $uri = 'https://api.airtable.com/v0/{0}/{1}' -f $BaseId,$TableId
  Invoke-At PATCH $uri @{ records = @(@{ id = $RecordId; fields = $Fields }); typecast = $true } | Out-Null
}
function Find-At {
  param([string]$TableId,[string]$FieldName,[string]$Value)
  $safe = $Value.Replace("'", "\\'")
  $formula = "{$FieldName} = '$safe'"
  $encoded = [uri]::EscapeDataString($formula)
  $uri = 'https://api.airtable.com/v0/{0}/{1}?filterByFormula={2}&maxRecords=1' -f $BaseId,$TableId,$encoded
  $res = Invoke-At GET $uri
  if ($res.records.Count -gt 0) { return $res.records[0] }
  return $null
}
function Upsert-At {
  param([string]$TableId,[string]$FieldName,[string]$Value,[hashtable]$Fields)
  $uri = 'https://api.airtable.com/v0/{0}/{1}' -f $BaseId,$TableId
  $existing = Find-At $TableId $FieldName $Value
  if ($null -eq $existing) { Invoke-At POST $uri @{ records=@(@{ fields=$Fields }); typecast=$true } | Out-Null }
  else { Invoke-At PATCH $uri @{ records=@(@{ id=$existing.id; fields=$Fields }); typecast=$true } | Out-Null }
}
function Is-IdLike {
  param([string]$Name)
  if ($Name -eq 'config_name') { return $true }
  if ($Name -match '(?i)(^|[_ /-])(id|key)(s)?($|[_ /-])') { return $true }
  if ($Name -match '(?i)(signature|record[_ ]id|primary_key|source_record_id|target_record_id|parent_.*key|canonical_parent_)') { return $true }
  if ($Name -match '(?i)^(source_|target_|parent_)') { return $true }
  return $false
}
function Choose-SlugSources {
  param($Table)
  $priority = @('title','name','summary','work item','test case','locator','surface','tool','object','control','plan','checkpoint','idea','event','finding','preference','purpose')
  $selected = New-Object System.Collections.Generic.List[string]
  foreach ($p in $priority) {
    foreach ($f in $Table.fields) {
      if ($selected.Count -ge 4) { break }
      if ($f.name -match ('(?i)' + [regex]::Escape($p)) -and -not (Is-IdLike $f.name) -and -not $selected.Contains($f.name)) { $selected.Add($f.name) }
    }
  }
  if ($selected.Count -eq 0) {
    $primary = $Table.fields | Where-Object { $_.id -eq $Table.primaryFieldId } | Select-Object -First 1
    if ($null -ne $primary) { $selected.Add($primary.name) }
  }
  return @($selected)
}
function TableCode {
  param([string]$Name)
  $parts = @([regex]::Matches($Name,'[A-Za-z0-9]+') | ForEach-Object { $_.Value })
  if ($parts.Count -eq 0) { return 'TBL' }
  if ($parts.Count -eq 1) { $c = $parts[0].ToUpperInvariant() } else { $c = ($parts | ForEach-Object { $_.Substring(0,1).ToUpperInvariant() }) -join '' }
  if ($c.Length -gt 10) { return $c.Substring(0,10) }
  return $c
}

$Schema = Invoke-At GET ('https://api.airtable.com/v0/meta/bases/{0}/tables' -f $BaseId)
$Tables = @{}
foreach ($t in $Schema.tables) { $Tables[$t.name] = $t.id }
foreach ($need in @('DCOIR Cleanup WBS','Plans','Queue Control','Validation Evidence')) { if (-not $Tables.ContainsKey($need)) { throw "Missing table $need" } }

$Rows = @()
foreach ($t in ($Schema.tables | Sort-Object name)) {
  $sources = Choose-SlugSources $t
  $Rows += [pscustomobject]@{
    table_name = $t.name
    table_id = $t.id
    table_code = TableCode $t.name
    canonical_slug_sources = $sources
    slug_normalization = 'lowercase, trim, collapse whitespace, replace non-alphanumeric runs with hyphen, trim hyphens'
    null_handling = 'skip empty source parts; if all empty, fall back to table code plus Airtable record id during later implementation review'
    review_note = 'planning design only; no schema changes performed'
  }
}

[pscustomobject]@{ run_id=$RunId; observed_at_utc=$NowUtc; table_count=$Schema.tables.Count; slug_source_design=$Rows } | ConvertTo-Json -Depth 20 | Set-Content -Path $JsonPath -Encoding UTF8
$md = @()
$md += '# WBS04 canonical slug source design'
$md += ''
$md += ('Run: {0}' -f $RunId)
$md += ('Observed UTC: {0}' -f $NowUtc)
$md += ''
foreach ($r in $Rows) {
  $md += ('## {0}' -f $r.table_name)
  $md += ('table_code: {0}' -f $r.table_code)
  $md += ('canonical_slug_sources: {0}' -f (($r.canonical_slug_sources) -join ', '))
  $md += 'normalization: lowercase, trim, collapse whitespace, replace non-alphanumeric runs with hyphen, trim hyphens'
  $md += ''
}
$md | Set-Content -Path $MdPath -Encoding UTF8

$Evidence02 = 'WBS04-02 corrected/closed after prior script parse failure. Table-specific component design basis is carried forward into WBS04-03 slug-source artifact.'
$Evidence03 = 'WBS04-03 completed by ' + $RunId + '. Canonical slug sources defined for ' + $Rows.Count + ' tables. Artifact files: wbs04_slug_sources.json and wbs04_slug_sources.md.'
Patch-At $Tables['DCOIR Cleanup WBS'] 'recrFmt9ic8RFtuLC' @{ state='complete'; validation_notes=$Evidence02 }
Patch-At $Tables['DCOIR Cleanup WBS'] 'recrTT6Z0JwQnu9fl' @{ state='complete'; validation_notes=$Evidence03 }
Patch-At $Tables['DCOIR Cleanup WBS'] 'recucvUq3rj7M1uDA' @{ state='active'; validation_notes=('Activated by ' + $RunId + ' after WBS04-03 completion. Next: define uniqueness suffix options.') }
Patch-At $Tables['Plans'] 'recoLHyurY4OZx3K8' @{ active_task_id='CLEANUP-WBS-04'; active_task_title='Calculated ID and Dedupe Signature Design'; active_plan_task_id='CLEANUP-WBS-04-04'; exact_resume_goal='Resume at CLEANUP-WBS-04-04 in WBS order.'; next_recommended_action='Continue with CLEANUP-WBS-04-04: Define uniqueness suffix options.'; last_updated_text=$NowUtc; plan_state='active' }
Patch-At $Tables['Queue Control'] 'recW8cAlClYFEVhjF' @{ branch_summary='Active branch: PLAN-AIRTABLE-CLEANUP-RESTRUCTURE / CLEANUP-WBS-04.'; branch_decision='WBS04-03 complete; WBS04-04 active.'; resume_rule='Resume cleanup plan at CLEANUP-WBS-04-04 unless live Airtable state changes.'; next_revalidation_trigger='After WBS04-04 uniqueness suffix options are complete.'; last_confirmed_text=$NowUtc }
Upsert-At $Tables['Validation Evidence'] 'evidence_key' 'EVID-CLEANUP-WBS-04-03-SLUG-SOURCES-20260505' @{ evidence_key='EVID-CLEANUP-WBS-04-03-SLUG-SOURCES-20260505'; validation_case_key='CLEANUP-WBS-04-03'; work_item_key='CLEANUP-WBS-04-03'; evidence_summary=$Evidence03; source_locator=$RunId }
Write-Host ('[{0}] success: WBS04-03 complete; WBS04-04 active.' -f $RunId)
