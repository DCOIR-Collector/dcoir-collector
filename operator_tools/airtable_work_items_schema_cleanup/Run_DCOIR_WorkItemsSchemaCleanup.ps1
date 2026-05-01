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
$env:PYTHONWARNINGS = 'ignore::DeprecationWarning'

$ModeLabels = @{
    'self-test' = '90_self_test'
    'dry-run' = '01_dry_run'
    'apply-options' = '02_apply_options'
    'apply-safe' = '03_apply_safe_cleanup'
    'verify' = '04_verify'
    'generate-option-delete-script' = '05_generate_option_delete_script'
    'attempt-api-option-delete' = '91_attempt_api_option_delete_DANGEROUS'
    'attempt-field-delete' = '92_attempt_field_delete_DANGEROUS'
}

function Resolve-DcoirOutputRoot {
    if (-not [string]::IsNullOrWhiteSpace($env:DCOIR_DOWNLOADS_DIR)) {
        return [pscustomobject]@{ Path = $env:DCOIR_DOWNLOADS_DIR; Source = 'DCOIR_DOWNLOADS_DIR' }
    }
    if (-not [string]::IsNullOrWhiteSpace($env:USERPROFILE)) {
        return [pscustomobject]@{ Path = (Join-Path $env:USERPROFILE 'Downloads'); Source = 'USERPROFILE fallback' }
    }
    return [pscustomobject]@{ Path = (Join-Path $PSScriptRoot 'out'); Source = 'script-folder fallback' }
}

function Resolve-DcoirValue {
    param(
        [string]$ParameterValue,
        [string]$EnvName,
        [string]$DefaultValue,
        [string]$ValueName
    )
    if (-not [string]::IsNullOrWhiteSpace($ParameterValue)) {
        return [pscustomobject]@{ Value = $ParameterValue; Source = "parameter:$ValueName" }
    }
    $envValue = [Environment]::GetEnvironmentVariable($EnvName)
    if (-not [string]::IsNullOrWhiteSpace($envValue)) {
        return [pscustomobject]@{ Value = $envValue; Source = $EnvName }
    }
    return [pscustomobject]@{ Value = $DefaultValue; Source = 'tool default' }
}

function Write-LogLine {
    param([string]$Message, [string]$Color = '')
    if ($Color) { Write-Host $Message -ForegroundColor $Color } else { Write-Host $Message }
    if ($script:LogPath) { Add-Content -LiteralPath $script:LogPath -Value $Message -Encoding UTF8 }
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

$OutputRoot = Resolve-DcoirOutputRoot
$Day = (Get-Date).ToUniversalTime().ToString('yyyyMMdd')
$OutDir = Join-Path $OutputRoot.Path (Join-Path 'DCOIR_WorkItemsSchemaCleanup' $Day)
if (!(Test-Path -LiteralPath $OutDir)) { New-Item -ItemType Directory -Force -Path $OutDir | Out-Null }
$env:DCOIR_DOWNLOADS_DIR = $OutDir

$EffectiveBase = Resolve-DcoirValue -ParameterValue $BaseId -EnvName 'DCOIR_AIRTABLE_BASE_ID' -DefaultValue 'appM4KSwnVf3G3OTK' -ValueName 'BaseId'
$EffectiveTable = Resolve-DcoirValue -ParameterValue $TableId -EnvName 'DCOIR_AIRTABLE_WORK_ITEMS_TABLE_ID' -DefaultValue 'tblgsQAVWvh8K7gIR' -ValueName 'TableId'

$RunLabel = $ModeLabels[$Mode]
if ([string]::IsNullOrWhiteSpace($RunLabel)) { $RunLabel = $Mode }
$env:DCOIR_TOOL_RUN_LABEL = $RunLabel
$Stamp = (Get-Date).ToUniversalTime().ToString('yyyyMMddTHHmmssZ')
$script:LogPath = Join-Path $OutDir ("work_items_schema_cleanup_${RunLabel}_${Stamp}.log")
$Py = Join-Path $ScriptDir 'dcoir_work_items_schema_cleanup.py'

try {
    New-Item -ItemType File -Force -Path $script:LogPath | Out-Null
    Write-LogLine 'DCOIR Work Items schema cleanup' 'Cyan'
    Write-LogLine "Mode: $Mode"
    Write-LogLine "Run label: $RunLabel"
    Write-LogLine "Folder: $ScriptDir"
    Write-LogLine "Log: $script:LogPath"
    Write-LogLine "Output root source: $($OutputRoot.Source)"
    Write-LogLine "Output folder: $OutDir"
    Write-LogLine "Base ID source: $($EffectiveBase.Source)"
    Write-LogLine "Table ID source: $($EffectiveTable.Source)"
    Write-LogLine 'Expected success marker: DCOIR_WORK_ITEMS_SCHEMA_CLEANUP_DONE'
    Write-LogLine 'Token source: DCOIR_AIRTABLE_TOKEN or AIRTABLE_TOKEN (value not printed)'
    Write-LogLine ''

    if (!(Test-Path -LiteralPath $Py)) { throw "Python script not found: $Py" }

    $PythonExe = $null
    $PythonPrefixArgs = @()
    if (Get-Command python -ErrorAction SilentlyContinue) {
        $PythonExe = 'python'
    } elseif (Get-Command py -ErrorAction SilentlyContinue) {
        $PythonExe = 'py'
        $PythonPrefixArgs = @('-3')
    }
    if (-not $PythonExe) { throw 'Python was not found. Install Python 3, then run this tool again.' }

    Write-LogLine 'Python found. Checking version...'
    $oldEap = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    & $PythonExe @PythonPrefixArgs --version 2>&1 | Tee-Object -FilePath $script:LogPath -Append
    $VersionExitCode = $LASTEXITCODE
    $ErrorActionPreference = $oldEap
    if ($VersionExitCode -ne 0) { throw "Python version check failed with exit code $VersionExitCode." }

    $ArgsList = @()
    $ArgsList += $PythonPrefixArgs
    $ArgsList += '-S'
    $ArgsList += @($Py, '--mode', $Mode, '--base-id', $EffectiveBase.Value, '--table-id', $EffectiveTable.Value)
    if ($DeletePrefixedFields) { $ArgsList += '--delete-prefixed-fields' }
    foreach ($f in $FieldId) { $ArgsList += @('--field-id', $f) }
    if ($ConfirmFieldDelete) { $ArgsList += @('--confirm-field-delete', $ConfirmFieldDelete) }
    if ($ConfirmOptionDelete) { $ArgsList += @('--confirm-option-delete', $ConfirmOptionDelete) }

    Write-LogLine ''
    Write-LogLine 'Running cleanup tool...' 'Cyan'
    $oldEap = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    & $PythonExe @ArgsList 2>&1 | Tee-Object -FilePath $script:LogPath -Append
    $ExitCode = $LASTEXITCODE
    $ErrorActionPreference = $oldEap
    if ($ExitCode -ne 0) { throw "Cleanup tool failed with exit code $ExitCode. See log: $script:LogPath" }

    Write-LogLine ''
    Write-LogLine 'DCOIR_WORK_ITEMS_SCHEMA_CLEANUP_WRAPPER_DONE' 'Green'
    Write-LogLine "Log saved to: $script:LogPath"
    Write-LogLine "Reports folder: $OutDir"
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
