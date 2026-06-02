<#
.SYNOPSIS
Assembles the DCOIR collector harness from checked-in source parts.

.DESCRIPTION
Concatenates the ordered harness source parts into a generated run_DCOIR_Tests script.
This keeps the harness reviewable in smaller chunks while preserving the existing
script invocation contract for validation workflows and direct operator runs.
#>

param(
  [string]$PartsDirectory = (Join-Path $PSScriptRoot 'source\parts'),
  [string]$OutputPath = (Join-Path $PSScriptRoot 'run_DCOIR_Tests.generated.ps1'),
  [string]$ExpectedSha256 = '5176bff51c73877bbb287467cbcf92d15b7ae63301319baf3161f3f1fb858988'
)

Set-StrictMode -Version 2
$ErrorActionPreference = 'Stop'

if (-not (Test-Path -LiteralPath $PartsDirectory)) {
  throw "Harness parts directory not found: $PartsDirectory"
}

$parts = @(Get-ChildItem -LiteralPath $PartsDirectory -File -Filter 'run_DCOIR_Tests.part-*.ps1.txt' | Sort-Object Name)
if (@($parts).Count -eq 0) {
  throw "No harness parts found under: $PartsDirectory"
}

$outputDirectory = Split-Path -Parent $OutputPath
if (-not (Test-Path -LiteralPath $outputDirectory)) {
  New-Item -Path $outputDirectory -ItemType Directory -Force | Out-Null
}

$writer = New-Object System.Text.UTF8Encoding($false)
$builder = New-Object System.Text.StringBuilder
foreach ($part in $parts) {
  $text = [System.IO.File]::ReadAllText($part.FullName) -replace "`r`n", "`n" -replace "`r", "`n"
  [void]$builder.Append($text)
  if (-not $text.EndsWith("`n")) {
    [void]$builder.Append("`n")
  }
}

[System.IO.File]::WriteAllText($OutputPath, $builder.ToString(), $writer)

if (-not [string]::IsNullOrWhiteSpace($ExpectedSha256)) {
  $actualSha256 = (Get-FileHash -LiteralPath $OutputPath -Algorithm SHA256).Hash.ToLowerInvariant()
  if ($actualSha256 -ne $ExpectedSha256.ToLowerInvariant()) {
    throw "Generated harness SHA256 mismatch. Expected $ExpectedSha256 but got $actualSha256"
  }
}

Write-Host ("ASSEMBLED_HARNESS_PATH={0}" -f (Resolve-Path -LiteralPath $OutputPath).Path)
Write-Host ("ASSEMBLED_HARNESS_PARTS={0}" -f @($parts).Count)
