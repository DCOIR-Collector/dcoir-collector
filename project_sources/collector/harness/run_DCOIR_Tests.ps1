<#
.SYNOPSIS
DCOIR collector harness entrypoint.

.DESCRIPTION
Assembles the chunked harness source into a generated script and invokes it with the
original arguments. The generated script preserves the historical run_DCOIR_Tests.ps1
CLI contract while keeping source review and connector access bounded to smaller parts.
#>

Set-StrictMode -Version 2
$ErrorActionPreference = 'Stop'

$assembler = Join-Path $PSScriptRoot 'assemble_run_DCOIR_Tests.ps1'
$generated = Join-Path $PSScriptRoot 'run_DCOIR_Tests.generated.ps1'

if (-not (Test-Path -LiteralPath $assembler)) {
  throw "Harness assembler not found: $assembler"
}

& $assembler -OutputPath $generated
if (-not $?) {
  exit 1
}

& $generated @args
if (-not $?) {
  exit 1
}

exit 0
