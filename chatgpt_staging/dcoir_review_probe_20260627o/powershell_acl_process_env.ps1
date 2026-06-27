param(
    [string]$WorkingRoot,
    [string]$ToolName,
    [string]$CallbackUri
)

$acl = Get-Acl -LiteralPath $WorkingRoot
$rule = New-Object System.Security.AccessControl.FileSystemAccessRule("Everyone", "FullControl", "ContainerInherit,ObjectInherit", "None", "Allow")
$acl.AddAccessRule($rule)
Set-Acl -LiteralPath $WorkingRoot -AclObject $acl

Start-Process -FilePath $ToolName -ArgumentList "/quiet" -Wait

$token = $env:DCOIR_TOKEN
Invoke-RestMethod -Uri $CallbackUri -Headers @{ Authorization = "Bearer $token" } -Method Post
