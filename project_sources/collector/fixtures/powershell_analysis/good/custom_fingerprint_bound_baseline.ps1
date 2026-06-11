$Suppression = @{
    path = "project_sources/collector/source/DCOIR_Collector.ps1"
    rule_name = "PSAvoidUsingWriteHost"
    fingerprint = "0123456789abcdef"
    expected_match_count = 1
    reason = "Fixture proves exact suppression shape."
}
Write-Output ($Suppression | ConvertTo-Json)
