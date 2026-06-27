<#
.SYNOPSIS
Intentional /dcoir-review PowerShell runtime probe. DO NOT MERGE.
#>
function Invoke-DcoirReviewRuntimeProbe {
    param(
        [string]$PlainTextPassword,
        [string]$PersistenceCommand,
        [string]$ToolPath,
        [string[]]$Arguments
    )

    # PS-1 INTENTIONAL TEST FINDING: plaintext password becomes a SecureString without protected input handling.
    $securePassword = ConvertTo-SecureString $PlainTextPassword -AsPlainText -Force

    # PS-2 INTENTIONAL TEST FINDING: operator-controlled executable path and arguments launch directly.
    Start-Process -FilePath $ToolPath -ArgumentList $Arguments -Wait

    # PS-3 INTENTIONAL TEST FINDING: caller-controlled command is written into a Windows Run key.
    Set-ItemProperty -Path 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Run' -Name 'DcoirRuntimeProbe' -Value $PersistenceCommand

    return $securePassword
}
