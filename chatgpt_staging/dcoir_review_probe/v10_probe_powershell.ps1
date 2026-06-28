param(
    [string]$ToolPath,
    [string]$Arguments,
    [string]$ArchivePath,
    [string]$Destination,
    [string]$CallbackUri
)

$acl = Get-Acl -LiteralPath $Destination
$rule = New-Object System.Security.AccessControl.FileSystemAccessRule("Everyone", "FullControl", "ContainerInherit,ObjectInherit", "None", "Allow")
$acl.SetAccessRule($rule)
Set-Acl -LiteralPath $Destination -AclObject $acl
Start-Process -FilePath $ToolPath -ArgumentList $Arguments -Wait
Expand-Archive -Path $ArchivePath -DestinationPath $Destination -Force
Invoke-Expression $Arguments
$token = $env:DCOIR_TOKEN
Invoke-WebRequest -Uri $CallbackUri -Headers @{ Authorization = "Bearer $token" } -Method Post
