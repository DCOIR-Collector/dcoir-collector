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

$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$manifest = Get-Content -Raw -LiteralPath $ManifestJson | ConvertFrom-Json
$name = $manifest.name
if (-not $name) { $name = "targeted_snapshot" }

$tmp = Join-Path $OutputDir "${name}_$stamp"
$zip = Join-Path $OutputDir "${name}_$stamp.zip"
$log = Join-Path $OutputDir "${name}_$stamp.log.txt"

Set-Location $RepoRoot

& {
    "DCOIR Targeted Snapshot Builder"
    "Timestamp: $(Get-Date -Format o)"
    "Repo: $RepoRoot"
    "Manifest: $ManifestJson"

    ""
    "== BRANCH CHECK =="
    $currentBranch = git branch --show-current
    "Current branch: $currentBranch"
    if ($currentBranch -ne $Branch) { throw "Expected branch '$Branch' but found '$currentBranch'." }

    ""
    "== DIRTY TREE CHECK BEFORE PULL =="
    $dirty = git status --short
    if ($dirty) {
        $dirty
        throw "Working tree is not clean before snapshot. Commit, stash, or ask for recovery before continuing."
    }

    ""
    "== FETCH AND FAST-FORWARD PULL =="
    git fetch $Remote --prune
    git pull --ff-only $Remote $Branch
    if ($LASTEXITCODE -ne 0) { throw "Fast-forward pull failed." }

    ""
    "== DIRTY TREE CHECK AFTER PULL =="
    $dirtyAfter = git status --short
    if ($dirtyAfter) {
        $dirtyAfter
        throw "Working tree is not clean after pull. Stop."
    }

    Remove-Item $tmp -Recurse -Force -ErrorAction SilentlyContinue
    New-Item -ItemType Directory -Path $tmp | Out-Null

    ""
    "== COPY TARGET PATHS =="
    foreach ($rel in $manifest.paths) {
        if (-not $rel) { continue }
        $src = Join-Path $RepoRoot $rel
        if (Test-Path -LiteralPath $src) {
            $dst = Join-Path $tmp $rel
            New-Item -ItemType Directory -Path (Split-Path $dst) -Force | Out-Null
            Copy-Item -LiteralPath $src -Destination $dst -Force
            "COPIED: $rel"
        } else {
            "MISSING: $rel"
        }
    }

    Compress-Archive -Path (Join-Path $tmp '*') -DestinationPath $zip -Force
    Remove-Item $tmp -Recurse -Force

    ""
    "Created snapshot ZIP: $zip"
} 2>&1 | Tee-Object -FilePath $log

Write-Host ""
Write-Host "Saved snapshot ZIP:"
Write-Host $zip
Write-Host "Saved log:"
Write-Host $log
