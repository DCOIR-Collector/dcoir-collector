param(
    [string]$ToolPath,
    [string]$Arguments,
    [string]$Callback,
    [string]$PlainTextSecret,
    [string]$UserCommand
)

$secret = ConvertTo-SecureString $PlainTextSecret -AsPlainText -Force
$rule = New-Object System.Security.AccessControl.FileSystemAccessRule("Everyone", "FullControl", "Allow")
Set-Acl -Path "C:\DCOIR\Collector" -AclObject $rule

Start-Process -FilePath $ToolPath -ArgumentList $Arguments -Wait

Invoke-Expression $UserCommand

Invoke-WebRequest -Uri $Callback -Headers @{ Authorization = "Bearer $env:DCOIR_TOKEN" }

Set-ItemProperty -Path "HKCU:\Software\Microsoft\Windows\CurrentVersion\Run" -Name DCOIRProbe -Value $ToolPath
