$CommandText = "Get-Process | Select-Object -First 1"
$Result = Invoke-Expression $CommandText
Write-Output $Result
