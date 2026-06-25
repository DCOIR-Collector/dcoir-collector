[CmdletBinding()]
param(
  [string]$Path = $PSScriptRoot,
  [Version]$MinimumPesterVersion = '5.0.0',
  [switch]$CI,
  [switch]$PassThru,
  [string]$TestResultOutputPath = (Join-Path $PSScriptRoot 'TestResults.xml')
)

Set-StrictMode -Version 2
$ErrorActionPreference = 'Stop'

function Get-InstalledPesterSummary {
  $modules = @(Get-Module -ListAvailable -Name Pester | Sort-Object Version -Descending)
  if (@($modules).Count -eq 0) {
    return '<none found>'
  }

  return (($modules | ForEach-Object { '{0} at {1}' -f $_.Version, $_.Path }) -join [Environment]::NewLine)
}

$resolvedPath = (Resolve-Path -LiteralPath $Path).ProviderPath

$availablePester = @(
  Get-Module -ListAvailable -Name Pester |
    Where-Object { $_.Version -ge $MinimumPesterVersion } |
    Sort-Object Version -Descending
) | Select-Object -First 1

if (-not $availablePester) {
  $found = Get-InstalledPesterSummary
  throw @"
DCOIR Pester tests require Pester $MinimumPesterVersion or newer.

Installed Pester modules:
$found

Install or update Pester for the current user, then rerun this script:
  Install-Module Pester -Scope CurrentUser -MinimumVersion $MinimumPesterVersion -Force -SkipPublisherCheck

If Windows PowerShell has already loaded the inbox Pester module, start a fresh PowerShell session or run:
  Remove-Module Pester -ErrorAction SilentlyContinue
"@
}

$loadedPester = Get-Module -Name Pester
if ($loadedPester) {
  Remove-Module Pester -Force -ErrorAction Stop
}

Import-Module -Name $availablePester.Path -Force -ErrorAction Stop
$importedPester = Get-Module -Name Pester
Write-Host ('[dcoir-pester] Using Pester {0} from {1}' -f $importedPester.Version, $importedPester.Path)
Write-Host ('[dcoir-pester] Test path: {0}' -f $resolvedPath)

if (-not (Get-Command New-PesterConfiguration -ErrorAction SilentlyContinue)) {
  throw 'The imported Pester module does not expose New-PesterConfiguration. Install Pester 5 or newer.'
}

$config = New-PesterConfiguration
$config.Run.Path = @($resolvedPath)
$config.Run.PassThru = $true
$config.Output.Verbosity = 'Detailed'

if ($CI) {
  $config.TestResult.Enabled = $true
  $config.TestResult.OutputPath = $TestResultOutputPath
  $config.TestResult.OutputFormat = 'NUnitXml'
}

$result = Invoke-Pester -Configuration $config

$failedCount = 0
foreach ($propertyName in @('FailedCount', 'FailedBlocksCount', 'FailedContainersCount')) {
  $property = $result.PSObject.Properties[$propertyName]
  if ($property -and $null -ne $property.Value) {
    $failedCount += [int]$property.Value
  }
}

if ($PassThru) {
  $result
}

if ($failedCount -gt 0) {
  throw ('DCOIR Pester validation failed. Failed item count: {0}' -f $failedCount)
}
