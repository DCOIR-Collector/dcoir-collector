param(
  [switch]$AdminPhase,
  [string]$StatePath = "",
  [string]$BootstrapStatusPath = ""
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version 2

$BaseDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$OutputDir = Join-Path $BaseDir '_test_output'
if (-not (Test-Path -LiteralPath $OutputDir)) {
  New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null
}
if ([string]::IsNullOrWhiteSpace($BootstrapStatusPath)) {
  $BootstrapStatusPath = Join-Path $OutputDir 'bootstrap_status.json'
}
$ControlPath = Join-Path $BaseDir 'dcoir_manual_test_control.json'

$script:BootstrapStatuses = [ordered]@{}

function Save-BootstrapStatus {
  $payload = @{ steps = $script:BootstrapStatuses }
  $payload | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $BootstrapStatusPath -Encoding UTF8
}

function Write-TerminalNote {
  param([string]$Text)
  Write-Host ''
  Write-Host $Text -ForegroundColor Cyan
}

function Refresh-SessionPath {
  $machinePath = [Environment]::GetEnvironmentVariable('Path', 'Machine')
  $userPath = [Environment]::GetEnvironmentVariable('Path', 'User')
  if ([string]::IsNullOrWhiteSpace($machinePath) -and [string]::IsNullOrWhiteSpace($userPath)) {
    return
  }
  if ([string]::IsNullOrWhiteSpace($machinePath)) {
    $env:Path = $userPath
  } elseif ([string]::IsNullOrWhiteSpace($userPath)) {
    $env:Path = $machinePath
  } else {
    $env:Path = "$machinePath;$userPath"
  }
}

function Record-BootstrapState {
  param(
    [string]$Key,
    [string]$Status,
    [string]$Detail
  )
  $script:BootstrapStatuses[$Key] = [ordered]@{
    status = $Status
    detail = $Detail
    timestamp = (Get-Date).ToString('o')
  }
  Save-BootstrapStatus
}

function Resolve-GitCommand {
  try { return (Get-Command git -ErrorAction Stop).Source } catch { return $null }
}

function Resolve-PythonCommand {
  try {
    $pyProbe = & py -3 -c "import sys; print(sys.executable)" 2>$null
    if ($LASTEXITCODE -eq 0 -and -not [string]::IsNullOrWhiteSpace(($pyProbe | Out-String).Trim())) {
      return [pscustomobject]@{ Display = 'py -3'; Executable = 'py'; PrefixArgs = @('-3') }
    }
  } catch {}
  try {
    $pythonCmd = (Get-Command python -ErrorAction Stop).Source
    return [pscustomobject]@{ Display = $pythonCmd; Executable = $pythonCmd; PrefixArgs = @() }
  } catch {
    return $null
  }
}

function Ensure-WingetAvailable {
  return [bool](Get-Command winget -ErrorAction SilentlyContinue)
}

function Install-WithWinget {
  param(
    [string]$PackageId,
    [string]$FriendlyName
  )
  if (-not (Ensure-WingetAvailable)) {
    throw "winget is not available. Install $FriendlyName manually, then rerun this launcher."
  }
  Write-TerminalNote "Installing $FriendlyName with winget..."
  & winget install --id $PackageId -e --accept-package-agreements --accept-source-agreements --disable-interactivity
  if ($LASTEXITCODE -ne 0) {
    throw "winget could not install $FriendlyName automatically. Install it manually, then rerun this launcher."
  }
  Start-Sleep -Seconds 2
  Refresh-SessionPath
}

function Ensure-Git {
  $git = Resolve-GitCommand
  if ($git) {
    Record-BootstrapState -Key 'git_check' -Status 'FOUND' -Detail "Git already available at $git"
    return $git
  }
  Record-BootstrapState -Key 'git_check' -Status 'INSTALLING' -Detail 'Git not found. Attempting automatic install.'
  Install-WithWinget -PackageId 'Git.Git' -FriendlyName 'Git'
  $git = Resolve-GitCommand
  if ($git) {
    Record-BootstrapState -Key 'git_check' -Status 'INSTALLED' -Detail "Git installed and available at $git"
    return $git
  }
  Record-BootstrapState -Key 'git_check' -Status 'ACTION' -Detail 'Git appears installed but is not yet visible in this PowerShell session. Close this window, open a new one, and rerun the launcher.'
  throw 'Git appears installed but is not visible in the current shell yet. Close this window, open a new PowerShell window, and rerun the launcher.'
}

function Ensure-Python {
  $python = Resolve-PythonCommand
  if ($python) {
    Record-BootstrapState -Key 'python_check' -Status 'FOUND' -Detail "Python already available through $($python.Display)"
    return $python
  }
  Record-BootstrapState -Key 'python_check' -Status 'INSTALLING' -Detail 'Python not found. Attempting automatic install.'
  Install-WithWinget -PackageId 'Python.Python.3.11' -FriendlyName 'Python 3.11'
  $python = Resolve-PythonCommand
  if ($python) {
    Record-BootstrapState -Key 'python_check' -Status 'INSTALLED' -Detail "Python installed and available through $($python.Display)"
    return $python
  }
  Record-BootstrapState -Key 'python_check' -Status 'ACTION' -Detail 'Python appears installed but is not yet visible in this PowerShell session. Close this window, open a new one, and rerun the launcher.'
  throw 'Python appears installed but is not visible in the current shell yet. Close this window, open a new PowerShell window, and rerun the launcher.'
}

function Ensure-GitLongPaths {
  $needsSystem = $true
  try {
    $val = (& git config --system --get core.longpaths 2>$null | Out-String).Trim()
    if ($LASTEXITCODE -eq 0 -and $val -eq 'true') {
      $needsSystem = $false
    }
  } catch {}
  if (-not $needsSystem) {
    Record-BootstrapState -Key 'git_longpaths' -Status 'FOUND' -Detail 'Git long paths already enabled.'
    return
  }
  try {
    & git config --system core.longpaths true
    if ($LASTEXITCODE -eq 0) {
      Record-BootstrapState -Key 'git_longpaths' -Status 'INSTALLED' -Detail 'Git long paths enabled at the system level.'
      return
    }
  } catch {}
  try {
    & git config --global core.longpaths true
    if ($LASTEXITCODE -eq 0) {
      Record-BootstrapState -Key 'git_longpaths' -Status 'INSTALLED' -Detail 'Git long paths enabled at the user level.'
      return
    }
  } catch {}
  Record-BootstrapState -Key 'git_longpaths' -Status 'ACTION' -Detail 'Could not confirm Git long paths automatically. If the repo clone fails with filename-too-long, enable git long paths manually and rerun.'
}

function Ensure-ControlFile {
  if (-not (Test-Path -LiteralPath $ControlPath)) {
    throw "Control file missing: $ControlPath"
  }
}

try {
  Write-TerminalNote 'Preparing the DCOIR manual test runner...'
  Refresh-SessionPath
  Ensure-ControlFile
  $null = Ensure-Git
  $python = Ensure-Python
  Ensure-GitLongPaths

  $runnerPath = Join-Path $BaseDir 'dcoir_manual_test_runner.py'
  if (-not (Test-Path -LiteralPath $runnerPath)) {
    throw "Runner file missing: $runnerPath"
  }

  Record-BootstrapState -Key 'launcher' -Status 'FOUND' -Detail "Launching Python runner from $runnerPath"

  $invokeArgs = @()
  $invokeArgs += $python.PrefixArgs
  $invokeArgs += @($runnerPath, '--bootstrap-status-path', $BootstrapStatusPath)
  if ($AdminPhase) {
    $invokeArgs += '--admin-phase'
  }
  if (-not [string]::IsNullOrWhiteSpace($StatePath)) {
    $invokeArgs += @('--state-path', $StatePath)
  }

  Write-TerminalNote 'Starting the dashboard...'
  & $python.Executable @invokeArgs
  exit $LASTEXITCODE
} catch {
  Record-BootstrapState -Key 'launcher' -Status 'FAIL' -Detail $_.Exception.Message
  Write-Host ''
  Write-Host 'Launcher could not continue.' -ForegroundColor Red
  Write-Host $_.Exception.Message -ForegroundColor Yellow
  Write-Host ''
  Write-Host 'Next step:' -ForegroundColor Cyan
  Write-Host '1. Read the message above.' -ForegroundColor White
  Write-Host "2. If software was just installed, close this PowerShell window, open a new one, and rerun $($MyInvocation.MyCommand.Name)." -ForegroundColor White
  Write-Host "3. If the problem mentions path length, move the framework to a short path such as C:\DCOIR, make sure Windows long paths are enabled, restart the PC, and rerun." -ForegroundColor White
  Write-Host "4. If the problem is something else, open $BootstrapStatusPath and the latest report in _test_output for details." -ForegroundColor White
  exit 1
}
