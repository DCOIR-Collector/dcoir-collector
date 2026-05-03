[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][string]$PayloadZip,
    [string]$RequestId,
    [string]$RepoRoot,
    [switch]$Overwrite
)

$ErrorActionPreference = 'Stop'
$ToolVersion = '2026-05-03.1'

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

if ([string]::IsNullOrWhiteSpace($RepoRoot)) {
    $RepoRoot = [Environment]::GetEnvironmentVariable('DCOIR_REPO_ROOT', 'Machine')
}
if ([string]::IsNullOrWhiteSpace($RepoRoot)) { $RepoRoot = (Get-Location).Path }
$RepoRoot = [System.IO.Path]::GetFullPath($RepoRoot)
if (-not (Test-Path -LiteralPath $RepoRoot -PathType Container)) { throw "Repo root not found: $RepoRoot" }

$payloadZipFull = [System.IO.Path]::GetFullPath($PayloadZip)
if (-not (Test-Path -LiteralPath $payloadZipFull -PathType Leaf)) { throw "Payload ZIP not found: $payloadZipFull" }

if ([string]::IsNullOrWhiteSpace($RequestId)) {
    $RequestId = '{0}-{1}' -f (ConvertTo-SafeRequestId ([IO.Path]::GetFileNameWithoutExtension($payloadZipFull))), (Get-Date -Format 'yyyyMMdd-HHmmss')
}
if (-not (Test-SafeRequestId $RequestId)) { throw 'RequestId may contain only letters, numbers, dot, underscore, and dash.' }

$entries = Test-ZipHasApplyManifest -ZipPath $payloadZipFull
$sourceSha = Get-Sha256Hex -Path $payloadZipFull
$bytes = [System.IO.File]::ReadAllBytes($payloadZipFull)
$encoded = [Convert]::ToBase64String($bytes, [Base64FormattingOptions]::InsertLineBreaks)

$stagingDir = Join-Path $RepoRoot (Join-Path 'chatgpt_staging\in' $RequestId)
$payloadB64Path = Join-Path $stagingDir 'payload.zip.b64'
$reportPath = Join-Path $stagingDir 'payload_staging_report.json'
if ((Test-Path -LiteralPath $payloadB64Path -PathType Leaf) -and -not $Overwrite) { throw "Payload already exists: $payloadB64Path" }

New-Item -ItemType Directory -Force -Path $stagingDir | Out-Null
Write-AsciiText -Path $payloadB64Path -Text ($encoded + [Environment]::NewLine)

$readBack = Get-Content -LiteralPath $payloadB64Path -Raw
if ($readBack -match 'ERROR TRUNCATED') { throw 'Staged payload contains ERROR TRUNCATED marker.' }
$decoded = [Convert]::FromBase64String($readBack)
$tempZip = Join-Path ([IO.Path]::GetTempPath()) ('dcoir_apply_in_' + [guid]::NewGuid().ToString('N') + '.zip')
try {
    [System.IO.File]::WriteAllBytes($tempZip, $decoded)
    $roundTripSha = Get-Sha256Hex -Path $tempZip
    if ($roundTripSha -ne $sourceSha) { throw "Round-trip SHA256 mismatch. Source=$sourceSha RoundTrip=$roundTripSha" }
    Test-ZipHasApplyManifest -ZipPath $tempZip | Out-Null
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
    source_payload_zip = $payloadZipFull
    source_payload_sha256 = $sourceSha
    source_payload_bytes = $bytes.Length
    round_trip_validated = $true
    zip_entry_count = $entries.Count
    workflow_dispatch_payload_b64_path = $relativePayload
    next_action = 'Commit and push the staged payload.zip.b64 and report to trigger the apply-in workflow, or use workflow_dispatch with the payload path.'
}
Write-Utf8NoBom -Path $reportPath -Text ($report | ConvertTo-Json -Depth 10)

$result = [ordered]@{
    success = $true
    request_id = $RequestId
    staged_payload_path = $relativePayload
    staging_report_path = $relativeReport
    source_payload_sha256 = $sourceSha
    round_trip_validated = $true
}
$result | ConvertTo-Json -Depth 8
