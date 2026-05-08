$ErrorActionPreference = 'Stop'
$expected = '[REDACTED:DCOIR_AIRTABLE_BASE_ID]'
$configured = [Environment]::GetEnvironmentVariable('DCOIR_AIRTABLE_BASE_ID','Machine')
$downloads = [Environment]::GetEnvironmentVariable('DCOIR_DOWNLOADS_DIR','Machine')
if ([string]::IsNullOrWhiteSpace($downloads)) { throw 'Missing DCOIR_DOWNLOADS_DIR' }
$outDir = Join-Path $downloads 'airtable_base_id_compare_001'
New-Item -ItemType Directory -Force -Path $outDir | Out-Null
function Sha256Text([string]$s) { $sha=[System.Security.Cryptography.SHA256]::Create(); $bytes=[System.Text.Encoding]::UTF8.GetBytes($s); return ([BitConverter]::ToString($sha.ComputeHash($bytes))).Replace('-','').ToLowerInvariant() }
if ([string]::IsNullOrWhiteSpace($configured)) { throw 'Missing DCOIR_AIRTABLE_BASE_ID' }
$result = [ordered]@{ schema='dcoir.airtable_base_id_compare.v1'; generated_at_utc=(Get-Date).ToUniversalTime().ToString('s') + 'Z'; expected_base_sha256=(Sha256Text $expected); configured_base_sha256=(Sha256Text $configured); configured_matches_expected=($configured -eq $expected); configured_length=$configured.Length; expected_length=$expected.Length }
$result | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (Join-Path $outDir 'airtable_base_id_compare.json') -Encoding UTF8
Write-Host 'Airtable base-id compare complete'
Write-Host ("Configured matches expected: {0}" -f $result.configured_matches_expected)
Write-Host ("Configured length: {0}" -f $result.configured_length)
Write-Host ("Output directory: {0}" -f $outDir)
