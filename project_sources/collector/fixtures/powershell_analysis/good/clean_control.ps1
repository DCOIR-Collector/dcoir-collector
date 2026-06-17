function Invoke-DcoirFixtureCleanup {
    [CmdletBinding(SupportsShouldProcess)]
    param([string]$Root)
    $SafeRoot = (Resolve-Path -LiteralPath $Root).Path
    if ($PSCmdlet.ShouldProcess($SafeRoot, "Remove fixture output")) {
        Remove-Item -LiteralPath (Join-Path $SafeRoot "known-output.txt") -Force
    }
}

$Events = Get-WinEvent -FilterHashtable @{ LogName = "Security"; Id = 4688 } -MaxEvents 20
& robocopy.exe "source" "destination"
if ($LASTEXITCODE -gt 7) {
    throw "robocopy failed with $LASTEXITCODE"
}
try {
    Write-Output $Events.Count
} catch {
    throw
}
