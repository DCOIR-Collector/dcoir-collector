function Get-QuickUsageText {
  $cmd = Get-CollectorPowerShellCommandBase
  return @(
    "Quick command examples:",
    "  $cmd -Quick collect-t1",
    "  $cmd -Quick collect-t2",
    '  $cmd -Quick collect-targeted-popup -Target "User reported popup around 2026-04-08T09:00Z"',
    '  $cmd -Quick collect-targeted-script -Target "Suspicious script execution follow-up" -Target2 "powershell.exe"',
    "  $cmd -Quick enrich-start-tcp",
    "  $cmd -Quick enrich-add-tcp",
    "  $cmd -Quick enrich-start-logtext -Target Security",
    "  $cmd -Quick enrich-add-logtext -Target Security",
    "  $cmd -Quick enrich-start-lograw -Target Security",
    "  $cmd -Quick enrich-add-lograw -Target Security",
    "  $cmd -Quick enrich-start-sigcheck -Target C:\Windows\System32\notepad.exe",
    "  $cmd -Quick enrich-add-sigcheck -Target C:\Windows\System32\notepad.exe",
    "  $cmd -Quick enrich-start-listdlls -Target 1234",
    "  $cmd -Quick enrich-add-listdlls -Target 1234",
    "  $cmd -Quick enrich-finalize",
    "  $cmd -Quick cleanup"
  ) -join [Environment]::NewLine
}

function Get-CollectorHelpText {
  $cmd = Get-CollectorPowerShellCommandBase
  $lines = @()
  $lines += "DCOIR Collector Help"
  $lines += ""
  $lines += "Top-level usage:"
  $lines += "  $cmd -Help"
  $lines += "  $cmd -Mode Collect -Tier T1"
  $lines += "  $cmd -Mode Collect -Tier T2"
  $lines += "  $cmd -Mode Enrich -Action TcpvconRefresh -NewEnrichSession"
  $lines += "  $cmd -Mode Cleanup"
  $lines += ""
  $lines += "Quick usage:"
  $lines += (Get-QuickUsageText)
  $lines += ""
  $lines += "Accepted top-level modes: Collect, Enrich, Cleanup"
  $lines += "Accepted tiers: T1, T2"
  $lines += "Accepted target profiles: Generic, PopupWindow, ScriptExecution, PersistenceFollowUp, NetworkOnly, ProcessAndPowerShell"
  $lines += ""
  $lines += "Targeted usage examples:"
  $lines += '  $cmd -Targeted -TargetProfile PopupWindow -WindowStart "2026-04-08T09:00:00Z" -WindowEnd "2026-04-08T10:00:00Z" -UserReport "User reported popup"'
  $lines += '  $cmd -Targeted -TargetProfile ScriptExecution -WindowStart "2026-04-08T09:00:00Z" -WindowEnd "2026-04-08T10:00:00Z" -UserReport "Suspicious script execution" -FocusProcess "powershell.exe"'
  $lines += '  $cmd -Targeted -TargetProfile NetworkOnly -Hours 6 -FocusIndicator "198.51.100.25" -FocusIndicatorType "ip"'
  $lines += ""
  $lines += "Targeted guidance:"
  $lines += "  - Targeted mode currently narrows guidance, scope intent, artifact prioritization, and next actions."
  $lines += "  - It does not yet rewrite every baseline helper into exact start/end filtering across all artifact families."
  $lines += "  - Use -WindowStart and -WindowEnd to annotate explicit time windows for analyst guidance and follow-up."
  $lines += "  - Use -IncludeArtifactCategory, -FocusProcess, -FocusPath, -FocusIndicator, and -UserReport to make the request narrower and more explainable."
  $lines += ""
  $lines += "Accepted enrich actions:"
  $lines += "  SigcheckPath, ListDllsPid, AccessChkFile, AccessChkService, AccessChkReg, StringsPath, StreamsPath, TcpvconRefresh, LogText, LogRaw, PullSuspiciousFile, PullScriptOrConfig, PullTaskXml, PullServiceBinary, PullWmiReferencedFile"
  $lines += ""
  $lines += "Lane guidance:"
  $lines += "  - Endpoint response-console usage should wrap the PowerShell command in an Elastic response action."
  $lines += "  - Local workstation and regression usage should run the PowerShell command directly without the response-action wrapper."
  $lines += "  - Prefer PowerShell 5.1 syntax and the runtime filename DCOIR_Collector.ps1."
  return ($lines -join [Environment]::NewLine)
}

function Apply-QuickShortcut {
  param()

  if ([string]::IsNullOrWhiteSpace($Quick)) { return }
  $q = $Quick.ToLowerInvariant().Replace('_','-')

  function Require-QuickTargetPath {
    if ([string]::IsNullOrWhiteSpace($Target)) { throw ("Quick {0} requires -Target <path>." -f $q) }
    return $Target
  }

  function Require-QuickTargetName {
    param([string]$Label)
    if ([string]::IsNullOrWhiteSpace($Target)) { throw ("Quick {0} requires -Target <{1}>." -f $q, $Label) }
    return $Target
  }

  function Require-QuickTargetPid {
    if ([string]::IsNullOrWhiteSpace($Target)) { throw ("Quick {0} requires -Target <pid>." -f $q) }
    $tmp = 0
    if (-not [int]::TryParse($Target, [ref]$tmp)) { throw ("Quick {0} requires a numeric -Target <pid>." -f $q) }
    return $tmp
  }

  switch ($q) {
    "collect-t1" { $script:Mode = "Collect"; $script:Tier = "T1"; if ($Hours -eq 24) { $script:Hours = 24 }; return }
    "collect-t2" { $script:Mode = "Collect"; $script:Tier = "T2"; if ($Hours -eq 24) { $script:Hours = 72 }; return }
    "collect-targeted-popup" {
      $script:Mode = "Collect"
      $script:Tier = "T1"
      $script:Targeted = $true
      $script:TargetProfile = "PopupWindow"
      if ($Hours -eq 24) { $script:Hours = 12 }
      if (-not [string]::IsNullOrWhiteSpace($Target)) { $script:UserReport = $Target }
      return
    }
    "collect-targeted-script" {
      $script:Mode = "Collect"
      $script:Tier = "T1"
      $script:Targeted = $true
      $script:TargetProfile = "ScriptExecution"
      if ($Hours -eq 24) { $script:Hours = 12 }
      if (-not [string]::IsNullOrWhiteSpace($Target)) { $script:UserReport = $Target }
      if (-not [string]::IsNullOrWhiteSpace($Target2)) { $script:FocusProcess = $Target2 }
      return
    }
    "enrich-start-tcp" { $script:Mode = "Enrich"; $script:NewEnrichSession = $true; $script:Action = "TcpvconRefresh"; return }
    "enrich-add-tcp" { $script:Mode = "Enrich"; $script:Action = "TcpvconRefresh"; return }
    "enrich-start-logtext" { $script:Mode = "Enrich"; $script:NewEnrichSession = $true; $script:Action = "LogText"; $script:LogName = if ([string]::IsNullOrWhiteSpace($Target)) { "Security" } else { $Target }; return }
    "enrich-add-logtext" { $script:Mode = "Enrich"; $script:Action = "LogText"; $script:LogName = if ([string]::IsNullOrWhiteSpace($Target)) { "Security" } else { $Target }; return }
    "enrich-start-lograw" { $script:Mode = "Enrich"; $script:NewEnrichSession = $true; $script:Action = "LogRaw"; $script:LogName = if ([string]::IsNullOrWhiteSpace($Target)) { "Security" } else { $Target }; return }
    "enrich-add-lograw" { $script:Mode = "Enrich"; $script:Action = "LogRaw"; $script:LogName = if ([string]::IsNullOrWhiteSpace($Target)) { "Security" } else { $Target }; return }
    "enrich-start-sigcheck" { $script:Mode = "Enrich"; $script:NewEnrichSession = $true; $script:Action = "SigcheckPath"; $script:Path = Require-QuickTargetPath; return }
    "enrich-add-sigcheck" { $script:Mode = "Enrich"; $script:Action = "SigcheckPath"; $script:Path = Require-QuickTargetPath; return }
    "enrich-start-listdlls" { $script:Mode = "Enrich"; $script:NewEnrichSession = $true; $script:Action = "ListDllsPid"; $script:TargetPid = Require-QuickTargetPid; return }
    "enrich-add-listdlls" { $script:Mode = "Enrich"; $script:Action = "ListDllsPid"; $script:TargetPid = Require-QuickTargetPid; return }
    "enrich-start-access-file" { $script:Mode = "Enrich"; $script:NewEnrichSession = $true; $script:Action = "AccessChkFile"; $script:Path = Require-QuickTargetPath; return }
    "enrich-add-access-file" { $script:Mode = "Enrich"; $script:Action = "AccessChkFile"; $script:Path = Require-QuickTargetPath; return }
    "enrich-start-access-service" { $script:Mode = "Enrich"; $script:NewEnrichSession = $true; $script:Action = "AccessChkService"; $script:ServiceName = Require-QuickTargetName "service name"; return }
    "enrich-add-access-service" { $script:Mode = "Enrich"; $script:Action = "AccessChkService"; $script:ServiceName = Require-QuickTargetName "service name"; return }
    "enrich-start-access-reg" { $script:Mode = "Enrich"; $script:NewEnrichSession = $true; $script:Action = "AccessChkReg"; $script:RegistryPath = Require-QuickTargetName "registry path"; return }
    "enrich-add-access-reg" { $script:Mode = "Enrich"; $script:Action = "AccessChkReg"; $script:RegistryPath = Require-QuickTargetName "registry path"; return }
    "enrich-start-strings" { $script:Mode = "Enrich"; $script:NewEnrichSession = $true; $script:Action = "StringsPath"; $script:Path = Require-QuickTargetPath; return }
    "enrich-add-strings" { $script:Mode = "Enrich"; $script:Action = "StringsPath"; $script:Path = Require-QuickTargetPath; return }
    "enrich-start-streams" { $script:Mode = "Enrich"; $script:NewEnrichSession = $true; $script:Action = "StreamsPath"; $script:Path = Require-QuickTargetPath; return }
    "enrich-add-streams" { $script:Mode = "Enrich"; $script:Action = "StreamsPath"; $script:Path = Require-QuickTargetPath; return }
    "enrich-start-pull-file" { $script:Mode = "Enrich"; $script:NewEnrichSession = $true; $script:Action = "PullSuspiciousFile"; $script:Path = Require-QuickTargetPath; return }
    "enrich-add-pull-file" { $script:Mode = "Enrich"; $script:Action = "PullSuspiciousFile"; $script:Path = Require-QuickTargetPath; return }
    "enrich-start-pull-script" { $script:Mode = "Enrich"; $script:NewEnrichSession = $true; $script:Action = "PullScriptOrConfig"; $script:Path = Require-QuickTargetPath; return }
    "enrich-add-pull-script" { $script:Mode = "Enrich"; $script:Action = "PullScriptOrConfig"; $script:Path = Require-QuickTargetPath; return }
    "enrich-start-pull-task" { $script:Mode = "Enrich"; $script:NewEnrichSession = $true; $script:Action = "PullTaskXml"; $script:Path = Require-QuickTargetName "task path"; return }
    "enrich-add-pull-task" { $script:Mode = "Enrich"; $script:Action = "PullTaskXml"; $script:Path = Require-QuickTargetName "task path"; return }
    "enrich-start-pull-service" { $script:Mode = "Enrich"; $script:NewEnrichSession = $true; $script:Action = "PullServiceBinary"; $script:ServiceName = Require-QuickTargetName "service name"; return }
    "enrich-add-pull-service" { $script:Mode = "Enrich"; $script:Action = "PullServiceBinary"; $script:ServiceName = Require-QuickTargetName "service name"; return }
    "enrich-start-pull-wmi-file" { $script:Mode = "Enrich"; $script:NewEnrichSession = $true; $script:Action = "PullWmiReferencedFile"; $script:Path = Require-QuickTargetPath; return }
    "enrich-add-pull-wmi-file" { $script:Mode = "Enrich"; $script:Action = "PullWmiReferencedFile"; $script:Path = Require-QuickTargetPath; return }
    "enrich-finalize" { $script:Mode = "Enrich"; $script:FinalizeEnrichSession = $true; return }
    "cleanup" { $script:Mode = "Cleanup"; return }
    "help" { throw (Get-CollectorHelpText) }
    default { throw ("Unknown -Quick value: {0}`r`n{1}" -f $Quick, (Get-CollectorHelpText)) }
  }
}

function Write-QuickNextSteps {
  param([string]$Phase)

  $cmd = Get-CollectorPowerShellCommandBase
  Write-Output "NEXT_QUICK_COMMANDS"
  switch ($Phase) {
    "Collect" {
      Write-Output ('1. execute --command "{0} -Quick enrich-start-tcp" --comment "Run DCOIR TCP enrichment"' -f $cmd)
      Write-Output ('2. execute --command "{0} -Quick enrich-start-lograw -Target Security" --comment "Run DCOIR raw Security log enrichment"' -f $cmd)
      Write-Output ('3. If Gemini upload is the next step, prefer UPLOAD_SUMMARY_PATH, ATTACHMENT_BUDGET_MANIFEST_PATH, COLLECTION_SCOPE_PATH, and representative final_artifacts slices before the full baseline report.' )
      Write-Output ('4. execute --command "{0} -Quick cleanup" --comment "Running Cleanup on DCOIR_Collector"' -f $cmd)
    }
    "EnrichOpen" {
      Write-Output ('1. execute --command "{0} -Quick enrich-add-logtext -Target Security" --comment "Add Security log text enrichment to current DCOIR session"' -f $cmd)
      Write-Output ('2. execute --command "{0} -Quick enrich-finalize" --comment "Finalize current DCOIR enrichment session"' -f $cmd)
      Write-Output '3. enrich-add-* should reuse the current open session unless you explicitly request a new one.'
    }
    "EnrichFinalized" {
      Write-Output '1. Review the finalized bundle you already retrieved before recommending another endpoint retrieval of the same path.'
      Write-Output ('2. execute --command "{0} -Quick cleanup" --comment "Running Cleanup on DCOIR_Collector"' -f $cmd)
    }
    "Cleanup" {
      Write-Output '1. Local script file remains in place by design unless you run the explicit delete command.'
      Write-Output ('2. execute --command "{0} -Quick collect-t1" --comment "Run DCOIR collect T1"' -f $cmd)
      Write-Output ('3. execute --command "{0} -Quick collect-targeted-popup -Target ""User reported popup follow-up""" --comment "Run DCOIR targeted popup-style collect"' -f $cmd)
    }
  }
}

function Invoke-Cleanup {
  param($StateObject)
  $targets = @([string]$StateObject.PackagePath,[string]$StateObject.RunRoot) | Where-Object { $_ -and (Test-Path -LiteralPath $_) }
  foreach ($target in $targets) {
    Remove-Item -LiteralPath $target -Recurse -Force -ErrorAction SilentlyContinue
  }
}