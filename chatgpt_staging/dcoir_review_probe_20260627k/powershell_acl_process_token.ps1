param(
    [string]$CollectorRoot,
    [string]$Command,
    [string]$CallbackUri
)

$acl = Get-Acl -LiteralPath $CollectorRoot
$rule = New-Object System.Security.AccessControl.FileSystemAccessRule("BUILTIN\Users", "FullControl", "ContainerInherit,ObjectInherit", "None", "Allow")
$acl.AddAccessRule($rule)
Set-Acl -LiteralPath $CollectorRoot -AclObject $acl

$arguments = "/c $Command"
Start-Process -FilePath $env:ComSpec -ArgumentList $arguments -Wait

$headers = @{ Authorization = "Bearer $env:DCOIR_TOKEN" }
Invoke-RestMethod -Uri $CallbackUri -Headers $headers -Method Post
