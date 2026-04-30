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
if (-not $OutputDir) { $OutputDir = Join-Path $env:USERPROFILE "Downloads" }
if (-not (Test-Path -LiteralPath $ManifestJson)) { throw "Manifest not found: $ManifestJson" }
if (-not (Test-Path -LiteralPath $RepoRoot)) { throw "Repo root not found: $RepoRoot" }

$RepoRoot = (Resolve-Path -LiteralPath $RepoRoot).Path
$OutputDir = if (Test-Path -LiteralPath $OutputDir) { (Resolve-Path -LiteralPath $OutputDir).Path } else { $OutputDir }
New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null

$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$manifest = Get-Content -Raw -LiteralPath $ManifestJson | ConvertFrom-Json
$name = $manifest.name
if (-not $name) { $name = "targeted_snapshot" }

$tmp = Join-Path $env:TEMP "${name}_$stamp"
$stage = Join-Path $tmp "repo_snapshot"
$zip = Join-Path $OutputDir "${name}_$stamp.zip"
$log = Join-Path $OutputDir "${name}_$stamp.log.txt"

function Write-Log {
    param([AllowEmptyString()][string]$Text)
    $Text | Tee-Object -FilePath $log -Append | Out-Null
}

function Invoke-GitLogged {
    param(
        [Parameter(Mandatory = $true)]
        [string[]]$Arguments
    )

    Write-Log ""
    Write-Log (">>> git " + ($Arguments -join " "))

    Push-Location $RepoRoot
    try {
        $output = & git @Arguments 2>&1
        $exitCode = $LASTEXITCODE
    }
    finally {
        Pop-Location
    }

    foreach ($line in $output) { Write-Log ([string]$line) }

    if ($exitCode -ne 0) {
        throw "git $($Arguments -join ' ') failed with exit code $exitCode"
    }

    return @($output | ForEach-Object { [string]$_ })
}

function Copy-RepoPath {
    param(
        [Parameter(Mandatory = $true)]
        [string]$RelativePath
    )

    $src = Join-Path $RepoRoot $RelativePath
    if (-not (Test-Path -LiteralPath $src)) {
        throw "Missing requested path: $RelativePath"
    }

    $dst = Join-Path $stage $RelativePath
    $parent = Split-Path -Parent $dst
    if ($parent) { New-Item -ItemType Directory -Force -Path $parent | Out-Null }

    if (Test-Path -LiteralPath $src -PathType Container) {
        New-Item -ItemType Directory -Force -Path $dst | Out-Null
        Get-ChildItem -LiteralPath $src -Force | ForEach-Object {
            Copy-Item -LiteralPath $_.FullName -Destination $dst -Recurse -Force
        }
    }
    else {
        Copy-Item -LiteralPath $src -Destination $dst -Force
    }

    Write-Log "COPIED: $RelativePath"
}

try {
    Write-Log "DCOIR Targeted Snapshot Builder"
    Write-Log "Timestamp: $(Get-Date -Format o)"
    Write-Log "Repo: $RepoRoot"
    Write-Log "Manifest: $ManifestJson"
    Write-Log "OutputDir: $OutputDir"

    Write-Log ""
    Write-Log "== BRANCH CHECK =="
    $currentBranch = (Invoke-GitLogged @('branch', '--show-current') | Select-Object -Last 1).Trim()
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

    Write-Log ""
    Write-Log "== COPY TARGET PATHS =="
    if (-not $manifest.paths) { throw "Manifest has no paths array." }
    foreach ($rel in $manifest.paths) {
        if (-not $rel) { continue }
        Copy-RepoPath -RelativePath ([string]$rel)
    }

    if (Test-Path -LiteralPath $zip) { Remove-Item -LiteralPath $zip -Force }
    Compress-Archive -Path (Join-Path $stage '*') -DestinationPath $zip -Force
    Remove-Item -LiteralPath $tmp -Recurse -Force -ErrorAction SilentlyContinue

    Write-Log ""
    Write-Log "== Snapshot complete =="
    Write-Log "ZIP: $zip"
    Write-Log "LOG: $log"

    Write-Host ""
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
