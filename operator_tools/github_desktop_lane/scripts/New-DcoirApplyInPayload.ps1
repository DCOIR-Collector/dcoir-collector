[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][string]$PayloadZip,
    [string]$RequestId,
    [string]$RepoRoot,
    [string]$LogPath,
    [switch]$Overwrite
)

$ErrorActionPreference = 'Stop'
$ToolVersion = '2026-05-03.2'
$script:LogPath = $null

function Get-Sha256Hex {
    param([Parameter(Mandatory=$true)][string]$Path)
    return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()
}

function Test-SafeRequestId {
    param([string]$Value)
    return (-not [string]::IsNullOrWhiteSpace($Value) -and $Value -match '^[A-Za-z0-9._-]+$')
}

function ConvertTo-SafeRequestId {
    param([string]$Value)
    $safe = ([string]$Value -replace '[^A-Za-z0-9._-]', '-').Trim('-')
    if ([string]::IsNullOrWhiteSpace($safe)) { $safe = 'request' }
    return $safe
}

function Write-Utf8NoBom {
    param([Parameter(Mandatory=$true)][string]$Path, [AllowNull()][string]$Text)
    $parent = Split-Path -Parent $Path
    if ($parent -and -not (Test-Path -LiteralPath $parent -PathType Container)) {
        New-Item -ItemType Directory -Force -Path $parent | Out-Null
    }
    $enc = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText($Path, [string]$Text, $enc)
}

function Write-AsciiText {
    param([Parameter(Mandatory=$true)][string]$Path, [AllowNull()][string]$Text)
    $parent = Split-Path -Parent $Path
    if ($parent -and -not (Test-Path -LiteralPath $parent -PathType Container)) {
        New-Item -ItemType Directory -Force -Path $parent | Out-Null
    }
    [System.IO.File]::WriteAllText($Path, [string]$Text, [System.Text.Encoding]::ASCII)
}

function Add-LogLine {
    param([AllowNull()][string]$Message)
    $line = '[{0}] {1}' -f (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'), [string]$Message
    Write-Host $line
    if (-not [string]::IsNullOrWhiteSpace($script:LogPath)) {
        $parent = Split-Path -Parent $script:LogPath
        if ($parent -and -not (Test-Path -LiteralPath $parent -PathType Container)) {
            New-Item -ItemType Directory -Force -Path $parent | Out-Null
        }
        [System.IO.File]::AppendAllText($script:LogPath, $line + [Environment]::NewLine, (New-Object System.Text.UTF8Encoding($false)))
    }
}

function Test-ZipHasApplyManifest {
    param([Parameter(Mandatory=$true)][string]$ZipPath)
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    $zip = [System.IO.Compression.ZipFile]::OpenRead($ZipPath)
    try {
        $entries = @($zip.Entries | ForEach-Object { $_.FullName })
        if ($entries -notcontains 'apply_manifest.json') {
            throw 'Input ZIP must contain apply_manifest.json at archive root.'
        }
        return $entries
    }
    finally {
        if ($zip) { $zip.Dispose() }
    }
}

function Resolve-DefaultLogPath {
    param([string]$RequestedLogPath)
    if (-not [string]::IsNullOrWhiteSpace($RequestedLogPath)) {
        return [System.IO.Path]::GetFullPath($RequestedLogPath)
    }
    $downloads = [Environment]::GetEnvironmentVariable('DCOIR_DOWNLOADS_DIR', 'Machine')
    if ([string]::IsNullOrWhiteSpace($downloads)) {
        $downloads = [Environment]::GetEnvironmentVariable('USERPROFILE', 'Process')
        if (-not [string]::IsNullOrWhiteSpace($downloads)) { $downloads = Join-Path $downloads 'Downloads' }
    }
    if ([string]::IsNullOrWhiteSpace($downloads)) { $downloads = (Get-Location).Path }
    if (-not (Test-Path -LiteralPath $downloads -PathType Container)) { New-Item -ItemType Directory -Force -Path $downloads | Out-Null }
    return (Join-Path $downloads ('dcoir_apply_in_payload_stager_{0}.log.txt' -f (Get-Date -Format 'yyyyMMdd_HHmmss')))
}

$script:LogPath = Resolve-DefaultLogPath -RequestedLogPath $LogPath
$success = $false
$result = $null

try {
    Add-LogLine 'Starting DCOIR apply-in payload staging helper.'
    Add-LogLine ('Tool version: {0}' -f $ToolVersion)
    Add-LogLine ('Current directory: {0}' -f (Get-Location).Path)
    Add-LogLine ('Log path: {0}' -f $script:LogPath)
    Add-LogLine ('Raw PayloadZip argument: {0}' -f $PayloadZip)
    Add-LogLine ('Raw RequestId argument: {0}' -f $RequestId)

    if ([string]::IsNullOrWhiteSpace($RepoRoot)) {
        $RepoRoot = [Environment]::GetEnvironmentVariable('DCOIR_REPO_ROOT', 'Machine')
        Add-LogLine ('DCOIR_REPO_ROOT present: {0}' -f (-not [string]::IsNullOrWhiteSpace($RepoRoot)))
    }
    if ([string]::IsNullOrWhiteSpace($RepoRoot)) { $RepoRoot = (Get-Location).Path }
    $RepoRoot = [System.IO.Path]::GetFullPath($RepoRoot)
    Add-LogLine ('Resolved repo root: {0}' -f $RepoRoot)
    if (-not (Test-Path -LiteralPath $RepoRoot -PathType Container)) { throw "Repo root not found: $RepoRoot" }

    $payloadZipFull = [System.IO.Path]::GetFullPath($PayloadZip)
    Add-LogLine ('Resolved payload ZIP: {0}' -f $payloadZipFull)
    if (-not (Test-Path -LiteralPath $payloadZipFull -PathType Leaf)) {
        throw "Payload ZIP not found: $payloadZipFull. Create or provide an apply-in ZIP containing apply_manifest.json, then rerun with -PayloadZip pointing to that ZIP."
    }

    if ([string]::IsNullOrWhiteSpace($RequestId)) {
        $RequestId = '{0}-{1}' -f (ConvertTo-SafeRequestId ([IO.Path]::GetFileNameWithoutExtension($payloadZipFull))), (Get-Date -Format 'yyyyMMdd-HHmmss')
    }
    if (-not (Test-SafeRequestId $RequestId)) { throw 'RequestId may contain only letters, numbers, dot, underscore, and dash.' }
    Add-LogLine ('Resolved request id: {0}' -f $RequestId)

    $entries = Test-ZipHasApplyManifest -ZipPath $payloadZipFull
    Add-LogLine ('Input ZIP entry count: {0}' -f $entries.Count)
    $sourceSha = Get-Sha256Hex -Path $payloadZipFull
    Add-LogLine ('Input ZIP SHA256: {0}' -f $sourceSha)
    $bytes = [System.IO.File]::ReadAllBytes($payloadZipFull)
    Add-LogLine ('Input ZIP bytes: {0}' -f $bytes.Length)
    $encoded = [Convert]::ToBase64String($bytes, [Base64FormattingOptions]::InsertLineBreaks)

    $stagingDir = Join-Path $RepoRoot (Join-Path 'chatgpt_staging\in' $RequestId)
    $payloadB64Path = Join-Path $stagingDir 'payload.zip.b64'
    $reportPath = Join-Path $stagingDir 'payload_staging_report.json'
    Add-LogLine ('Staging directory: {0}' -f $stagingDir)
    if ((Test-Path -LiteralPath $payloadB64Path -PathType Leaf) -and -not $Overwrite) { throw "Payload already exists: $payloadB64Path. Use -Overwrite to replace it." }

    New-Item -ItemType Directory -Force -Path $stagingDir | Out-Null
    Write-AsciiText -Path $payloadB64Path -Text ($encoded + [Environment]::NewLine)
    Add-LogLine ('Wrote payload base64: {0}' -f $payloadB64Path)

    $readBack = Get-Content -LiteralPath $payloadB64Path -Raw
    if ($readBack -match 'ERROR TRUNCATED') { throw 'Staged payload contains ERROR TRUNCATED marker.' }
    $decoded = [Convert]::FromBase64String($readBack)
    $tempZip = Join-Path ([IO.Path]::GetTempPath()) ('dcoir_apply_in_' + [guid]::NewGuid().ToString('N') + '.zip')
    try {
        [System.IO.File]::WriteAllBytes($tempZip, $decoded)
        $roundTripSha = Get-Sha256Hex -Path $tempZip
        Add-LogLine ('Round-trip ZIP SHA256: {0}' -f $roundTripSha)
        if ($roundTripSha -ne $sourceSha) { throw "Round-trip SHA256 mismatch. Source=$sourceSha RoundTrip=$roundTripSha" }
        Test-ZipHasApplyManifest -ZipPath $tempZip | Out-Null
        Add-LogLine 'Round-trip validation passed.'
    }
    finally {
        if (Test-Path -LiteralPath $tempZip -PathType Leaf) { Remove-Item -LiteralPath $tempZip -Force }
    }

    $relativePayload = 'chatgpt_staging/in/{0}/payload.zip.b64' -f $RequestId
    $relativeReport = 'chatgpt_staging/in/{0}/payload_staging_report.json' -f $RequestId
    $report = [ordered]@{
        tool = 'New-DcoirApplyInPayload.ps1'
        tool_version = $ToolVersion
        created_at = (Get-Date -Format o)
        request_id = $RequestId
        staged_payload_path = $relativePayload
        staging_report_path = $relativeReport
        log_path = $script:LogPath
        source_payload_zip = $payloadZipFull
        source_payload_sha256 = $sourceSha
        source_payload_bytes = $bytes.Length
        round_trip_validated = $true
        zip_entry_count = $entries.Count
        workflow_dispatch_payload_b64_path = $relativePayload
        next_action = 'Commit and push the staged payload.zip.b64 and report to trigger the apply-in workflow, or use workflow_dispatch with the payload path.'
    }
    Write-Utf8NoBom -Path $reportPath -Text ($report | ConvertTo-Json -Depth 10)
    Add-LogLine ('Wrote staging report: {0}' -f $reportPath)

    $success = $true
    $result = [ordered]@{
        success = $true
        request_id = $RequestId
        staged_payload_path = $relativePayload
        staging_report_path = $relativeReport
        source_payload_sha256 = $sourceSha
        round_trip_validated = $true
        log_path = $script:LogPath
    }
    Add-LogLine 'Completed successfully.'
}
catch {
    Add-LogLine ('ERROR: {0}' -f $_.Exception.Message)
    Add-LogLine ('ERROR TYPE: {0}' -f $_.Exception.GetType().FullName)
    if ($_.ScriptStackTrace) { Add-LogLine ('STACK: {0}' -f ($_.ScriptStackTrace -replace "`r?`n", ' | ')) }
    $result = [ordered]@{
        success = $false
        error_message = $_.Exception.Message
        error_type = $_.Exception.GetType().FullName
        log_path = $script:LogPath
        next_action = 'Upload the log_path file to ChatGPT, or rerun with -PayloadZip pointing to a valid apply-in ZIP containing apply_manifest.json.'
    }
    $result | ConvertTo-Json -Depth 8
    exit 1
}

$result | ConvertTo-Json -Depth 8
if (-not $success) { exit 1 }
