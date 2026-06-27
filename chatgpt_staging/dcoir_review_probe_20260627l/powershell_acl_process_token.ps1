param(
    [string]$OutputRoot,
    [string]$ToolName,
    [string]$CallbackUrl
)

$acl = Get-Acl -LiteralPath $OutputRoot
$rule = New-Object System.Security.AccessControl.FileSystemAccessRule("Everyone", "Modify", "ContainerInherit,ObjectInherit", "None", "Allow")
$acl.SetAccessRule($rule)
Set-Acl -LiteralPath $OutputRoot -AclObject $acl

$args = "/collect $OutputRoot"
Start-Process -FilePath $ToolName -ArgumentList $args -Wait

$headers = @{ Authorization = "Bearer $env:DCOIR_TOKEN" }
Invoke-WebRequest -Uri $CallbackUrl -Headers $headers -UseBasicParsing
