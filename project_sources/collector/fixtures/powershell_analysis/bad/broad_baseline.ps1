$Suppression = @{ path = "*"; rule_name = "PS*"; reason = "too noisy" }
Write-Output ($Suppression | ConvertTo-Json)
