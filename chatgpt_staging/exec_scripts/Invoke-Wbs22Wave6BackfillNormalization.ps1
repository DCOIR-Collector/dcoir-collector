[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version 2.0

$RequestId = 'exec-20260508-wbs22-wave6-backfill-normalization-001'
$Expected = @{
  ARecords = 2; ACells = 2
  BRecords = 105; BCells = 262; BExcludedDq = 4; BAmbiguous = 0
  CRecords = 31; CCells = 59
}
$ExpectedBFields = @{ created_at = 33; updated_at = 61; review_after = 105; result = 26; retention_class = 37 }
$ExpectedCFields = @{ created_at = 30; updated_at = 29 }

function New-RunDir {
  $downloads = [Environment]::GetEnvironmentVariable('DCOIR_DOWNLOADS_DIR','Machine')
  if ([string]::IsNullOrWhiteSpace($downloads)) { throw 'DCOIR_DOWNLOADS_DIR is missing.' }
  $stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
  $out = Join-Path $downloads ("wbs22_wave6_backfill_normalization_{0}" -f $stamp)
  New-Item -ItemType Directory -Force -Path $out | Out-Null
  return $out
}
function Write-JsonFile { param([string]$Path, $Object, [int]$Depth = 80) $json = $Object | ConvertTo-Json -Depth $Depth; [System.IO.File]::WriteAllText($Path, $json, [System.Text.UTF8Encoding]::new($false)) }
function Has-Value { param($Value) if ($null -eq $Value) { return $false }; if ($Value -is [string]) { return -not [string]::IsNullOrWhiteSpace($Value) }; if ($Value -is [System.Array]) { return $Value.Count -gt 0 }; return $true }
function Get-PropValue { param($Object,[string]$Name) if ($null -eq $Object) { return $null }; $p = $Object.PSObject.Properties[$Name]; if ($null -eq $p) { return $null }; return $p.Value }
function Normalize-Value { param($Value) if ($null -eq $Value) { return '<NULL>' }; if ($Value -is [System.Array]) { return (($Value | ConvertTo-Json -Compress -Depth 20)) }; return [string]$Value }
function Values-Equal { param($A,$B) return ((Normalize-Value $A) -eq (Normalize-Value $B)) }
function Text-Lower { param($Value) if ($null -eq $Value) { return '' }; return ([string]$Value).ToLowerInvariant() }
function Add-FieldCount { param([hashtable]$Counts,[string]$Field) if (-not $Counts.ContainsKey($Field)) { $Counts[$Field] = 0 }; $Counts[$Field]++ }
function Compare-FieldCounts { param([hashtable]$Actual,[hashtable]$ExpectedCounts,[string]$Name)
  foreach ($k in $ExpectedCounts.Keys) { if (-not $Actual.ContainsKey($k) -or [int]$Actual[$k] -ne [int]$ExpectedCounts[$k]) { throw "$Name field count drift for $k. Expected $($ExpectedCounts[$k]), got $($Actual[$k])" } }
  foreach ($k in $Actual.Keys) { if (-not $ExpectedCounts.ContainsKey($k)) { throw "$Name unexpected field in payload: $k" } }
}

function Invoke-At { param([string]$Method,[string]$Uri,$Body=$null)
  $args = @{ Method=$Method; Uri=$Uri; Headers=$script:Headers; ErrorAction='Stop' }
  if ($null -ne $Body) { $args['Body'] = ($Body | ConvertTo-Json -Depth 80); $args['ContentType'] = 'application/json' }
  return Invoke-RestMethod @args
}
function Get-RecordOrNull { param([string]$TableId,[string]$RecordId)
  $uri = 'https://api.airtable.com/v0/{0}/{1}/{2}' -f $script:BaseId, [System.Uri]::EscapeDataString($TableId), $RecordId
  try { return Invoke-At -Method 'GET' -Uri $uri } catch { if ($_.Exception.Response -and [int]$_.Exception.Response.StatusCode -eq 404) { return $null }; throw }
}
function Get-AllRecords { param([string]$TableId)
  $all = New-Object System.Collections.Generic.List[object]
  $offset = $null
  do {
    $uri = 'https://api.airtable.com/v0/{0}/{1}?pageSize=100' -f $script:BaseId, [System.Uri]::EscapeDataString($TableId)
    if (-not [string]::IsNullOrWhiteSpace($offset)) { $uri = $uri + '&offset=' + [System.Uri]::EscapeDataString($offset) }
    $resp = Invoke-At -Method 'GET' -Uri $uri
    foreach ($r in @($resp.records)) { $all.Add($r) | Out-Null }
    $offset = Get-PropValue $resp 'offset'
  } while (-not [string]::IsNullOrWhiteSpace($offset))
  return @($all.ToArray())
}

function Test-DeleteQueueRelatedEvidence { param($Fields)
  $key = Text-Lower (Get-PropValue $Fields 'evidence_key')
  $summary = Text-Lower (Get-PropValue $Fields 'evidence_summary')
  $text = $key + ' ' + $summary
  $directKeyMarkers = @('wave4','wave5','delete-queue','delete_queue')
  $directSummaryMarkers = @('delete queue processing only','delete queue candidate creation only','queue-candidate batch','queue rows were processed','process approved delete queue')
  foreach ($m in $directKeyMarkers) { if ($key.Contains($m)) { return $true } }
  foreach ($m in $directSummaryMarkers) { if ($text.Contains($m)) { return $true } }
  return $false
}
function Infer-ValidationResult { param($Fields)
  if (Test-DeleteQueueRelatedEvidence $Fields) { return [pscustomobject]@{ Value = $null; Why = 'excluded_delete_queue_scope' } }
  $key = Text-Lower (Get-PropValue $Fields 'evidence_key')
  $summary = Text-Lower (Get-PropValue $Fields 'evidence_summary')
  $text = $key + ' ' + $summary
  $pending = @('prepared before execution','review record prepared','pre-execution','review scope','scope:','planning metadata','not completion evidence','await real','awaiting')
  foreach ($m in $pending) { if ($text.Contains($m)) { return [pscustomobject]@{ Value = 'pending'; Why = 'review_or_pre_execution_record' } } }
  if ($text.Contains('blocked') -or $text.Contains('unresolved blocker')) { return [pscustomobject]@{ Value = 'blocked'; Why = 'blocked_marker' } }
  if ($key.Contains('bug')) {
    $resolved = @('fixed','resolved','closed','patched','passed','verified','success','succeeded','clean')
    $hasResolved = $false; foreach ($m in $resolved) { if ($text.Contains($m)) { $hasResolved = $true } }
    if (-not $hasResolved) { return [pscustomobject]@{ Value = 'blocked'; Why = 'bug_without_resolution_marker' } }
  }
  $passMarkers = @('passed',' pass','verified','completed','success','succeeded','confirmed','inspected','clean','integrity passed','readback','artifact files:','produced and verified','zero rows','found, 17')
  foreach ($m in $passMarkers) { if ($text.Contains($m)) { return [pscustomobject]@{ Value = 'pass'; Why = 'pass_success_verification_marker' } } }
  return [pscustomobject]@{ Value = $null; Why = 'ambiguous_no_result_inference' }
}
function Get-ReviewDate { param([string]$Retention,[string]$Result) if (@('operational','retain','core') -contains $Retention -or $Result -eq 'pass') { return '2026-08-06' }; return '2026-06-08' }
function New-Update { param([string]$Batch,[string]$Table,[string]$TableId,[string]$RecordId,$Before,[hashtable]$Fields,[string]$Key,[string[]]$Reasons)
  return [pscustomobject]@{ batch=$Batch; table=$Table; table_id=$TableId; record_id=$RecordId; key=$Key; before=$Before; fields=$Fields; reasons=$Reasons }
}
function Get-CellCount { param([object[]]$Updates) $n = 0; foreach ($u in $Updates) { $n += $u.fields.Keys.Count }; return $n }

function Build-Payload {
  $vtcTable = 'tblRnMpQUomIGyFVL'; $veTable = 'tblrPFQH2uZEYBYE9'; $scTable = 'tblTe75HKZOJaPDGn'
  $a = New-Object System.Collections.Generic.List[object]
  foreach ($r in @(Get-AllRecords $vtcTable)) {
    $f = $r.fields
    if (-not (Has-Value (Get-PropValue $f 'Test Case'))) {
      $tid = Get-PropValue $f 'Test ID'
      if ($tid -eq 'GEM-GROUND-001') { $proposal = 'Gemini Enterprise web-grounding lane honesty' }
      elseif ($tid -eq 'GEM-UPLOAD-001') { $proposal = 'Gemini upload-only internal-knowledge honesty' }
      else { $proposal = Get-PropValue $f 'Feature or Behavior'; if (-not (Has-Value $proposal)) { $proposal = $tid } }
      $before = [pscustomobject]@{ 'Test Case' = Get-PropValue $f 'Test Case'; 'Test ID' = $tid; 'Feature or Behavior' = Get-PropValue $f 'Feature or Behavior' }
      $a.Add((New-Update -Batch 'A' -Table 'Validation Test Cases' -TableId $vtcTable -RecordId $r.id -Before $before -Fields @{ 'Test Case' = $proposal } -Key $tid -Reasons @('blank primary Test Case value; source fields already describe the test case'))) | Out-Null
    }
  }
  $b = New-Object System.Collections.Generic.List[object]
  $excluded = New-Object System.Collections.Generic.List[object]
  $ambig = New-Object System.Collections.Generic.List[object]
  foreach ($r in @(Get-AllRecords $veTable)) {
    $f = $r.fields
    if (Test-DeleteQueueRelatedEvidence $f) { $excluded.Add([pscustomobject]@{ record_id=$r.id; evidence_key=(Get-PropValue $f 'evidence_key') }) | Out-Null; continue }
    $upd = @{}; $reasons = New-Object System.Collections.Generic.List[string]
    $curResult = Get-PropValue $f 'result'; $curRet = Get-PropValue $f 'retention_class'
    if ($curResult -eq 'passed') { $upd['result']='pass'; $reasons.Add('normalize result passed -> pass') | Out-Null }
    elseif (-not (Has-Value $curResult)) { $inf = Infer-ValidationResult $f; if (Has-Value $inf.Value) { $upd['result'] = $inf.Value; $reasons.Add(('infer result={0}: {1}' -f $inf.Value,$inf.Why)) | Out-Null } else { $ambig.Add([pscustomobject]@{ record_id=$r.id; evidence_key=(Get-PropValue $f 'evidence_key'); reason=$inf.Why }) | Out-Null } }
    $finalResult = if ($upd.ContainsKey('result')) { $upd['result'] } else { $curResult }
    if ($curRet -eq 'passed') { $upd['retention_class']='operational'; $reasons.Add('normalize retention_class passed -> operational') | Out-Null }
    elseif (-not (Has-Value $curRet)) { if ($finalResult -eq 'pass') { $upd['retention_class']='operational'; $reasons.Add('blank retention_class -> operational from pass evidence') | Out-Null } elseif (@('pending','blocked') -contains $finalResult) { $upd['retention_class']='review'; $reasons.Add(('blank retention_class -> review from result={0}' -f $finalResult)) | Out-Null } else { $upd['retention_class']='review'; $reasons.Add('blank retention_class -> review because result remains ambiguous') | Out-Null } }
    $created = Get-PropValue $f 'created_at'; $proposedCreated = if (Has-Value $created) { $created } else { $r.createdTime }
    if (-not (Has-Value $created)) { $upd['created_at'] = $proposedCreated; $reasons.Add('blank created_at -> Airtable createdTime') | Out-Null }
    if (-not (Has-Value (Get-PropValue $f 'updated_at'))) { $upd['updated_at'] = if (Has-Value $created) { $created } else { $proposedCreated }; $reasons.Add('blank updated_at -> existing/proposed created_at') | Out-Null }
    $finalRet = if ($upd.ContainsKey('retention_class')) { $upd['retention_class'] } else { $curRet }
    if (-not (Has-Value (Get-PropValue $f 'review_after'))) { $upd['review_after'] = Get-ReviewDate -Retention $finalRet -Result $finalResult; $reasons.Add('blank review_after -> standard date from retention/result') | Out-Null }
    if ($upd.Keys.Count -gt 0) {
      $before = [pscustomobject]@{ result=$curResult; retention_class=$curRet; created_at=(Get-PropValue $f 'created_at'); updated_at=(Get-PropValue $f 'updated_at'); review_after=(Get-PropValue $f 'review_after') }
      $b.Add((New-Update -Batch 'B' -Table 'Validation Evidence' -TableId $veTable -RecordId $r.id -Before $before -Fields $upd -Key (Get-PropValue $f 'evidence_key') -Reasons @($reasons.ToArray()))) | Out-Null
    }
  }
  $c = New-Object System.Collections.Generic.List[object]
  foreach ($r in @(Get-AllRecords $scTable)) {
    $f = $r.fields; $upd = @{}; $reasons = New-Object System.Collections.Generic.List[string]
    $checkpointAt = Get-PropValue $f 'checkpoint_at'; $createdAt = Get-PropValue $f 'created_at'
    if (-not (Has-Value $createdAt)) { $upd['created_at'] = if (Has-Value $checkpointAt) { $checkpointAt } else { $r.createdTime }; $reasons.Add('blank created_at -> checkpoint_at else Airtable createdTime') | Out-Null }
    if (-not (Has-Value (Get-PropValue $f 'updated_at'))) { $upd['updated_at'] = if (Has-Value $checkpointAt) { $checkpointAt } elseif (Has-Value $createdAt) { $createdAt } else { $r.createdTime }; $reasons.Add('blank updated_at -> checkpoint_at/created_at') | Out-Null }
    if ($upd.Keys.Count -gt 0) {
      $before = [pscustomobject]@{ created_at=$createdAt; updated_at=(Get-PropValue $f 'updated_at'); checkpoint_at=$checkpointAt }
      $c.Add((New-Update -Batch 'C' -Table 'Session Checkpoints' -TableId $scTable -RecordId $r.id -Before $before -Fields $upd -Key (Get-PropValue $f 'checkpoint_id') -Reasons @($reasons.ToArray()))) | Out-Null
    }
  }
  return [pscustomobject]@{ A=@($a.ToArray()); B=@($b.ToArray()); C=@($c.ToArray()); excluded_delete_queue_related_rows=@($excluded.ToArray()); ambiguous_result_rows=@($ambig.ToArray()) }
}

function Validate-Payload { param($Payload)
  if ($Payload.A.Count -ne $Expected.ARecords -or (Get-CellCount $Payload.A) -ne $Expected.ACells) { throw "Batch A count drift. Expected $($Expected.ARecords)/$($Expected.ACells), got $($Payload.A.Count)/$(Get-CellCount $Payload.A)" }
  if ($Payload.B.Count -ne $Expected.BRecords -or (Get-CellCount $Payload.B) -ne $Expected.BCells) { throw "Batch B count drift. Expected $($Expected.BRecords)/$($Expected.BCells), got $($Payload.B.Count)/$(Get-CellCount $Payload.B)" }
  if ($Payload.C.Count -ne $Expected.CRecords -or (Get-CellCount $Payload.C) -ne $Expected.CCells) { throw "Batch C count drift. Expected $($Expected.CRecords)/$($Expected.CCells), got $($Payload.C.Count)/$(Get-CellCount $Payload.C)" }
  if ($Payload.excluded_delete_queue_related_rows.Count -ne $Expected.BExcludedDq) { throw "Excluded Delete Queue-related evidence count drift. Expected $($Expected.BExcludedDq), got $($Payload.excluded_delete_queue_related_rows.Count)" }
  if ($Payload.ambiguous_result_rows.Count -ne $Expected.BAmbiguous) { throw "Ambiguous result count drift. Expected $($Expected.BAmbiguous), got $($Payload.ambiguous_result_rows.Count)" }
  $bCounts=@{}; foreach ($u in $Payload.B) { foreach ($k in $u.fields.Keys) { Add-FieldCount $bCounts $k } }; Compare-FieldCounts -Actual $bCounts -ExpectedCounts $ExpectedBFields -Name 'Batch B'
  $cCounts=@{}; foreach ($u in $Payload.C) { foreach ($k in $u.fields.Keys) { Add-FieldCount $cCounts $k } }; Compare-FieldCounts -Actual $cCounts -ExpectedCounts $ExpectedCFields -Name 'Batch C'
  foreach ($u in @($Payload.A + $Payload.B + $Payload.C)) {
    if ($u.table -eq 'Delete Queue' -or $u.table_id -eq 'tbl1lMz5N6n7zShO0') { throw 'Delete Queue target appeared in payload.' }
    if ($u.table -eq 'Validation Evidence') {
      $live = Get-RecordOrNull -TableId $u.table_id -RecordId $u.record_id
      if ($null -eq $live) { throw "Target record missing during payload validation: $($u.record_id)" }
      if (Test-DeleteQueueRelatedEvidence $live.fields) { throw "Delete Queue-related evidence appeared in update payload: $($u.record_id)" }
    }
  }
}

function Verify-BeforeValues { param([object[]]$Updates)
  foreach ($u in $Updates) {
    $live = Get-RecordOrNull -TableId $u.table_id -RecordId $u.record_id
    if ($null -eq $live) { throw "Target record missing before update: $($u.record_id)" }
    foreach ($p in $u.before.PSObject.Properties) {
      $current = Get-PropValue $live.fields $p.Name
      if (-not (Values-Equal $current $p.Value)) { throw "Before-value drift for $($u.record_id) field $($p.Name). Expected '$($p.Value)' got '$current'." }
    }
  }
}
function Apply-Updates { param([object[]]$Updates)
  $byTable = $Updates | Group-Object table_id
  foreach ($group in $byTable) {
    $tableId = $group.Name
    $items = @($group.Group)
    for ($i=0; $i -lt $items.Count; $i += 10) {
      $end = [Math]::Min($i + 9, $items.Count - 1)
      $chunk = @($items[$i..$end])
      $records = @($chunk | ForEach-Object { [pscustomobject]@{ id = $_.record_id; fields = $_.fields } })
      $body = [pscustomobject]@{ records = $records; typecast = $false }
      $uri = 'https://api.airtable.com/v0/{0}/{1}' -f $script:BaseId, [System.Uri]::EscapeDataString($tableId)
      Invoke-At -Method 'PATCH' -Uri $uri -Body $body | Out-Null
    }
  }
}
function Verify-AfterValues { param([object[]]$Updates)
  $results = New-Object System.Collections.Generic.List[object]
  foreach ($u in $Updates) {
    $live = Get-RecordOrNull -TableId $u.table_id -RecordId $u.record_id
    if ($null -eq $live) { throw "Target record missing after update: $($u.record_id)" }
    foreach ($k in $u.fields.Keys) {
      $current = Get-PropValue $live.fields $k
      $expectedValue = $u.fields[$k]
      if (-not (Values-Equal $current $expectedValue)) { throw "After-readback mismatch for $($u.record_id) field $k. Expected '$expectedValue' got '$current'." }
      $results.Add([pscustomobject]@{ record_id=$u.record_id; table=$u.table; field=$k; value=$current }) | Out-Null
    }
  }
  return @($results.ToArray())
}

$OutDir = New-RunDir
$started = (Get-Date).ToUniversalTime().ToString('o')
try {
  $repo = [Environment]::GetEnvironmentVariable('DCOIR_REPO_ROOT','Machine')
  if ([string]::IsNullOrWhiteSpace($repo)) { throw 'DCOIR_REPO_ROOT is missing.' }
  $module = Join-Path $repo 'operator_tools\github_desktop_lane\modules\Dcoir.Airtable\Dcoir.Airtable.psm1'
  if (-not (Test-Path -LiteralPath $module -PathType Leaf)) { throw "Dcoir.Airtable module not found: $module" }
  Import-Module $module -Force
  $script:BaseId = Get-DcoirAirtableSystemEnvValue -Name 'DCOIR_AIRTABLE_BASE_ID' -Required
  $token = Get-DcoirAirtableSystemEnvValue -Name 'DCOIR_AIRTABLE_TOKEN' -Required
  $script:Headers = New-DcoirAirtableAuthHeader -ApiToken $token
  $payload = Build-Payload
  Validate-Payload $payload
  $updates = @($payload.A + $payload.B + $payload.C)
  Verify-BeforeValues $updates
  Write-JsonFile -Path (Join-Path $OutDir 'planned_payload.json') -Object $payload
  Apply-Updates $updates
  $after = Verify-AfterValues $updates
  $finished = (Get-Date).ToUniversalTime().ToString('o')
  $summary = [pscustomobject]@{
    request_id = $RequestId
    result = 'success'
    started_utc = $started
    finished_utc = $finished
    batches = [pscustomobject]@{
      A = [pscustomobject]@{ records=$payload.A.Count; cells=(Get-CellCount $payload.A) }
      B = [pscustomobject]@{ records=$payload.B.Count; cells=(Get-CellCount $payload.B); excluded_delete_queue_related_rows=$payload.excluded_delete_queue_related_rows.Count; ambiguous_result_rows=$payload.ambiguous_result_rows.Count }
      C = [pscustomobject]@{ records=$payload.C.Count; cells=(Get-CellCount $payload.C) }
    }
    total_records = $updates.Count
    total_cells = (Get-CellCount $updates)
    verification_cells = $after.Count
    delete_queue_scope = 'excluded'
    no_schema_changes = $true
    no_select_option_changes = $true
    no_delete_queue_records_touched = $true
  }
  Write-JsonFile -Path (Join-Path $OutDir 'execution_summary.json') -Object $summary
  Write-JsonFile -Path (Join-Path $OutDir 'after_readback_verification.json') -Object $after
  $summary | ConvertTo-Json -Depth 80
}
catch {
  $err = [pscustomobject]@{ request_id=$RequestId; result='failed'; started_utc=$started; failed_utc=(Get-Date).ToUniversalTime().ToString('o'); error_message=$_.Exception.Message; script_stack_trace=$_.ScriptStackTrace; output_folder=$OutDir }
  Write-JsonFile -Path (Join-Path $OutDir 'error_report.json') -Object $err
  $err | ConvertTo-Json -Depth 80
  exit 1
}
