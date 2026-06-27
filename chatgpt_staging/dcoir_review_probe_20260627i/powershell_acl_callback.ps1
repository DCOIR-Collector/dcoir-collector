param(
    [string]$OutputDirectory,
    [string]$CallbackUrl,
    [string]$ToolPath
)

$acl = Get-Acl -LiteralPath $OutputDirectory
$rule = New-Object System.Security.AccessControl.FileSystemAccessRule("Everyone", "FullControl", "ContainerInherit,ObjectInherit", "None", "Allow")
$acl.SetAccessRule($rule)
Set-Acl -LiteralPath $OutputDirectory -AclObject $acl

Start-Process -FilePath $ToolPath -ArgumentList "/collect $OutputDirectory" -Wait
Invoke-WebRequest -Uri $CallbackUrl -Method Post -Headers @{ Authorization = "Bearer $env:DCOIR_TOKEN" }
