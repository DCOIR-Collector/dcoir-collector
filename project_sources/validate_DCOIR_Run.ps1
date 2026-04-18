param(
  [string]$RunRoot,
  [string]$ManifestPath,
  [switch]$PushMode,
  [switch]$Json
)

Set-StrictMode -Version 2
$ErrorActionPreference = 'Stop'

function Get-LatestRunRoot {
  param([string]$BasePath)
  $dirs = Get-ChildItem -LiteralPath $BasePath -Directory -ErrorAction Stop |
    Where-Object { $_.Name -like 'DCOIR_*' } |
    Sort-Object LastWriteTime -Descending
  if (-not $dirs) { throw "No DCOIR run directories found under $BasePath" }
  return $dirs[0].FullName
}

function Add-CheckResult {
  param(
    [System.Collections.ArrayList]$Results,
    [string]$Name,
    [string]$Status,
    [string]$Message,
    [string]$Path
  )
  [void]$Results.Add([pscustomobject]@{
    Name = $Name
    Status = $Status
    Message = $Message
    Path = $Path
  })
}

function Test-TextContains {
  param([string]$Path,[string[]]$Patterns)
  if (-not (Test-Path -LiteralPath $Path)) { return $false }
  $text = Get-Content -LiteralPath $Path -Raw
  foreach ($pattern in $Patterns) {
    if ($text -notmatch [regex]::Escape($pattern)) { return $false }
  }
  return $true
}

$results = New-Object System.Collections.ArrayList

if (-not $ManifestPath) {
  if (-not $RunRoot) {
    $RunRoot = Get-LatestRunRoot -BasePath (Join-Path (Get-Location).Path '..')
  }
  $ManifestPath = Join-Path $RunRoot 'manifest_collect.json'
} elseif (-not $RunRoot) {
  $RunRoot = Split-Path -Parent $ManifestPath
}

if (-not (Test-Path -LiteralPath $ManifestPath)) {
  throw "Manifest not found: $ManifestPath"
}

$manifest = Get-Content -LiteralPath $ManifestPath -Raw | ConvertFrom-Json
$files = @($manifest.files)
$extra = $manifest.extra

$requiredKeys = @(
  'execution_context',
  'security_audit_policy',
  'security_filtered',
  'security_high_signal_summary',
  'netstat_owner_aware_status',
  'is_elevated',
  'analyst_overview'
)

foreach ($key in $requiredKeys) {
  if ($null -ne $extra.$key -and -not [string]::IsNullOrWhiteSpace([string]$extra.$key)) {
    Add-CheckResult -Results $results -Name ("manifest_extra_{0}" -f $key) -Status 'PASS' -Message 'Present in manifest extra.' -Path ([string]$extra.$key)
  } else {
    Add-CheckResult -Results $results -Name ("manifest_extra_{0}" -f $key) -Status 'FAIL' -Message 'Missing in manifest extra.' -Path ''
  }
}

foreach ($pathKey in @('execution_context','security_audit_policy','security_filtered','security_high_signal_summary','analyst_overview','parallel_execution_proof','netstat_pid_only')) {
  $candidate = [string]$extra.$pathKey
  if ([string]::IsNullOrWhiteSpace($candidate)) {
    if ($pathKey -eq 'netstat_pid_only' -or $pathKey -eq 'parallel_execution_proof') {
      Add-CheckResult -Results $results -Name ("artifact_{0}" -f $pathKey) -Status 'INFO' -Message 'Optional artifact not present.' -Path ''
    } else {
      Add-CheckResult -Results $results -Name ("artifact_{0}" -f $pathKey) -Status 'FAIL' -Message 'Required artifact path missing from manifest.' -Path ''
    }
    continue
  }
  if (Test-Path -LiteralPath $candidate) {
    Add-CheckResult -Results $results -Name ("artifact_{0}" -f $pathKey) -Status 'PASS' -Message 'Artifact exists.' -Path $candidate
  } else {
    Add-CheckResult -Results $results -Name ("artifact_{0}" -f $pathKey) -Status 'FAIL' -Message 'Artifact path does not exist.' -Path $candidate
  }
}

$executionContextPath = [string]$extra.execution_context
if ($executionContextPath -and (Test-Path -LiteralPath $executionContextPath)) {
  if (Test-TextContains -Path $executionContextPath -Patterns @('EXECUTION_CONTEXT','IsElevated=')) {
    Add-CheckResult -Results $results -Name 'execution_context_content' -Status 'PASS' -Message 'Execution context artifact contains expected markers.' -Path $executionContextPath
  } else {
    Add-CheckResult -Results $results -Name 'execution_context_content' -Status 'FAIL' -Message 'Execution context artifact is missing expected markers.' -Path $executionContextPath
  }
}

$auditPolicyPath = [string]$extra.security_audit_policy
if ($auditPolicyPath -and (Test-Path -LiteralPath $auditPolicyPath)) {
  if (Test-TextContains -Path $auditPolicyPath -Patterns @('Logon','Special Logon','Process Creation')) {
    Add-CheckResult -Results $results -Name 'security_audit_policy_content' -Status 'PASS' -Message 'Audit policy artifact contains expected subcategories.' -Path $auditPolicyPath
  } else {
    Add-CheckResult -Results $results -Name 'security_audit_policy_content' -Status 'FAIL' -Message 'Audit policy artifact is missing expected subcategories.' -Path $auditPolicyPath
  }
}

$netstatStatus = [string]$extra.netstat_owner_aware_status
if ($netstatStatus -eq 'OWNER_AWARE_OK' -or $netstatStatus -eq 'OWNER_AWARE_REQUIRES_ELEVATION' -or $netstatStatus -eq 'OWNER_AWARE_FAILED') {
  Add-CheckResult -Results $results -Name 'netstat_owner_aware_status_value' -Status 'PASS' -Message ("Recognized owner-aware netstat status: {0}" -f $netstatStatus) -Path ''
} else {
  Add-CheckResult -Results $results -Name 'netstat_owner_aware_status_value' -Status 'FAIL' -Message ("Unexpected owner-aware netstat status: {0}" -f $netstatStatus) -Path ''
}

$securityFilteredPath = [string]$extra.security_filtered
if ($securityFilteredPath -and (Test-Path -LiteralPath $securityFilteredPath)) {
  $securityFilteredText = Get-Content -LiteralPath $securityFilteredPath -Raw
  if ($securityFilteredText -match 'CHANNEL=Security' -or $securityFilteredText -match 'Security event query returned no matching events in the current non-elevated collection context') {
    Add-CheckResult -Results $results -Name 'security_filtered_semantics' -Status 'PASS' -Message 'Security filtered artifact expresses either collected events or explicit non-elevated visibility limitation.' -Path $securityFilteredPath
  } else {
    Add-CheckResult -Results $results -Name 'security_filtered_semantics' -Status 'FAIL' -Message 'Security filtered artifact does not express expected collected or diagnostic semantics.' -Path $securityFilteredPath
  }
}

$securitySummaryPath = [string]$extra.security_high_signal_summary
if ($securitySummaryPath -and (Test-Path -LiteralPath $securitySummaryPath)) {
  $securitySummaryText = Get-Content -LiteralPath $securitySummaryPath -Raw
  if ($securitySummaryText -match 'SECURITY_HIGH_SIGNAL_SUMMARY' -or $securitySummaryText -match 'Security event query returned no matching events in the current non-elevated collection context') {
    Add-CheckResult -Results $results -Name 'security_summary_semantics' -Status 'PASS' -Message 'Security summary artifact expresses either high-signal summary or explicit non-elevated visibility limitation.' -Path $securitySummaryPath
  } else {
    Add-CheckResult -Results $results -Name 'security_summary_semantics' -Status 'FAIL' -Message 'Security summary artifact does not express expected collected or diagnostic semantics.' -Path $securitySummaryPath
  }
}

$parallelProofPath = [string]$extra.parallel_execution_proof
if ($parallelProofPath -and (Test-Path -LiteralPath $parallelProofPath)) {
  $proofText = Get-Content -LiteralPath $parallelProofPath -Raw
  if ($proofText -match 'proof_status' -and $proofText -match 'worker_count') {
    Add-CheckResult -Results $results -Name 'parallel_proof_content' -Status 'PASS' -Message 'Parallel proof artifact contains proof markers.' -Path $parallelProofPath
  } else {
    Add-CheckResult -Results $results -Name 'parallel_proof_content' -Status 'FAIL' -Message 'Parallel proof artifact is missing proof markers.' -Path $parallelProofPath
  }
}

$bundlePath = [string]$extra.collect_bundle
if (-not $bundlePath) { $bundlePath = [string]$manifest.extra.collect_bundle }
if ($bundlePath -and (Test-Path -LiteralPath $bundlePath)) {
  Add-Type -AssemblyName System.IO.Compression.FileSystem
  $zip = [System.IO.Compression.ZipFile]::OpenRead($bundlePath)
  try {
    $entryNames = @($zip.Entries | Select-Object -ExpandProperty FullName)
    $mustContain = @('DCOIR_ANALYST_OVERVIEW','security_audit_policy','execution_context')
    foreach ($token in $mustContain) {
      if ($entryNames | Where-Object { $_ -match [regex]::Escape($token) }) {
        Add-CheckResult -Results $results -Name ("bundle_contains_{0}" -f $token) -Status 'PASS' -Message 'Bundle contains expected diagnostic/overview content.' -Path $bundlePath
      } else {
        Add-CheckResult -Results $results -Name ("bundle_contains_{0}" -f $token) -Status 'FAIL' -Message 'Bundle is missing expected diagnostic/overview content.' -Path $bundlePath
      }
    }
  } finally {
    $zip.Dispose()
  }
}

$summary = [pscustomobject]@{
  RunRoot = $RunRoot
  ManifestPath = $ManifestPath
  Mode = $(if ($PushMode) { 'validate-on-push' } else { 'validate-on-run' })
  Results = @($results)
  FailureCount = @($results | Where-Object { $_.Status -eq 'FAIL' }).Count
}

if ($Json) {
  $summary | ConvertTo-Json -Depth 6
} else {
  Write-Output ("MODE={0}" -f $summary.Mode)
  Write-Output ("RUN_ROOT={0}" -f $summary.RunRoot)
  Write-Output ("MANIFEST_PATH={0}" -f $summary.ManifestPath)
  Write-Output ("FAILURE_COUNT={0}" -f $summary.FailureCount)
  foreach ($row in $summary.Results) {
    Write-Output ("[{0}] {1} :: {2}{3}" -f $row.Status, $row.Name, $row.Message, $(if ($row.Path) { " PATH=$($row.Path)" } else { '' }))
  }
}

if ($summary.FailureCount -gt 0) { exit 1 }
exit 0
