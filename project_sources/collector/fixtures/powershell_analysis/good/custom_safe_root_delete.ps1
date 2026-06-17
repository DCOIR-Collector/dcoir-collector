$OutputRoot = Resolve-Path -LiteralPath (Join-Path $env:TEMP "dcoir-fixture")
$Target = Join-Path $OutputRoot "scratch"
if (-not $Target.StartsWith($OutputRoot.Path, [System.StringComparison]::OrdinalIgnoreCase)) {
    throw "Cleanup target escaped controlled root"
}
Remove-Item -LiteralPath $Target -Recurse -Force
