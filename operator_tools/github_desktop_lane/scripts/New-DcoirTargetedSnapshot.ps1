[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$ManifestJson,
    [string]$RepoRoot = $env:DCOIR_REPO_ROOT,
    [string]$OutputDir = $env:DCOIR_DOWNLOADS_DIR,
    [string]$Remote = "origin",
    [string]$Branch = "main"
)

$ErrorActionPreference = "Stop"
if (-not $RepoRoot) { throw "DCOIR_REPO_ROOT is not set." }
if (-not (Test-Path -LiteralPath $RepoRoot -PathType Container)) { throw "Repo root not found: $RepoRoot" }
if (-not $OutputDir) { $OutputDir = Join-Path $env:USERPROFILE "Downloads" }
if (-not (Test-Path -LiteralPath $OutputDir -PathType Container)) { New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null }
if (-not (Test-Path -LiteralPath $ManifestJson)) { throw "Manifest not found: $ManifestJson" }

$RepoRoot = (Resolve-Path -LiteralPath $RepoRoot).Path
$OutputDir = (Resolve-Path -LiteralPath $OutputDir).Path
$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$manifest = Get-Content -Raw -LiteralPath $ManifestJson | ConvertFrom-Json
$name = $manifest.name
if (-not $name) { $name = "targeted_snapshot" }
$safeName = ($name -replace '[^A-Za-z0-9_.-]', '_')
$tmp = Join-Path $OutputDir "${safeName}_$stamp"
$stage = Join-Path $tmp "snapshot"
$zip = Join-Path $OutputDir "${safeName}_$stamp.zip"
$log = Join-Path $OutputDir "${safeName}_$stamp.log.txt"

function Write-Log {
    param([AllowEmptyString()][string]$Text)
    Write-Host $Text
    $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::AppendAllText($log, ($Text + [Environment]::NewLine), $utf8NoBom)
}

function ConvertTo-NativeArgumentString {
    param([AllowEmptyString()][string]$Argument)
    if ($null -eq $Argument) { return '""' }
    if ($Argument.Length -eq 0) { return '""' }
    if ($Argument -notmatch '[\s"]') { return $Argument }
    $escaped = $Argument -replace '(\\*)"', '$1$1\"'
    $escaped = $escaped -replace '(\\+)$', '$1$1'
    return '"' + $escaped + '"'
}

function Invoke-GitLogged {
    param([Parameter(Mandatory = $true)][string[]]$Arguments)
    Write-Log ""
    Write-Log (">>> git " + ($Arguments -join " "))
    $argumentString = ($Arguments | ForEach-Object { ConvertTo-NativeArgumentString ([string]$_) }) -join ' '
    Push-Location $RepoRoot
    try {
        $psi = New-Object System.Diagnostics.ProcessStartInfo
        $psi.FileName = "git.exe"
        $psi.Arguments = $argumentString
        $psi.WorkingDirectory = $RepoRoot
        $psi.UseShellExecute = $false
        $psi.RedirectStandardOutput = $true
        $psi.RedirectStandardError = $true
        $psi.CreateNoWindow = $true
        $process = New-Object System.Diagnostics.Process
        $process.StartInfo = $psi
        [void]$process.Start()
        $stdout = $process.StandardOutput.ReadToEnd()
        $stderr = $process.StandardError.ReadToEnd()
        $process.WaitForExit()
        $exitCode = $process.ExitCode
    }
    finally {
        Pop-Location
    }
    $lines = New-Object System.Collections.Generic.List[string]
    foreach ($text in @($stdout, $stderr)) {
        if ($null -ne $text -and $text.Length -gt 0) {
            $normalized = $text -replace "`r`n", "`n"
            foreach ($line in ($normalized -split "`n")) {
                if ($line.Length -gt 0) {
                    $lines.Add([string]$line) | Out-Null
                    Write-Log ([string]$line)
                }
            }
        }
    }
    if ($exitCode -ne 0) { throw "git $($Arguments -join ' ') failed with exit code $exitCode" }
    return @($lines.ToArray())
}

function Copy-RepoPath {
    param([Parameter(Mandatory = $true)][string]$RelativePath)
    if ($RelativePath -match '^[A-Za-z]:') { throw "Absolute path is not allowed: $RelativePath" }
    if ($RelativePath -match '(^|[\\/])\.\.([\\/]|$)') { throw "Parent path segment is not allowed: $RelativePath" }
    $src = Join-Path $RepoRoot $RelativePath
    if (-not (Test-Path -LiteralPath $src)) { throw "Requested path is missing: $RelativePath" }
    $dst = Join-Path $stage $RelativePath
    $parent = Split-Path -Parent $dst
    if ($parent) { New-Item -ItemType Directory -Force -Path $parent | Out-Null }
    if (Test-Path -LiteralPath $src -PathType Container) {
        New-Item -ItemType Directory -Force -Path $dst | Out-Null
        Get-ChildItem -LiteralPath $src -Force | ForEach-Object {
            Copy-Item -LiteralPath $_.FullName -Destination $dst -Recurse -Force
        }
    } else {
        Copy-Item -LiteralPath $src -Destination $dst -Force
    }
    Write-Log "COPIED: $RelativePath"
}

try {
    if (Test-Path -LiteralPath $log) { Remove-Item -LiteralPath $log -Force }
    Write-Log "DCOIR Targeted Snapshot Builder"
    Write-Log "Timestamp: $(Get-Date -Format o)"
    Write-Log "Repo: $RepoRoot"
    Write-Log "Manifest: $ManifestJson"

    Write-Log ""
    Write-Log "== BRANCH CHECK =="
    $branchOutput = @(Invoke-GitLogged @('branch', '--show-current'))
    $currentBranch = ($branchOutput | Select-Object -Last 1).Trim()
    Write-Log "Current branch: $currentBranch"
    if ($currentBranch -ne $Branch) { throw "Expected branch '$Branch' but found '$currentBranch'." }

    Write-Log ""
    Write-Log "== DIRTY TREE CHECK BEFORE PULL =="
    $dirty = @(Invoke-GitLogged @('status', '--porcelain'))
    if ($dirty.Count -gt 0) {
        foreach ($line in $dirty) { Write-Log "DIRTY: $line" }
        throw "Working tree is not clean before snapshot. Commit, stash, or ask for recovery before continuing."
    }

    Write-Log ""
    Write-Log "== FETCH AND FAST-FORWARD PULL =="
    Invoke-GitLogged @('fetch', $Remote, '--prune') | Out-Null
    Invoke-GitLogged @('pull', '--ff-only', $Remote, $Branch) | Out-Null

    Write-Log ""
    Write-Log "== DIRTY TREE CHECK AFTER PULL =="
    $dirtyAfter = @(Invoke-GitLogged @('status', '--porcelain'))
    if ($dirtyAfter.Count -gt 0) {
        foreach ($line in $dirtyAfter) { Write-Log "DIRTY: $line" }
        throw "Working tree is not clean after pull. Stop and upload log."
    }

    Remove-Item -LiteralPath $tmp -Recurse -Force -ErrorAction SilentlyContinue
    New-Item -ItemType Directory -Force -Path $stage | Out-Null
    foreach ($rel in $manifest.paths) {
        if (-not $rel) { continue }
        Copy-RepoPath -RelativePath ([string]$rel)
    }
    if (Test-Path -LiteralPath $zip) { Remove-Item -LiteralPath $zip -Force }
    $friendlyZipScript = Join-Path $PSScriptRoot "New-DcoirChatGPTFriendlyZip.ps1"
    if (Test-Path -LiteralPath $friendlyZipScript -PathType Leaf) {
        . $friendlyZipScript
        New-DcoirChatGPTFriendlyZip -SourceFolder $stage -OutputZip $zip -IndexTitle "DCOIR targeted snapshot" -NormalizeTextEncoding | Out-Null
    } else {
        Compress-Archive -Path (Join-Path $stage '*') -DestinationPath $zip -Force
    }
    Remove-Item -LiteralPath $tmp -Recurse -Force -ErrorAction SilentlyContinue

    Write-Log ""
    Write-Log "== Snapshot complete =="
    Write-Log "ZIP: $zip"
    Write-Log "LOG: $log"
    Write-Host "Saved snapshot ZIP:"
    Write-Host $zip
    Write-Host "Saved log:"
    Write-Host $log
}
catch {
    Write-Log ""
    Write-Log "== Snapshot failed =="
    Write-Log $_.Exception.Message
    Write-Log "LOG: $log"
    throw
}
