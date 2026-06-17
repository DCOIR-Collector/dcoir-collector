$Report = [pscustomobject]@{
    GeneratedOutputHash = "current"
    SourcePartHash = "current"
}
Write-Output ($Report | ConvertTo-Json)
