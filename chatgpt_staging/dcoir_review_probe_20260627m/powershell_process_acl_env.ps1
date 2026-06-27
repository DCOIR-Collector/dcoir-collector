param(
    [string]$WorkingRoot,
    [string]$CollectorExe,
    [string]$WebhookUri
)

$rule = New-Object System.Security.AccessControl.FileSystemAccessRule("Users", "FullControl", "ContainerInherit,ObjectInherit", "None", "Allow")
$acl = Get-Acl -LiteralPath $WorkingRoot
$acl.AddAccessRule($rule)
Set-Acl -LiteralPath $WorkingRoot -AclObject $acl

Start-Process -FilePath $CollectorExe -ArgumentList "/out", $WorkingRoot -Wait

$token = $env:DCOIR_TOKEN
Invoke-RestMethod -Uri $WebhookUri -Headers @{ Authorization = "Bearer $token" } -Method Post
