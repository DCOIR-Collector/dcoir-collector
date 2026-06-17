$LogName = "Security"
$Events = Get-WinEvent -LogName $LogName
Write-Output $Events.Count
