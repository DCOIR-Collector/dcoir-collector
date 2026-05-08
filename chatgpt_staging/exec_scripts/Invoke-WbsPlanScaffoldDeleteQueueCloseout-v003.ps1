[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version 2.0

$RequestId = 'exec-20260508-cleanup-plan-scaffold-delete-queue-closeout-003'
$PlanKey = 'PLAN-AIRTABLE-CLEANUP-RESTRUCTURE'
$Now = (Get-Date).ToUniversalTime().ToString('o')

function Write-JsonFile {
  param([string]$Path, $Object, [int]$Depth = 80)
  $json = $Object | ConvertTo-Json -Depth $Depth
  [System.IO.File]::WriteAllText($Path, $json, [System.Text.UTF8Encoding]::new($false))
}
function New-RunDir {
  $downloads = [Environment]::GetEnvironmentVariable('DCOIR_DOWNLOADS_DIR','Machine')
  if ([string]::IsNullOrWhiteSpace($downloads)) { throw 'DCOIR_DOWNLOADS_DIR is missing.' }
  $stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
  $out = Join-Path $downloads ("cleanup_plan_scaffold_delete_queue_closeout_v003_{0}" -f $stamp)
  New-Item -ItemType Directory -Force -Path $out | Out-Null
  return $out
}
function Get-PropValue {
  param($Object,[string]$Name)
  if ($null -eq $Object) { return $null }
  $p = $Object.PSObject.Properties[$Name]
  if ($null -eq $p) { return $null }
  return $p.Value
}
function Invoke-At {
  param([string]$Method,[string]$Uri,$Body=$null)
  $args = @{ Method=$Method; Uri=$Uri; Headers=$script:Headers; ErrorAction='Stop' }
  if ($null -ne $Body) {
    $args['Body'] = ($Body | ConvertTo-Json -Depth 80)
    $args['ContentType'] = 'application/json'
  }
  return Invoke-RestMethod @args
}
function Get-AllRecords {
  param([string]$TableId,[string]$FilterFormula=$null)
  $all = New-Object System.Collections.Generic.List[object]
  $offset = $null
  do {
    $uri = 'https://api.airtable.com/v0/{0}/{1}?pageSize=100' -f $script:BaseId, [System.Uri]::EscapeDataString($TableId)
    if (-not [string]::IsNullOrWhiteSpace($FilterFormula)) { $uri += '&filterByFormula=' + [System.Uri]::EscapeDataString($FilterFormula) }
    if (-not [string]::IsNullOrWhiteSpace($offset)) { $uri += '&offset=' + [System.Uri]::EscapeDataString($offset) }
    $resp = Invoke-At -Method 'GET' -Uri $uri
    foreach ($r in @($resp.records)) { $all.Add($r) | Out-Null }
    $offset = Get-PropValue $resp 'offset'
  } while (-not [string]::IsNullOrWhiteSpace($offset))
  return @($all.ToArray())
}
function Get-RecordOrNull {
  param([string]$TableId,[string]$RecordId)
  $uri = 'https://api.airtable.com/v0/{0}/{1}/{2}' -f $script:BaseId, [System.Uri]::EscapeDataString($TableId), $RecordId
  try { return Invoke-At -Method 'GET' -Uri $uri }
  catch {
    if ($_.Exception.Response -and [int]$_.Exception.Response.StatusCode -eq 404) { return $null }
    throw
  }
}
function Add-QueueRecords {
  param([object[]]$QueueRows)
  $created = New-Object System.Collections.Generic.List[object]
  for ($i=0; $i -lt $QueueRows.Count; $i += 10) {
    $end = [Math]::Min($i + 9, $QueueRows.Count - 1)
    $chunk = @($QueueRows[$i..$end])
    $body = [pscustomobject]@{ records = @($chunk | ForEach-Object { [pscustomobject]@{ fields = $_ } }); typecast = $false }
    $uri = 'https://api.airtable.com/v0/{0}/{1}' -f $script:BaseId, [System.Uri]::EscapeDataString($script:DeleteQueueTable)
    $resp = Invoke-At -Method 'POST' -Uri $uri -Body $body
    foreach ($r in @($resp.records)) { $created.Add($r) | Out-Null }
  }
  return @($created.ToArray())
}

$OutDir = New-RunDir
try {
  $repo = [Environment]::GetEnvironmentVariable('DCOIR_REPO_ROOT','Machine')
  if ([string]::IsNullOrWhiteSpace($repo)) { throw 'DCOIR_REPO_ROOT is missing.' }
  $module = Join-Path $repo 'operator_tools\github_desktop_lane\modules\Dcoir.Airtable\Dcoir.Airtable.psm1'
  if (-not (Test-Path -LiteralPath $module -PathType Leaf)) { throw "Dcoir.Airtable module not found: $module" }
  Import-Module $module -Force
  $script:BaseId = Get-DcoirAirtableSystemEnvValue -Name 'DCOIR_AIRTABLE_BASE_ID' -Required
  $token = Get-DcoirAirtableSystemEnvValue -Name 'DCOIR_AIRTABLE_TOKEN' -Required
  $script:Headers = New-DcoirAirtableAuthHeader -ApiToken $token

  $planTable = 'tblBcp5FyMIfOm7Xe'
  $wbsTable = 'tblRxTmpW0VunQlUK'
  $scaffoldTable = 'tblvtcId7PiFKvfKO'
  $script:DeleteQueueTable = 'tbl1lMz5N6n7zShO0'

  $safePlanKey = $PlanKey.Replace("'", "\\'")
  $planRows = @(Get-AllRecords -TableId $planTable -FilterFormula ("{plan_id}='" + $safePlanKey + "'"))
  $wbsRows = @(Get-AllRecords -TableId $wbsTable -FilterFormula ("{plan_key}='" + $safePlanKey + "'"))
  $scaffoldRows = @(Get-AllRecords -TableId $scaffoldTable -FilterFormula ("{plan_key}='" + $safePlanKey + "'"))

  if ($planRows.Count -ne 1) { throw "Expected exactly 1 plan row for $PlanKey, found $($planRows.Count)." }
  if ($wbsRows.Count -lt 150) { throw "Expected at least 150 WBS rows for $PlanKey, found $($wbsRows.Count)." }
  if ($scaffoldRows.Count -ne 5) { throw "Expected exactly 5 scaffold rows for $PlanKey, found $($scaffoldRows.Count)." }

  $targets = New-Object System.Collections.Generic.List[object]
  foreach ($r in $wbsRows) { $targets.Add([pscustomobject]@{ table='DCOIR Cleanup WBS'; table_id=$wbsTable; record_id=$r.id; key=(Get-PropValue $r.fields 'wbs_key') }) | Out-Null }
  foreach ($r in $scaffoldRows) { $targets.Add([pscustomobject]@{ table='DCOIR Cleanup Scaffold Registry'; table_id=$scaffoldTable; record_id=$r.id; key=(Get-PropValue $r.fields 'scaffold_key') }) | Out-Null }
  foreach ($r in $planRows) { $targets.Add([pscustomobject]@{ table='Plans'; table_id=$planTable; record_id=$r.id; key=(Get-PropValue $r.fields 'plan_id') }) | Out-Null }

  $targetArray = @($targets.ToArray())
  $queueRows = @($targetArray | ForEach-Object {
    @{
      'delete_key' = ('DQ-CLOSEOUT-{0}-{1}' -f $PlanKey, $_.record_id)
      'target_table' = $_.table
      'target_record_id' = $_.record_id
      'reason' = ('Approved current cleanup plan closeout. Target belongs to closed plan {0}; durable closeout checkpoint retained outside deletion set; next work moves to new database redesign plan.' -f $PlanKey)
      'requested_by' = 'ChatGPT / operator-approved closeout'
      'requested_at' = $Now
      'verification_notes' = ('Queued by {0}. Source key: {1}. Scope: closed plan scaffold cleanup only.' -f $RequestId, $_.key)
      'approved_to_delete' = $true
      'retention_class' = 'operational'
      'delete_stage' = 'pending'
    }
  })

  if ($queueRows.Count -ne $targetArray.Count) { throw "Queue row count mismatch. Targets=$($targetArray.Count), queueRows=$($queueRows.Count)." }
  if ($queueRows.Count -lt 150) { throw "Unexpectedly small queue set: $($queueRows.Count)." }

  Write-JsonFile -Path (Join-Path $OutDir 'target_records.json') -Object $targetArray
  Write-JsonFile -Path (Join-Path $OutDir 'planned_delete_queue_rows.json') -Object $queueRows

  $created = @(Add-QueueRecords -QueueRows $queueRows)
  if ($created.Count -ne $queueRows.Count) { throw "Created Delete Queue count mismatch. Expected $($queueRows.Count), got $($created.Count)." }

  Start-Sleep -Seconds 20

  $sampleChecks = New-Object System.Collections.Generic.List[object]
  foreach ($t in @($targetArray | Select-Object -First 20)) {
    $live = Get-RecordOrNull -TableId $t.table_id -RecordId $t.record_id
    $sampleChecks.Add([pscustomobject]@{ table=$t.table; record_id=$t.record_id; still_present=($null -ne $live) }) | Out-Null
  }

  $summary = [pscustomobject]@{
    request_id = $RequestId
    result = 'success'
    plan_key = $PlanKey
    queue_rows_created = $created.Count
    targets = [pscustomobject]@{ plans=$planRows.Count; wbs=$wbsRows.Count; scaffold=$scaffoldRows.Count; total=$targetArray.Count }
    approved_to_delete = $true
    delete_stage = 'pending'
    checkpoint_preserved = 'CHK-DCOIR-CLEANUP-PLAN-CLOSEOUT-DB-REDESIGN-NEXT-20260508-1759Z'
    sample_target_checks_after_wait = @($sampleChecks.ToArray())
    note = 'Delete Queue automation may remove target and queue rows asynchronously after insertion.'
  }
  Write-JsonFile -Path (Join-Path $OutDir 'execution_summary.json') -Object $summary
  Write-JsonFile -Path (Join-Path $OutDir 'created_delete_queue_rows.json') -Object $created
  $summary | ConvertTo-Json -Depth 80
}
catch {
  $err = [pscustomobject]@{ request_id=$RequestId; result='failed'; error_message=$_.Exception.Message; script_stack_trace=$_.ScriptStackTrace; output_folder=$OutDir }
  Write-JsonFile -Path (Join-Path $OutDir 'error_report.json') -Object $err
  $err | ConvertTo-Json -Depth 80
  exit 1
}
