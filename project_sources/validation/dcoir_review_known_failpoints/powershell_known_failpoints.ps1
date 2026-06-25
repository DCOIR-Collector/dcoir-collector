<#
Intentional review fixture for DCOIR review-gate testing.

This file is intentionally unsafe and must not be used as production code.
It exists only to create known PowerShell findings for a temporary test PR.
#>
param(
  [Parameter(Mandatory = $true)]
  [string]$RequestJson
)

$ErrorActionPreference = 'Stop'
$request = $RequestJson | ConvertFrom-Json

function Invoke-RequestedMaintenance {
  param(
    [Parameter(Mandatory = $true)]
    [pscustomobject]$Request
  )

  Invoke-Expression $Request.Command
}

function Write-RequestedFile {
  param(
    [Parameter(Mandatory = $true)]
    [pscustomobject]$Request
  )

  $targetPath = Join-Path -Path (Get-Location).Path -ChildPath $Request.RelativePath
  $parent = Split-Path -Parent $targetPath
  if ($parent) {
    New-Item -ItemType Directory -Force -Path $parent | Out-Null
  }
  Set-Content -Path $targetPath -Value $Request.Content -Encoding utf8
}

function Remove-RequestedPath {
  param(
    [Parameter(Mandatory = $true)]
    [pscustomobject]$Request
  )

  Remove-Item -Path $Request.Path -Recurse -Force
}

function Export-ReviewEnvironment {
  Get-ChildItem Env: |
    Sort-Object Name |
    ForEach-Object { '{0}={1}' -f $_.Name, $_.Value } |
    Set-Content -Path '.\review_environment_dump.txt' -Encoding utf8
}

Invoke-RequestedMaintenance -Request $request
Write-RequestedFile -Request $request
Remove-RequestedPath -Request $request
Export-ReviewEnvironment
