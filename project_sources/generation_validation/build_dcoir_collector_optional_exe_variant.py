#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

MANIFEST_NAME = 'Collector_Runtime_Package_Manifest.json.txt'


def run_step(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, text=True, capture_output=True)


def load_manifest(source_dir: Path) -> dict:
    return json.loads((source_dir / 'project_sources' / MANIFEST_NAME).read_text(encoding='utf-8'))


def write_report(output_dir: Path, report: dict) -> None:
    report_path = output_dir / 'build_dcoir_collector_optional_exe_variant_report.json'
    report_path.write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report, indent=2))


def find_compiled_collector(output_dir: Path, manifest: dict) -> Path:
    compiled_name = manifest.get('compiled_runtime_name', 'DCOIR_Collector.ps1')
    candidate = output_dir / 'compiled_runtime' / compiled_name
    if not candidate.exists():
        raise FileNotFoundError(f'Compiled collector was not produced: {candidate}')
    return candidate


def main() -> int:
    ap = argparse.ArgumentParser(description='Build an optional PS2EXE-based DCOIR collector EXE variant.')
    ap.add_argument('--source-dir', required=True, help='Repository root containing project_sources/.')
    ap.add_argument('--output-dir', required=True, help='Output directory for compiled runtime, EXE variant, and reports.')
    ap.add_argument('--version', default=None, help='Optional package version override forwarded to the normal collector package builder.')
    ap.add_argument('--skip-ps2exe-install', action='store_true', help='Do not attempt to install PS2EXE. Fail if Invoke-PS2EXE is unavailable.')
    args = ap.parse_args()

    source_dir = Path(args.source_dir).resolve()
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    package_builder = Path(__file__).resolve().parent / 'build_dcoir_collector_runtime_package.py'
    manifest = load_manifest(source_dir)
    steps = []

    normal_cmd = [sys.executable, str(package_builder), '--source-dir', str(source_dir), '--output-dir', str(output_dir)]
    if args.version:
        normal_cmd.extend(['--version', args.version])
    normal_proc = run_step(normal_cmd)
    steps.append({'name': 'build_transport_safe_ps1_package', 'cmd': normal_cmd, 'returncode': normal_proc.returncode, 'stdout': normal_proc.stdout, 'stderr': normal_proc.stderr})
    if normal_proc.returncode != 0:
        write_report(output_dir, {'success': False, 'stage': 'build_transport_safe_ps1_package', 'steps': steps, 'exe_variant_role': 'optional_additive_only'})
        return 1

    compiled_collector = find_compiled_collector(output_dir, manifest)
    exe_output_dir = output_dir / 'optional_exe_variant'
    exe_output_dir.mkdir(parents=True, exist_ok=True)
    exe_path = exe_output_dir / 'DCOIR_Collector_optional_exe_variant.exe'

    ps_script = f"""
$ErrorActionPreference = 'Stop'
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
if (-not (Get-Command Invoke-PS2EXE -ErrorAction SilentlyContinue)) {{
  if ({'$true' if args.skip_ps2exe_install else '$false'}) {{
    throw 'Invoke-PS2EXE is unavailable and --skip-ps2exe-install was set.'
  }}
  try {{
    Set-PSRepository -Name PSGallery -InstallationPolicy Trusted -ErrorAction SilentlyContinue
  }} catch {{}}
  Install-Module -Name ps2exe -Repository PSGallery -Scope CurrentUser -Force -AllowClobber -Confirm:$false
  Import-Module ps2exe -Force
}}
if (-not (Get-Command Invoke-PS2EXE -ErrorAction SilentlyContinue)) {{
  throw 'Invoke-PS2EXE is unavailable after install/import attempt.'
}}
Invoke-PS2EXE -InputFile '{compiled_collector}' -OutputFile '{exe_path}' -NoConsole:$false -RequireAdmin:$false -Verbose
if (-not (Test-Path -LiteralPath '{exe_path}')) {{
  throw 'Expected EXE output was not produced: {exe_path}'
}}
""".strip()

    exe_cmd = ['powershell.exe', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-Command', ps_script]
    exe_proc = run_step(exe_cmd)
    steps.append({'name': 'build_optional_exe_variant', 'cmd': ['powershell.exe', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-Command', '<ps2exe build script>'], 'returncode': exe_proc.returncode, 'stdout': exe_proc.stdout, 'stderr': exe_proc.stderr})
    if exe_proc.returncode != 0:
        write_report(output_dir, {
            'success': False,
            'stage': 'build_optional_exe_variant',
            'steps': steps,
            'compiled_collector': str(compiled_collector),
            'exe_variant_role': 'optional_additive_only',
            'ps1_contract_status': 'unchanged_primary_delivery_contract',
            'note': 'The EXE variant is optional. A failed EXE build does not invalidate the PS1-first collector delivery package by itself.',
        })
        return 1

    readme = exe_output_dir / 'README_OPTIONAL_EXE_VARIANT.txt'
    readme.write_text(
        '\n'.join([
            'DCOIR optional EXE variant',
            '',
            'This EXE is an optional/manual-trigger variant built from the compiled DCOIR_Collector.ps1 runtime.',
            'It does not replace the PS1-first collector delivery contract.',
            'Use the normal transport-safe PS1 delivery package unless the optional EXE variant has been explicitly validated for the target environment.',
            '',
            'Primary collector contract remains:',
            '- compiled DCOIR_Collector.ps1 runtime',
            '- run_DCOIR_Tests.ps1 harness',
            '- transport-safe delivery package with .txt script suffixes',
            '',
            f'EXE path: {exe_path.name}',
        ]) + '\n',
        encoding='utf-8',
    )

    report = {
        'success': True,
        'stage': 'complete',
        'steps': steps,
        'compiled_collector': str(compiled_collector),
        'exe_path': str(exe_path),
        'exe_readme': str(readme),
        'exe_variant_role': 'optional_additive_only',
        'ps1_contract_status': 'unchanged_primary_delivery_contract',
    }
    write_report(output_dir, report)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
