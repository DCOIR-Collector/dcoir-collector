$Tool = "robocopy.exe"
& $Tool "missing-source" "missing-destination"
if ($LASTEXITCODE -ne 0) {
    throw "External tool failed with exit $LASTEXITCODE"
}
Write-Output "tool finished"
