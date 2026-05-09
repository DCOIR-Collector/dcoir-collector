[CmdletBinding()]
param(
    [switch]$SkipBrowserInstall,
    [switch]$NoNpmInstall
)

Set-StrictMode -Version 2.0
$ErrorActionPreference = 'Stop'

$repo = [Environment]::GetEnvironmentVariable('DCOIR_REPO_ROOT','Machine')
if ([string]::IsNullOrWhiteSpace($repo)) { throw 'Missing required Local Configuration Registry variable: DCOIR_REPO_ROOT' }
if (-not (Test-Path -LiteralPath $repo -PathType Container)) { throw ('DCOIR_REPO_ROOT does not exist: ' + $repo) }

$downloads = [Environment]::GetEnvironmentVariable('DCOIR_DOWNLOADS_DIR','Machine')
if ([string]::IsNullOrWhiteSpace($downloads)) { throw 'Missing required Local Configuration Registry variable: DCOIR_DOWNLOADS_DIR' }
if (-not (Test-Path -LiteralPath $downloads -PathType Container)) { throw ('DCOIR_DOWNLOADS_DIR does not exist: ' + $downloads) }

$timestamp = (Get-Date).ToUniversalTime().ToString('yyyyMMddTHHmmssZ')
$outDir = Join-Path $downloads ('dcoir_wbs09_airtable_ui_install_' + $timestamp)
New-Item -ItemType Directory -Path $outDir -Force | Out-Null
$logPath = Join-Path $outDir 'install.log'
$resultPath = Join-Path $outDir 'install_result.json'

function Write-InstallLog {
    param([string]$Message)
    $line = ('{0} {1}' -f (Get-Date).ToUniversalTime().ToString('o'), $Message)
    Add-Content -LiteralPath $logPath -Value $line -Encoding UTF8
    Write-Host $line
}

function Write-ResultJson {
    param([hashtable]$Data)
    ($Data | ConvertTo-Json -Depth 8) | Set-Content -LiteralPath $resultPath -Encoding UTF8
}

Write-InstallLog 'Starting WBS09 Airtable UI automation prerequisite install/check.'
Write-InstallLog ('Repo root: ' + $repo)
Write-InstallLog ('Downloads dir: ' + $downloads)

$toolRoot = Join-Path $repo 'operator_tools\github_desktop_lane\ui_automation\airtable_wbs09_views'
if (-not (Test-Path -LiteralPath $toolRoot -PathType Container)) { throw ('Tool root not found: ' + $toolRoot) }

$node = Get-Command node -ErrorAction SilentlyContinue
$npm = Get-Command npm -ErrorAction SilentlyContinue
if ($null -eq $node) { throw 'Node.js is required but was not found on PATH. Install Node.js LTS, reopen PowerShell, then rerun this installer.' }
if ($null -eq $npm) { throw 'npm is required but was not found on PATH. Install Node.js LTS, reopen PowerShell, then rerun this installer.' }

Push-Location $toolRoot
try {
    $nodeVersion = (& $node.Source --version) -join ' '
    $npmVersion = (& $npm.Source --version) -join ' '
    Write-InstallLog ('Node version: ' + $nodeVersion)
    Write-InstallLog ('npm version: ' + $npmVersion)

    if (-not $NoNpmInstall) {
        Write-InstallLog 'Running npm install in tool root.'
        & $npm.Source install 2>&1 | Tee-Object -FilePath (Join-Path $outDir 'npm_install.output.txt')
        if ($LASTEXITCODE -ne 0) { throw ('npm install failed with exit code ' + $LASTEXITCODE) }
    } else {
        Write-InstallLog 'Skipped npm install by parameter.'
    }

    if (-not $SkipBrowserInstall) {
        Write-InstallLog 'Installing Playwright Chromium browser.'
        & $npm.Source exec -- playwright install chromium 2>&1 | Tee-Object -FilePath (Join-Path $outDir 'playwright_install.output.txt')
        if ($LASTEXITCODE -ne 0) { throw ('playwright install chromium failed with exit code ' + $LASTEXITCODE) }
    } else {
        Write-InstallLog 'Skipped Playwright browser install by parameter.'
    }

    Write-ResultJson @{
        success = $true
        tool_root = $toolRoot
        output_dir = $outDir
        log_path = $logPath
        node_version = $nodeVersion
        npm_version = $npmVersion
        next_recommended_command = "$repo\operator_tools\github_desktop_lane\scripts\Invoke-DcoirAirtableWbs09UiViewTool.ps1 -DryRun"
    }
    Write-InstallLog 'Install/check completed successfully.'
    Write-Host ('Install output directory: ' + $outDir)
}
finally {
    Pop-Location
}
