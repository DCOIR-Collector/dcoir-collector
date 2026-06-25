[CmdletBinding()]
param(
  [Version]$MinimumPesterVersion = '5.0.0'
)

Set-StrictMode -Version 2
$ErrorActionPreference = 'Stop'

Write-Host ('[dcoir-pester] Installing/updating Pester {0}+ for CurrentUser' -f $MinimumPesterVersion)
Install-Module Pester -Scope CurrentUser -MinimumVersion $MinimumPesterVersion -Force -SkipPublisherCheck

Remove-Module Pester -Force -ErrorAction SilentlyContinue
Import-Module Pester -MinimumVersion $MinimumPesterVersion -Force -ErrorAction Stop

Get-Module Pester | Select-Object Name, Version, Path | Format-List
