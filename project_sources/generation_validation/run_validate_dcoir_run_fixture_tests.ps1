param(
  [string]$ValidatorPath = ".\validate_DCOIR_Run.ps1",
  [string]$OutputRoot = ".\generation_validation\out_validate_dcoir_run_fixtures"
)

Set-StrictMode -Version 2
$ErrorActionPreference = "Stop"

function Ensure-Directory {
  param([string]$Path)
  if (-not (Test-Path -LiteralPath $Path)) {
    New-Item -Path $Path -ItemType Directory -Force | Out-Null
  }
}

function Write-Text {
  param([string]$Path,[string]$Text)
  Ensure-Directory -Path (Split-Path -Parent $Path)
  Set-Content -LiteralPath $Path -Value $Text -Encoding UTF8
}

function New-BundleZip {
  param([string]$ZipPath,[string[]]$Paths)
  if (Test-Path -LiteralPath $ZipPath) {
    Remove-Item -LiteralPath $ZipPath -Force
  }
  $existingPaths = @($Paths | Where-Object { $_ -and (Test-Path -LiteralPath $_) })
  if (@($existingPaths).Count -eq 0) {
    throw "No input paths were available to create fixture zip: $ZipPath"
  }
  Compress-Archive -LiteralPath $existingPaths -DestinationPath $ZipPath -Force
}

function New-FixtureRun {
  param(
    [string]$Root,
    [string]$Name,
    [string]$AuditPolicyAccessStatus,
    [bool]$IsElevated,
    [int[]]$AuditExitCodes
  )

  $runRoot = Join-Path $Root ("DCOIR_{0}" -f $Name)
  $reportsDir = Join-Path $runRoot 'reports'
  $artifactsDir = Join-Path $runRoot 'final_artifacts'
  $bundleDir = Join-Path $runRoot 'bundles'
  Ensure-Directory $reportsDir
  Ensure-Directory $artifactsDir
  Ensure-Directory $bundleDir

  $executionContextPath = Join-Path $artifactsDir '99_COLLECTION_METADATA_execution_context.txt'
  $auditPolicyPath = Join-Path $artifactsDir '99_COLLECTION_METADATA_security_audit_policy.txt'
  $securityFilteredPath = Join-Path $artifactsDir '25_EVENT_TIMELINE_TEXT_security_filtered.txt'
  $securitySummaryPath = Join-Path $artifactsDir '25A_EVENT_TIMELINE_TEXT_security_high_signal_summary.txt'
  $parallelProofPath = Join-Path $artifactsDir '99_PARALLEL_EXECUTION_parallel_execution_proof.json.txt'
  $pidOnlyPath = Join-Path $artifactsDir '99_NETWORK_STATE_netstat_ano_supplemental.txt'
  $overviewPath = Join-Path $reportsDir 'DCOIR_ANALYST_OVERVIEW_TEST.txt'
  $baselinePath = Join-Path $reportsDir 'DCOIR_BASELINE_TEST.txt'
  $metadataPath = Join-Path $reportsDir 'DCOIR_METADATA_TEST.txt'
  $uploadSummaryPath = Join-Path $reportsDir 'DCOIR_UPLOAD_SUMMARY_TEST.txt'
  $budgetManifestPath = Join-Path $reportsDir 'DCOIR_ATTACHMENT_BUDGET_MANIFEST_TEST.json.txt'
  $bundlePath = Join-Path $bundleDir 'DCOIR_COLLECT_BUNDLE_TEST.zip'
  $manifestPath = Join-Path $runRoot 'manifest_collect.json'

  Write-Text -Path $executionContextPath -Text @"
EXECUTION_CONTEXT
UserContext=fixture\User
IsElevated=$IsElevated
Host=fixture-host
ProcessId=1234
PowerShellVersion=5.1
CurrentDirectory=C:\fixture
"@

  $auditBlocks = New-Object System.Collections.ArrayList
  $subcats = @('Logon','Logoff','Special Logon','Process Creation')
  for ($i = 0; $i -lt $subcats.Count; $i++) {
    $code = $AuditExitCodes[$i]
    [void]$auditBlocks.Add(@"
COMMAND=auditpol.exe /get /subcategory:$($subcats[$i])
EXIT_CODE=$code
$($subcats[$i])
  Success and Failure
"@)
  }
  Write-Text -Path $auditPolicyPath -Text ($auditBlocks -join ([Environment]::NewLine + [Environment]::NewLine))

  if ($AuditPolicyAccessStatus -eq 'PRIVILEGE_REQUIRED_NON_ELEVATED') {
    Write-Text -Path $securityFilteredPath -Text 'Security event query returned no matching events in the current non-elevated collection context. Verify the same query in an elevated shell before concluding the window is empty.'
    Write-Text -Path $securitySummaryPath -Text 'Security event query returned no matching events in the current non-elevated collection context. Verify the same query in an elevated shell before concluding the window is empty.'
  } else {
    Write-Text -Path $securityFilteredPath -Text @"
CHANNEL=Security
WINDOW_HOURS=24
EVENT_COUNT=2
"@
    Write-Text -Path $securitySummaryPath -Text @"
SECURITY_HIGH_SIGNAL_SUMMARY
WINDOW_HOURS=24
RAW_EVENT_COUNT=2
INTERESTING_EVENT_COUNT=2
SUPPRESSED_EVENT_COUNT=0
"@
  }

  Write-Text -Path $parallelProofPath -Text '{"proof_status":"OVERLAP_CONFIRMED","worker_count":4}'
  Write-Text -Path $pidOnlyPath -Text 'Active Connections'
  Write-Text -Path $overviewPath -Text 'Analyst overview fixture'
  Write-Text -Path $baselinePath -Text 'Baseline fixture'
  Write-Text -Path $metadataPath -Text "Metadata fixture`nAuditPolicyAccessStatus=$AuditPolicyAccessStatus"
  Write-Text -Path $uploadSummaryPath -Text 'Upload summary fixture'
  Write-Text -Path $budgetManifestPath -Text '{"budget":{"safe":true}}'

  New-BundleZip -ZipPath $bundlePath -Paths @($overviewPath, $auditPolicyPath, $executionContextPath)

  $manifest = [ordered]@{
    files = @(
      $baselinePath,
      $metadataPath,
      $overviewPath,
      $executionContextPath,
      $auditPolicyPath,
      $securityFilteredPath,
      $securitySummaryPath,
      $parallelProofPath,
      $pidOnlyPath,
      $uploadSummaryPath,
      $budgetManifestPath
    )
    extra = [ordered]@{
      execution_context = $executionContextPath
      security_audit_policy = $auditPolicyPath
      audit_policy_access_status = $AuditPolicyAccessStatus
      security_filtered = $securityFilteredPath
      security_high_signal_summary = $securitySummaryPath
      netstat_owner_aware_status = 'OWNER_AWARE_REQUIRES_ELEVATION'
      netstat_pid_only = $pidOnlyPath
      is_elevated = [string]$IsElevated
      analyst_overview = $overviewPath
      parallel_execution_proof = $parallelProofPath
      collect_bundle = $bundlePath
      upload_summary = $uploadSummaryPath
      attachment_budget_manifest = $budgetManifestPath
      default_gemini_upload_set_status = 'SAFE_DEFAULT_SET'
    }
  }
  $manifest | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $manifestPath -Encoding UTF8
  return $runRoot
}

function Invoke-ValidatorExpectation {
  param(
    [string]$CaseName,
    [string]$RunRoot,
    [bool]$ShouldPass,
    [System.Collections.ArrayList]$Results
  )

  $stdoutPath = Join-Path $OutputRoot ($CaseName + '.stdout.txt')
  $stderrPath = Join-Path $OutputRoot ($CaseName + '.stderr.txt')

  $process = Start-Process -FilePath 'powershell.exe' `
    -ArgumentList @('-NoProfile','-ExecutionPolicy','Bypass','-File',$ValidatorPath,'-RunRoot',$RunRoot) `
    -NoNewWindow -Wait -PassThru `
    -RedirectStandardOutput $stdoutPath `
    -RedirectStandardError $stderrPath

  $stdout = if (Test-Path -LiteralPath $stdoutPath) { Get-Content -LiteralPath $stdoutPath -Raw } else { '' }
  $stderr = if (Test-Path -LiteralPath $stderrPath) { Get-Content -LiteralPath $stderrPath -Raw } else { '' }
  $passed = ($process.ExitCode -eq 0)

  [void]$Results.Add([pscustomobject]@{
    case = $CaseName
    run_root = $RunRoot
    expected = $(if ($ShouldPass) { 'PASS' } else { 'FAIL' })
    actual = $(if ($passed) { 'PASS' } else { 'FAIL' })
    exit_code = [int]$process.ExitCode
    stdout_path = $stdoutPath
    stderr_path = $stderrPath
  })

  if ($passed -ne $ShouldPass) {
    throw "Validator expectation failed for $CaseName. Expected pass=$ShouldPass, actual exit code=$($process.ExitCode)."
  }

  if ($ShouldPass -and ($stdout -notmatch 'FAILURE_COUNT=0')) {
    throw "Validator success case $CaseName did not report FAILURE_COUNT=0."
  }

  if ((-not $ShouldPass) -and ($stdout -notmatch 'FAILURE_COUNT=')) {
    throw "Validator failure case $CaseName did not emit FAILURE_COUNT."
  }
}

Ensure-Directory -Path $OutputRoot

if (-not (Test-Path -LiteralPath $ValidatorPath)) {
  throw "Validator script not found: $ValidatorPath"
}

$results = New-Object System.Collections.ArrayList

$fixtureRoot = Join-Path $OutputRoot 'fixtures'
Ensure-Directory -Path $fixtureRoot

$case1 = New-FixtureRun -Root $fixtureRoot -Name 'fixture_audit_policy_ok' -AuditPolicyAccessStatus 'OK' -IsElevated $true -AuditExitCodes @(0,0,0,0)
$case2 = New-FixtureRun -Root $fixtureRoot -Name 'fixture_audit_policy_privilege_required' -AuditPolicyAccessStatus 'PRIVILEGE_REQUIRED_NON_ELEVATED' -IsElevated $false -AuditExitCodes @(1314,1314,1314,1314)
$case3 = New-FixtureRun -Root $fixtureRoot -Name 'fixture_audit_policy_mismatch_should_fail' -AuditPolicyAccessStatus 'OK' -IsElevated $false -AuditExitCodes @(1314,1314,1314,1314)

Invoke-ValidatorExpectation -CaseName 'case_ok' -RunRoot $case1 -ShouldPass $true -Results $results
Invoke-ValidatorExpectation -CaseName 'case_privilege_required' -RunRoot $case2 -ShouldPass $true -Results $results
Invoke-ValidatorExpectation -CaseName 'case_mismatch_should_fail' -RunRoot $case3 -ShouldPass $false -Results $results

$summary = [ordered]@{
  validator_path = (Resolve-Path -LiteralPath $ValidatorPath).Path
  output_root = (Resolve-Path -LiteralPath $OutputRoot).Path
  result_count = @($results).Count
  results = @($results)
}

$summaryPath = Join-Path $OutputRoot 'summary.json'
$summary | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $summaryPath -Encoding UTF8
Write-Output "VALIDATOR_FIXTURE_TESTS=PASS"
Write-Output "SUMMARY_PATH=$summaryPath"
