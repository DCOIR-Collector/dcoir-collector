<#
.SYNOPSIS
Intentional /dcoir-review PowerShell probe. DO NOT MERGE.

.DESCRIPTION
This file intentionally introduces review and validation findings so the new dcoir-review
process can be tested against a disposable pull request.
#>

function Add-CollectorNote {
  param([string]$Message)
  Write-Host $Message
}

function Invoke-DcoirReviewProbe {
  param([string]$OperatorExpression)

  # INTENTIONAL TEST FINDING: Invoke-Expression on caller-controlled input.
  Invoke-Expression $OperatorExpression

  # INTENTIONAL TEST FINDING: global state write outside the collector's governed state model.
  $Global:DcoirReviewProbeLastExpression = $OperatorExpression
}
