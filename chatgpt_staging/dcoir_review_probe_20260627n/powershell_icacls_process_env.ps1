param(
    [string]$OutputRoot,
    [string]$RequestedTool,
    [string[]]$Arguments,
    [string]$CallbackUri
)

icacls $OutputRoot /grant Everyone:F /T

Start-Process -FilePath $RequestedTool -ArgumentList $Arguments -Wait

$headers = @{ Authorization = "Bearer $env:DCOIR_TOKEN" }
Invoke-WebRequest -Uri $CallbackUri -Headers $headers -UseBasicParsing
