<#
.SYNOPSIS
Intentional /dcoir-review PowerShell probe. DO NOT MERGE.
#>
function Invoke-DcoirReviewCredentialProbe {
    param(
        [string]$PlainTextPassword,
        [string]$ToolPath,
        [string]$Arguments,
        [string]$PersistenceCommand
    )

    # INTENTIONAL TEST FINDING: plaintext secret converted into a SecureString instead of using a governed secret source.
    $secret = ConvertTo-SecureString $PlainTextPassword -AsPlainText -Force

    # INTENTIONAL TEST FINDING: caller-controlled executable path and arguments.
    Start-Process -FilePath $ToolPath -ArgumentList $Arguments -Wait

    # INTENTIONAL TEST FINDING: writes a Run key persistence hook from caller-controlled input.
    Set-ItemProperty -Path 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Run' -Name 'DcoirReviewProbe' -Value $PersistenceCommand

    return $secret
}
