param(
    [ValidateSet('self-test','dry-run','apply-options','apply-safe','verify','generate-option-delete-script','attempt-api-option-delete','attempt-field-delete')]
    [string]$Mode = 'dry-run',
    [string]$BaseId = '',
    [string]$TableId = '',
    [switch]$DeletePrefixedFields,
    [string[]]$FieldId = @(),
    [string]$ConfirmFieldDelete = '',
    [string]$ConfirmOptionDelete = '',
    [switch]$NoPause
)

$ErrorActionPreference = 'Stop'

function Get-DcoirDownloadsDir {
    if (-not [string]::IsNullOrWhiteSpace($env:DCOIR_DOWNLOADS_DIR)) {
        return $env:DCOIR_DOWNLOADS_DIR
    }
    if (-not [string]::IsNullOrWhiteSpace($env:USERPROFILE)) {
        return (Join-Path $env:USERPROFILE 'Downloads\DCOIR')
    }
    return (Join-Path $PSScriptRoot 'out')
}

function Write-LogLine {
    param(
        [string]$Message,
        [string]$Color = ''
    )
    if ($Color) {
        Write-Host $Message -ForegroundColor $Color
    } else {
        Write-Host $Message
    }
    if ($script:LogPath) {
        Add-Content -LiteralPath $script:LogPath -Value $Message -Encoding UTF8
    }
}

function Pause-BeforeExit {
    param([int]$ExitCode = 0)
    if (-not $NoPause) {
        Write-Host ''
        Write-Host 'Press Enter to close this window...'
        [void][System.Console]::ReadLine()
    }
    exit $ExitCode
}

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
if ([string]::IsNullOrWhiteSpace($ScriptDir)) { $ScriptDir = (Get-Location).Path }
Set-Location $ScriptDir

$OutDir = Get-DcoirDownloadsDir
if (!(Test-Path -LiteralPath $OutDir)) { New-Item -ItemType Directory -Force -Path $OutDir | Out-Null }
$env:DCOIR_DOWNLOADS_DIR = $OutDir
$Stamp = (Get-Date).ToUniversalTime().ToString('yyyyMMddTHHmmssZ')
$script:LogPath = Join-Path $OutDir ("work_items_schema_cleanup_${Mode}_${Stamp}.log")
$Py = Join-Path $ScriptDir 'dcoir_work_items_schema_cleanup.py'

try {
    New-Item -ItemType File -Force -Path $script:LogPath | Out-Null
    Write-LogLine "DCOIR Work Items schema cleanup" 'Cyan'
    Write-LogLine "Mode: $Mode"
    Write-LogLine "Folder: $ScriptDir"
    Write-LogLine "Log: $script:LogPath"
    Write-LogLine "Output folder: $OutDir"
    Write-LogLine "Expected success marker: DCOIR_WORK_ITEMS_SCHEMA_CLEANUP_DONE"
    Write-LogLine "Token source: DCOIR_AIRTABLE_TOKEN or AIRTABLE_TOKEN (value not printed)"
    Write-LogLine ""

    if (!(Test-Path -LiteralPath $Py)) {
        throw "Python script not found: $Py"
    }

    $PythonExe = $null
    $PythonPrefixArgs = @()
    if (Get-Command python -ErrorAction SilentlyContinue) {
        $PythonExe = 'python'
    } elseif (Get-Command py -ErrorAction SilentlyContinue) {
        $PythonExe = 'py'
        $PythonPrefixArgs = @('-3')
    }
    if (-not $PythonExe) {
        throw 'Python was not found. Install Python 3, then run this tool again.'
    }

    Write-LogLine 'Python found. Checking version...'
    & $PythonExe @PythonPrefixArgs --version 2>&1 | Tee-Object -FilePath $script:LogPath -Append
    if ($LASTEXITCODE -ne 0) {
        throw "Python version check failed with exit code $LASTEXITCODE."
    }

    $ArgsList = @()
    $ArgsList += $PythonPrefixArgs
    $ArgsList += '-S'
    $ArgsList += @($Py, '--mode', $Mode)
    if ($BaseId) { $ArgsList += @('--base-id', $BaseId) }
    if ($TableId) { $ArgsList += @('--table-id', $TableId) }
    if ($DeletePrefixedFields) { $ArgsList += '--delete-prefixed-fields' }
    foreach ($f in $FieldId) { $ArgsList += @('--field-id', $f) }
    if ($ConfirmFieldDelete) { $ArgsList += @('--confirm-field-delete', $ConfirmFieldDelete) }
    if ($ConfirmOptionDelete) { $ArgsList += @('--confirm-option-delete', $ConfirmOptionDelete) }

    Write-LogLine ''
    Write-LogLine 'Running cleanup tool...' 'Cyan'
    & $PythonExe @ArgsList 2>&1 | Tee-Object -FilePath $script:LogPath -Append
    $ExitCode = $LASTEXITCODE
    if ($ExitCode -ne 0) {
        throw "Cleanup tool failed with exit code $ExitCode. See log: $script:LogPath"
    }

    Write-LogLine ''
    Write-LogLine 'DCOIR_WORK_ITEMS_SCHEMA_CLEANUP_WRAPPER_DONE' 'Green'
    Write-LogLine "Log saved to: $script:LogPath"
    Pause-BeforeExit 0
}
catch {
    Write-Host ''
    Write-Host 'DCOIR Work Items schema cleanup failed:' -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    if ($script:LogPath) {
        Add-Content -LiteralPath $script:LogPath -Value '' -Encoding UTF8
        Add-Content -LiteralPath $script:LogPath -Value 'DCOIR Work Items schema cleanup failed:' -Encoding UTF8
        Add-Content -LiteralPath $script:LogPath -Value $_.Exception.Message -Encoding UTF8
        Write-Host ''
        Write-Host "Log saved to: $script:LogPath" -ForegroundColor Yellow
    }
    Write-Host ''
    Write-Host 'Copy the error text or upload the log to ChatGPT. Do not include your Airtable token.' -ForegroundColor Yellow
    Pause-BeforeExit 1
}
