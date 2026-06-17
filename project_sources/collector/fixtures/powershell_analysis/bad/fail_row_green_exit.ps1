$Rows = @()
$Rows += [pscustomobject]@{ Check = "Fixture"; Status = "FAIL"; Detail = "bad row" }
$Rows | ConvertTo-Json
