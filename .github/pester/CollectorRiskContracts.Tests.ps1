Set-StrictMode -Version 2
$ErrorActionPreference = 'Stop'
Describe 'DCOIR collector high-risk behavior contracts' {
  BeforeAll {
    . (Join-Path $PSScriptRoot 'DcoirPester.Helpers.ps1')
    $script:Layout = Get-DcoirCollectorLayout
    $script:Manifest = Read-DcoirJson -Path $script:Layout.CollectorManifest
    $script:SourceFiles = Get-DcoirCollectorSourceFiles -Layout $script:Layout -Manifest $script:Manifest
    $script:EntryParse = Get-DcoirParsedFile -Path $script:Layout.CollectorEntry
  }

  It 'keeps cleanup and collect pre-purge deletion guarded by normalized authority checks and ShouldProcess' {
    $invokeCleanup = Get-DcoirFunctionTextByName -Paths $script:SourceFiles -Name 'Invoke-Cleanup'
    $purgePreviousRuns = Get-DcoirFunctionTextByName -Paths $script:SourceFiles -Name 'Purge-PreviousRuns'
    $withinRoot = Get-DcoirFunctionTextByName -Paths $script:SourceFiles -Name 'Test-DCOIRCleanupPathWithinRoot'

    Assert-DcoirTextContains -Text $invokeCleanup -Needle '[CmdletBinding(SupportsShouldProcess=$true)]' -Because 'cleanup deletion must remain WhatIf/Confirm aware'
    Assert-DcoirTextContains -Text $invokeCleanup -Needle 'Resolve-DCOIRRunId -CurrentRunId $authorityRunId -RejectBlank' -Because 'cleanup must validate the selected RunId before deriving deletion targets'
    Assert-DcoirTextContains -Text $invokeCleanup -Needle 'Test-DCOIRCleanupPathEquals' -Because 'cleanup must compare state paths against recomputed expected paths'
    Assert-DcoirTextContains -Text $invokeCleanup -Needle 'Test-DCOIRCleanupPathWithinRoot' -Because 'cleanup must refuse state-provided targets outside the selected OutRoot'
    Assert-DcoirTextContains -Text $invokeCleanup -Needle 'Add-DCOIRCleanupRefusal' -Because 'cleanup refusals must be observable evidence, not silent skips'
    Assert-DcoirTextContains -Text $invokeCleanup -Needle 'Remove-Item -LiteralPath' -Because 'cleanup deletion must avoid wildcard interpretation'
    Assert-DcoirTextDoesNotMatch -Text $invokeCleanup -Pattern 'Remove-Item\s+-Path' -Because 'cleanup must not delete with wildcard-capable -Path'

    Assert-DcoirTextContains -Text $purgePreviousRuns -Needle '[CmdletBinding(SupportsShouldProcess=$true)]' -Because 'collect pre-purge must remain WhatIf/Confirm aware'
    Assert-DcoirTextContains -Text $purgePreviousRuns -Needle 'Test-DCOIRExactCustomRunRootPurgeCandidate' -Because 'custom RunId purge must prove collector ownership before deletion'
    Assert-DcoirTextContains -Text $purgePreviousRuns -Needle 'Test-DCOIRBulkPurgeRunDirectoryName' -Because 'bulk pre-purge must stay limited to timestamp-style run roots'
    Assert-DcoirTextContains -Text $purgePreviousRuns -Needle 'CUSTOM_RUN_PURGE_SKIPPED' -Because 'declined custom RunId purge must produce a stable skipped-prep reason'
    Assert-DcoirTextContains -Text $purgePreviousRuns -Needle 'Remove-Item -LiteralPath' -Because 'pre-purge deletion must avoid wildcard interpretation'
    Assert-DcoirTextDoesNotMatch -Text $purgePreviousRuns -Pattern 'Remove-Item\s+-Path' -Because 'pre-purge must not delete with wildcard-capable -Path'

    Assert-DcoirTextContains -Text $withinRoot -Needle '$rootPath + [System.IO.Path]::DirectorySeparatorChar' -Because 'root-prefix checks must reject similarly named sibling directories'
    Assert-DcoirTextContains -Text $withinRoot -Needle 'OrdinalIgnoreCase' -Because 'Windows cleanup path comparison must remain case-insensitive'
  }

  It 'keeps quick shortcut assignments aligned with the public Action and TargetProfile ValidateSet contracts' {
    $actionParameter = Get-DcoirEntryParameterAst -Ast $script:EntryParse.Ast -Name 'Action'
    $targetProfileParameter = Get-DcoirEntryParameterAst -Ast $script:EntryParse.Ast -Name 'TargetProfile'
    $actionValidateSet = @(Get-DcoirAttributePositionalValues -ParameterAst $actionParameter -AttributeName 'ValidateSet')
    $targetProfileValidateSet = @(Get-DcoirAttributePositionalValues -ParameterAst $targetProfileParameter -AttributeName 'ValidateSet')
    $quickShortcut = Get-DcoirFunctionTextByName -Paths $script:SourceFiles -Name 'Apply-QuickShortcut'

    $assignedActions = @(Get-DcoirAssignedStringValues -Text $quickShortcut -VariableName 'script:Action')
    $assignedTargetProfiles = @(Get-DcoirAssignedStringValues -Text $quickShortcut -VariableName 'script:TargetProfile')

    $assignedActions.Count | Should -BeGreaterThan 0 -Because 'quick enrich shortcuts should continue mapping to concrete Action values'
    $unknownActions = @($assignedActions | Where-Object { $_ -notin $actionValidateSet })
    $unknownActions | Should -BeNullOrEmpty -Because 'every quick shortcut action assignment must be accepted by the public -Action ValidateSet'

    $assignedTargetProfiles.Count | Should -BeGreaterThan 0 -Because 'targeted quick collect shortcuts should continue mapping to concrete TargetProfile values'
    $unknownProfiles = @($assignedTargetProfiles | Where-Object { $_ -notin $targetProfileValidateSet })
    $unknownProfiles | Should -BeNullOrEmpty -Because 'every quick shortcut TargetProfile assignment must be accepted by the public -TargetProfile ValidateSet'
  }

  It 'keeps explicit event-window fallback and bounded event-query behavior visible in source' {
    $effectiveWindow = Get-DcoirFunctionTextByName -Paths $script:SourceFiles -Name 'Get-CollectorEffectiveEventWindow'
    $filterBuilder = Get-DcoirFunctionTextByName -Paths $script:SourceFiles -Name 'Get-CollectorEventFilterHashtable'
    $boundedQuery = Get-DcoirFunctionTextByName -Paths $script:SourceFiles -Name 'Invoke-CollectorBoundedWinEventQuery'
    $summary = Get-DcoirFunctionTextByName -Paths $script:SourceFiles -Name 'Get-SecurityHighSignalSummaryText'

    Assert-DcoirTextContains -Text $effectiveWindow -Needle '[datetime]::TryParse($WindowStart' -Because 'explicit WindowStart must be parsed before use'
    Assert-DcoirTextContains -Text $effectiveWindow -Needle '[datetime]::TryParse($WindowEnd' -Because 'explicit WindowEnd must be parsed before use'
    Assert-DcoirTextContains -Text $effectiveWindow -Needle '$script:WindowStart = $null' -Because 'rejected explicit windows must be cleared so downstream scope text cannot reuse invalid input'
    Assert-DcoirTextContains -Text $effectiveWindow -Needle '$script:WindowEnd = $null' -Because 'rejected explicit windows must be cleared so downstream scope text cannot reuse invalid input'
    Assert-DcoirTextContains -Text $effectiveWindow -Needle 'EffectiveHours' -Because 'fallback behavior must stay observable in metadata'

    Assert-DcoirTextContains -Text $filterBuilder -Needle 'StartTime = $Window.StartTime' -Because 'event filter must always be start-bounded'
    Assert-DcoirTextContains -Text $filterBuilder -Needle '$fh.EndTime = $Window.EndTime' -Because 'explicit end bounds must be carried into event filters when present'
    Assert-DcoirTextContains -Text $filterBuilder -Needle '$fh.Id = $Ids' -Because 'event filters must preserve selected Event IDs'

    Assert-DcoirTextContains -Text $boundedQuery -Needle 'if ($MaxEvents -lt 1)' -Because 'event reads must refuse non-positive query limits'
    Assert-DcoirTextContains -Text $boundedQuery -Needle 'Get-WinEvent -FilterHashtable $FilterHashtable -MaxEvents $MaxEvents' -Because 'event reads must stay MaxEvents-bounded'
    Assert-DcoirTextContains -Text $summary -Needle '$queryLimit = [Math]::Max(0, ($Take * 4))' -Because 'high-signal summary must keep a deterministic upper bound before suppression filtering'
  }

  It 'keeps upload-safe chunking and late metadata finalization safeguards in place' {
    $chunker = Get-DcoirFunctionTextByName -Paths $script:SourceFiles -Name 'Split-TextArtifactIntoUploadSafeChunks'
    $safeLength = Get-DcoirFunctionTextByName -Paths $script:SourceFiles -Name 'Get-Utf8SafeChunkLength'
    $companion = Get-DcoirFunctionTextByName -Paths $script:SourceFiles -Name 'New-ProductionUploadSafeChunkCompanionsWithSkipStatus'
    $lateCollect = Get-DcoirFunctionTextByName -Paths $script:SourceFiles -Name 'New-CollectUploadArtifactsWithLateMetadataReport'
    $lateOverview = Get-DcoirFunctionTextByName -Paths $script:SourceFiles -Name 'New-AnalystOverviewArtifactWithLateMetadataReport'

    Assert-DcoirTextContains -Text $safeLength -Needle 'param([byte[]]$Bytes' -Because 'chunk boundaries must operate on raw bytes rather than character counts'
    Assert-DcoirTextContains -Text $safeLength -Needle '($Bytes[$lead] -band 0xC0) -eq 0x80' -Because 'UTF-8 continuation bytes must be detected before choosing a safe boundary'
    Assert-DcoirTextContains -Text $chunker -Needle '[System.IO.File]::ReadAllBytes($SourcePath)' -Because 'upload-safe chunking must read the source as bytes'
    Assert-DcoirTextContains -Text $chunker -Needle '[System.IO.File]::WriteAllBytes($chunkPath, $chunkBytes)' -Because 'upload-safe chunking must write byte-preserving chunks'
    Assert-DcoirTextContains -Text $chunker -Needle 'Get-Utf8SafeChunkLength' -Because 'upload-safe chunking must use UTF-8-safe boundaries'
    Assert-DcoirTextContains -Text $chunker -Needle 'chunk_count' -Because 'chunk manifests must expose chunk counts for analyst upload planning'
    Assert-DcoirTextContains -Text $companion -Needle 'UploadSafeChunkCompanionSkipped' -Because 'WhatIf/skipped companion generation must remain visible in state'
    Assert-DcoirTextContains -Text $lateCollect -Needle 'MetadataReportPath' -Because 'collect upload guidance must be built after the final metadata path is known'
    Assert-DcoirTextContains -Text $lateOverview -Needle 'MetadataReportPath' -Because 'analyst overview must reference the late-bound metadata path'
  }
}
