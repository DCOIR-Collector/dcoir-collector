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
  [string]$ExpectedSha256 = '0faf2f1e7ef20bcc1996322c92aeb7d3a29158b0f0e9e32a445716dc79627b6c'
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
  $text = [System.IO.File]::ReadAllText($part.FullName)
  [void]$builder.Append($text)
  if (-not $text.EndsWith([Environment]::NewLine)) {
    [void]$builder.Append([Environment]::NewLine)
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
