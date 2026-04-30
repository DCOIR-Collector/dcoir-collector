[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$ManifestJson,
    [Parameter(Mandatory = $true)]
    [string]$PayloadRoot,
    [string]$RepoRoot = $env:DCOIR_REPO_ROOT,
    [string]$OutputDir = $env:DCOIR_DOWNLOADS_DIR,
    [string]$Remote = "origin",
    [string]$Branch = "main",
    [switch]$SkipFetch,
    [switch]$AllowDirtyTree,
    [switch]$WhatIfOnly
)

$ErrorActionPreference = "Stop"
$ToolVersion = "2026-05-01.2"

if (-not $RepoRoot) { throw "DCOIR_REPO_ROOT is not set. Set it to your local dcoir-collector repo root or pass -RepoRoot." }
if (-not (Test-Path -LiteralPath $RepoRoot -PathType Container)) { throw "Repo root not found: $RepoRoot" }
if (-not (Test-Path -LiteralPath $ManifestJson -PathType Leaf)) { throw "Manifest not found: $ManifestJson" }
if (-not (Test-Path -LiteralPath $PayloadRoot -PathType Container)) { throw "Payload root not found: $PayloadRoot" }
if (-not $OutputDir) { $OutputDir = Join-Path $env:USERPROFILE "Downloads" }
if (-not (Test-Path -LiteralPath $OutputDir -PathType Container)) { New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null }

$RepoRoot = (Resolve-Path -LiteralPath $RepoRoot).Path
$PayloadRoot = (Resolve-Path -LiteralPath $PayloadRoot).Path
$OutputDir = (Resolve-Path -LiteralPath $OutputDir).Path
$ManifestJson = (Resolve-Path -LiteralPath $ManifestJson).Path
$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$logPath = Join-Path $OutputDir "dcoir_repo_patch_apply_$stamp.log.txt"
$resultPath = Join-Path $OutputDir "dcoir_repo_patch_apply_$stamp.result.json"

$AppliedCopies = New-Object System.Collections.Generic.List[object]
$AppliedDeletes = New-Object System.Collections.Generic.List[object]
$Warnings = New-Object System.Collections.Generic.List[string]

function Write-Log {
    param([AllowEmptyString()][string]$Text)
    Write-Host $Text
    $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::AppendAllText($logPath, ($Text + [Environment]::NewLine), $utf8NoBom)
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

function Test-RelativePathSafe {
    param([string]$RelativePath)
    if ([string]::IsNullOrWhiteSpace($RelativePath)) { return $false }
    if ($RelativePath -match '^[A-Za-z]:') { return $false }
    if ($RelativePath.StartsWith('\\')) { return $false }
    if ($RelativePath.StartsWith('/')) { return $false }
    if ($RelativePath -match '(^|[\\/])\.\.([\\/]|$)') { return $false }
    return $true
}

function Normalize-RelativePath {
    param([string]$RelativePath)
    if (-not (Test-RelativePathSafe -RelativePath $RelativePath)) { throw "Unsafe relative path: $RelativePath" }
    return ($RelativePath -replace '\\', '/').TrimStart('/')
}

function Resolve-UnderRoot {
    param(
        [string]$Root,
        [string]$RelativePath
    )
    $rel = Normalize-RelativePath -RelativePath $RelativePath
    $candidate = Join-Path $Root ($rel -replace '/', [System.IO.Path]::DirectorySeparatorChar)
    $rootFull = [System.IO.Path]::GetFullPath($Root).TrimEnd([System.IO.Path]::DirectorySeparatorChar, [System.IO.Path]::AltDirectorySeparatorChar) + [System.IO.Path]::DirectorySeparatorChar
    $candidateFull = [System.IO.Path]::GetFullPath($candidate)
    if (-not $candidateFull.StartsWith($rootFull, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Path escapes root: $RelativePath"
    }
    return $candidateFull
}

function Get-FileSha256 {
    param([string]$Path)
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) { return $null }
    $sha = Get-FileHash -Algorithm SHA256 -LiteralPath $Path
    return $sha.Hash.ToLowerInvariant()
}

function Test-AllowedTargetRoot {
    param(
        [string]$RelativePath,
        [object[]]$AllowedRoots
    )
    if (-not $AllowedRoots -or $AllowedRoots.Count -eq 0) { throw "Manifest must define allowed_target_roots." }
    $rel = (Normalize-RelativePath -RelativePath $RelativePath).ToLowerInvariant()
    foreach ($root in $AllowedRoots) {
        if (-not $root) { continue }
        $r = (Normalize-RelativePath -RelativePath ([string]$root)).ToLowerInvariant().TrimEnd('/')
        if ($rel -eq $r -or $rel.StartsWith($r + '/')) { return $true }
    }
    return $false
}

function Find-PayloadBase {
    param(
        [string]$BaseRoot,
        [object[]]$CopyMap,
        [string]$Policy
    )
    $policyValue = "auto"
    if ($Policy) { $policyValue = ([string]$Policy).ToLowerInvariant() }
    if ($policyValue -eq "none") { return $BaseRoot }
    if ($policyValue -ne "auto" -and $policyValue -ne "single-child") { throw "Unsupported payload_root_policy: $Policy" }

    $roots = New-Object System.Collections.Generic.List[string]
    $roots.Add($BaseRoot) | Out-Null
    $children = @(Get-ChildItem -LiteralPath $BaseRoot -Directory -Force -ErrorAction SilentlyContinue)
    if ($children.Count -eq 1) { $roots.Add($children[0].FullName) | Out-Null }

    foreach ($root in $roots) {
        $allFound = $true
        foreach ($item in $CopyMap) {
            $sourcePath = [string]$item.source
            if (-not $sourcePath) { continue }
            $candidate = Resolve-UnderRoot -Root $root -RelativePath $sourcePath
            if (-not (Test-Path -LiteralPath $candidate -PathType Leaf)) { $allFound = $false; break }
        }
        if ($allFound) { return $root }
    }

    if ($policyValue -eq "single-child" -and $children.Count -eq 1) { return $children[0].FullName }
    return $BaseRoot
}

function Write-ResultJson {
    param([string]$Status, [string]$Message)
    $result = [ordered]@{
        tool = "Invoke-DcoirRepoPatchApply.ps1"
        tool_version = $ToolVersion
        status = $Status
        message = $Message
        created_at = (Get-Date -Format o)
        manifest = $ManifestJson
        payload_root = $PayloadRoot
        repo_root = $RepoRoot
        log_path = $logPath
        copied = @($AppliedCopies.ToArray())
        deleted = @($AppliedDeletes.ToArray())
        warnings = @($Warnings.ToArray())
        what_if_only = [bool]$WhatIfOnly
    }
    $result | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $resultPath -Encoding UTF8
}

try {
    foreach ($path in @($logPath, $resultPath)) { if (Test-Path -LiteralPath $path) { Remove-Item -LiteralPath $path -Force } }
    Write-Log "DCOIR Repo Patch Apply"
    Write-Log "Version: $ToolVersion"
    Write-Log "Timestamp: $(Get-Date -Format o)"
    Write-Log "RepoRoot: $RepoRoot"
    Write-Log "PayloadRoot: $PayloadRoot"
    Write-Log "Manifest: $ManifestJson"
    Write-Log "WhatIfOnly: $([bool]$WhatIfOnly)"

    $manifest = Get-Content -Raw -LiteralPath $ManifestJson | ConvertFrom-Json
    if (-not $manifest.allowed_target_roots) { throw "Manifest requires allowed_target_roots." }
    if (-not $manifest.copy_map -and -not $manifest.delete_paths) { throw "Manifest requires copy_map or delete_paths." }

    Write-Log ""
    Write-Log "== BRANCH CHECK =="
    $branchOutput = @(Invoke-GitLogged @('branch', '--show-current'))
    $currentBranch = ($branchOutput | Select-Object -Last 1).Trim()
    $expectedBranch = $Branch
    if ($manifest.expected_branch) { $expectedBranch = [string]$manifest.expected_branch }
    Write-Log "Current branch: $currentBranch"
    Write-Log "Expected branch: $expectedBranch"
    if ($currentBranch -ne $expectedBranch) { throw "Expected branch '$expectedBranch' but found '$currentBranch'." }

    if (-not $SkipFetch) {
        Write-Log ""
        Write-Log "== FETCH AND FAST-FORWARD CHECK =="
        Invoke-GitLogged @('fetch', $Remote, '--prune') | Out-Null
        $behindAhead = @(Invoke-GitLogged @('rev-list', '--left-right', '--count', "HEAD...$Remote/$expectedBranch"))
        $counts = ($behindAhead | Select-Object -Last 1).Trim() -split '\s+'
        if ($counts.Count -ge 2) {
            $behind = [int]$counts[1]
            if ($behind -gt 0) { throw "Local branch is behind $Remote/$expectedBranch. Pull with the safe pre-pull tool before applying." }
        }
    }

    Write-Log ""
    Write-Log "== DIRTY TREE CHECK =="
    $dirty = @(Invoke-GitLogged @('status', '--porcelain'))
    if ($dirty.Count -gt 0) {
        foreach ($line in $dirty) { Write-Log "DIRTY: $line" }
        $manifestAllowsDirty = $false
        if ($manifest.allow_dirty_tree) { $manifestAllowsDirty = [bool]$manifest.allow_dirty_tree }
        if (-not $AllowDirtyTree -and -not $manifestAllowsDirty) {
            throw "Working tree is not clean. Commit, stash, or rerun with an explicit dirty-tree allowance only if the dirty paths are expected."
        }
        $Warnings.Add("dirty_tree_allowed") | Out-Null
    } else { Write-Log "Working tree appears clean." }

    Write-Log ""
    Write-Log "== PRECHECK HASHES =="
    if ($manifest.precheck_existing_hashes) {
        foreach ($check in $manifest.precheck_existing_hashes) {
            $path = Normalize-RelativePath -RelativePath ([string]$check.path)
            if (-not (Test-AllowedTargetRoot -RelativePath $path -AllowedRoots $manifest.allowed_target_roots)) { throw "Precheck path outside allowed roots: $path" }
            $repoFile = Resolve-UnderRoot -Root $RepoRoot -RelativePath $path
            $actual = Get-FileSha256 -Path $repoFile
            $allowMissing = $false
            if ($check.allow_missing) { $allowMissing = [bool]$check.allow_missing }
            if (-not $actual) {
                if ($allowMissing) { Write-Log "PRECHECK MISSING ALLOWED: $path"; continue }
                throw "Precheck file missing: $path"
            }
            if ($check.sha256) {
                $expected = ([string]$check.sha256).ToLowerInvariant()
                Write-Log "PRECHECK: $path $actual"
                if ($actual -ne $expected) { throw "Precheck hash mismatch for $path. Expected $expected actual $actual" }
            } else {
                Write-Log "PRECHECK OBSERVED: $path $actual"
            }
        }
    } else { Write-Log "No precheck hashes declared." }

    $copyMap = @()
    if ($manifest.copy_map) { $copyMap = @($manifest.copy_map) }
    $payloadPolicy = "auto"
    if ($manifest.payload_root_policy) { $payloadPolicy = [string]$manifest.payload_root_policy }
    $payloadBase = Find-PayloadBase -BaseRoot $PayloadRoot -CopyMap $copyMap -Policy $payloadPolicy
    Write-Log ""
    Write-Log "== PAYLOAD BASE =="
    Write-Log $payloadBase

    Write-Log ""
    Write-Log "== APPLY COPY MAP =="
    foreach ($item in $copyMap) {
        $sourceRel = Normalize-RelativePath -RelativePath ([string]$item.source)
        $targetRel = Normalize-RelativePath -RelativePath ([string]$item.target)
        if (-not (Test-AllowedTargetRoot -RelativePath $targetRel -AllowedRoots $manifest.allowed_target_roots)) { throw "Target path outside allowed roots: $targetRel" }
        $sourcePath = Resolve-UnderRoot -Root $payloadBase -RelativePath $sourceRel
        if (-not (Test-Path -LiteralPath $sourcePath -PathType Leaf)) { throw "Payload source missing: $sourceRel" }
        $targetPath = Resolve-UnderRoot -Root $RepoRoot -RelativePath $targetRel
        $targetParent = Split-Path -Parent $targetPath
        $sourceHash = Get-FileSha256 -Path $sourcePath
        $existingHash = Get-FileSha256 -Path $targetPath
        Write-Log "COPY: $sourceRel -> $targetRel"
        Write-Log "SOURCE_SHA256: $sourceHash"
        if ($existingHash) { Write-Log "EXISTING_SHA256: $existingHash" } else { Write-Log "EXISTING: missing" }
        if (-not $WhatIfOnly) {
            if ($targetParent) { New-Item -ItemType Directory -Force -Path $targetParent | Out-Null }
            Copy-Item -LiteralPath $sourcePath -Destination $targetPath -Force
        }
        $newHash = if ($WhatIfOnly) { $existingHash } else { Get-FileSha256 -Path $targetPath }
        $AppliedCopies.Add([pscustomobject]@{ source = $sourceRel; target = $targetRel; source_sha256 = $sourceHash; previous_sha256 = $existingHash; new_sha256 = $newHash }) | Out-Null
    }

    Write-Log ""
    Write-Log "== APPLY DELETE PATHS =="
    if ($manifest.delete_paths) {
        foreach ($deletePathValue in $manifest.delete_paths) {
            $deleteRel = Normalize-RelativePath -RelativePath ([string]$deletePathValue)
            if (-not (Test-AllowedTargetRoot -RelativePath $deleteRel -AllowedRoots $manifest.allowed_target_roots)) { throw "Delete path outside allowed roots: $deleteRel" }
            $deleteFull = Resolve-UnderRoot -Root $RepoRoot -RelativePath $deleteRel
            $existed = Test-Path -LiteralPath $deleteFull
            Write-Log "DELETE: $deleteRel existed=$existed"
            if ($existed -and -not $WhatIfOnly) {
                Invoke-GitLogged @('rm', '-r', '--', $deleteRel) | Out-Null
            }
            $AppliedDeletes.Add([pscustomobject]@{ path = $deleteRel; existed = [bool]$existed }) | Out-Null
        }
    } else { Write-Log "No delete paths declared." }

    Write-Log ""
    Write-Log "== POSTCHECK REQUIRED PATHS =="
    if ($manifest.postcheck_required_paths) {
        foreach ($requiredPathValue in $manifest.postcheck_required_paths) {
            $requiredRel = Normalize-RelativePath -RelativePath ([string]$requiredPathValue)
            if (-not (Test-AllowedTargetRoot -RelativePath $requiredRel -AllowedRoots $manifest.allowed_target_roots)) { throw "Postcheck path outside allowed roots: $requiredRel" }
            $requiredFull = Resolve-UnderRoot -Root $RepoRoot -RelativePath $requiredRel
            if (-not $WhatIfOnly -and -not (Test-Path -LiteralPath $requiredFull)) { throw "Postcheck required path missing: $requiredRel" }
            Write-Log "POSTCHECK EXISTS: $requiredRel"
        }
    } else { Write-Log "No postcheck required paths declared." }

    Write-Log ""
    Write-Log "== POSTCHECK HASHES =="
    if ($manifest.postcheck_hashes) {
        foreach ($check in $manifest.postcheck_hashes) {
            $path = Normalize-RelativePath -RelativePath ([string]$check.path)
            if (-not (Test-AllowedTargetRoot -RelativePath $path -AllowedRoots $manifest.allowed_target_roots)) { throw "Postcheck hash path outside allowed roots: $path" }
            $repoFile = Resolve-UnderRoot -Root $RepoRoot -RelativePath $path
            if (-not $WhatIfOnly) {
                $actual = Get-FileSha256 -Path $repoFile
                if (-not $actual) { throw "Postcheck hash file missing: $path" }
                if ($check.sha256) {
                    $expected = ([string]$check.sha256).ToLowerInvariant()
                    if ($actual -ne $expected) { throw "Postcheck hash mismatch for $path. Expected $expected actual $actual" }
                }
                Write-Log "POSTCHECK HASH: $path $actual"
            } else { Write-Log "POSTCHECK HASH SKIPPED IN WHATIF: $path" }
        }
    } else { Write-Log "No postcheck hashes declared." }

    Write-Log ""
    Write-Log "== FINAL GIT STATUS =="
    $finalStatus = @(Invoke-GitLogged @('status', '--short'))
    foreach ($line in $finalStatus) { Write-Log "STATUS: $line" }
    Write-ResultJson -Status "success" -Message "Apply completed. Review changes in GitHub Desktop before commit."
    Write-Log ""
    Write-Log "RESULT_JSON: $resultPath"
    Write-Host "Patch/apply completed. Review in GitHub Desktop before commit."
    Write-Host "Log: $logPath"
    Write-Host "Result JSON: $resultPath"
}
catch {
    Write-Log ""
    Write-Log "== Apply failed =="
    Write-Log $_.Exception.Message
    Write-ResultJson -Status "failure" -Message $_.Exception.Message
    Write-Host "Patch/apply failed. Upload the log and result JSON."
    Write-Host "Log: $logPath"
    Write-Host "Result JSON: $resultPath"
    throw
}
