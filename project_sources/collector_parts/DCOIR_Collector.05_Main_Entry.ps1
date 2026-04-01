Apply-QuickShortcut

try {
  Ensure-Directory -Path $OutRoot

  switch ($Mode) {
    "Collect" {
      if ([string]::IsNullOrWhiteSpace($RunId)) {
        $RunId = Get-NewRunId
      }

      Purge-PreviousRuns -Root $OutRoot -CurrentPackageName $PackageName
      $dirs = Initialize-RunStructure -Root $OutRoot -CurrentRunId $RunId
      $Global:CurrentRunId = $RunId
      $Global:ExecutionTxtPath = Join-Path $dirs.LogsDir "collect_execution_log.txt"
      $Global:ExecutionJsonlPath = Join-Path $dirs.LogsDir "collect_execution_log.jsonl"
      $Global:ErrorsLogPath = Join-Path $dirs.LogsDir "errors.log"
      Set-Content -Path $Global:ExecutionTxtPath -Value ("DCOIR Collect Execution Log`r`nRunId={0}" -f $RunId) -Encoding UTF8
      Set-Content -Path $Global:ExecutionJsonlPath -Value "" -Encoding UTF8
      Set-Content -Path $Global:ErrorsLogPath -Value "" -Encoding UTF8

      $packagePath = Move-PackageToOutRoot -Root $OutRoot -CurrentPackageName $PackageName
      Expand-PackageToTools -PackagePath $packagePath -ToolsDir $dirs.ToolsDir

      $toolMap = Get-ToolMap -ToolsDir $dirs.ToolsDir
      $baselineReportPath = Join-Path $dirs.ReportsDir ("DCOIR_BASELINE_{0}_{1}.txt" -f $env:COMPUTERNAME, $RunId)
      $metadataReportPath = Join-Path $dirs.ReportsDir ("DCOIR_METADATA_{0}_{1}.txt" -f $env:COMPUTERNAME, $RunId)

      $state = @{
        RunId = $RunId
        Host = $env:COMPUTERNAME
        OutRoot = $OutRoot
        RunRoot = $dirs.RunRoot
        ToolsDir = $dirs.ToolsDir
        ReportsDir = $dirs.ReportsDir
        ArtifactsDir = $dirs.ArtifactsDir
        EnrichSessionsDir = $dirs.EnrichSessionsDir
        LogsDir = $dirs.LogsDir
        BundlesDir = $dirs.BundlesDir
        StatePath = $dirs.StatePath
        PackagePath = $packagePath
        BaselineReportPath = $baselineReportPath
        MetadataReportPath = $metadataReportPath
        CollectBundlePath = $null
        EnrichSessions = @()
        EnrichSessionCounter = 0
        OpenEnrichSessionId = $null
        CreatedLocal = (Get-Date).ToString("o")
        CreatedUTC = (Get-Date).ToUniversalTime().ToString("o")
        CollectorVersion = $ScriptVersion
      }

      $baseline = New-BaselineReport -State $state -ToolMap $toolMap
      Write-ReportFile -Path $baselineReportPath -Text $baseline.ReportText

      $metadataText = New-MetadataReport -State $state -ToolMap $toolMap
      Write-ReportFile -Path $metadataReportPath -Text $metadataText

      $collectManifest = New-Manifest -ManifestPath (Join-Path $state.RunRoot "manifest_collect.json") -State $state -ModeName "Collect" -TierName $Tier -Files (
        @($baselineReportPath, $metadataReportPath, $Global:ExecutionTxtPath, $Global:ExecutionJsonlPath, $Global:ErrorsLogPath) + $baseline.ArtifactPaths
      ) -ToolMap $toolMap -Extra @{ collect_bundle = $null }

      $bundlePath = New-BundleZip -BundlesDir $state.BundlesDir -BundleName ("DCOIR_COLLECT_BUNDLE_{0}_{1}.zip" -f $env:COMPUTERNAME, $RunId) -Paths @(
        $baselineReportPath,
        $metadataReportPath,
        $state.ArtifactsDir,
        $Global:ExecutionTxtPath,
        $Global:ExecutionJsonlPath,
        $Global:ErrorsLogPath,
        $collectManifest
      )

      $state.CollectBundlePath = $bundlePath
      Save-State -State $state

      $metadataText = New-MetadataReport -State $state -ToolMap $toolMap
      Write-ReportFile -Path $metadataReportPath -Text $metadataText
      $collectManifest = New-Manifest -ManifestPath (Join-Path $state.RunRoot "manifest_collect.json") -State $state -ModeName "Collect" -TierName $Tier -Files (
        @($baselineReportPath, $metadataReportPath, $Global:ExecutionTxtPath, $Global:ExecutionJsonlPath, $Global:ErrorsLogPath) + $baseline.ArtifactPaths
      ) -ToolMap $toolMap -Extra @{ collect_bundle = $bundlePath }

      $status = "SUCCESS"
      if (@($Global:CollectorErrors).Count -gt 0) { $status = "PARTIAL_SUCCESS" }

      $collectorCommandBase = Get-CollectorPowerShellCommandBase
      $deleteScriptCommand = Get-CollectorDeleteScriptCommandText

      Write-Output ("STATUS={0}" -f $status)
      Write-Output ("RUN_ID={0}" -f $RunId)
      Write-Output ("BASELINE_REPORT_PATH={0}" -f $baselineReportPath)
      Write-Output ("METADATA_REPORT_PATH={0}" -f $metadataReportPath)
      Write-Output ("COLLECT_BUNDLE_PATH={0}" -f $bundlePath)
      Write-Output ('NEXT_GET_FILE=get-file --path "{0}" --comment "Retrieve DCOIR collect bundle"' -f $bundlePath)
      Write-Output ('CLEANUP_COMMAND=execute --command "{0} -Quick cleanup" --comment "Running Cleanup on DCOIR_Collector"' -f $collectorCommandBase)
      Write-Output ("DELETE_SCRIPT_COMMAND={0}" -f $deleteScriptCommand)
      Write-QuickNextSteps -Phase "Collect"
    }

    "Enrich" {
      $loaded = Load-State -Root $OutRoot -CurrentRunId $RunId
      $state = Convert-StateObjectToHashtable -InputObject $loaded
      $Global:CurrentRunId = [string]$state.RunId

      if (-not $Action -and -not $FinalizeEnrichSession) {
        throw "Enrich mode requires -Action or -FinalizeEnrichSession."
      }

      $session = Initialize-EnrichSession -State $state -RequestedSessionId $EnrichSessionId -ForceNew:$NewEnrichSession

      $logStamp = Get-Date -Format "yyyyMMdd_HHmmss"
      $actionLabel = if ($Action) { $Action } else { "FinalizeSession" }
      $Global:ExecutionTxtPath = Join-Path $session.LogsDir ("enrich_{0}_{1}_execution_log.txt" -f $actionLabel, $logStamp)
      $Global:ExecutionJsonlPath = Join-Path $session.LogsDir ("enrich_{0}_{1}_execution_log.jsonl" -f $actionLabel, $logStamp)
      $Global:ErrorsLogPath = Join-Path $session.LogsDir ("enrich_{0}_{1}_errors.log" -f $actionLabel, $logStamp)
      Set-Content -Path $Global:ExecutionTxtPath -Value ("DCOIR Enrich Execution Log`r`nRunId={0}`r`nEnrichSessionId={1}`r`nAction={2}" -f $state.RunId, $session.SessionId, $actionLabel) -Encoding UTF8
      Set-Content -Path $Global:ExecutionJsonlPath -Value "" -Encoding UTF8
      Set-Content -Path $Global:ErrorsLogPath -Value "" -Encoding UTF8

      $toolMap = Get-ToolMap -ToolsDir $state.ToolsDir

      $result = $null
      if ($Action) {
        $result = Invoke-EnrichmentAction -State $state -Session $session -ToolMap $toolMap
      }

      $bundlePath = $null
      $sessionStatus = "OPEN"
      if ($FinalizeEnrichSession) {
        $bundlePath = Finalize-EnrichSession -State $state -Session $session -ToolMap $toolMap
        $sessionStatus = "FINALIZED"
      }

      Save-State -State $state

      $status = "SUCCESS"
      if (@($Global:CollectorErrors).Count -gt 0) { $status = "PARTIAL_SUCCESS" }

      $deleteScriptCommand = Get-CollectorDeleteScriptCommandText

      Write-Output ("STATUS={0}" -f $status)
      Write-Output ("RUN_ID={0}" -f $state.RunId)
      Write-Output ("ENRICH_SESSION_ID={0}" -f $session.SessionId)
      if ($result) {
        Write-Output ("ENRICH_REPORT_PATH={0}" -f $result.ReportPath)
        Write-Output ("ACTION_ARTIFACT_PATH={0}" -f $result.ActionArtifactPath)
        if ($result.StagedPath) {
          Write-Output ("STAGED_PATH={0}" -f $result.StagedPath)
        }
      } else {
        Write-Output ("ENRICH_REPORT_PATH={0}" -f $session.SummaryPath)
      }
      Write-Output ("SESSION_STATUS={0}" -f $sessionStatus)
      if ($bundlePath) {
        Write-Output ("ENRICH_BUNDLE_PATH={0}" -f $bundlePath)
        Write-Output ('NEXT_GET_FILE=get-file --path "{0}" --comment "Retrieve DCOIR enrich bundle"' -f $bundlePath)
      } else {
        Write-Output ("NEXT_OPTIONS=Continue current session with -EnrichSessionId {0} or finalize it with -FinalizeEnrichSession" -f $session.SessionId)
      }
      Write-Output ("DELETE_SCRIPT_COMMAND={0}" -f $deleteScriptCommand)
      if ($sessionStatus -eq "FINALIZED") {
        Write-QuickNextSteps -Phase "EnrichFinalized"
      } else {
        Write-QuickNextSteps -Phase "EnrichOpen"
      }
    }

    "Cleanup" {
      $loaded = Load-State -Root $OutRoot -CurrentRunId $RunId
      Invoke-Cleanup -StateObject $loaded
      Write-Output ("CLEANUP_STATUS=COMPLETE")
      Write-Output ("RUN_ID={0}" -f $loaded.RunId)
      Write-Output ("DELETE_SCRIPT_COMMAND={0}" -f (Get-CollectorDeleteScriptCommandText))
      Write-QuickNextSteps -Phase "Cleanup"
    }
  }
} catch {
  Add-CollectorError $_.Exception.Message
  Write-Output ("STATUS=ERROR")
  Write-Output ("MESSAGE={0}" -f $_.Exception.Message)
  exit 1
}
