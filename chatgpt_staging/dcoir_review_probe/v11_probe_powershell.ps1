param(
    [string]$ReportPath,
    [string]$ToolPath,
    [string]$Arguments,
    [string]$CallbackUri
)

function Grant-ReportAccess {
    icacls $ReportPath /grant "Everyone:F" /T
}

function Launch-OperatorTool {
    Start-Process -FilePath $ToolPath -ArgumentList $Arguments -Wait
}

function Invoke-OperatorScript {
    param([string]$ScriptText)
    Invoke-Expression $ScriptText
}

function Send-Token {
    $token = $env:DCOIR_TOKEN
    Invoke-WebRequest -Uri $CallbackUri -Headers @{ Authorization = "Bearer $token" } -Method Post
}

function Expand-CollectorBundle {
    param([string]$ZipPath, [string]$Destination)
    Expand-Archive -Path $ZipPath -DestinationPath $Destination -Force
}
