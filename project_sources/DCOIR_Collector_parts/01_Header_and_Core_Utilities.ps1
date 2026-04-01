param(
  [ValidateSet("Collect","Enrich","Cleanup")]
  [string]$Mode = "Collect",

  [ValidateSet("T1","T2")]
  [string]$Tier = "T1",

  [int]$Hours = 24,

  [string]$OutRoot = "C:\Temp",

  [string]$PackageName = "DCOIR_Collector.zip",

  [string]$RunId,

  [ValidateSet(
    "SigcheckPath",
    "ListDllsPid",
    "AccessChkFile",
    "AccessChkService",
    "AccessChkReg",
    "StringsPath",
    "StreamsPath",
    "TcpvconRefresh",
    "LogText",
    "LogRaw",
    "PullSuspiciousFile",
    "PullScriptOrConfig",
    "PullTaskXml",
    "PullServiceBinary",
    "PullWmiReferencedFile"
  )]
  [string]$Action,

  [int]$TargetPid,

  [string]$Path,

  [string]$ServiceName,

  [string]$RegistryPath,

  [string]$LogName,

  [int[]]$EventId,

  [int]$MaxEvents = 500,

  [string]$EnrichSessionId,

  [switch]$NewEnrichSession,

  [switch]$FinalizeEnrichSession,

  [string]$Quick,
  [string]$Target,
  [string]$Target2
)

Set-StrictMode -Version 2
$ErrorActionPreference = "Continue"
$ScriptFilePath = $MyInvocation.MyCommand.Path
$ScriptVersion = "3.1.4"

$Global:CollectorErrors = New-Object System.Collections.ArrayList
$Global:CollectorNotes = New-Object System.Collections.ArrayList
$Global:RecommendedActions = New-Object System.Collections.ArrayList
$Global:ExecutionTxtPath = $null
$Global:ExecutionJsonlPath = $null
$Global:ErrorsLogPath = $null
$Global:CurrentRunId = $null

function Add-CollectorError {
  param([string]$Message)
  if ([string]::IsNullOrWhiteSpace($Message)) { return }
  [void]$Global:CollectorErrors.Add($Message)
  if ($Global:ErrorsLogPath) {
    Add-Content -Path $Global:ErrorsLogPath -Value ("[{0}] ERROR {1}" -f ((Get-Date).ToUniversalTime().ToString("o")), $Message) -Encoding UTF8
  }
}

function Add-CollectorNote {
  param([string]$Message)
  if ([string]::IsNullOrWhiteSpace($Message)) { return }
  [void]$Global:CollectorNotes.Add($Message)
}

function Add-Recommendation {
  param([string]$Message)
  if ([string]::IsNullOrWhiteSpace($Message)) { return }
  [void]$Global:RecommendedActions.Add($Message)
}

function Ensure-Directory {
  param([Parameter(Mandatory=$true)][string]$Path)
  if (-not (Test-Path -LiteralPath $Path)) {
    New-Item -Path $Path -ItemType Directory -Force | Out-Null
  }
}

function Remove-IfExists {
  param([string]$LiteralPath)
  if (-not [string]::IsNullOrWhiteSpace($LiteralPath) -and (Test-Path -LiteralPath $LiteralPath)) {
    Remove-Item -LiteralPath $LiteralPath -Recurse -Force -ErrorAction SilentlyContinue
  }
}

function Join-ArgString {
  param([string[]]$Arguments)
  if (-not $Arguments) { return "" }
  $parts = foreach ($arg in $Arguments) {
    if ($null -eq $arg) { continue }
    if ($arg -match '[\s"]') {
      '"' + ($arg -replace '"', '\"') + '"'
    } else {
      $arg
    }
  }
  return ($parts -join ' ')
}

function Write-StepLog {
  param(
    [string]$StepName,
    [string]$Status,
    [datetime]$StartTime,
    [datetime]$EndTime,
    [int]$ExitCode,
    [string]$Command,
    [string]$ArtifactPath,
    [string]$Message
  )

  $durationMs = [int]([TimeSpan]($EndTime - $StartTime)).TotalMilliseconds
  $txtLine = "[{0}] {1} {2} duration_ms={3} exit_code={4}" -f $EndTime.ToUniversalTime().ToString("o"), $Status, $StepName, $durationMs, $ExitCode
  if ($ArtifactPath) { $txtLine += (" artifact={0}" -f $ArtifactPath) }
  if ($Message) { $txtLine += (" message={0}" -f $Message) }

  if ($Global:ExecutionTxtPath) {
    Add-Content -Path $Global:ExecutionTxtPath -Value $txtLine -Encoding UTF8
    if ($Command) {
      Add-Content -Path $Global:ExecutionTxtPath -Value ("  COMMAND={0}" -f $Command) -Encoding UTF8
    }
  }

  if ($Global:ExecutionJsonlPath) {
    $obj = [ordered]@{
      ts_utc = $EndTime.ToUniversalTime().ToString("o")
      run_id = $Global:CurrentRunId
      step = $StepName
      status = $Status
      duration_ms = $durationMs
      exit_code = $ExitCode
      command = $Command
      artifact_path = $ArtifactPath
      message = $Message
    }
    Add-Content -Path $Global:ExecutionJsonlPath -Value ($obj | ConvertTo-Json -Compress) -Encoding UTF8
  }
}

function Invoke-ProcessCapture {
  param(
    [Parameter(Mandatory=$true)][string]$FilePath,
    [string[]]$Arguments,
    [Parameter(Mandatory=$true)][string]$StepName,
    [int[]]$AllowedExitCodes = @(0)
  )

  $startTime = Get-Date
  $commandText = $FilePath
  if ($Arguments) {
    $commandText = "$FilePath $(Join-ArgString -Arguments $Arguments)"
  }

  try {
    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName = $FilePath
    $psi.Arguments = (Join-ArgString -Arguments $Arguments)
    $psi.UseShellExecute = $false
    $psi.RedirectStandardOutput = $true
    $psi.RedirectStandardError = $true
    $psi.CreateNoWindow = $true

    $proc = New-Object System.Diagnostics.Process
    $proc.StartInfo = $psi
    [void]$proc.Start()
    $stdout = $proc.StandardOutput.ReadToEnd()
    $stderr = $proc.StandardError.ReadToEnd()
    $proc.WaitForExit()

    $endTime = Get-Date
    $status = "OK"
    $message = ""
    if (@($AllowedExitCodes) -notcontains [int]$proc.ExitCode) {
      $status = "ERROR"
      $message = ("ExitCode={0}" -f $proc.ExitCode)
      Add-CollectorError ("Step [{0}] failed. {1}. Command: {2}" -f $StepName, $message, $commandText)
    }

    Write-StepLog -StepName $StepName -Status $status -StartTime $startTime -EndTime $endTime -ExitCode $proc.ExitCode -Command $commandText -ArtifactPath "" -Message $message

    return [pscustomobject]@{
      StdOut = $stdout
      StdErr = $stderr
      ExitCode = [int]$proc.ExitCode
      Command = $commandText
      Status = $status
    }
  } catch {
    $endTime = Get-Date
    $message = $_.Exception.Message
    Add-CollectorError ("Step [{0}] raised an exception. {1}. Command: {2}" -f $StepName, $message, $commandText)
    Write-StepLog -StepName $StepName -Status "EXCEPTION" -StartTime $startTime -EndTime $endTime -ExitCode -1 -Command $commandText -ArtifactPath "" -Message $message
    return [pscustomobject]@{
      StdOut = ""
      StdErr = $message
      ExitCode = -1
      Command = $commandText
      Status = "EXCEPTION"
    }
  }
}

function Invoke-CmdCapture {
  param(
    [Parameter(Mandatory=$true)][string]$Command,
    [Parameter(Mandatory=$true)][string]$StepName,
    [int[]]$AllowedExitCodes = @(0)
  )
  return (Invoke-ProcessCapture -FilePath "cmd.exe" -Arguments @("/c", $Command) -StepName $StepName -AllowedExitCodes $AllowedExitCodes)
}

function Get-CombinedProcessOutput {
  param($Result)
  $lines = New-Object System.Collections.ArrayList
  [void]$lines.Add(("COMMAND={0}" -f $Result.Command))
  [void]$lines.Add(("EXIT_CODE={0}" -f $Result.ExitCode))
  [void]$lines.Add("")
  [void]$lines.Add("STDOUT:")
  [void]$lines.Add(($Result.StdOut))
  [void]$lines.Add("")
  [void]$lines.Add("STDERR:")
  [void]$lines.Add(($Result.StdErr))
  return ($lines -join [Environment]::NewLine)
}

function Get-NewRunId {
  return (Get-Date -Format "yyyyMMdd_HHmmss")
}

function Get-RunRoot {
  param([string]$Root,[string]$CurrentRunId)
  return (Join-Path $Root ("DCOIR_{0}_{1}" -f $env:COMPUTERNAME, $CurrentRunId))
}

function Get-StatePath {
  param([string]$Root,[string]$CurrentRunId)
  return (Join-Path (Get-RunRoot -Root $Root -CurrentRunId $CurrentRunId) "state.json")
}

function Save-State {
  param([Parameter(Mandatory=$true)][hashtable]$State)
  $json = $State | ConvertTo-Json -Depth 12
  Set-Content -Path $State.StatePath -Value $json -Encoding UTF8
}

function Load-State {
  param([string]$Root,[string]$CurrentRunId)

  if ([string]::IsNullOrWhiteSpace($CurrentRunId)) {
    $dirs = Get-ChildItem -LiteralPath $Root -Directory -ErrorAction SilentlyContinue |
      Where-Object { $_.Name -like "DCOIR_*" } |
      Sort-Object LastWriteTime -Descending
    if (-not $dirs) {
      throw "No DCOIR run directories found under $Root"
    }
    $selected = $dirs | Select-Object -First 1
    $statePath = Join-Path $selected.FullName "state.json"
    if (-not (Test-Path -LiteralPath $statePath)) {
      throw "State file not found: $statePath"
    }
    return (Get-Content -LiteralPath $statePath -Raw | ConvertFrom-Json)
  }

  $statePath = Get-StatePath -Root $Root -CurrentRunId $CurrentRunId
  if (-not (Test-Path -LiteralPath $statePath)) {
    throw "State file not found: $statePath"
  }

  return (Get-Content -LiteralPath $statePath -Raw | ConvertFrom-Json)
}

function Convert-StateObjectToHashtable {
  param([object]$InputObject)

  if ($null -eq $InputObject) { return $null }

  if ($InputObject -is [System.Collections.IDictionary]) {
    $hash = @{}
    foreach ($key in $InputObject.Keys) {
      $hash[$key] = Convert-StateObjectToHashtable -InputObject $InputObject[$key]
    }
    return $hash
  }

  if (($InputObject -is [System.Collections.IEnumerable]) -and -not ($InputObject -is [string])) {
    $list = @()
    foreach ($item in $InputObject) {
      $list += ,(Convert-StateObjectToHashtable -InputObject $item)
    }
    return $list
  }

  $psProps = @()
  try { $psProps = @($InputObject.PSObject.Properties) } catch { $psProps = @() }
  if (@($psProps).Count -gt 0 -and -not ($InputObject -is [string])) {
    $hash = @{}
    foreach ($prop in $psProps) {
      $hash[$prop.Name] = Convert-StateObjectToHashtable -InputObject $prop.Value
    }
    return $hash
  }

  return $InputObject
}

function Convert-ToArrayList {
  param([object]$InputObject)

  $list = New-Object System.Collections.ArrayList

  if ($null -eq $InputObject) {
    return $list
  }

  if (($InputObject -is [System.Collections.IEnumerable]) -and -not ($InputObject -is [string]) -and -not ($InputObject -is [System.Collections.IDictionary])) {
    foreach ($item in $InputObject) {
      [void]$list.Add($item)
    }
    return $list
  }

  [void]$list.Add($InputObject)
  return $list
}

function Get-ScriptDirectory {
  if (-not [string]::IsNullOrWhiteSpace($ScriptFilePath)) {
    return (Split-Path -Parent $ScriptFilePath)
  }
  if ($PSScriptRoot) {
    return $PSScriptRoot
  }
  return (Get-Location).Path
}

function Get-AbsoluteScriptPath {
  if (-not [string]::IsNullOrWhiteSpace($ScriptFilePath)) {
    return [System.IO.Path]::GetFullPath($ScriptFilePath)
  }
  return [System.IO.Path]::GetFullPath((Join-Path (Get-ScriptDirectory) "DCOIR_Collector.ps1"))
}

function Get-QuotedAbsoluteScriptPath {
  return ('"{0}"' -f (Get-AbsoluteScriptPath))
}

function Resolve-Tool {
  param([string]$ToolsDir,[string]$BaseName)

  $candidates = @(
    (Join-Path $ToolsDir ("{0}64.exe" -f $BaseName)),
    (Join-Path $ToolsDir ("{0}.exe" -f $BaseName))
  )

  foreach ($candidate in $candidates) {
    if (Test-Path -LiteralPath $candidate) { return $candidate }
  }
  return $null
}

function New-SectionHeader {
  param([string]$Name)
  return @(
    ""
    ("=" * 80)
    $Name
    ("=" * 80)
    ""
  )
}

function Add-Section {
  param(
    [System.Text.StringBuilder]$Builder,
    [string]$Name,
    [string]$Text
  )
  foreach ($line in (New-SectionHeader -Name $Name)) {
    [void]$Builder.AppendLine($line)
  }
  [void]$Builder.AppendLine(($Text | Out-String))
}

function Convert-ToTextBlock {
  param([object]$InputObject)
  if ($null -eq $InputObject) { return "" }
  return ($InputObject | Out-String -Width 500)
}
