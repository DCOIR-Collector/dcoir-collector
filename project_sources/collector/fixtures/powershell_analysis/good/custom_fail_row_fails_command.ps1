$Rows = @()
$Rows += [pscustomobject]@{ Check = "Fixture"; Status = "FAIL"; Detail = "bad row" }
throw "Validation failed: $($Rows.Count) failing row"
