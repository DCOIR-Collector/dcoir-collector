function Remove-DcoirFixtureOutput {
    param([string]$Path)
    Remove-Item -Path $Path -Recurse -Force
}
