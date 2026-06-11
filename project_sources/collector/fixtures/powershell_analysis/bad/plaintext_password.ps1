function Invoke-DcoirPlaintextPasswordFixture {
    param([string]$Password = "HardCodedFixturePassword!")
    Write-Output $Password.Length
}
