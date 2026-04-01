function Get-QuickUsageText {
  $cmd = Get-CollectorPowerShellCommandBase
  return @(
    "Quick command examples:"
    "  $cmd -Quick collect-t1"
    "  $cmd -Quick collect-t2"
    "  $cmd -Quick enrich-start-tcp"
    "  $cmd -Quick enrich-add-tcp"
    "  $cmd -Quick enrich-start-logtext -Target Security"
    "  $cmd -Quick enrich-add-logtext -Target Security"
    "  $cmd -Quick enrich-start-lograw -Target Security"
    "  $cmd -Quick enrich-add-lograw -Target Security"
    "  $cmd -Quick enrich-start-sigcheck -Target C:\Windows\System32\notepad.exe"
    "  $cmd -Quick enrich-add-sigcheck -Target C:\Windows\System32\notepad.exe"
    "  $cmd -Quick enrich-start-listdlls -Target 1234"
    "  $cmd -Quick enrich-add-listdlls -Target 1234"
    "  $cmd -Quick enrich-start-access-file -Target C:\Windows\System32\notepad.exe"
    "  $cmd -Quick enrich-add-access-file -Target C:\Windows\System32\notepad.exe"
    "  $cmd -Quick enrich-start-access-service -Target EventLog"
    "  $cmd -Quick enrich-add-access-service -Target EventLog"
    "  $cmd -Quick enrich-start-access-reg -Target HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon"
    "  $cmd -Quick enrich-add-access-reg -Target HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon"
    "  $cmd -Quick enrich-start-strings -Target C:\Windows\System32\notepad.exe"
    "  $cmd -Quick enrich-add-strings -Target C:\Windows\System32\notepad.exe"
    "  $cmd -Quick enrich-start-streams -Target C:\Windows\System32\notepad.exe"
    "  $cmd -Quick enrich-add-streams -Target C:\Windows\System32\notepad.exe"
    "  $cmd -Quick enrich-start-pull-file -Target C:\Windows\System32\notepad.exe"
    "  $cmd -Quick enrich-add-pull-file -Target C:\Windows\System32\notepad.exe"
    "  $cmd -Quick enrich-start-pull-script -Target C:\Temp\sample.ps1"
    "  $cmd -Quick enrich-add-pull-script -Target C:\Temp\sample.ps1"
    "  $cmd -Quick enrich-start-pull-task -Target \\Microsoft\\Windows\\Defrag\\ScheduledDefrag"
    "  $cmd -Quick enrich-add-pull-task -Target \\Microsoft\\Windows\\Defrag\\ScheduledDefrag"
    "  $cmd -Quick enrich-start-pull-service -Target EventLog"
    "  $cmd -Quick enrich-add-pull-service -Target EventLog"
    "  $cmd -Quick enrich-start-pull-wmi-file -Target C:\Temp\sample.ps1"
    "  $cmd -Quick enrich-add-pull-wmi-file -Target C:\Temp\sample.ps1"
    "  $cmd -Quick enrich-finalize"
    "  $cmd -Quick cleanup"
  ) -join [Environment]::NewLine
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
    "collect-t1" {
      $script:Mode = "Collect"
      $script:Tier = "T1"
      if ($Hours -eq 24) { $script:Hours = 24 }
      return
    }
    "collect-t2" {
      $script:Mode = "Collect"
      $script:Tier = "T2"
      if ($Hours -eq 24) { $script:Hours = 72 }
      return
    }
    "enrich-start-tcp" {
      $script:Mode = "Enrich"
      $script:NewEnrichSession = $true
      $script:Action = "TcpvconRefresh"
      return
    }
    "enrich-add-tcp" {
      $script:Mode = "Enrich"
      $script:Action = "TcpvconRefresh"
      return
    }
    "enrich-start-logtext" {
      $script:Mode = "Enrich"
      $script:NewEnrichSession = $true
      $script:Action = "LogText"
      $script:LogName = if ([string]::IsNullOrWhiteSpace($Target)) { "Security" } else { $Target }
      return
    }
    "enrich-add-logtext" {
      $script:Mode = "Enrich"
      $script:Action = "LogText"
      $script:LogName = if ([string]::IsNullOrWhiteSpace($Target)) { "Security" } else { $Target }
      return
    }
    "enrich-start-lograw" {
      $script:Mode = "Enrich"
      $script:NewEnrichSession = $true
      $script:Action = "LogRaw"
      $script:LogName = if ([string]::IsNullOrWhiteSpace($Target)) { "Security" } else { $Target }
      return
    }
    "enrich-add-lograw" {
      $script:Mode = "Enrich"
      $script:Action = "LogRaw"
      $script:LogName = if ([string]::IsNullOrWhiteSpace($Target)) { "Security" } else { $Target }
      return
    }
    "enrich-start-sigcheck" {
      $script:Mode = "Enrich"
      $script:NewEnrichSession = $true
      $script:Action = "SigcheckPath"
      $script:Path = Require-QuickTargetPath
      return
    }
    "enrich-add-sigcheck" {
      $script:Mode = "Enrich"
      $script:Action = "SigcheckPath"
      $script:Path = Require-QuickTargetPath
      return
    }
    "enrich-start-listdlls" {
      $script:Mode = "Enrich"
      $script:NewEnrichSession = $true
      $script:Action = "ListDllsPid"
      $script:TargetPid = Require-QuickTargetPid
      return
    }
    "enrich-add-listdlls" {
      $script:Mode = "Enrich"
      $script:Action = "ListDllsPid"
      $script:TargetPid = Require-QuickTargetPid
      return
    }
    "enrich-start-access-file" {
      $script:Mode = "Enrich"
      $script:NewEnrichSession = $true
      $script:Action = "AccessChkFile"
      $script:Path = Require-QuickTargetPath
      return
    }
    "enrich-add-access-file" {
      $script:Mode = "Enrich"
      $script:Action = "AccessChkFile"
      $script:Path = Require-QuickTargetPath
      return
    }
    "enrich-start-access-service" {
      $script:Mode = "Enrich"
      $script:NewEnrichSession = $true
      $script:Action = "AccessChkService"
      $script:ServiceName = Require-QuickTargetName "service name"
      return
    }
    "enrich-add-access-service" {
      $script:Mode = "Enrich"
      $script:Action = "AccessChkService"
      $script:ServiceName = Require-QuickTargetName "service name"
      return
    }
    "enrich-start-access-reg" {
      $script:Mode = "Enrich"
      $script:NewEnrichSession = $true
      $script:Action = "AccessChkReg"
      $script:RegistryPath = Require-QuickTargetName "registry path"
      return
    }
    "enrich-add-access-reg" {
      $script:Mode = "Enrich"
      $script:Action = "AccessChkReg"
      $script:RegistryPath = Require-QuickTargetName "registry path"
      return
    }
    "enrich-start-strings" {
      $script:Mode = "Enrich"
      $script:NewEnrichSession = $true
      $script:Action = "StringsPath"
      $script:Path = Require-QuickTargetPath
      return
    }
    "enrich-add-strings" {
      $script:Mode = "Enrich"
      $script:Action = "StringsPath"
      $script:Path = Require-QuickTargetPath
      return
    }
    "enrich-start-streams" {
      $script:Mode = "Enrich"
      $script:NewEnrichSession = $true
      $script:Action = "StreamsPath"
      $script:Path = Require-QuickTargetPath
      return
    }
    "enrich-add-streams" {
      $script:Mode = "Enrich"
      $script:Action = "StreamsPath"
      $script:Path = Require-QuickTargetPath
      return
    }
    "enrich-start-pull-file" {
      $script:Mode = "Enrich"
      $script:NewEnrichSession = $true
      $script:Action = "PullSuspiciousFile"
      $script:Path = Require-QuickTargetPath
      return
    }
    "enrich-add-pull-file" {
      $script:Mode = "Enrich"
      $script:Action = "PullSuspiciousFile"
      $script:Path = Require-QuickTargetPath
      return
    }
    "enrich-start-pull-script" {
      $script:Mode = "Enrich"
      $script:NewEnrichSession = $true
      $script:Action = "PullScriptOrConfig"
      $script:Path = Require-QuickTargetPath
      return
    }
    "enrich-add-pull-script" {
      $script:Mode = "Enrich"
      $script:Action = "PullScriptOrConfig"
      $script:Path = Require-QuickTargetPath
      return
    }
    "enrich-start-pull-task" {
      $script:Mode = "Enrich"
      $script:NewEnrichSession = $true
      $script:Action = "PullTaskXml"
      $script:Path = Require-QuickTargetName "task path"
      return
    }
    "enrich-add-pull-task" {
      $script:Mode = "Enrich"
      $script:Action = "PullTaskXml"
      $script:Path = Require-QuickTargetName "task path"
      return
    }
    "enrich-start-pull-service" {
      $script:Mode = "Enrich"
      $script:NewEnrichSession = $true
      $script:Action = "PullServiceBinary"
      $script:ServiceName = Require-QuickTargetName "service name"
      return
    }
    "enrich-add-pull-service" {
      $script:Mode = "Enrich"
      $script:Action = "PullServiceBinary"
      $script:ServiceName = Require-QuickTargetName "service name"
      return
    }
    "enrich-start-pull-wmi-file" {
      $script:Mode = "Enrich"
      $script:NewEnrichSession = $true
      $script:Action = "PullWmiReferencedFile"
      $script:Path = Require-QuickTargetPath
      return
    }
    "enrich-add-pull-wmi-file" {
      $script:Mode = "Enrich"
      $script:Action = "PullWmiReferencedFile"
      $script:Path = Require-QuickTargetPath
      return
    }
    "enrich-finalize" {
      $script:Mode = "Enrich"
      $script:FinalizeEnrichSession = $true
      return
    }
    "cleanup" {
      $script:Mode = "Cleanup"
      return
    }
    "help" {
      throw (Get-QuickUsageText)
    }
    default {
      throw ("Unknown -Quick value: {0}`r`n{1}" -f $Quick, (Get-QuickUsageText))
    }
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
      Write-Output ('3. execute --command "{0} -Quick cleanup" --comment "Running Cleanup on DCOIR_Collector"' -f $cmd)
    }
    "EnrichOpen" {
      Write-Output ('1. execute --command "{0} -Quick enrich-add-logtext -Target Security" --comment "Add Security log text enrichment to current DCOIR session"' -f $cmd)
      Write-Output ('2. execute --command "{0} -Quick enrich-finalize" --comment "Finalize current DCOIR enrichment session"' -f $cmd)
    }
    "EnrichFinalized" {
      Write-Output '1. Retrieve the enrich bundle with the NEXT_GET_FILE command shown above'
      Write-Output ('2. execute --command "{0} -Quick cleanup" --comment "Running Cleanup on DCOIR_Collector"' -f $cmd)
    }
    "Cleanup" {
      Write-Output '1. Local script file remains in place by design'
      Write-Output ('2. execute --command "{0} -Quick collect-t1" --comment "Run DCOIR collect T1"' -f $cmd)
      Write-Output ('3. execute --command "{0} -Quick collect-t2" --comment "Run DCOIR collect T2"' -f $cmd)
    }
  }
}

function Invoke-Cleanup {
  param($StateObject)

  $targets = @(
    [string]$StateObject.PackagePath,
    [string]$StateObject.RunRoot
  ) | Where-Object { $_ -and (Test-Path -LiteralPath $_) }

  foreach ($target in $targets) {
    Remove-Item -LiteralPath $target -Recurse -Force -ErrorAction SilentlyContinue
  }
}
