$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'

$repo = [Environment]::GetEnvironmentVariable('DCOIR_REPO_ROOT','Machine')
$downloads = [Environment]::GetEnvironmentVariable('DCOIR_DOWNLOADS_DIR','Machine')
if ([string]::IsNullOrWhiteSpace($repo)) { throw 'Missing DCOIR_REPO_ROOT' }
if ([string]::IsNullOrWhiteSpace($downloads)) { throw 'Missing DCOIR_DOWNLOADS_DIR' }

$outDir = Join-Path $downloads 'dlt_airtable_to_supabase_001'
New-Item -ItemType Directory -Force -Path $outDir | Out-Null
$script = Join-Path $repo 'chatgpt_staging\scripts\run_dlt_airtable_to_supabase.py'
if (-not (Test-Path -LiteralPath $script -PathType Leaf)) { throw "Missing script: $script" }

python -m pip install --upgrade pip | Out-Host
python -m pip install "dlt[postgres]>=1.0" requests psycopg2-binary | Out-Host

$env:DCOIR_DLT_REPORT_PATH = Join-Path $outDir 'dlt_airtable_to_supabase_report.json'
$env:DCOIR_DLT_MD_PATH = Join-Path $outDir 'dlt_airtable_to_supabase_report.md'
$env:DCOIR_DLT_DATASET_NAME = 'airtable_import'

python $script
