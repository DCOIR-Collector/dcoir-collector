[CmdletBinding()]
param(
    [string]$SourceFolder,
    [string]$OutputZip,
    [string]$IndexTitle = "DCOIR ChatGPT-friendly upload package",
    [string[]]$SkipDirectoryNames = @(".git", "__pycache__", "node_modules", ".pytest_cache", ".mypy_cache", ".ruff_cache", ".venv", "venv", "env", "dist", "build", "target", "__MACOSX"),
    [string[]]$SkipFileNames = @(".DS_Store", "Thumbs.db", "Desktop.ini"),
    [int]$MaxArchivePathLength = 180,
    [switch]$NormalizeTextEncoding,
    [switch]$NoIndex
)

$ErrorActionPreference = "Stop"
$Script:DcoirChatGPTFriendlyZipVersion = "2026-05-01.1"

function Get-DcoirFileSha256 {
    param([Parameter(Mandatory = $true)][string]$Path)
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) { return $null }
    return (Get-FileHash -Algorithm SHA256 -LiteralPath $Path).Hash.ToLowerInvariant()
}

function Get-DcoirRelativePath {
    param(
        [Parameter(Mandatory = $true)][string]$Root,
        [Parameter(Mandatory = $true)][string]$Path
    )
    $rootFull = [System.IO.Path]::GetFullPath($Root).TrimEnd([System.IO.Path]::DirectorySeparatorChar, [System.IO.Path]::AltDirectorySeparatorChar) + [System.IO.Path]::DirectorySeparatorChar
    $pathFull = [System.IO.Path]::GetFullPath($Path)
    if (-not $pathFull.StartsWith($rootFull, [System.StringComparison]::OrdinalIgnoreCase)) { throw "Path escapes source root: $Path" }
    return ($pathFull.Substring($rootFull.Length) -replace '\\', '/')
}

function Get-DcoirEncodingGuess {
    param([Parameter(Mandatory = $true)][string]$Path)
    $bytes = [System.IO.File]::ReadAllBytes($Path)
    if ($bytes.Length -ge 3 -and $bytes[0] -eq 0xEF -and $bytes[1] -eq 0xBB -and $bytes[2] -eq 0xBF) { return "utf-8-bom" }
    if ($bytes.Length -ge 2 -and $bytes[0] -eq 0xFF -and $bytes[1] -eq 0xFE) { return "utf-16le" }
    if ($bytes.Length -ge 2 -and $bytes[0] -eq 0xFE -and $bytes[1] -eq 0xFF) { return "utf-16be" }
    $limit = [Math]::Min($bytes.Length, 8192)
    for ($i = 0; $i -lt $limit; $i++) { if ($bytes[$i] -eq 0) { return "binary-or-utf16-no-bom" } }
    return "utf-8-or-ascii"
}

function Test-DcoirHiddenOrSystemPath {
    param(
        [Parameter(Mandatory = $true)][System.IO.FileInfo]$File,
        [Parameter(Mandatory = $true)][string]$RelativePath,
        [string[]]$DirectoryNames,
        [string[]]$FileNames
    )
    if (($File.Attributes -band [System.IO.FileAttributes]::Hidden) -or ($File.Attributes -band [System.IO.FileAttributes]::System)) { return $true }
    if ($FileNames -contains $File.Name) { return $true }
    if ($File.Name.StartsWith('.')) { return $true }
    foreach ($part in ($RelativePath -split '/')) {
        if ($DirectoryNames -contains $part) { return $true }
        if ($part -eq "__MACOSX") { return $true }
    }
    return $false
}

function Copy-DcoirFriendlyFile {
    param(
        [Parameter(Mandatory = $true)][string]$SourcePath,
        [Parameter(Mandatory = $true)][string]$DestinationPath,
        [switch]$NormalizeTextEncoding
    )
    $parent = Split-Path -Parent $DestinationPath
    if ($parent) { New-Item -ItemType Directory -Force -Path $parent | Out-Null }
    $guess = Get-DcoirEncodingGuess -Path $SourcePath
    $textExts = @(".txt", ".md", ".json", ".csv", ".log", ".ps1", ".psm1", ".psd1", ".yml", ".yaml", ".xml")
    $ext = [System.IO.Path]::GetExtension($SourcePath).ToLowerInvariant()
    if ($NormalizeTextEncoding -and ($textExts -contains $ext) -and ($guess -eq "utf-16le" -or $guess -eq "utf-16be" -or $guess -eq "utf-8-bom")) {
        $text = [System.IO.File]::ReadAllText($SourcePath)
        $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
        [System.IO.File]::WriteAllText($DestinationPath, $text, $utf8NoBom)
        return "normalized:$guess-to-utf8"
    }
    Copy-Item -LiteralPath $SourcePath -Destination $DestinationPath -Force
    return "copied:$guess"
}

function New-DcoirChatGPTFriendlyZip {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][string]$SourceFolder,
        [Parameter(Mandatory = $true)][string]$OutputZip,
        [string]$IndexTitle = "DCOIR ChatGPT-friendly upload package",
        [string[]]$SkipDirectoryNames = @(".git", "__pycache__", "node_modules", ".pytest_cache", ".mypy_cache", ".ruff_cache", ".venv", "venv", "env", "dist", "build", "target", "__MACOSX"),
        [string[]]$SkipFileNames = @(".DS_Store", "Thumbs.db", "Desktop.ini"),
        [int]$MaxArchivePathLength = 180,
        [switch]$NormalizeTextEncoding,
        [switch]$NoIndex
    )
    if (-not (Test-Path -LiteralPath $SourceFolder -PathType Container)) { throw "SourceFolder not found: $SourceFolder" }
    $source = (Resolve-Path -LiteralPath $SourceFolder).Path
    $outputParent = Split-Path -Parent $OutputZip
    if (-not $outputParent) { $outputParent = (Get-Location).Path }
    if (-not (Test-Path -LiteralPath $outputParent -PathType Container)) { New-Item -ItemType Directory -Force -Path $outputParent | Out-Null }
    $output = [System.IO.Path]::GetFullPath($OutputZip)
    $stageRoot = Join-Path ([System.IO.Path]::GetTempPath()) ("dcoir_chatgpt_zip_" + [System.Guid]::NewGuid().ToString("N"))
    $stage = Join-Path $stageRoot "payload"
    $captured = New-Object System.Collections.Generic.List[object]
    $skipped = New-Object System.Collections.Generic.List[object]
    try {
        New-Item -ItemType Directory -Force -Path $stage | Out-Null
        foreach ($file in @(Get-ChildItem -LiteralPath $source -Recurse -File -Force)) {
            $rel = Get-DcoirRelativePath -Root $source -Path $file.FullName
            if ($rel.Length -gt $MaxArchivePathLength) {
                $skipped.Add([pscustomobject]@{ path = $rel; reason = "archive_path_too_long"; size_bytes = $file.Length }) | Out-Null
                continue
            }
            if (Test-DcoirHiddenOrSystemPath -File $file -RelativePath $rel -DirectoryNames $SkipDirectoryNames -FileNames $SkipFileNames) {
                $skipped.Add([pscustomobject]@{ path = $rel; reason = "hidden_or_system_metadata"; size_bytes = $file.Length }) | Out-Null
                continue
            }
            $dest = Join-Path $stage ($rel -replace '/', [System.IO.Path]::DirectorySeparatorChar)
            $copyMode = Copy-DcoirFriendlyFile -SourcePath $file.FullName -DestinationPath $dest -NormalizeTextEncoding:$NormalizeTextEncoding
            $captured.Add([pscustomobject]@{
                path = $rel
                size_bytes = $file.Length
                sha256 = Get-DcoirFileSha256 -Path $file.FullName
                encoding_guess = Get-DcoirEncodingGuess -Path $file.FullName
                copy_mode = $copyMode
            }) | Out-Null
        }
        $createdAt = Get-Date -Format o
        $capturedJson = [ordered]@{
            tool = "New-DcoirChatGPTFriendlyZip.ps1"
            tool_version = $Script:DcoirChatGPTFriendlyZipVersion
            created_at = $createdAt
            source_folder = $source
            output_zip = $output
            normalize_text_encoding = [bool]$NormalizeTextEncoding
            captured_count = $captured.Count
            skipped_count = $skipped.Count
            captured_files = @($captured.ToArray())
            skipped_files = @($skipped.ToArray())
        }
        $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
        [System.IO.File]::WriteAllText((Join-Path $stage "captured_files.json"), ($capturedJson | ConvertTo-Json -Depth 8), $utf8NoBom)
        if (-not $NoIndex) {
            $index = @(
                "# $IndexTitle", "", "Created: $createdAt", "Tool: New-DcoirChatGPTFriendlyZip.ps1 $Script:DcoirChatGPTFriendlyZipVersion",
                "Source folder: $source", "Captured files: $($captured.Count)", "Skipped files: $($skipped.Count)",
                "Normalize text encoding: $([bool]$NormalizeTextEncoding)", "", "## Important files", "- captured_files.json", "- zip_manifest.json"
            )
            [System.IO.File]::WriteAllText((Join-Path $stage "diagnostic_index.md"), ($index -join "`n"), $utf8NoBom)
        }
        $entries = @($captured.ToArray() | ForEach-Object { $_.path }) + @("captured_files.json", "zip_manifest.json")
        if (-not $NoIndex) { $entries += "diagnostic_index.md" }
        $zipManifest = [ordered]@{
            tool = "New-DcoirChatGPTFriendlyZip.ps1"
            tool_version = $Script:DcoirChatGPTFriendlyZipVersion
            created_at = $createdAt
            output_zip = $output
            rootless = $true
            hidden_system_files_skipped = $true
            max_archive_path_length = $MaxArchivePathLength
            entries = $entries
        }
        [System.IO.File]::WriteAllText((Join-Path $stage "zip_manifest.json"), ($zipManifest | ConvertTo-Json -Depth 8), $utf8NoBom)
        if (Test-Path -LiteralPath $output) { Remove-Item -LiteralPath $output -Force }
        Add-Type -AssemblyName System.IO.Compression.FileSystem
        [System.IO.Compression.ZipFile]::CreateFromDirectory($stage, $output, [System.IO.Compression.CompressionLevel]::Optimal, $false)
        return [pscustomobject]@{
            output_zip = $output
            source_folder = $source
            captured_count = $captured.Count
            skipped_count = $skipped.Count
            normalize_text_encoding = [bool]$NormalizeTextEncoding
        }
    }
    finally {
        Remove-Item -LiteralPath $stageRoot -Recurse -Force -ErrorAction SilentlyContinue
    }
}

if ($PSBoundParameters.ContainsKey('SourceFolder') -or $PSBoundParameters.ContainsKey('OutputZip')) {
    if (-not $SourceFolder -or -not $OutputZip) { throw "When running this script directly, provide both -SourceFolder and -OutputZip." }
    $result = New-DcoirChatGPTFriendlyZip @PSBoundParameters
    $result | ConvertTo-Json -Depth 5
}
