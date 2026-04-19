$ErrorActionPreference = 'Stop'

$ZipPath    = 'C:\Users\batch_lrjfue\Downloads\dcoir_manual_test_framework_bundle_v8_full.zip'
$InstallDir = 'C:\DCOIR_TESTER'
$OutputDir  = Join-Path $InstallDir '_test_output'
$StageDir   = Join-Path $env:TEMP ('DCOIR_STAGE_' + [guid]::NewGuid().ToString('N'))

Write-Host ''
Write-Host '=== DCOIR_TESTER framework install + launch ===' -ForegroundColor Cyan

if (-not (Test-Path -LiteralPath $ZipPath)) {
    Write-Host "Zip not found: $ZipPath" -ForegroundColor Red
    exit 1
}

New-Item -ItemType Directory -Path $InstallDir -Force | Out-Null
New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null
New-Item -ItemType Directory -Path $StageDir -Force | Out-Null

try {
    Write-Host 'Extracting downloaded bundle...' -ForegroundColor Cyan
    Expand-Archive -LiteralPath $ZipPath -DestinationPath $StageDir -Force

    Write-Host 'Removing previous framework app files...' -ForegroundColor Cyan
    $OldFrameworkItems = @(
        'run_dcoir_manual_tests.ps1',
        'dcoir_manual_test_runner.py',
        'dcoir_manual_test_control.json',
        'README_FIRST.txt',
        'install_and_run_from_downloads.ps1',
        'DCOIR_manual_test_plan.md',
        '__pycache__'
    )
    foreach ($item in $OldFrameworkItems) {
        $target = Join-Path $InstallDir $item
        if (Test-Path $target) {
            Remove-Item -LiteralPath $target -Recurse -Force
        }
    }

    Write-Host 'Ensuring framework folders exist...' -ForegroundColor Cyan
    foreach ($folder in @('_test_output','_history','_work','_runs')) {
        New-Item -ItemType Directory -Path (Join-Path $InstallDir $folder) -Force | Out-Null
    }

    Write-Host 'Clearing live state files...' -ForegroundColor Cyan
    $LiveStateFiles = @(
        'DCOIR_Collector_Full_Signoff_Report.txt',
        '_runner_state.json',
        '_session_info.json',
        'bootstrap_status.json'
    )
    foreach ($item in $LiveStateFiles) {
        $target = Join-Path $OutputDir $item
        if (Test-Path $target) {
            Remove-Item -LiteralPath $target -Force
        }
    }

    Write-Host 'Copying new framework files into C:\DCOIR_TESTER...' -ForegroundColor Cyan
    Copy-Item -Path (Join-Path $StageDir '*') -Destination $InstallDir -Recurse -Force

    Write-Host 'Deleting downloaded zip...' -ForegroundColor Cyan
    Remove-Item -LiteralPath $ZipPath -Force

    Write-Host 'Cleaning up temporary extraction files...' -ForegroundColor Cyan
    Remove-Item -LiteralPath $StageDir -Recurse -Force

    Set-Location $InstallDir

    Write-Host ''
    Write-Host 'Launching the DCOIR_TESTER manual test framework...' -ForegroundColor Green
    Write-Host ''

    powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\run_dcoir_manual_tests.ps1
}
catch {
    Write-Host ''
    Write-Host 'Install/launch failed.' -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Yellow

    if (Test-Path $StageDir) {
        try { Remove-Item -LiteralPath $StageDir -Recurse -Force } catch {}
    }

    Write-Host ''
    Write-Host 'Next step: send me the exact error text shown above.' -ForegroundColor Cyan
    exit 1
}
