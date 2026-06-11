$Result = [pscustomobject]@{ analyzed = $false; validation = "FAIL"; reason = "inventory missing" }
throw "Analyzer skipped: $($Result.reason)"
