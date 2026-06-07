<#
.SYNOPSIS
DCOIR collector quick-interface, help-text, and cleanup helpers.

.DESCRIPTION
Builds the operator-facing quick-command examples and help text, translates supported
-Quick shortcuts into full collector parameter sets, prints next-step guidance after
major phases, and removes run/package artifacts during cleanup.

.FILE NAME
DCOIR_Collector.04_Quick_Interface_And_Output.ps1

.INPUTS
Collector runtime globals such as Quick, Target, Target2, Hours, and the current state
object passed to cleanup.

.OUTPUTS
Strings for help/usage and next-step guidance, updated collector runtime parameters for
quick shortcuts, and cleanup side effects on package/run paths.
#>

<#
.SYNOPSIS
Builds the short quick-command usage text.

.DESCRIPTION
Returns the operator-facing quick-command examples used by the collector help surface.

.FUNCTION NAME
Get-QuickUsageText

.INPUTS
No direct parameters.

.OUTPUTS
String containing newline-joined quick-command examples.
#>
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
    "  $cmd -Quick cleanup",
    "  $cmd -Quick help-collect",
    "  $cmd -Quick help-enrich",
    "  $cmd -Quick help-cleanup",
    "  $cmd -Quick help-targeted",
    "  $cmd -Quick help-version"
  ) -join [Environment]::NewLine
}

<#
.SYNOPSIS
Builds the collector build-identity string.

.DESCRIPTION
Returns the transport/runtime identity string used by version output and validation.

.FUNCTION NAME
Get-CollectorBuildIdentity

.INPUTS
Optional version string.

.OUTPUTS
String build identity.
#>
function Get-CollectorBuildIdentity {
  param([string]$Version = $ScriptVersion)
  return ("DCOIR_Collector.ps1/{0}" -f $Version)
}

<#
.SYNOPSIS
Builds the collector version text block.

.DESCRIPTION
Returns the collector version, build identity, runtime filename, package name, and
script path in key-value form.

.FUNCTION NAME
Get-CollectorVersionText

.INPUTS
No direct parameters.

.OUTPUTS
String containing newline-joined version/build metadata.
#>
function Get-CollectorVersionText {
  $scriptPath = Get-CollectorAbsolutePath
  $resolvedPackageName = if ([string]::IsNullOrWhiteSpace($PackageName)) { "DCOIR_Collector.zip" } else { $PackageName }
  return @(
    ("COLLECTOR_VERSION={0}" -f $ScriptVersion),
    ("COLLECTOR_BUILD_IDENTITY={0}" -f (Get-CollectorBuildIdentity)),
    "COLLECTOR_RUNTIME_FILENAME=DCOIR_Collector.ps1",
    ("EXPECTED_PACKAGE_NAME={0}" -f $resolvedPackageName),
    ("COLLECTOR_SCRIPT_PATH={0}" -f $scriptPath)
  ) -join [Environment]::NewLine
}

<#
.SYNOPSIS
Builds the delete-script command text.

.DESCRIPTION
Returns the response-action-safe literal-path script-removal command for the uploaded
collector file.

.FUNCTION NAME
Get-CollectorDeleteScriptCommandText

.INPUTS
No direct parameters.

.OUTPUTS
String delete-script command.
#>
function Get-CollectorDeleteScriptCommandText {
  $collectorPath = Get-CollectorAbsolutePath
  return ('execute --command "powershell.exe -NoProfile -ExecutionPolicy Bypass -Command Remove-Item -LiteralPath ''{0}'' -Force" --comment "Remove uploaded DCOIR_Collector script"' -f $collectorPath)
}

<#
.SYNOPSIS
Builds contextual collector help for a specific workflow area.

.DESCRIPTION
Returns a narrower help block for collect, enrich, cleanup, targeted, or version guidance
when the operator asks for area-specific help.

.FUNCTION NAME
Get-CollectorContextualHelpText

.INPUTS
Optional topic string.

.OUTPUTS
String containing newline-joined contextual help text.
#>
function Get-CollectorContextualHelpText {
  param([string]$Topic)

  $cmd = Get-CollectorPowerShellCommandBase
  $responseCmd = Get-CollectorResponseActionCommandBase
  $topicKey = if ([string]::IsNullOrWhiteSpace($Topic)) { 'general' } else { $Topic.ToLowerInvariant() }
  $lines = @()

  switch ($topicKey) {
    'collect' {
      $lines += 'DCOIR Collector Contextual Help - Collect'
      $lines += ''
      $lines += 'Use this when you need a baseline collection bundle.'
      $lines += 'Recommended first commands:'
      $lines += "  $cmd -Quick collect-t1"
      $lines += "  $cmd -Quick collect-t2"
      $lines += ''
      $lines += 'Response-action-safe examples:'
      $lines += ('  execute --command "{0} -Quick collect-t1" --comment "Run DCOIR collect T1"' -f $responseCmd)
      $lines += ('  execute --command "{0} -Quick collect-t2" --comment "Run DCOIR collect T2"' -f $responseCmd)
      $lines += ''
      $lines += 'Use T1 when you want the smaller baseline-first path.'
      $lines += 'Use T2 when you need the deeper persistence and investigative path.'
      $lines += 'Run -Version first if you are validating a specific PS1/ZIP pair.'
    }
    'enrich' {
      $lines += 'DCOIR Collector Contextual Help - Enrich'
      $lines += ''
      $lines += 'Use this when you already have a run id and want targeted follow-up collection.'
      $lines += 'Session pattern:'
      $lines += "  $cmd -Quick enrich-start-tcp"
      $lines += "  $cmd -Quick enrich-add-lograw -Target Security"
      $lines += "  $cmd -Quick enrich-finalize"
      $lines += ''
      $lines += 'Response-action-safe examples:'
      $lines += ('  execute --command "{0} -Quick enrich-start-tcp" --comment "Run DCOIR TCP enrichment"' -f $responseCmd)
      $lines += ('  execute --command "{0} -Quick enrich-add-lograw -Target Security" --comment "Add raw Security log enrichment"' -f $responseCmd)
      $lines += ('  execute --command "{0} -Quick enrich-finalize" --comment "Finalize current DCOIR enrichment session"' -f $responseCmd)
      $lines += ''
      $lines += 'Start a session once, add related actions to the same session, then finalize before cleanup.'
    }
    'cleanup' {
      $lines += 'DCOIR Collector Contextual Help - Cleanup'
      $lines += ''
      $lines += 'Cleanup removes the run root and consumed package state.'
      $lines += 'If a collect run failed before state.json was saved, cleanup removes only the latest matching DCOIR_* orphan under the selected OutRoot and reports MISSING_STATE_ORPHAN_CLEANED.'
      $lines += 'Cleanup reports NO_TARGET_FOUND when no state-backed run or bounded orphan cleanup target exists.'
      $lines += 'Cleanup reports SKIPPED when WhatIf or confirmation handling leaves all state-backed targets in place.'
      $lines += 'Cleanup does not remove the uploaded collector script unless you run DELETE_SCRIPT_COMMAND explicitly.'
      $lines += ''
      $lines += 'Response-action-safe example:'
      $lines += ('  execute --command "{0} -Quick cleanup" --comment "Running Cleanup on DCOIR_Collector"' -f $responseCmd)
      $lines += ''
      $lines += 'If you plan another collect-style run in the response-action lane, restage the runtime zip first.'
    }
    'targeted' {
      $lines += 'DCOIR Collector Contextual Help - Targeted'
      $lines += ''
      $lines += 'Use targeted mode when the operator has a narrower event window, user report, process, path, or indicator.'
      $lines += 'Examples:'
      $lines += "  $cmd -Quick collect-targeted-popup -Target ""User reported popup around 2026-04-08T09:00Z"""
      $lines += "  $cmd -Quick collect-targeted-script -Target ""Suspicious script execution follow-up"" -Target2 ""powershell.exe"""
      $lines += ''
      $lines += 'Pair targeted mode with WindowStart/WindowEnd and the most specific focus fields you have.'
      $lines += 'Targeted mode narrows guidance and prioritization even when full exact-time filtering is not universal yet.'
    }
    'version' {
      $lines += 'DCOIR Collector Contextual Help - Version'
      $lines += ''
      $lines += 'Use version preflight before collect, enrich, cleanup, or package movement when you need to prove the runtime identity.'
      $lines += 'Examples:'
      $lines += "  $cmd -Version"
      $lines += ('  execute --command "{0} -Version" --comment "Get DCOIR collector version"' -f $responseCmd)
      $lines += ''
      $lines += 'Compare COLLECTOR_VERSION, COLLECTOR_BUILD_IDENTITY, and EXPECTED_PACKAGE_NAME before live validation.'
    }
    default {
      return $null
    }
  }

  return ($lines -join [Environment]::NewLine)
}

<#
.SYNOPSIS
Builds the full collector help text.

.DESCRIPTION
Returns the operator-facing help text including top-level usage, quick shortcuts,
version/build preflight guidance, targeted examples, and lane guidance.

.FUNCTION NAME
Get-CollectorHelpText

.INPUTS
Optional topic string.

.OUTPUTS
String containing newline-joined help text.
#>
function Get-CollectorHelpText {
  param([string]$Topic)

  $contextual = Get-CollectorContextualHelpText -Topic $Topic
  if (-not [string]::IsNullOrWhiteSpace($contextual)) {
    return $contextual
  }

  $cmd = Get-CollectorPowerShellCommandBase
  $responseCmd = Get-CollectorResponseActionCommandBase
  $lines = @()
  $lines += "DCOIR Collector Help"
  $lines += ""
  $lines += "Top-level usage:"
  $lines += "  $cmd -Help"
  $lines += "  $cmd -Version"
  $lines += "  $cmd -Mode Collect -Tier T1"
  $lines += "  $cmd -Mode Collect -Tier T2"
  $lines += "  $cmd -Mode Enrich -Action TcpvconRefresh -NewEnrichSession"
  $lines += "  $cmd -Mode Cleanup"
  $lines += ""
  $lines += "Quick usage:"
  $lines += (Get-QuickUsageText)
  $lines += ""
  $lines += "Contextual help shortcuts:"
  $lines += "  $cmd -Quick help-collect"
  $lines += "  $cmd -Quick help-enrich"
  $lines += "  $cmd -Quick help-cleanup"
  $lines += "  $cmd -Quick help-targeted"
  $lines += "  $cmd -Quick help-version"
  $lines += ""
  $lines += "Accepted top-level modes: Collect, Enrich, Cleanup"
  $lines += "Accepted tiers: T1, T2"
  $lines += "Accepted target profiles: Generic, PopupWindow, ScriptExecution, PersistenceFollowUp, NetworkOnly, ProcessAndPowerShell"
  $lines += ""
  $lines += "Version/build preflight:"
  $lines += "  - Run -Version before collect, enrich, cleanup, package movement, or other stateful test steps."
  $lines += "  - Compare COLLECTOR_VERSION and COLLECTOR_BUILD_IDENTITY to the PS1/ZIP you intended to validate before continuing."
  $lines += ('  - Response-action-safe example: execute --command "{0} -Version" --comment "Get DCOIR collector version"' -f $responseCmd)
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
  $lines += "  - Use the response-action-safe runtime pattern with doubled double quotes around .\DCOIR_Collector.ps1 inside the execute --command string."
  $lines += "  - Use the collector-emitted DELETE_SCRIPT_COMMAND literal-path form for script removal in the response-action lane."
  $lines += "  - Local workstation and regression usage should run the PowerShell command directly without the response-action wrapper."
  $lines += "  - Prefer PowerShell 5.1 syntax and the runtime filename DCOIR_Collector.ps1."
  return ($lines -join [Environment]::NewLine)
}

<#
.SYNOPSIS
Translates supported quick shortcuts into full collector parameters.

.DESCRIPTION
Maps -Quick values into mode, tier, action, target, and finalize/session settings.

.FUNCTION NAME
Apply-QuickShortcut

.INPUTS
No direct parameters. Uses collector runtime globals.

.OUTPUTS
No direct output. Updates script-scoped collector parameters.
#>
function Apply-QuickShortcut {
  param()

  if ([string]::IsNullOrWhiteSpace($Quick)) { return }
  $q = $Quick.ToLowerInvariant().Replace('_','-')

  <#
  .SYNOPSIS
  Validates that a quick shortcut has a path target.

  .DESCRIPTION
  Throws when -Target is missing for a quick action that requires a file path.

  .FUNCTION NAME
  Require-QuickTargetPath

  .INPUTS
  No direct parameters. Uses -Target and the current quick shortcut name.

  .OUTPUTS
  Returns the validated target path string.
  #>
  function Require-QuickTargetPath {
    if ([string]::IsNullOrWhiteSpace($Target)) { throw ("Quick {0} requires -Target <path>." -f $q) }
    return $Target
  }

  <#
  .SYNOPSIS
  Validates that a quick shortcut has a named target.

  .DESCRIPTION
  Throws when -Target is missing for a quick action that requires a named target such as
  a service name, task path, or registry path.

  .FUNCTION NAME
  Require-QuickTargetName

  .INPUTS
  Label string describing the required target type.

  .OUTPUTS
  Returns the validated target string.
  #>
  function Require-QuickTargetName {
    param([string]$Label)
    if ([string]::IsNullOrWhiteSpace($Target)) { throw ("Quick {0} requires -Target <{1}>." -f $q, $Label) }
    return $Target
  }

  <#
  .SYNOPSIS
  Validates that a quick shortcut has a numeric PID target.

  .DESCRIPTION
  Throws when -Target is missing or non-numeric for a quick action that requires a PID.

  .FUNCTION NAME
  Require-QuickTargetPid

  .INPUTS
  No direct parameters. Uses -Target and the current quick shortcut name.

  .OUTPUTS
  Returns the validated PID integer.
  #>
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
    "help" { $script:ShowHelp = $true; $script:ContextualHelpTopic = $null; return }
    "help-collect" { $script:ShowHelp = $true; $script:ContextualHelpTopic = "collect"; return }
    "help-enrich" { $script:ShowHelp = $true; $script:ContextualHelpTopic = "enrich"; return }
    "help-cleanup" { $script:ShowHelp = $true; $script:ContextualHelpTopic = "cleanup"; return }
    "help-targeted" { $script:ShowHelp = $true; $script:ContextualHelpTopic = "targeted"; return }
    "help-version" { $script:ShowHelp = $true; $script:ContextualHelpTopic = "version"; return }
    default { throw ("Unknown -Quick value: {0}`r`n{1}" -f $Quick, (Get-CollectorHelpText)) }
  }
}

<#
.SYNOPSIS
Prints operator next-step quick commands.

.DESCRIPTION
Emits phase-specific follow-up commands and workflow guidance after collect, enrich, and
cleanup phases.

.FUNCTION NAME
Write-QuickNextSteps

.INPUTS
Phase string.

.OUTPUTS
Writes next-step lines to standard output.
#>
function Write-QuickNextSteps {
  param([string]$Phase)

  $responseCmd = Get-CollectorResponseActionCommandBase
  Write-Output "NEXT_QUICK_COMMANDS"
  switch ($Phase) {
    "Collect" {
      Write-Output ('1. execute --command "{0} -Quick enrich-start-tcp" --comment "Run DCOIR TCP enrichment"' -f $responseCmd)
      Write-Output ('2. execute --command "{0} -Quick enrich-start-lograw -Target Security" --comment "Run DCOIR raw Security log enrichment"' -f $responseCmd)
      Write-Output ('3. If Gemini upload is the next step, prefer UPLOAD_SUMMARY_PATH, ATTACHMENT_BUDGET_MANIFEST_PATH, COLLECTION_SCOPE_PATH, and representative final_artifacts slices. No merged baseline report is emitted in this build.' )
      Write-Output ('4. execute --command "{0} -Quick cleanup" --comment "Running Cleanup on DCOIR_Collector"' -f $responseCmd)
    }
    "EnrichOpen" {
      Write-Output ('1. execute --command "{0} -Quick enrich-add-logtext -Target Security" --comment "Add Security log text enrichment to current DCOIR session"' -f $responseCmd)
      Write-Output ('2. execute --command "{0} -Quick enrich-finalize" --comment "Finalize current DCOIR enrichment session"' -f $responseCmd)
      Write-Output '3. enrich-add-* should reuse the current open session unless you explicitly request a new one.'
    }
    "EnrichFinalized" {
      Write-Output '1. Review the finalized bundle you already retrieved before recommending another endpoint retrieval of the same path.'
      Write-Output ('2. execute --command "{0} -Quick cleanup" --comment "Running Cleanup on DCOIR_Collector"' -f $responseCmd)
    }
    "Cleanup" {
      Write-Output '1. Local script file remains in place by design unless you run the explicit delete command.'
      Write-Output ('2. execute --command "{0} -Quick collect-t1" --comment "Run DCOIR collect T1"' -f $responseCmd)
      Write-Output ('3. execute --command "{0} -Quick collect-targeted-popup -Target ""User reported popup follow-up""" --comment "Run DCOIR targeted popup-style collect"' -f $responseCmd)
    }
  }
}

<#
.SYNOPSIS
Normalizes a cleanup path for comparison.

.DESCRIPTION
Returns a full path string for state-backed cleanup authority checks.

.FUNCTION NAME
Resolve-DCOIRCleanupFullPath

.INPUTS
Path string.

.OUTPUTS
Full path string or null for blank input.
#>
function Resolve-DCOIRCleanupFullPath {
  param([string]$Path)
  if ([string]::IsNullOrWhiteSpace($Path)) { return $null }
  return [System.IO.Path]::GetFullPath($Path)
}

<#
.SYNOPSIS
Normalizes a cleanup directory path for boundary comparisons.

.DESCRIPTION
Returns a full directory path without trailing separators so root-prefix checks cannot be
fooled by similarly prefixed sibling directories.

.FUNCTION NAME
Resolve-DCOIRCleanupDirectoryText

.INPUTS
Directory path string.

.OUTPUTS
Normalized directory path string or null for blank input.
#>
function Resolve-DCOIRCleanupDirectoryText {
  param([string]$Path)
  $fullPath = Resolve-DCOIRCleanupFullPath -Path $Path
  if ([string]::IsNullOrWhiteSpace($fullPath)) { return $null }
  $separators = [char[]]@([System.IO.Path]::DirectorySeparatorChar, [System.IO.Path]::AltDirectorySeparatorChar)
  return $fullPath.TrimEnd($separators)
}

<#
.SYNOPSIS
Compares cleanup paths after normalization.

.DESCRIPTION
Performs a case-insensitive exact comparison of normalized full paths.

.FUNCTION NAME
Test-DCOIRCleanupPathEquals

.INPUTS
Actual and expected path strings.

.OUTPUTS
Boolean.
#>
function Test-DCOIRCleanupPathEquals {
  param([string]$Actual,[string]$Expected)
  $actualPath = Resolve-DCOIRCleanupFullPath -Path $Actual
  $expectedPath = Resolve-DCOIRCleanupFullPath -Path $Expected
  if ([string]::IsNullOrWhiteSpace($actualPath) -or [string]::IsNullOrWhiteSpace($expectedPath)) { return $false }
  return [string]::Equals($actualPath, $expectedPath, [System.StringComparison]::OrdinalIgnoreCase)
}

<#
.SYNOPSIS
Checks whether a cleanup target is inside the selected OutRoot.

.DESCRIPTION
Normalizes both paths and accepts only the same directory or a true child path. Sibling
paths that share a string prefix with OutRoot are rejected.

.FUNCTION NAME
Test-DCOIRCleanupPathWithinRoot

.INPUTS
Root path and candidate path.

.OUTPUTS
Boolean.
#>
function Test-DCOIRCleanupPathWithinRoot {
  param([string]$Root,[string]$Path)
  $rootPath = Resolve-DCOIRCleanupDirectoryText -Path $Root
  $candidatePath = Resolve-DCOIRCleanupFullPath -Path $Path
  if ([string]::IsNullOrWhiteSpace($rootPath) -or [string]::IsNullOrWhiteSpace($candidatePath)) { return $false }
  $separators = [char[]]@([System.IO.Path]::DirectorySeparatorChar, [System.IO.Path]::AltDirectorySeparatorChar)
  $candidateDirectoryText = $candidatePath.TrimEnd($separators)
  if ([string]::Equals($candidateDirectoryText, $rootPath, [System.StringComparison]::OrdinalIgnoreCase)) { return $true }
  $rootPrefix = $rootPath + [System.IO.Path]::DirectorySeparatorChar
  return $candidatePath.StartsWith($rootPrefix, [System.StringComparison]::OrdinalIgnoreCase)
}

<#
.SYNOPSIS
Adds a refused cleanup target and reason.

.DESCRIPTION
Records path-authority validation failures without deleting state-provided paths.

.FUNCTION NAME
Add-DCOIRCleanupRefusal

.INPUTS
Refused target list, refusal reason list, target, and reason.

.OUTPUTS
No direct output. Mutates the supplied lists.
#>
function Add-DCOIRCleanupRefusal {
  param(
    [System.Collections.ArrayList]$Targets,
    [System.Collections.ArrayList]$Reasons,
    [string]$Target,
    [string]$Reason
  )
  $targetLabel = if ([string]::IsNullOrWhiteSpace($Target)) { '<missing>' } else { $Target }
  if (-not @($Targets).Contains($targetLabel)) { [void]$Targets.Add($targetLabel) }
  [void]$Reasons.Add(("{0} :: {1}" -f $targetLabel, $Reason))
}

<#
.SYNOPSIS
Builds the cleanup result object.

.DESCRIPTION
Creates a consistent cleanup result including optional refused target evidence.

.FUNCTION NAME
New-DCOIRCleanupResult

.INPUTS
Status and cleanup target lists.

.OUTPUTS
Cleanup result object.
#>
function New-DCOIRCleanupResult {
  param(
    [string]$Status,
    [System.Collections.ArrayList]$Targets,
    [System.Collections.ArrayList]$RemovedTargets,
    [System.Collections.ArrayList]$SkippedTargets,
    [System.Collections.ArrayList]$FailedTargets,
    [System.Collections.ArrayList]$RefusedTargets,
    [System.Collections.ArrayList]$RefusalReasons
  )

  return [pscustomobject][ordered]@{
    Status = $Status
    TargetCount = @($Targets).Count
    RemovedCount = @($RemovedTargets).Count
    SkippedCount = @($SkippedTargets).Count
    FailedCount = @($FailedTargets).Count
    RefusedCount = @($RefusedTargets).Count
    RemovedTargets = @($RemovedTargets)
    SkippedTargets = @($SkippedTargets)
    FailedTargets = @($FailedTargets)
    RefusedTargets = @($RefusedTargets)
    RefusalReasons = @($RefusalReasons)
  }
}

<#
.SYNOPSIS
Removes run/package artifacts during cleanup.

.DESCRIPTION
Treats state.json as evidence, not deletion authority. It recomputes the allowed run root,
state path, and package path from the selected OutRoot, loaded RunId, and current package
name, then refuses state-backed cleanup if state-provided paths do not match that bounded
authority surface.

.FUNCTION NAME
Invoke-Cleanup

.INPUTS
Collector state object, selected OutRoot, and current package name.

.OUTPUTS
Cleanup result object with status, target, removed, skipped, failed, and refused counts.
#>
function Invoke-Cleanup {
  [CmdletBinding(SupportsShouldProcess=$true)]
  param(
    $StateObject,
    [Parameter(Mandatory=$true)][string]$Root,
    [Parameter(Mandatory=$true)][string]$CurrentPackageName
  )

  $targets = New-Object System.Collections.ArrayList
  $removedTargets = New-Object System.Collections.ArrayList
  $skippedTargets = New-Object System.Collections.ArrayList
  $failedTargets = New-Object System.Collections.ArrayList
  $refusedTargets = New-Object System.Collections.ArrayList
  $refusalReasons = New-Object System.Collections.ArrayList

  $resolvedRoot = Resolve-DCOIRCleanupFullPath -Path $Root
  if ([string]::IsNullOrWhiteSpace($resolvedRoot)) {
    Add-DCOIRCleanupRefusal -Targets $refusedTargets -Reasons $refusalReasons -Target $Root -Reason 'Selected OutRoot is blank or invalid.'
  }

  $stateRunId = if ($StateObject) { [string]$StateObject.RunId } else { $null }
  $safeRunId = $null
  try {
    $safeRunId = Resolve-DCOIRRunId -CurrentRunId $stateRunId -RejectBlank
  } catch {
    Add-DCOIRCleanupRefusal -Targets $refusedTargets -Reasons $refusalReasons -Target $stateRunId -Reason ("State RunId failed validation: {0}" -f $_.Exception.Message)
  }

  $expectedRunRoot = $null
  $expectedStatePath = $null
  $expectedPackagePath = $null
  if ($resolvedRoot -and $safeRunId) {
    $expectedRunRoot = Resolve-DCOIRCleanupFullPath -Path (Get-RunRoot -Root $resolvedRoot -CurrentRunId $safeRunId)
    $expectedStatePath = Resolve-DCOIRCleanupFullPath -Path (Join-Path $expectedRunRoot 'state.json')
  }
  if ($resolvedRoot -and -not [string]::IsNullOrWhiteSpace($CurrentPackageName)) {
    $expectedPackagePath = Resolve-DCOIRCleanupFullPath -Path (Join-Path $resolvedRoot $CurrentPackageName)
  }

  $stateRunRoot = if ($StateObject) { [string]$StateObject.RunRoot } else { $null }
  $statePath = if ($StateObject -and ($StateObject.PSObject.Properties.Name -contains 'StatePath')) { [string]$StateObject.StatePath } else { $null }
  $statePackagePath = if ($StateObject) { [string]$StateObject.PackagePath } else { $null }

  if (-not (Test-DCOIRCleanupPathWithinRoot -Root $resolvedRoot -Path $stateRunRoot)) {
    Add-DCOIRCleanupRefusal -Targets $refusedTargets -Reasons $refusalReasons -Target $stateRunRoot -Reason 'State RunRoot is outside the selected OutRoot or is blank.'
  }
  if (-not (Test-DCOIRCleanupPathEquals -Actual $stateRunRoot -Expected $expectedRunRoot)) {
    Add-DCOIRCleanupRefusal -Targets $refusedTargets -Reasons $refusalReasons -Target $stateRunRoot -Reason ("State RunRoot does not match expected run root {0}." -f $expectedRunRoot)
  }
  if ($expectedRunRoot -and -not (Test-DCOIRRunDirectoryName -Name ([System.IO.Path]::GetFileName($expectedRunRoot)))) {
    Add-DCOIRCleanupRefusal -Targets $refusedTargets -Reasons $refusalReasons -Target $expectedRunRoot -Reason 'Expected run root name is not a collector run directory name.'
  }

  if (-not (Test-DCOIRCleanupPathWithinRoot -Root $resolvedRoot -Path $statePath)) {
    Add-DCOIRCleanupRefusal -Targets $refusedTargets -Reasons $refusalReasons -Target $statePath -Reason 'StatePath is outside the selected OutRoot or is blank.'
  }
  if (-not (Test-DCOIRCleanupPathEquals -Actual $statePath -Expected $expectedStatePath)) {
    Add-DCOIRCleanupRefusal -Targets $refusedTargets -Reasons $refusalReasons -Target $statePath -Reason ("StatePath does not match expected state path {0}." -f $expectedStatePath)
  }

  if (-not (Test-DCOIRCleanupPathWithinRoot -Root $resolvedRoot -Path $statePackagePath)) {
    Add-DCOIRCleanupRefusal -Targets $refusedTargets -Reasons $refusalReasons -Target $statePackagePath -Reason 'PackagePath is outside the selected OutRoot or is blank.'
  }
  if (-not (Test-DCOIRCleanupPathEquals -Actual $statePackagePath -Expected $expectedPackagePath)) {
    Add-DCOIRCleanupRefusal -Targets $refusedTargets -Reasons $refusalReasons -Target $statePackagePath -Reason ("PackagePath does not match expected package path {0}." -f $expectedPackagePath)
  }

  if (@($refusedTargets).Count -gt 0) {
    return (New-DCOIRCleanupResult -Status 'REFUSED' -Targets $targets -RemovedTargets $removedTargets -SkippedTargets $skippedTargets -FailedTargets $failedTargets -RefusedTargets $refusedTargets -RefusalReasons $refusalReasons)
  }

  foreach ($candidate in @($expectedPackagePath,$expectedRunRoot)) {
    if ([string]::IsNullOrWhiteSpace($candidate)) { continue }
    if (-not (Test-Path -LiteralPath $candidate)) { continue }
    if (-not @($targets).Contains($candidate)) { [void]$targets.Add($candidate) }
  }

  foreach ($target in @($targets)) {
    if ($PSCmdlet.ShouldProcess($target, 'Remove collector cleanup target')) {
      Remove-Item -LiteralPath $target -Recurse -Force -ErrorAction SilentlyContinue
      if (Test-Path -LiteralPath $target) {
        [void]$failedTargets.Add($target)
      } else {
        [void]$removedTargets.Add($target)
      }
    } else {
      [void]$skippedTargets.Add($target)
    }
  }

  $status = 'COMPLETE'
  if (@($targets).Count -eq 0) {
    $status = 'NO_TARGET_FOUND'
  } elseif (@($removedTargets).Count -eq 0 -and @($skippedTargets).Count -gt 0 -and @($failedTargets).Count -eq 0) {
    $status = 'SKIPPED'
  } elseif (@($skippedTargets).Count -gt 0 -or @($failedTargets).Count -gt 0) {
    $status = 'PARTIAL'
  }

  return (New-DCOIRCleanupResult -Status $status -Targets $targets -RemovedTargets $removedTargets -SkippedTargets $skippedTargets -FailedTargets $failedTargets -RefusedTargets $refusedTargets -RefusalReasons $refusalReasons)
}
