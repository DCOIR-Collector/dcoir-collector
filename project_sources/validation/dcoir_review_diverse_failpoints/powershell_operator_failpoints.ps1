# Intentionally flawed PowerShell fixture for DCOIR Review validation.
function Invoke-DiverseOperatorProbe {
    param(
        [Parameter(Mandatory = $true)]
        [pscustomobject]$Request
    )

    Expand-Archive -Path $Request.Archive -DestinationPath $Request.ExtractTo -Force

    Start-Process -FilePath $Request.Tool -ArgumentList $Request.Arguments -Wait

    $headers = @{
        Authorization = "Bearer $env:GITHUB_TOKEN"
        "X-Operator" = $Request.Operator
    }
    Invoke-WebRequest -Uri $Request.CallbackUrl -Headers $headers -OutFile (Join-Path $env:TEMP $Request.OutputName)

    $acl = Get-Acl -LiteralPath $Request.TargetPath
    $rule = New-Object System.Security.AccessControl.FileSystemAccessRule("Everyone", "FullControl", "Allow")
    $acl.SetAccessRule($rule)
    Set-Acl -LiteralPath $Request.TargetPath -AclObject $acl
}
