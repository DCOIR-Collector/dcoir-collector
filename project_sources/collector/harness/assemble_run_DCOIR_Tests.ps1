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
  [string]$ExpectedSha256 = '154d9adca38cccbe8ab089bfee4d4421eb0e2107a977f600360b7a94fc17ecf7',
  [string]$ExpectedHarnessPath = (Join-Path $PSScriptRoot 'run_DCOIR_Tests.ps1')
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
$partDiagnostics = New-Object System.Collections.ArrayList
foreach ($part in $parts) {
  $text = [System.IO.File]::ReadAllText($part.FullName) -replace "`r`n", "`n" -replace "`r", "`n"
  [void]$builder.Append($text)
  if (-not $text.EndsWith("`n")) {
    [void]$builder.Append("`n")
  }
  $partHash = (Get-FileHash -LiteralPath $part.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
  [void]$partDiagnostics.Add(("{0} sha256={1} bytes={2}" -f $part.Name, $partHash, (Get-Item -LiteralPath $part.FullName).Length))
}

[System.IO.File]::WriteAllText($OutputPath, $builder.ToString(), $writer)

$actualSha256 = (Get-FileHash -LiteralPath $OutputPath -Algorithm SHA256).Hash.ToLowerInvariant()
if (-not [string]::IsNullOrWhiteSpace($ExpectedSha256)) {
  if ($actualSha256 -ne $ExpectedSha256.ToLowerInvariant()) {
    $diagnosticText = ($partDiagnostics -join [Environment]::NewLine)
    throw ("Generated harness SHA256 mismatch. Expected {0} but got {1}. Parts used, in order:{2}{3}" -f $ExpectedSha256, $actualSha256, [Environment]::NewLine, $diagnosticText)
  }
}

if (-not [string]::IsNullOrWhiteSpace($ExpectedHarnessPath)) {
  if (-not (Test-Path -LiteralPath $ExpectedHarnessPath)) {
    throw "Expected checked-in harness not found: $ExpectedHarnessPath"
  }
  $expectedHarnessSha256 = (Get-FileHash -LiteralPath $ExpectedHarnessPath -Algorithm SHA256).Hash.ToLowerInvariant()
  if ($actualSha256 -ne $expectedHarnessSha256) {
    $diagnosticText = ($partDiagnostics -join [Environment]::NewLine)
    throw ("Checked-in harness mismatch. Generated {0} has SHA256 {1}, but checked-in harness {2} has SHA256 {3}. Parts used, in order:{4}{5}" -f $OutputPath, $actualSha256, $ExpectedHarnessPath, $expectedHarnessSha256, [Environment]::NewLine, $diagnosticText)
  }
  Write-Host ("CHECKED_IN_HARNESS_PATH={0}" -f (Resolve-Path -LiteralPath $ExpectedHarnessPath).Path)
  Write-Host ("CHECKED_IN_HARNESS_SHA256={0}" -f $expectedHarnessSha256)
}

Write-Host ("ASSEMBLED_HARNESS_PATH={0}" -f (Resolve-Path -LiteralPath $OutputPath).Path)
Write-Host ("ASSEMBLED_HARNESS_SHA256={0}" -f $actualSha256)
Write-Host ("ASSEMBLED_HARNESS_PARTS={0}" -f @($parts).Count)
