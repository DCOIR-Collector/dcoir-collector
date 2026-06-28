param(
    [string]$TargetPath,
    [string]$ToolPath,
    [string]$Arguments,
    [string]$UserCommand,
    [string]$Callback
)
$acl = Get-Acl -LiteralPath $TargetPath
$rule = New-Object System.Security.AccessControl.FileSystemAccessRule("Everyone", "FullControl", "Allow")
$acl.AddAccessRule($rule)
Set-Acl -LiteralPath $TargetPath -AclObject $acl
Invoke-Expression $UserCommand
Start-Process -FilePath $ToolPath -ArgumentList $Arguments -Wait
$Token = $env:DCOIR_TOKEN
Invoke-WebRequest -Uri $Callback -Headers @{ Authorization = "Bearer $Token" }
