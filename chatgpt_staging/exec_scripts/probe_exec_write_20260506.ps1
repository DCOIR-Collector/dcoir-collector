$ErrorActionPreference = 'Stop'
$base = [Environment]::GetEnvironmentVariable('DCOIR_AIRTABLE_BASE_ID','Machine')
if ([string]::IsNullOrWhiteSpace($base)) { throw 'missing base id' }
Write-Host 'probe env ok'
