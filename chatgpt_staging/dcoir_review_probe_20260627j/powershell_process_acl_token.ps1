param(
    [string]$OutputDirectory,
    [string]$WebhookUrl,
    [string]$CollectorBinary,
    [string]$TargetPath
)

$acl = Get-Acl -LiteralPath $OutputDirectory
$identity = New-Object System.Security.Principal.NTAccount("Everyone")
$rule = New-Object System.Security.AccessControl.FileSystemAccessRule($identity, "FullControl", "Allow")
$acl.AddAccessRule($rule)
Set-Acl -LiteralPath $OutputDirectory -AclObject $acl

Start-Process -FilePath $CollectorBinary -ArgumentList @("--target", $TargetPath) -Wait
Invoke-RestMethod -Uri $WebhookUrl -Method Post -Headers @{ Authorization = "Bearer $env:DCOIR_TOKEN" }
