$AnalyzerResult = @{ analyzed = $false; skipped_reason = "missing policy"; validation = "success" }
Write-Output ($AnalyzerResult | ConvertTo-Json)
