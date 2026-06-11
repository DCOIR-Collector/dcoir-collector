try {
    throw "fixture failure"
} catch {
    Write-Warning $_
}
