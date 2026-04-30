[CmdletBinding()]
param(
    [string]$RepoRoot = $env:DCOIR_REPO_ROOT,
    [string]$OutputDir = $env:DCOIR_DOWNLOADS_DIR,
    [string]$SnapshotName = "dcoir_text_only_repo_snapshot",
    [Int64]$MaxFileBytes = 5242880,
    [string[]]$ExcludeDirectoryNames = @(
        ".git", ".github-desktop", ".vs", ".vscode", "node_modules", "__pycache__",
        ".pytest_cache", ".mypy_cache", ".ruff_cache", ".venv", "venv", "env",
        "bin", "obj", "dist", "build", "target", ".terraform"
    ),
    [string[]]$ExcludeExtensions = @(
        ".7z", ".a", ".appx", ".bin", ".bmp", ".cab", ".class", ".dll", ".doc", ".docx",
        ".dylib", ".eot", ".exe", ".gif", ".gz", ".ico", ".iso", ".jar", ".jpeg", ".jpg",
        ".lib", ".mp3", ".mp4", ".msi", ".nupkg", ".otf", ".pdf", ".pdb", ".png", ".ppt",
        ".pptx", ".pyc", ".rar", ".so", ".tar", ".tgz", ".ttf", ".war", ".webp", ".woff",
        ".woff2", ".xls", ".xlsx", ".zip"
    ),
    [switch]$IncludeDotDirectories,
    [switch]$NoGitCleanCheck
)

$ErrorActionPreference = "Stop"
if (-not $RepoRoot) { throw "DCOIR_REPO_ROOT is not set. Set it to your local dcoir-collector repo root or pass -RepoRoot." }
if (-not (Test-Path -LiteralPath $RepoRoot -PathType Container)) { throw "Repo root not found: $RepoRoot" }
$RepoRoot = (Resolve-Path -LiteralPath $RepoRoot).Path
if (-not $OutputDir) { $OutputDir = Join-Path $env:USERPROFILE "Downloads" }
if (-not (Test-Path -LiteralPath $OutputDir -PathType Container)) { New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null }
$OutputDir = (Resolve-Path -LiteralPath $OutputDir).Path

$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$safeName = ($SnapshotName -replace '[^A-Za-z0-9_.-]', '_')
$tmpRoot = Join-Path ([System.IO.Path]::GetTempPath()) "${safeName}_$stamp"
$stage = Join-Path $tmpRoot "snapshot"
$zipPath = Join-Path $OutputDir "${safeName}_$stamp.zip"
$logPath = Join-Path $OutputDir "${safeName}_$stamp.log.txt"
$manifestPath = Join-Path $OutputDir "${safeName}_$stamp.manifest.json"
$included = New-Object System.Collections.Generic.List[object]
$skipped = New-Object System.Collections.Generic.List[object]

function Write-Log { param([AllowEmptyString()][string]$Text) $Text | Tee-Object -FilePath $logPath -Append | Out-Null }
function Add-Skip {
    param([string]$RelativePath, [string]$Reason, [Nullable[Int64]]$Size = $null)
    $skipped.Add([pscustomobject]@{ path = $RelativePath; reason = $Reason; size_bytes = $Size }) | Out-Null
    Write-Log "SKIP [$Reason]: $RelativePath"
}
function Test-UnderPath {
    param([string]$Path, [string]$Root)
    $fullPath = [System.IO.Path]::GetFullPath($Path)
    $fullRoot = [System.IO.Path]::GetFullPath($Root).TrimEnd([System.IO.Path]::DirectorySeparatorChar, [System.IO.Path]::AltDirectorySeparatorChar) + [System.IO.Path]::DirectorySeparatorChar
    return $fullPath.StartsWith($fullRoot, [System.StringComparison]::OrdinalIgnoreCase)
}
function Get-RelativePathSafe {
    param([string]$Path)
    $repoUri = [System.Uri]::new(($RepoRoot.TrimEnd('\','/') + [System.IO.Path]::DirectorySeparatorChar))
    $fileUri = [System.Uri]::new($Path)
    return [System.Uri]::UnescapeDataString($repoUri.MakeRelativeUri($fileUri).ToString()).Replace('/', [System.IO.Path]::DirectorySeparatorChar)
}
function Test-LikelyBinary {
    param([string]$Path)
    $bufferSize = 8192
    $stream = [System.IO.File]::Open($Path, [System.IO.FileMode]::Open, [System.IO.FileAccess]::Read, [System.IO.FileShare]::ReadWrite)
    try {
        $length = [Math]::Min($bufferSize, [int]$stream.Length)
        if ($length -le 0) { return $false }
        $buffer = New-Object byte[] $length
        [void]$stream.Read($buffer, 0, $length)
        for ($i = 0; $i -lt $length; $i++) { if ($buffer[$i] -eq 0) { return $true } }
        return $false
    }
    finally { $stream.Dispose() }
}
function Invoke-GitStatusPorcelain {
    $git = Get-Command git.exe -ErrorAction SilentlyContinue
    if (-not $git) { return @("git.exe unavailable; clean-tree check skipped") }
    $psi = [System.Diagnostics.ProcessStartInfo]::new()
    $psi.FileName = $git.Source
    $psi.Arguments = "status --porcelain"
    $psi.WorkingDirectory = $RepoRoot
    $psi.UseShellExecute = $false
    $psi.RedirectStandardOutput = $true
    $psi.RedirectStandardError = $true
    $psi.CreateNoWindow = $true
    $process = [System.Diagnostics.Process]::new()
    $process.StartInfo = $psi
    [void]$process.Start()
    $stdout = $process.StandardOutput.ReadToEnd()
    $stderr = $process.StandardError.ReadToEnd()
    $process.WaitForExit()
    if ($process.ExitCode -ne 0) { return @("git status failed: $stderr") }
    if ([string]::IsNullOrWhiteSpace($stdout)) { return @() }
    return @($stdout -replace "`r`n", "`n" -split "`n" | Where-Object { $_ })
}

try {
    Remove-Item -LiteralPath $tmpRoot -Recurse -Force -ErrorAction SilentlyContinue
    New-Item -ItemType Directory -Force -Path $stage | Out-Null
    foreach ($path in @($zipPath, $logPath, $manifestPath)) { if (Test-Path -LiteralPath $path) { Remove-Item -LiteralPath $path -Force } }
    Write-Log "DCOIR Text-Only Repo Snapshot"
    Write-Log "Timestamp: $(Get-Date -Format o)"
    Write-Log "RepoRoot: $RepoRoot"
    Write-Log "OutputDir: $OutputDir"
    Write-Log "MaxFileBytes: $MaxFileBytes"
    Write-Log "Read-only: true"
    if (-not $NoGitCleanCheck) {
        Write-Log ""
        Write-Log "== GIT STATUS CHECK =="
        $statusLines = @(Invoke-GitStatusPorcelain)
        if ($statusLines.Count -gt 0) {
            foreach ($line in $statusLines) { Write-Log "GIT-STATUS: $line" }
            Write-Log "Git status output is logged for context only. Snapshot will continue because this tool is read-only."
        } else { Write-Log "Git working tree appears clean." }
    }
    Write-Log ""
    Write-Log "== SCAN AND COPY TEXT FILES =="
    $allFiles = Get-ChildItem -LiteralPath $RepoRoot -Recurse -Force -File
    foreach ($file in $allFiles) {
        $full = $file.FullName
        if (-not (Test-UnderPath -Path $full -Root $RepoRoot)) { Add-Skip -RelativePath $full -Reason "outside_repo_root" -Size $file.Length; continue }
        $rel = Get-RelativePathSafe -Path $full
        $parts = $rel -split '[\\/]'
        $dirParts = if ($parts.Count -gt 1) { $parts[0..($parts.Count - 2)] } else { @() }
        $excludedDir = $null
        foreach ($part in $dirParts) {
            if ($ExcludeDirectoryNames -contains $part) { $excludedDir = $part; break }
            if (-not $IncludeDotDirectories -and $part.StartsWith('.') -and $part -ne '.github') { $excludedDir = $part; break }
        }
        if ($excludedDir) { Add-Skip -RelativePath $rel -Reason "excluded_directory:$excludedDir" -Size $file.Length; continue }
        $ext = $file.Extension.ToLowerInvariant()
        if ($ExcludeExtensions -contains $ext) { Add-Skip -RelativePath $rel -Reason "excluded_extension:$ext" -Size $file.Length; continue }
        if ($file.Length -gt $MaxFileBytes) { Add-Skip -RelativePath $rel -Reason "over_max_file_bytes" -Size $file.Length; continue }
        if (Test-LikelyBinary -Path $full) { Add-Skip -RelativePath $rel -Reason "binary_sniff" -Size $file.Length; continue }
        $dest = Join-Path $stage $rel
        $parent = Split-Path -Parent $dest
        if ($parent) { New-Item -ItemType Directory -Force -Path $parent | Out-Null }
        Copy-Item -LiteralPath $full -Destination $dest -Force
        $included.Add([pscustomobject]@{ path = $rel; size_bytes = $file.Length; extension = $ext }) | Out-Null
        Write-Log "INCLUDE: $rel"
    }
    Compress-Archive -Path (Join-Path $stage '*') -DestinationPath $zipPath -Force
    $manifest = [ordered]@{
        tool = "New-DcoirTextOnlyRepoSnapshot.ps1"
        tool_version = "2026-05-01.1"
        created_at = (Get-Date -Format o)
        repo_root = $RepoRoot
        output_zip = $zipPath
        output_log = $logPath
        max_file_bytes = $MaxFileBytes
        include_dot_directories = [bool]$IncludeDotDirectories
        no_git_clean_check = [bool]$NoGitCleanCheck
        counts = [ordered]@{ included_files = $included.Count; skipped_files = $skipped.Count }
        included_files = @($included.ToArray())
        skipped_files = @($skipped.ToArray())
    }
    $manifest | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $manifestPath -Encoding UTF8
    Write-Log ""
    Write-Log "== Snapshot complete =="
    Write-Log "Included files: $($included.Count)"
    Write-Log "Skipped files: $($skipped.Count)"
    Write-Log "ZIP: $zipPath"
    Write-Log "LOG: $logPath"
    Write-Log "MANIFEST: $manifestPath"
    Write-Host "Saved text-only snapshot ZIP:"
    Write-Host $zipPath
    Write-Host "Saved log:"
    Write-Host $logPath
    Write-Host "Saved manifest:"
    Write-Host $manifestPath
}
catch {
    Write-Log ""
    Write-Log "== Snapshot failed =="
    Write-Log $_.Exception.Message
    Write-Log "LOG: $logPath"
    throw
}
finally { Remove-Item -LiteralPath $tmpRoot -Recurse -Force -ErrorAction SilentlyContinue }
