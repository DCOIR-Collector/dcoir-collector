try {
    throw "fixture failure"
} catch {
    Write-Warning $_
    throw
}
