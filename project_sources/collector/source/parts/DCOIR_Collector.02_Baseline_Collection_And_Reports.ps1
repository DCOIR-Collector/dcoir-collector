<#
.SYNOPSIS
DCOIR collector baseline collection and reporting helpers.

.DESCRIPTION
Builds the baseline collection surface, including execution-context and audit-policy
artifacts, host, identity, process, network, persistence, security, and event-log
artifacts, plus the analyst-facing baseline report, metadata report, upload summary, and
attachment-budget manifest.

.FILE NAME
DCOIR_Collector.02_Baseline_Collection_And_Reports.ps1

.INPUTS
Collector state and tool-map hashtables, current tier and hour settings, artifact paths,
and collector-global notes, errors, recommendations, and targeted runtime settings.

.OUTPUTS
Baseline and metadata report text, upload-summary artifacts, attachment-budget manifest
artifacts, and helper return values used by the collector runtime.
#>

<#
.SYNOPSIS
Returns the Gemini upload budget thresholds used by the collector.

.DESCRIPTION
Defines the hard and safe per-file and total-size thresholds used to decide whether the
recommended Gemini upload set fits comfortably within the environment budget.

.FUNCTION NAME
Get-CollectorUploadBudget

.INPUTS
No direct parameters.

.OUTPUTS
Hashtable containing hard and safe per-file and total-size budget values in KB.
#>
function Get-CollectorUploadBudget {
  return @{
    HardPerFileKB = 1000
    HardTotalKB = 2000
    SafePerFileKB = 900
    SafeTotalKB = 1800
  }
}

<#
.SYNOPSIS
Returns the size of one file in KB.

.DESCRIPTION
Checks whether the file exists and returns a rounded-up KB size for the file. Returns
zero when the path does not exist.

.FUNCTION NAME
Get-FileSizeKB

.INPUTS
Path string for the file to inspect.

.OUTPUTS
Integer file size in KB.
#>
function Get-FileSizeKB {
  param([string]$Path)
  if (-not (Test-Path -LiteralPath $Path)) { return 0 }
  return [int][Math]::Ceiling(((Get-Item -LiteralPath $Path -ErrorAction Stop).Length) / 1KB)
}

<#
.SYNOPSIS
Returns the SHA256 hash for one file when available.

.DESCRIPTION
Computes a SHA256 digest for provenance and reconstruction metadata. Returns an empty
string when the path is blank, missing, or cannot be hashed.

.FUNCTION NAME
Get-FileSha256

.INPUTS
Path string for the file to inspect.

.OUTPUTS
SHA256 hash string or an empty string.
#>
function Get-FileSha256 {
  param([string]$Path)
  if ([string]::IsNullOrWhiteSpace($Path) -or -not (Test-Path -LiteralPath $Path)) { return "" }
  try {
    return (Get-FileHash -LiteralPath $Path -Algorithm SHA256 -ErrorAction Stop).Hash
  } catch {
    Add-CollectorError ("Failed to hash file [{0}]: {1}" -f $Path, $_.Exception.Message)
    return ""
  }
}

<#
.SYNOPSIS
Chooses a UTF-8 safe byte length for one upload-safe chunk.

.DESCRIPTION
Returns a chunk length that stays within the target byte budget without ending in the
middle of a UTF-8 multibyte character whenever the source bytes are valid UTF-8.

.FUNCTION NAME
Get-Utf8SafeChunkLength

.INPUTS
Source byte array, current offset, and target chunk byte count.

.OUTPUTS
Integer byte length for the next chunk.
#>
function Get-Utf8SafeChunkLength {
  param([byte[]]$Bytes,[int]$Offset,[int]$TargetBytes)

  $remaining = $Bytes.Length - $Offset
  if ($remaining -le 0) { return 0 }
  $length = [Math]::Min($TargetBytes, $remaining)
  if (($Offset + $length) -ge $Bytes.Length) { return $length }

  $end = $Offset + $length
  $lead = $end - 1
  while (($lead -gt $Offset) -and (($Bytes[$lead] -band 0xC0) -eq 0x80)) { $lead -= 1 }
  $leadByte = $Bytes[$lead]

  if (($leadByte -band 0x80) -eq 0) { return $length }
  if (($leadByte -band 0xE0) -eq 0xC0) { $charLength = 2 }
  elseif (($leadByte -band 0xF0) -eq 0xE0) { $charLength = 3 }
  elseif (($leadByte -band 0xF8) -eq 0xF0) { $charLength = 4 }
  else { return $length }

  if (($lead + $charLength) -le $end) { return $length }
  $safeLength = $lead - $Offset
  if ($safeLength -gt 0) { return $safeLength }
  return [Math]::Min($charLength, $remaining)
}

<#
.SYNOPSIS
Splits a real text artifact into upload-safe chunk companions.

.DESCRIPTION
Creates ordered byte-preserving chunks that can be concatenated to reconstruct the original
artifact exactly. The source artifact is preserved; this helper writes derivative chunk
companions plus metadata used by the aggregate upload-safe chunk manifest.

.FUNCTION NAME
Split-TextArtifactIntoUploadSafeChunks

.INPUTS
Source artifact path, artifact directory, source key, target chunk size, and origin label.

.OUTPUTS
Ordered hashtable describing chunk paths, sizes, hashes, source provenance, and reconstruction.
#>
function Split-TextArtifactIntoUploadSafeChunks {
  [CmdletBinding(SupportsShouldProcess=$true)]
  param(
    [string]$SourcePath,
    [string]$ArtifactsDir,
    [string]$SourceKey,
    [int]$TargetChunkKB,
    [string]$Origin = 'collector_production_upload_safe'
  )

  $chunkPaths = New-Object System.Collections.ArrayList
  $chunkSizes = New-Object System.Collections.ArrayList
  $chunkSha256 = New-Object System.Collections.ArrayList
  $targetBytes = [Math]::Max(1, $TargetChunkKB) * 1024
  $sourceBytes = [System.IO.File]::ReadAllBytes($SourcePath)
  $safeKey = ($SourceKey -replace '[\/:*?"<>| ]','_')
  $chunkIndex = 1
  $offset = 0

  if ($sourceBytes.Length -eq 0) {
    $chunkPath = Join-Path $ArtifactsDir ("90_UPLOAD_SAFE_CHUNKS_{0}_chunk_{1:000}.txt" -f $safeKey, $chunkIndex)
    if ($PSCmdlet.ShouldProcess($chunkPath, 'Write upload-safe empty chunk companion')) {
      [System.IO.File]::WriteAllBytes($chunkPath, [byte[]]@())
      [void]$chunkPaths.Add($chunkPath)
      [void]$chunkSizes.Add((Get-FileSizeKB -Path $chunkPath))
      [void]$chunkSha256.Add((Get-FileSha256 -Path $chunkPath))
    } elseif ($WhatIfPreference) {
      return $null
    } else {
      throw ("Upload-safe chunk write was skipped before completing chunk set: {0}" -f $chunkPath)
    }
  }

  while ($offset -lt $sourceBytes.Length) {
    $length = Get-Utf8SafeChunkLength -Bytes $sourceBytes -Offset $offset -TargetBytes $targetBytes
    if ($length -le 0) { $length = [Math]::Min($targetBytes, ($sourceBytes.Length - $offset)) }
    $chunkBytes = New-Object byte[] $length
    [Array]::Copy($sourceBytes, $offset, $chunkBytes, 0, $length)
    $chunkPath = Join-Path $ArtifactsDir ("90_UPLOAD_SAFE_CHUNKS_{0}_chunk_{1:000}.txt" -f $safeKey, $chunkIndex)
    if ($PSCmdlet.ShouldProcess($chunkPath, 'Write upload-safe chunk companion')) {
      [System.IO.File]::WriteAllBytes($chunkPath, $chunkBytes)
      [void]$chunkPaths.Add($chunkPath)
      [void]$chunkSizes.Add((Get-FileSizeKB -Path $chunkPath))
      [void]$chunkSha256.Add((Get-FileSha256 -Path $chunkPath))
    } elseif ($WhatIfPreference) {
      return $null
    } else {
      throw ("Upload-safe chunk write was skipped before completing chunk set: {0}" -f $chunkPath)
    }
    $offset += $length
    $chunkIndex += 1
  }

  return [ordered]@{
    origin = $Origin
    source_artifact_key = $SourceKey
    source_path = $SourcePath
    source_size_kb = Get-FileSizeKB -Path $SourcePath
    source_size_bytes = $sourceBytes.Length
    source_sha256 = Get-FileSha256 -Path $SourcePath
    target_chunk_kb = $TargetChunkKB
    chunk_count = @($chunkPaths).Count
    chunk_paths = @($chunkPaths)
    chunk_file_sizes_kb = @($chunkSizes)
    chunk_sha256 = @($chunkSha256)
    reconstruction_order = 'Concatenate chunk_paths in listed order as bytes to reconstruct the original source artifact exactly.'
  }
}
<#
.SYNOPSIS
Creates upload-safe chunk companions for selected oversized real artifacts.

.DESCRIPTION
Detects selected human-readable artifact keys that exceed the configured safe per-file
budget, writes ordered chunk companions, and returns manifest rows for the normal collect
handoff surfaces.

.FUNCTION NAME
New-ProductionUploadSafeChunkCompanions

.INPUTS
Collector state, artifact map, and upload budget.

.OUTPUTS
Array of ordered manifest rows.
#>
function New-ProductionUploadSafeChunkCompanions {
  [CmdletBinding()]
  param([hashtable]$State,[hashtable]$ArtifactMap,[hashtable]$Budget)

  $rows = New-Object System.Collections.ArrayList
  foreach ($key in @('security_filtered','powershell_operational_filtered','taskscheduler_operational_filtered')) {
    if (-not $ArtifactMap.ContainsKey($key)) { continue }
    $sourcePath = [string]$ArtifactMap[$key]
    if ([string]::IsNullOrWhiteSpace($sourcePath) -or -not (Test-Path -LiteralPath $sourcePath)) { continue }
    $sourceSizeKB = Get-FileSizeKB -Path $sourcePath
    if ($sourceSizeKB -le [int]$Budget.SafePerFileKB) { continue }

    $chunkResult = Split-TextArtifactIntoUploadSafeChunks -SourcePath $sourcePath -ArtifactsDir $State.ArtifactsDir -SourceKey $key -TargetChunkKB ([Math]::Min(700, [int]$Budget.SafePerFileKB))
    if ([int]$chunkResult.chunk_count -le 0) { continue }
    [void]$rows.Add($chunkResult)
    foreach ($chunkPath in @($chunkResult.chunk_paths)) {
      [void]$ArtifactMap.Add(("{0}_upload_safe_chunk_{1:000}" -f $key, (@($ArtifactMap.Keys | Where-Object { $_ -like ("{0}_upload_safe_chunk_*" -f $key) }).Count + 1)), $chunkPath)
    }
  }

  return @($rows)
}

<#
.SYNOPSIS
Converts one object into safe JSON text for artifact writing.

.DESCRIPTION
Serializes the supplied object with a high JSON depth and appends a trailing newline so
artifact JSON text files remain stable and readable.

.FUNCTION NAME
Convert-ToSafeJsonText

.INPUTS
InputObject to serialize.

.OUTPUTS
String containing newline-terminated JSON text.
#>
function Convert-ToSafeJsonText {
  param([object]$InputObject)
  return (Convert-ToCollectorJsonText -InputObject $InputObject -Label 'safe JSON artifact' -AppendNewline -ThrowOnTruncation)
}

<#
.SYNOPSIS
Determines whether the current collector context is elevated.

.DESCRIPTION
Queries the current Windows identity and returns true when the current principal is in
the local Administrators role. Returns false on any lookup error.

.FUNCTION NAME
Test-CollectorIsElevated

.INPUTS
No direct parameters.

.OUTPUTS
Boolean indicating whether the current collector context is elevated.
#>
function Test-CollectorIsElevated {
  try {
    $identity = [System.Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object System.Security.Principal.WindowsPrincipal($identity)
    return $principal.IsInRole([System.Security.Principal.WindowsBuiltInRole]::Administrator)
  } catch {
    return $false
  }
}

<#
.SYNOPSIS
Builds the execution-context text artifact.

.DESCRIPTION
Collects the current user, elevation state, host, process, PowerShell version, and
working-directory context, then adds a short diagnostic note describing the expected
visibility posture for elevated versus non-elevated collection.

.FUNCTION NAME
Get-CollectorExecutionContextText

.INPUTS
No direct parameters.

.OUTPUTS
String containing the execution-context text artifact.
#>
function Get-CollectorExecutionContextText {
  $isElevated = Test-CollectorIsElevated
  $identityName = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name
  $lines = @(
    'EXECUTION_CONTEXT',
    ("UserContext={0}" -f $identityName),
    ("IsElevated={0}" -f $isElevated),
    ("Host={0}" -f $env:COMPUTERNAME),
    ("ProcessId={0}" -f $PID),
    ("PowerShellVersion={0}" -f $PSVersionTable.PSVersion),
    ("CurrentDirectory={0}" -f (Get-Location).Path)
  )
  if ($isElevated) {
    $lines += 'DiagnosticContext=Elevated execution should allow owner-aware netstat capture and broader Security log visibility when audit policy supports it.'
  } else {
    $lines += 'DiagnosticContext=Non-elevated execution can restrict owner-aware netstat capture and Security log visibility on some hosts.'
  }
  return ($lines -join [Environment]::NewLine)
}

<#
.SYNOPSIS
Builds the netstat capture bundle for the current run.

.DESCRIPTION
Attempts owner-aware netstat capture first, classifies elevation-required or other
failure modes, optionally captures a PID-only supplemental netstat surface, and returns
both text surfaces plus the owner-aware capture status.

.FUNCTION NAME
Get-NetstatCaptureBundle

.INPUTS
IsElevated boolean describing the current collector context.

.OUTPUTS
Hashtable containing owner-aware text, owner-aware status, owner-aware exit code, and
optional PID-only text.
#>
function Get-NetstatCaptureBundle {
  param([bool]$IsElevated)

  $ownerAwareResult = Invoke-CmdCapture -Command 'netstat -abno' -StepName 'NETWORK_NETSTAT_OWNER_AWARE' -AllowedExitCodes @(0,1)
  $ownerAwareText = Get-CombinedProcessOutput -Result $ownerAwareResult
  $combinedOutput = (([string]$ownerAwareResult.StdOut) + ' ' + ([string]$ownerAwareResult.StdErr)).Trim()
  $requiresElevation = ($ownerAwareResult.ExitCode -ne 0) -and ($combinedOutput -match '(?i)requires elevation')

  $pidOnlyResult = $null
  $pidOnlyText = $null
  $status = 'OWNER_AWARE_OK'

  if ($requiresElevation) {
    $status = 'OWNER_AWARE_REQUIRES_ELEVATION'
    Add-CollectorNote 'Owner-aware netstat capture (netstat -abno) requires elevation in the current execution context. A supplemental PID-only netstat capture was collected separately, but executable ownership attribution remains unavailable until an elevated run.'
    $pidOnlyResult = Invoke-CmdCapture -Command 'netstat -ano' -StepName 'NETWORK_NETSTAT_PID_ONLY' -AllowedExitCodes @(0)
    $pidOnlyText = Get-CombinedProcessOutput -Result $pidOnlyResult
  } elseif ($ownerAwareResult.ExitCode -ne 0) {
    $status = 'OWNER_AWARE_FAILED'
    Add-CollectorError ('Owner-aware netstat capture (netstat -abno) failed for a reason other than missing elevation. Review the artifact for the exact command output. ExitCode={0}' -f $ownerAwareResult.ExitCode)
  }

  return @{
    OwnerAwareText = $ownerAwareText
    OwnerAwareStatus = $status
    OwnerAwareExitCode = [int]$ownerAwareResult.ExitCode
    PidOnlyText = $pidOnlyText
  }
}

<#
.SYNOPSIS
Creates the collect upload summary and attachment-budget manifest.

.DESCRIPTION
Selects the default analyst-first Gemini upload set, evaluates it against the safe and
hard environment budgets, writes the upload summary text and JSON manifest, and returns
the key status values to the caller.

.FUNCTION NAME
New-CollectUploadArtifacts

.INPUTS
Collector state hashtable and baseline result hashtable containing the artifact map.

.OUTPUTS
Hashtable containing upload-summary path, manifest path, default-set status, total KB,
and recommended file count.
#>
function New-CollectUploadArtifacts {
  [CmdletBinding(SupportsShouldProcess=$true)]
  param([hashtable]$State,[hashtable]$Baseline)

  $budget = Get-CollectorUploadBudget
  $artifactMap = $Baseline.ArtifactMap
  $chunkCompanions = New-ProductionUploadSafeChunkCompanions -State $State -ArtifactMap $artifactMap -Budget $budget
  $recommendedPaths = @()

  foreach ($key in @(
    'collection_metadata',
    'collection_notes_and_limitations',
    'security_high_signal_summary',
    'process_inventory',
    'structured_net',
    'defender_status',
    'analyst_follow_up_queue'
  )) {
    $candidatePath = if ($artifactMap.ContainsKey($key)) { [string]$artifactMap[$key] } else { $null }
    if (-not [string]::IsNullOrWhiteSpace($candidatePath) -and (Test-Path -LiteralPath $candidatePath)) {
      $recommendedPaths += $candidatePath
    }
  }

  if ($State.MetadataReportPath -and (Test-Path -LiteralPath $State.MetadataReportPath)) {
    $recommendedPaths = @($State.MetadataReportPath) + $recommendedPaths
  }

  $recommended = New-Object System.Collections.ArrayList
  $safeTotal = 0
  foreach ($path in $recommendedPaths) {
    $sizeKB = Get-FileSizeKB -Path $path
    $safeTotal += $sizeKB
    [void]$recommended.Add([ordered]@{
      path = $path
      relative_path = [string](Resolve-Path -LiteralPath $path | ForEach-Object { $_.Path.Replace($State.RunRoot + '\\', '') })
      size_kb = $sizeKB
      within_safe_per_file = ($sizeKB -le $budget.SafePerFileKB)
      within_hard_per_file = ($sizeKB -le $budget.HardPerFileKB)
    })
  }

  $setStatus = if (($safeTotal -le $budget.SafeTotalKB) -and (@($recommended | Where-Object { -not $_.within_safe_per_file }).Count -eq 0)) {
    'SAFE_DEFAULT_SET'
  } elseif (($safeTotal -le $budget.HardTotalKB) -and (@($recommended | Where-Object { -not $_.within_hard_per_file }).Count -eq 0)) {
    'HARD_LIMIT_ONLY'
  } else {
    'EXCEEDS_ENVIRONMENT_BUDGET'
  }

  $uploadSummaryPath = Join-Path $State.ReportsDir ("DCOIR_UPLOAD_SUMMARY_{0}_{1}.txt" -f $env:COMPUTERNAME, $State.RunId)
  $uploadManifestPath = Join-Path $State.ReportsDir ("DCOIR_ATTACHMENT_BUDGET_MANIFEST_{0}_{1}.json.txt" -f $env:COMPUTERNAME, $State.RunId)
  $chunkManifestPath = $null
  if (@($chunkCompanions).Count -gt 0) {
    $plannedChunkManifestPath = Join-Path $State.ReportsDir ("DCOIR_UPLOAD_SAFE_CHUNK_MANIFEST_{0}_{1}.json.txt" -f $env:COMPUTERNAME, $State.RunId)
    $chunkManifestObj = [ordered]@{
      run_id = $State.RunId
      origin = 'collector_production_upload_safe'
      budget = $budget
      chunked_artifact_count = @($chunkCompanions).Count
      chunked_artifacts = @($chunkCompanions)
    }
    if ($PSCmdlet.ShouldProcess($plannedChunkManifestPath, 'Write upload-safe chunk manifest')) {
      Set-Content -Path $plannedChunkManifestPath -Value (Convert-ToSafeJsonText -InputObject $chunkManifestObj) -Encoding UTF8 -ErrorAction Stop
      $chunkManifestPath = $plannedChunkManifestPath
      $State.UploadSafeChunkManifestPath = $chunkManifestPath
      $Baseline.ArtifactMap['upload_safe_chunk_manifest'] = $chunkManifestPath
      [void]$Baseline.ArtifactPaths.Add($chunkManifestPath)
      foreach ($chunkRow in @($chunkCompanions)) {
        foreach ($chunkPath in @($chunkRow.chunk_paths)) {
          [void]$Baseline.ArtifactPaths.Add($chunkPath)
        }
      }
    }
  }

  $summaryLines = @(
    "CollectorVersion=$ScriptVersion",
    "RunId=$($State.RunId)",
    "WorkflowPhase=CollectBaseline",
    "UploadModel=ChunkFirst",
    "DoNotAssumeMonolithicBaselineUpload=true",
    "HardPerFileKB=$($budget.HardPerFileKB)",
    "HardTotalKB=$($budget.HardTotalKB)",
    "SafePerFileKB=$($budget.SafePerFileKB)",
    "SafeTotalKB=$($budget.SafeTotalKB)",
    "DefaultSetStatus=$setStatus",
    "RecommendedUploadTotalKB=$safeTotal",
    "",
    "Recommended files for Gemini upload by default:"
  )
  foreach ($row in $recommended) {
    $summaryLines += ('- {0} [{1} KB]' -f $row.path, $row.size_kb)
  }
  $summaryLines += ""
  $summaryLines += "Default guidance:"
  $summaryLines += "- Prefer this upload summary, the metadata report, and the listed representative artifacts."
  $summaryLines += "- Do not assume the large merged baseline report is upload-safe in the office Gemini environment."
  $summaryLines += "- If this set must be trimmed further, keep metadata, follow-up queue, security high-signal summary, and one representative process/network artifact first."
  if (@($chunkCompanions).Count -gt 0) {
    $summaryLines += ""
    $summaryLines += "Upload-safe chunk companions:"
    if ($chunkManifestPath) {
      $summaryLines += ("- UPLOAD_SAFE_CHUNK_MANIFEST_PATH={0}" -f $chunkManifestPath)
    }
    foreach ($chunkRow in @($chunkCompanions)) {
      $summaryLines += ("- SourceKey={0} SourceSizeKB={1} ChunkCount={2} TargetChunkKB={3}" -f $chunkRow.source_artifact_key, $chunkRow.source_size_kb, $chunkRow.chunk_count, $chunkRow.target_chunk_kb)
      foreach ($chunkPath in @($chunkRow.chunk_paths)) {
        $summaryLines += ("  - {0}" -f $chunkPath)
      }
    }
    $summaryLines += "- Upload the high-signal summary first for triage; use full-fidelity chunk companions when the oversized source artifact is needed."
  }

  $uploadSummaryResultPath = $null
  if ($PSCmdlet.ShouldProcess($uploadSummaryPath, 'Write collect upload summary')) {
    Set-Content -Path $uploadSummaryPath -Value $summaryLines -Encoding UTF8 -ErrorAction Stop
    $uploadSummaryResultPath = $uploadSummaryPath
  }

  $manifestObj = [ordered]@{
    run_id = $State.RunId
    workflow_phase = 'collect_baseline'
    upload_model = 'chunk_first'
    budget = $budget
    default_set_status = $setStatus
    recommended_upload_total_kb = $safeTotal
    recommended_upload_files = @($recommended)
    upload_safe_chunk_manifest_path = $chunkManifestPath
    upload_safe_chunk_companions = @($chunkCompanions)
    baseline_report_path = $State.BaselineReportPath
    metadata_report_path = $State.MetadataReportPath
    note = 'The merged baseline report may be useful for local analyst review but is no longer the default Gemini-facing upload surface.'
  }
  $uploadManifestResultPath = $null
  if ($PSCmdlet.ShouldProcess($uploadManifestPath, 'Write attachment budget manifest')) {
    Set-Content -Path $uploadManifestPath -Value (Convert-ToSafeJsonText -InputObject $manifestObj) -Encoding UTF8 -ErrorAction Stop
    $uploadManifestResultPath = $uploadManifestPath
  }

  return @{
    UploadSummaryPath = $uploadSummaryResultPath
    UploadManifestPath = $uploadManifestResultPath
    DefaultSetStatus = $setStatus
    RecommendedUploadTotalKB = $safeTotal
    RecommendedUploadCount = @($recommended).Count
    UploadSafeChunkManifestPath = $chunkManifestPath
    UploadSafeChunkCompanionCount = @($chunkCompanions).Count
  }
}

<#
.SYNOPSIS
Runs one Tier 2 registry query through direct reg.exe capture.

.DESCRIPTION
Invokes reg.exe directly for one Tier 2 deep-check registry path, preserves the bounded
captured output, and records a collector error when the query returns a non-zero exit
code so the artifact remains the truth surface instead of failing invisibly.

.FUNCTION NAME
Invoke-Tier2RegistryQueryText

.INPUTS
RegistryPath string, StepName string, and optional FailureLabel string.

.OUTPUTS
String containing the combined direct-process output for the Tier 2 registry query.
#>
function Invoke-Tier2RegistryQueryText {
  param(
    [Parameter(Mandatory=$true)][string]$RegistryPath,
    [Parameter(Mandatory=$true)][string]$StepName,
    [string]$FailureLabel = 'Tier 2 registry query'
  )

  $result = Invoke-ProcessCapture -FilePath 'reg.exe' -Arguments @('query', $RegistryPath, '/s') -StepName $StepName -AllowedExitCodes @(0,1)
  if ($result.ExitCode -ne 0) {
    Add-CollectorError ('{0} returned ExitCode={1} for path [{2}]. Review the artifact for the exact bounded output.' -f $FailureLabel, $result.ExitCode, $RegistryPath)
  }
  return (Get-CombinedProcessOutput -Result $result)
}

<#
.SYNOPSIS
Builds the Tier 2 WMI persistence text surface class by class.

.DESCRIPTION
Queries the root\subscription WMI classes one at a time so one failing class does not
break the whole Tier 2 WMI persistence surface. Each class writes either formatted
results, NO_RESULTS, or one bounded error line that is also added to the collector error
list.

.FUNCTION NAME
Get-Tier2WmiPersistenceText

.INPUTS
No direct parameters.

.OUTPUTS
String containing the combined Tier 2 WMI persistence text surface.
#>
function Get-Tier2WmiPersistenceText {
  $classNames = @(
    '__EventFilter',
    'CommandLineEventConsumer',
    'ActiveScriptEventConsumer',
    'FilterToConsumerBinding'
  )

  $sections = New-Object System.Collections.ArrayList
  foreach ($className in $classNames) {
    [void]$sections.Add(('WMI_CLASS={0}' -f $className))
    [void]$sections.Add('')
    try {
      $instances = @(Get-CimInstance -Namespace 'root\subscription' -ClassName $className -ErrorAction Stop)
      if (@($instances).Count -gt 0) {
        [void]$sections.Add((($instances | Format-List * | Out-String -Width 500).TrimEnd()))
      } else {
        [void]$sections.Add('NO_RESULTS')
      }
    } catch {
      $message = 'ERROR collecting WMI persistence class [{0}]: {1}' -f $className, $_.Exception.Message
      Add-CollectorError $message
      [void]$sections.Add($message)
    }
    [void]$sections.Add('')
    [void]$sections.Add(('—' * 80))
    [void]$sections.Add('')
  }

  return ($sections -join [Environment]::NewLine)
}

<#
.SYNOPSIS
Builds the Tier 2 persistence deep-check text surface.

.DESCRIPTION
Collects Tier 2-only registry, WMI persistence, share, session, and firewall text
artifacts, writes each one to disk, and returns the combined text surface for report
inclusion.

.FUNCTION NAME
Get-Tier2PersistenceText

.INPUTS
Collector state hashtable and ToolMap hashtable.

.OUTPUTS
String containing the combined Tier 2 persistence and deep-check text surface.
#>
function Get-Tier2PersistenceText {
  param([hashtable]$State,[hashtable]$ToolMap)

  $sb = New-Object System.Text.StringBuilder

  $regIfeo = Invoke-Tier2RegistryQueryText -RegistryPath 'HKLM\Software\Microsoft\Windows NT\CurrentVersion\Image File Execution Options' -StepName 'TIER2_REG_IFEO' -FailureLabel 'Tier 2 IFEO registry query'
  [void](Write-ArtifactText -ArtifactsDir $State.ArtifactsDir -Section 'TIER2_DEEP_CHECKS' -Name 'tier2_reg_ifeo.txt' -Text $regIfeo)
  Add-Section -Builder $sb -Name 'TIER2_REG_IFEO' -Text $regIfeo

  $regWinlogon = Invoke-Tier2RegistryQueryText -RegistryPath 'HKLM\Software\Microsoft\Windows NT\CurrentVersion\Winlogon' -StepName 'TIER2_REG_WINLOGON' -FailureLabel 'Tier 2 Winlogon registry query'
  [void](Write-ArtifactText -ArtifactsDir $State.ArtifactsDir -Section 'TIER2_DEEP_CHECKS' -Name 'tier2_reg_winlogon.txt' -Text $regWinlogon)
  Add-Section -Builder $sb -Name 'TIER2_REG_WINLOGON' -Text $regWinlogon

  $regLsa = Invoke-Tier2RegistryQueryText -RegistryPath 'HKLM\SYSTEM\CurrentControlSet\Control\Lsa' -StepName 'TIER2_REG_LSA' -FailureLabel 'Tier 2 LSA registry query'
  [void](Write-ArtifactText -ArtifactsDir $State.ArtifactsDir -Section 'TIER2_DEEP_CHECKS' -Name 'tier2_reg_lsa.txt' -Text $regLsa)
  Add-Section -Builder $sb -Name 'TIER2_REG_LSA' -Text $regLsa

  $wmiText = Get-Tier2WmiPersistenceText
  [void](Write-ArtifactText -ArtifactsDir $State.ArtifactsDir -Section 'TIER2_DEEP_CHECKS' -Name 'tier2_wmi_persistence.txt' -Text $wmiText)
  Add-Section -Builder $sb -Name 'TIER2_WMI_PERSISTENCE' -Text $wmiText

  $netShare = Get-CmdText -Command 'net share' -StepName 'TIER2_NET_SHARE'
  [void](Write-ArtifactText -ArtifactsDir $State.ArtifactsDir -Section 'TIER2_DEEP_CHECKS' -Name 'tier2_net_share.txt' -Text $netShare)
  Add-Section -Builder $sb -Name 'TIER2_NET_SHARE' -Text $netShare

  $netSession = Get-CmdText -Command 'net session' -StepName 'TIER2_NET_SESSION' -AllowedExitCodes @(0,2)
  [void](Write-ArtifactText -ArtifactsDir $State.ArtifactsDir -Section 'TIER2_DEEP_CHECKS' -Name 'tier2_net_session.txt' -Text $netSession)
  Add-Section -Builder $sb -Name 'TIER2_NET_SESSION' -Text $netSession

  $fw = Get-CmdText -Command 'netsh advfirewall show allprofiles' -StepName 'TIER2_FIREWALL_PROFILES'
  [void](Write-ArtifactText -ArtifactsDir $State.ArtifactsDir -Section 'TIER2_DEEP_CHECKS' -Name 'tier2_firewall_profiles.txt' -Text $fw)
  Add-Section -Builder $sb -Name 'TIER2_FIREWALL_PROFILES' -Text $fw

  return $sb.ToString()
}

<#
.SYNOPSIS
Builds the baseline report and baseline artifact set.

.DESCRIPTION
Collects the baseline artifact families, writes them to disk, appends them into the
main baseline report, emits analyst follow-up recommendations, and returns the report
builder plus artifact path and map structures.

.FUNCTION NAME
New-BaselineReport

.INPUTS
Collector state hashtable and ToolMap hashtable.

.OUTPUTS
Hashtable containing ReportBuilder, ReportText, ArtifactPaths, and ArtifactMap.
#>
function New-BaselineReport {
  [CmdletBinding()]
  param([hashtable]$State,[hashtable]$ToolMap)

  $artifactPaths = New-Object System.Collections.ArrayList
  $artifactMap = @{}
  $sb = New-Object System.Text.StringBuilder
  $isElevated = Test-CollectorIsElevated

  if (-not $isElevated) {
    Add-CollectorNote 'Collector is running in a non-elevated context. Owner-aware netstat capture and Security log visibility may be restricted on this host.'
  }

  $metaText = @(
    "CollectorVersion=$ScriptVersion"
    "Mode=Collect"
    "Tier=$Tier"
    "Hours=$Hours"
    "MaxEvents=$MaxEvents"
    "Host=$env:COMPUTERNAME"
    "RunId=$($State.RunId)"
    "UserContext=$([System.Security.Principal.WindowsIdentity]::GetCurrent().Name)"
    "IsElevated=$isElevated"
    "TimeLocal=$(Get-Date -Format o)"
    "TimeUTC=$((Get-Date).ToUniversalTime().ToString('o'))"
    "RunRoot=$($State.RunRoot)"
    "ReportsDir=$($State.ReportsDir)"
    "ArtifactsDir=$($State.ArtifactsDir)"
    "EnrichSessionsDir=$($State.EnrichSessionsDir)"
  ) -join [Environment]::NewLine
  $p = Write-ArtifactText -ArtifactsDir $State.ArtifactsDir -Section "COLLECTION_METADATA" -Name "collection_metadata.txt" -Text $metaText
  [void]$artifactPaths.Add($p); $artifactMap['collection_metadata'] = $p
  Add-Section -Builder $sb -Name "COLLECTION_METADATA" -Text $metaText

  $executionContextText = Get-CollectorExecutionContextText
  $p = Write-ArtifactText -ArtifactsDir $State.ArtifactsDir -Section "COLLECTION_METADATA" -Name "execution_context.txt" -Text $executionContextText
  [void]$artifactPaths.Add($p); $artifactMap['execution_context'] = $p; $State.ExecutionContextPath = $p; $State.IsElevated = $isElevated

  $script:CollectorAuditPolicyAccessStatus = 'UNKNOWN'
  $auditPolicyText = Get-SecurityAuditPolicyText
  $State.AuditPolicyAccessStatus = if ($script:CollectorAuditPolicyAccessStatus) { [string]$script:CollectorAuditPolicyAccessStatus } else { 'UNKNOWN' }
  $p = Write-ArtifactText -ArtifactsDir $State.ArtifactsDir -Section "COLLECTION_METADATA" -Name "security_audit_policy.txt" -Text $auditPolicyText
  [void]$artifactPaths.Add($p); $artifactMap['security_audit_policy'] = $p; $State.SecurityAuditPolicyPath = $p
  Add-Section -Builder $sb -Name "EXECUTION_CONTEXT_AND_AUDIT_POLICY" -Text (@($executionContextText, '', ('AUDIT_POLICY_ACCESS_STATUS={0}' -f $State.AuditPolicyAccessStatus), '', $auditPolicyText) -join [Environment]::NewLine)

  $limitationLines = @(
    "Offline profile hives were not loaded by design.",
    "Only loaded HKU user Run keys were collected.",
    "Raw EVTX files are not part of baseline collection. Log text is exported for baseline review.",
    "Current run files remain in place until Cleanup runs.",
    "A new Collect run purges prior DCOIR run folders and the prior package zip.",
    "The merged baseline report remains useful for local analyst review, but it is no longer the default Gemini-facing upload surface. Prefer the upload summary and representative artifacts."
  )
  if (@($Global:CollectorNotes).Count -gt 0) {
    $limitationLines += ""
    $limitationLines += "Collection notes:"
    $limitationLines += $Global:CollectorNotes
  }
  if (@($Global:CollectorErrors).Count -gt 0) {
    $limitationLines += ""
    $limitationLines += "Collection errors seen so far:"
    $limitationLines += $Global:CollectorErrors
  }
  $limitationText = ($limitationLines -join [Environment]::NewLine)
  $p = Write-ArtifactText -ArtifactsDir $State.ArtifactsDir -Section "COLLECTION_NOTES_AND_LIMITATIONS" -Name "collection_notes_and_limitations.txt" -Text $limitationText
  [void]$artifactPaths.Add($p); $artifactMap['collection_notes_and_limitations'] = $p
  Add-Section -Builder $sb -Name "COLLECTION_NOTES_AND_LIMITATIONS" -Text $limitationText

  $timeHostText = Get-CmdText -Command 'date /t & time /t & hostname & ver' -StepName "HOST_DATE_TIME_HOSTNAME"
  $p = Write-ArtifactText -ArtifactsDir $State.ArtifactsDir -Section "HOST_BASELINE" -Name "time_host.txt" -Text $timeHostText
  [void]$artifactPaths.Add($p); $artifactMap['time_host'] = $p
  $systemInfoText = Get-CmdText -Command 'systeminfo' -StepName "HOST_SYSTEMINFO"
  $p = Write-ArtifactText -ArtifactsDir $State.ArtifactsDir -Section "HOST_BASELINE" -Name "systeminfo.txt" -Text $systemInfoText
  [void]$artifactPaths.Add($p); $artifactMap['systeminfo'] = $p
  Add-Section -Builder $sb -Name "HOST_BASELINE" -Text (@($timeHostText, "", $systemInfoText) -join [Environment]::NewLine)

  $whoamiText = Get-CmdText -Command 'whoami /all' -StepName "IDENTITY_WHOAMI_ALL"
  $p = Write-ArtifactText -ArtifactsDir $State.ArtifactsDir -Section "IDENTITY_AND_SESSION_CONTEXT" -Name "whoami_all.txt" -Text $whoamiText
  [void]$artifactPaths.Add($p); $artifactMap['whoami_all'] = $p
  $sessionsText = Get-CmdText -Command 'query user & qwinsta' -StepName "IDENTITY_QUERY_USER_QWINSTA"
  $p = Write-ArtifactText -ArtifactsDir $State.ArtifactsDir -Section "IDENTITY_AND_SESSION_CONTEXT" -Name "sessions.txt" -Text $sessionsText
  [void]$artifactPaths.Add($p); $artifactMap['sessions'] = $p
  $logonSessionsWmiText = Get-LogonSessionsWmiText
  $p = Write-ArtifactText -ArtifactsDir $State.ArtifactsDir -Section "IDENTITY_AND_SESSION_CONTEXT" -Name "logon_sessions_wmi.txt" -Text $logonSessionsWmiText
  [void]$artifactPaths.Add($p); $artifactMap['logon_sessions_wmi'] = $p
  Add-Section -Builder $sb -Name "IDENTITY_AND_SESSION_CONTEXT" -Text (@($whoamiText, "", $sessionsText, "", $logonSessionsWmiText) -join [Environment]::NewLine)

  $procInventory = Get-ProcessInventory
  $excludedPids = @([int]$PID)
  try {
    $selfProc = Get-CimInstance -ClassName Win32_Process -Filter ("ProcessId={0}" -f $PID) -ErrorAction Stop
    if ($selfProc.ParentProcessId) { $excludedPids += [int]$selfProc.ParentProcessId }
  } catch { }
  $procInventoryText = Convert-ToTextBlock -InputObject ($procInventory | Select-Object ProcessId, ParentProcessId, ParentProcessName, Name, Owner, ExecutablePath, CreationTime, CommandLine)
  $p = Write-ArtifactText -ArtifactsDir $State.ArtifactsDir -Section "PROCESS_EXECUTION_CONTEXT" -Name "process_inventory.txt" -Text $procInventoryText
  [void]$artifactPaths.Add($p); $artifactMap['process_inventory'] = $p
  $procParts = @($procInventoryText)
  if ($ToolMap['pslist']) {
    $pslistText = Invoke-ToolToText -ToolPath $ToolMap['pslist'] -Arguments @('-accepteula','-nobanner','-t') -StepName "SYSINTERNALS_PSLIST"
    $p = Write-ArtifactText -ArtifactsDir $State.ArtifactsDir -Section "PROCESS_EXECUTION_CONTEXT" -Name "pslist.txt" -Text $pslistText
    [void]$artifactPaths.Add($p); $artifactMap['pslist'] = $p
    $procParts += ""
    $procParts += $pslistText
  }
  Add-Section -Builder $sb -Name "PROCESS_EXECUTION_CONTEXT" -Text ($procParts -join [Environment]::NewLine)

  $ipconfigText = Get-CmdText -Command 'ipconfig /all' -StepName "NETWORK_IPCONFIG"
  $p = Write-ArtifactText -ArtifactsDir $State.ArtifactsDir -Section "NETWORK_STATE" -Name "ipconfig_all.txt" -Text $ipconfigText
  [void]$artifactPaths.Add($p); $artifactMap['ipconfig_all'] = $p
  $netstatBundle = Get-NetstatCaptureBundle -IsElevated $isElevated
  $netstatText = $netstatBundle.OwnerAwareText
  $State.NetstatOwnerAwareStatus = $netstatBundle.OwnerAwareStatus
  $p = Write-ArtifactText -ArtifactsDir $State.ArtifactsDir -Section "NETWORK_STATE" -Name "netstat_abno.txt" -Text $netstatText
  [void]$artifactPaths.Add($p); $artifactMap['netstat_abno'] = $p
  $structuredNetText = Get-BaselineNetText
  $p = Write-ArtifactText -ArtifactsDir $State.ArtifactsDir -Section "NETWORK_STATE" -Name "structured_net.txt" -Text $structuredNetText
  [void]$artifactPaths.Add($p); $artifactMap['structured_net'] = $p
  $dnsText = Get-CmdText -Command 'ipconfig /displaydns' -StepName "NETWORK_DNS_CACHE"
  $p = Write-ArtifactText -ArtifactsDir $State.ArtifactsDir -Section "NETWORK_STATE" -Name "dns_cache.txt" -Text $dnsText
  [void]$artifactPaths.Add($p); $artifactMap['dns_cache'] = $p
  $routeText = Get-CmdText -Command 'route print' -StepName "NETWORK_ROUTE_PRINT"
  $p = Write-ArtifactText -ArtifactsDir $State.ArtifactsDir -Section "NETWORK_STATE" -Name "route_print.txt" -Text $routeText
  [void]$artifactPaths.Add($p); $artifactMap['route_print'] = $p
  $arpText = Get-CmdText -Command 'arp -a' -StepName "NETWORK_ARP_A"
  $p = Write-ArtifactText -ArtifactsDir $State.ArtifactsDir -Section "NETWORK_STATE" -Name "arp_a.txt" -Text $arpText
  [void]$artifactPaths.Add($p); $artifactMap['arp_a'] = $p
  $networkParts = @($ipconfigText, "", $netstatText, "", $structuredNetText, "", $dnsText, "", $routeText, "", $arpText)
  if ($netstatBundle.PidOnlyText) {
    $p = Write-ArtifactText -ArtifactsDir $State.ArtifactsDir -Section "NETWORK_STATE" -Name "netstat_ano_supplemental.txt" -Text $netstatBundle.PidOnlyText
    [void]$artifactPaths.Add($p); $artifactMap['netstat_ano_supplemental'] = $p; $State.NetstatPidOnlyPath = $p
    $networkParts += ""
    $networkParts += $netstatBundle.PidOnlyText
  }
  if ($ToolMap['tcpvcon']) {
    $tcpvconText = Invoke-ToolToText -ToolPath $ToolMap['tcpvcon'] -Arguments @('-accepteula','-nobanner') -StepName "SYSINTERNALS_TCPVCON"
    $p = Write-ArtifactText -ArtifactsDir $State.ArtifactsDir -Section "NETWORK_STATE" -Name "tcpvcon.txt" -Text $tcpvconText
    [void]$artifactPaths.Add($p); $artifactMap['tcpvcon'] = $p
    $networkParts += ""
    $networkParts += $tcpvconText
  }
  if ($ToolMap['pipelist']) {
    $pipelistText = Invoke-ToolToText -ToolPath $ToolMap['pipelist'] -Arguments @('-accepteula','-nobanner') -StepName "SYSINTERNALS_PIPELIST"
    $p = Write-ArtifactText -ArtifactsDir $State.ArtifactsDir -Section "NETWORK_STATE" -Name "pipelist.txt" -Text $pipelistText
    [void]$artifactPaths.Add($p); $artifactMap['pipelist'] = $p
    $networkParts += ""
    $networkParts += $pipelistText
  }
  Add-Section -Builder $sb -Name "NETWORK_STATE" -Text ($networkParts -join [Environment]::NewLine)

  $servicesText = Get-CmdText -Command 'sc queryex type= service state= all' -StepName "PERSISTENCE_SERVICES"
  $p = Write-ArtifactText -ArtifactsDir $State.ArtifactsDir -Section "PERSISTENCE_AND_AUTOSTARTS" -Name "services.txt" -Text $servicesText
  [void]$artifactPaths.Add($p); $artifactMap['services'] = $p
  $tasksText = Get-CmdText -Command 'schtasks /query /fo LIST /v' -StepName "PERSISTENCE_SCHEDULED_TASKS"
  $p = Write-ArtifactText -ArtifactsDir $State.ArtifactsDir -Section "PERSISTENCE_AND_AUTOSTARTS" -Name "scheduled_tasks.txt" -Text $tasksText
  [void]$artifactPaths.Add($p); $artifactMap['scheduled_tasks'] = $p
  $hklmRunText = Get-RegistryQueryText -RegistryPath 'HKLM\Software\Microsoft\Windows\CurrentVersion\Run' -StepName "PERSISTENCE_HKLM_RUN"
  $p = Write-ArtifactText -ArtifactsDir $State.ArtifactsDir -Section "PERSISTENCE_AND_AUTOSTARTS" -Name "run_hklm.txt" -Text $hklmRunText
  [void]$artifactPaths.Add($p); $artifactMap['run_hklm'] = $p
  $hkuRunText = Get-LoadedUserRunKeysText
  $p = Write-ArtifactText -ArtifactsDir $State.ArtifactsDir -Section "PERSISTENCE_AND_AUTOSTARTS" -Name "run_hku_loaded_users.txt" -Text $hkuRunText
  [void]$artifactPaths.Add($p); $artifactMap['run_hku_loaded_users'] = $p
  $persistenceParts = @($servicesText, "", $tasksText, "", $hklmRunText, "", $hkuRunText)
  if ($ToolMap['autorunsc']) {
    $autorunsText = Invoke-ToolToText -ToolPath $ToolMap['autorunsc'] -Arguments @('-accepteula','-nobanner','-a','*','-c','-h','-s','*') -StepName "SYSINTERNALS_AUTORUNSC"
    $p = Write-ArtifactText -ArtifactsDir $State.ArtifactsDir -Section "PERSISTENCE_AND_AUTOSTARTS" -Name "autorunsc.csv.txt" -Text $autorunsText
    [void]$artifactPaths.Add($p); $artifactMap['autorunsc'] = $p
    $persistenceParts += ""
    $persistenceParts += $autorunsText
  }
  Add-Section -Builder $sb -Name "PERSISTENCE_AND_AUTOSTARTS" -Text ($persistenceParts -join [Environment]::NewLine)

  $defenderText = Get-DefenderStatusText
  $p = Write-ArtifactText -ArtifactsDir $State.ArtifactsDir -Section "SECURITY_POSTURE_AND_DEFENSIVE_STATE" -Name "defender_status.txt" -Text $defenderText
  [void]$artifactPaths.Add($p); $artifactMap['defender_status'] = $p
  $firewallText = Get-CmdText -Command 'netsh advfirewall show allprofiles' -StepName "SECURITY_FIREWALL_PROFILES"
  $p = Write-ArtifactText -ArtifactsDir $State.ArtifactsDir -Section "SECURITY_POSTURE_AND_DEFENSIVE_STATE" -Name "firewall_profiles.txt" -Text $firewallText
  [void]$artifactPaths.Add($p); $artifactMap['firewall_profiles'] = $p
  Add-Section -Builder $sb -Name "SECURITY_POSTURE_AND_DEFENSIVE_STATE" -Text (@($defenderText, "", $firewallText) -join [Environment]::NewLine)

  $securityIds = @(4624,4625,4634,4647,4648,4672,4688,4697,4698)
  $securityText = Get-EventText -Channel "Security" -WindowHours $Hours -Ids $securityIds -Take $MaxEvents
  $securityText += Get-TestTextPaddingFromEnvironment -Name 'DCOIR_TEST_SECURITY_FILTERED_OVERSIZE_KB'
  $p = Write-ArtifactText -ArtifactsDir $State.ArtifactsDir -Section "EVENT_TIMELINE_TEXT" -Name "security_filtered.txt" -Text $securityText
  [void]$artifactPaths.Add($p); $artifactMap['security_filtered'] = $p; $State.SecurityFilteredPath = $p
  $securityHighSignalText = Get-SecurityHighSignalSummaryText -WindowHours $Hours -Take ([Math]::Min($MaxEvents, 200))
  $p = Write-ArtifactText -ArtifactsDir $State.ArtifactsDir -Section "EVENT_TIMELINE_TEXT" -Name "security_high_signal_summary.txt" -Text $securityHighSignalText
  [void]$artifactPaths.Add($p); $artifactMap['security_high_signal_summary'] = $p; $State.SecurityHighSignalSummaryPath = $p
  $psOpText = Get-EventText -Channel "Microsoft-Windows-PowerShell/Operational" -WindowHours $Hours -Take $MaxEvents
  $psOpText += Get-TestTextPaddingFromEnvironment -Name 'DCOIR_TEST_POWERSHELL_OPERATIONAL_OVERSIZE_KB'
  $p = Write-ArtifactText -ArtifactsDir $State.ArtifactsDir -Section "EVENT_TIMELINE_TEXT" -Name "powershell_operational_filtered.txt" -Text $psOpText
  [void]$artifactPaths.Add($p); $artifactMap['powershell_operational_filtered'] = $p
  $taskOpText = Get-EventText -Channel "Microsoft-Windows-TaskScheduler/Operational" -WindowHours $Hours -Take $MaxEvents
  $taskOpText += Get-TestTextPaddingFromEnvironment -Name 'DCOIR_TEST_TASKSCHEDULER_OPERATIONAL_OVERSIZE_KB'
  $p = Write-ArtifactText -ArtifactsDir $State.ArtifactsDir -Section "EVENT_TIMELINE_TEXT" -Name "taskscheduler_operational_filtered.txt" -Text $taskOpText
  [void]$artifactPaths.Add($p); $artifactMap['taskscheduler_operational_filtered'] = $p
  Add-Section -Builder $sb -Name "EVENT_TIMELINE_TEXT_HIGH_SIGNAL" -Text $securityHighSignalText
  Add-Section -Builder $sb -Name "EVENT_TIMELINE_TEXT" -Text (@($securityText, "", $psOpText, "", $taskOpText) -join [Environment]::NewLine)

  if ($Tier -eq "T2") {
    Add-Section -Builder $sb -Name "TIER2_DEEP_CHECKS" -Text (Get-Tier2PersistenceText -State $State -ToolMap $ToolMap)
  }

  $findings = Get-SuspiciousProcessFindings -Processes $procInventory -ExcludedPids $excludedPids
  $collectorCommandBase = Get-CollectorPowerShellCommandBase
  if (@($findings).Count -gt 0) {
    Add-Recommendation 'The following process review candidates were selected by baseline heuristics. Treat them as triage prompts for analyst validation, not proof of malicious activity.'
    foreach ($finding in ($findings | Select-Object -First 10)) {
      $parentLabel = ""
      if ($null -ne $finding.ParentProcessId -or -not [string]::IsNullOrWhiteSpace([string]$finding.ParentProcessName)) {
        $parentName = if (-not [string]::IsNullOrWhiteSpace([string]$finding.ParentProcessName)) { [string]$finding.ParentProcessName } else { "unknown" }
        $parentPid = if ($null -ne $finding.ParentProcessId) { [string]$finding.ParentProcessId } else { "unknown" }
        $parentLabel = " parent={0} ({1})" -f $parentName, $parentPid
      }
      Add-Recommendation ("Process review candidate PID {0} ({1}){2} :: heuristic flags: {3}" -f $finding.ProcessId, $finding.Name, $parentLabel, $finding.Reasons)
      if ($finding.ExecutablePath) {
        $safePath = $finding.ExecutablePath
        Add-Recommendation ('Suggested next action if analyst review warrants deeper validation: {0} -Mode Enrich -RunId {1} -Action SigcheckPath -Path "{2}" -OutRoot "{3}"' -f $collectorCommandBase, $State.RunId, $safePath, $OutRoot)
        Add-Recommendation ('Suggested next action if analyst review warrants deeper validation: {0} -Mode Enrich -RunId {1} -Action StringsPath -Path "{2}" -OutRoot "{3}"' -f $collectorCommandBase, $State.RunId, $safePath, $OutRoot)
        Add-Recommendation ('Suggested next action if analyst review warrants file retrieval: {0} -Mode Enrich -RunId {1} -Action PullSuspiciousFile -Path "{2}" -OutRoot "{3}"' -f $collectorCommandBase, $State.RunId, $safePath, $OutRoot)
      }
    }
  } else {
    Add-Recommendation 'No heuristic-driven process review candidates were generated from baseline collection.'
  }

  $followUpText = ($Global:RecommendedActions -join [Environment]::NewLine)
  $p = Write-ArtifactText -ArtifactsDir $State.ArtifactsDir -Section "ANALYST_FOLLOW_UP_QUEUE" -Name "analyst_follow_up_queue.txt" -Text $followUpText
  [void]$artifactPaths.Add($p); $artifactMap['analyst_follow_up_queue'] = $p
  Add-Section -Builder $sb -Name "ANALYST_FOLLOW_UP_QUEUE" -Text $followUpText

  return @{
    ReportBuilder = $sb
    ReportText = $sb.ToString()
    ArtifactPaths = $artifactPaths
    ArtifactMap = $artifactMap
  }
}

<#
.SYNOPSIS
Builds the metadata report for a collect run.

.DESCRIPTION
Creates the post-collect metadata report with run-summary paths, tool availability,
notes, errors, recommendations, and analyst workflow guidance.

.FUNCTION NAME
New-MetadataReport

.INPUTS
Collector state hashtable and ToolMap hashtable.

.OUTPUTS
String containing the metadata report text.
#>
function New-MetadataReport {
  param([hashtable]$State,[hashtable]$ToolMap)

  $sb = New-Object System.Text.StringBuilder
  Add-Section -Builder $sb -Name "RUN_SUMMARY" -Text (
    @(
      "CollectorVersion=$ScriptVersion"
      "Mode=Collect"
      "Tier=$Tier"
      "Hours=$Hours"
      "Host=$env:COMPUTERNAME"
      "RunId=$($State.RunId)"
      "TimeLocal=$(Get-Date -Format o)"
      "TimeUTC=$((Get-Date).ToUniversalTime().ToString('o'))"
      "RunRoot=$($State.RunRoot)"
      "BaselineReport=$($State.BaselineReportPath)"
      "MetadataReport=$($State.MetadataReportPath)"
      "ExecutionContext=$($State.ExecutionContextPath)"
      "SecurityAuditPolicy=$($State.SecurityAuditPolicyPath)"
      "AuditPolicyAccessStatus=$($State.AuditPolicyAccessStatus)"
      "SecurityFiltered=$($State.SecurityFilteredPath)"
      "SecurityHighSignalSummary=$($State.SecurityHighSignalSummaryPath)"
      "NetstatOwnerAwareStatus=$($State.NetstatOwnerAwareStatus)"
      "NetstatPidOnlyPath=$($State.NetstatPidOnlyPath)"
      "CollectBundle=$($State.CollectBundlePath)"
      "UploadSummary=$($State.UploadSummaryPath)"
      "AttachmentBudgetManifest=$($State.UploadBudgetManifestPath)"
      "DefaultGeminiUploadSetStatus=$($State.DefaultGeminiUploadSetStatus)"
    ) -join [Environment]::NewLine
  )

  Add-Section -Builder $sb -Name "TOOL_AVAILABILITY" -Text (Get-CommandAvailabilityTable -ToolMap $ToolMap)

  $notesText = @(
    "Cleanup removes the selected run folder and the package zip.",
    "Artifact retrieval is a separate get-file step.",
    "A new Collect run purges prior DCOIR runs before starting.",
    "Follow-on Enrich sessions do not purge the current run.",
    "For Gemini uploads in the current office environment, prefer the upload summary plus representative artifacts over the monolithic baseline report."
  )
  if (@($Global:CollectorNotes).Count -gt 0) {
    $notesText += ""
    $notesText += "Notes:"
    $notesText += $Global:CollectorNotes
  }
  Add-Section -Builder $sb -Name "NOTES" -Text ($notesText -join [Environment]::NewLine)

  $errorsText = if (@($Global:CollectorErrors).Count -gt 0) { $Global:CollectorErrors -join [Environment]::NewLine } else { "No collection errors were recorded." }
  Add-Section -Builder $sb -Name "ERRORS" -Text $errorsText

  $recsText = if (@($Global:RecommendedActions).Count -gt 0) { $Global:RecommendedActions -join [Environment]::NewLine } else { "No enrichment recommendations were generated." }
  Add-Section -Builder $sb -Name "RECOMMENDED_ENRICHMENT_ACTIONS" -Text $recsText

  $workflowText = @(
    "1. Retrieve the collect bundle with get-file.",
    "2. For Gemini uploads, prefer the upload summary, metadata report, manifest, logs, and representative final_artifacts slices.",
    "3. Review the merged baseline locally when the full monolithic report is needed.",
    "4. Run one enrichment action at a time.",
    "5. Continue the same enrichment session or finalize it for ZIP retrieval.",
    "6. Keep the current run until Cleanup is explicitly run."
  ) -join [Environment]::NewLine
  Add-Section -Builder $sb -Name "WORKFLOW" -Text $workflowText

  return $sb.ToString()
}

<#
.SYNOPSIS
Writes one report file to disk.

.DESCRIPTION
Writes the supplied text to the target report path using UTF-8 encoding.

.FUNCTION NAME
Write-ReportFile

.INPUTS
Path string for the output file and Text string to write.

.OUTPUTS
No direct output. Writes the report file as a side effect.
#>
function Write-ReportFile {
  [CmdletBinding(SupportsShouldProcess=$true)]
  param([string]$Path,[string]$Text)
  if ($PSCmdlet.ShouldProcess($Path, 'Write collector report file')) {
    Set-Content -Path $Path -Value $Text -Encoding UTF8 -ErrorAction Stop
    return $Path
  }
  return $null
}