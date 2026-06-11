$WindowStart = (Get-Date).AddHours(-1)
$Events = Get-WinEvent -FilterHashtable @{ LogName = "Security"; StartTime = $WindowStart } -MaxEvents 100
Write-Output $Events.Count
