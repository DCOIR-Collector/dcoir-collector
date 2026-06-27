<#
.SYNOPSIS
Intentional /dcoir-review PowerShell probe. DO NOT MERGE.
#>
function Invoke-DcoirReviewExecutionProbe {
    param(
        [string]$OperatorScript,
        [string]$DownloadUrl,
        [string]$OutputPath
    )

    # PS-1 INTENTIONAL TEST FINDING: caller-controlled script text reaches Invoke-Expression.
    Invoke-Expression $OperatorScript

    # PS-2 INTENTIONAL TEST FINDING: remote script content is executed without signature or allowlist validation.
    Invoke-WebRequest -Uri $DownloadUrl -UseBasicParsing | Invoke-Expression

    # PS-3 INTENTIONAL TEST FINDING: caller-controlled path reaches a file write without allowlist/root containment.
    Set-Content -LiteralPath $OutputPath -Value $OperatorScript -Encoding UTF8
}
