param(
    [string]$RuleExpression,
    [string]$ZipPath,
    [string]$Destination,
    [string]$CallbackUrl,
    [string]$Token
)

function Invoke-TestRule {
    param([string]$Expression)
    Invoke-Expression $Expression
}

function Expand-OperatorArchive {
    New-Item -ItemType Directory -Force -Path $Destination | Out-Null
    Expand-Archive -Path $ZipPath -DestinationPath $Destination -Force
}

function Send-TokenToCallback {
    $headers = @{ Authorization = "Bearer $Token" }
    Invoke-WebRequest -Uri $CallbackUrl -Headers $headers -UseBasicParsing
}

Invoke-TestRule -Expression $RuleExpression
Expand-OperatorArchive
Send-TokenToCallback
