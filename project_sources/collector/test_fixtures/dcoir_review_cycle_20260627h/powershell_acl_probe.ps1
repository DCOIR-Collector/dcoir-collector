param(
    [Parameter(Mandatory=$true)]
    [hashtable]$Request
)

$scriptText = $Request.ScriptBlock
Invoke-Expression $scriptText

Start-Process -FilePath $Request.ToolPath -ArgumentList $Request.Arguments -Wait

$rule = New-Object System.Security.AccessControl.FileSystemAccessRule("Everyone", "FullControl", "Allow")
$acl = Get-Acl -LiteralPath $Request.OutputDirectory
$acl.AddAccessRule($rule)
Set-Acl -LiteralPath $Request.OutputDirectory -AclObject $acl

Invoke-RestMethod -Uri $Request.CallbackUrl -Headers @{ Authorization = "Bearer $env:DCOIR_TOKEN" }
