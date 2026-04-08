#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import zipfile
from pathlib import Path

MANIFEST_NAME = 'Collector_Runtime_Package_Manifest.json.txt'


def run_step(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, text=True, capture_output=True)


def load_manifest(source_dir: Path) -> dict:
    return json.loads((source_dir / 'project_sources' / MANIFEST_NAME).read_text(encoding='utf-8'))


def write_report(output_dir: Path, report: dict) -> None:
    report_path = output_dir / 'build_dcoir_collector_runtime_package_report.json'
    report_path.write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report, indent=2))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--source-dir', required=True)
    ap.add_argument('--output-dir', required=True)
    ap.add_argument('--version', default=None)
    args = ap.parse_args()

    source_dir = Path(args.source_dir).resolve()
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    validate_script = Path(__file__).resolve().parent / 'validate_dcoir_collector_runtime_package.py'
    compile_script = Path(__file__).resolve().parent / 'compile_dcoir_collector_runtime.py'

    steps = []

    validate_cmd = [sys.executable, str(validate_script), '--source-dir', str(source_dir), '--output-dir', str(output_dir)]
    validate_proc = run_step(validate_cmd)
    steps.append({'name': 'validate', 'cmd': validate_cmd, 'returncode': validate_proc.returncode, 'stdout': validate_proc.stdout, 'stderr': validate_proc.stderr})
    if validate_proc.returncode != 0:
        write_report(output_dir, {'success': False, 'stage': 'validate', 'steps': steps})
        return 1

    compile_cmd = [sys.executable, str(compile_script), '--source-dir', str(source_dir), '--output-dir', str(output_dir)]
    if args.version:
        compile_cmd.extend(['--version', args.version])
    compile_proc = run_step(compile_cmd)
    steps.append({'name': 'compile_single_runtime', 'cmd': compile_cmd, 'returncode': compile_proc.returncode, 'stdout': compile_proc.stdout, 'stderr': compile_proc.stderr})
    if compile_proc.returncode != 0:
        write_report(output_dir, {'success': False, 'stage': 'compile_single_runtime', 'steps': steps})
        return 1

    manifest = load_manifest(source_dir)
    version = args.version or manifest['bundle_version']
    bundle_name = manifest['bundle_name']
    top_level = f"{bundle_name}_v{version}"
    compiled_root = output_dir / 'compiled_runtime'
    compiled_collector = compiled_root / manifest.get('compiled_runtime_name', 'DCOIR_Collector.ps1')
    harness_source = source_dir / manifest['harness_source']

    zip_path = output_dir / f"{bundle_name}_v{version}.zip"
    emitted_files = []
    with zipfile.ZipFile(zip_path, 'w', compression=zipfile.ZIP_DEFLATED) as zf:
        for row in manifest.get('delivery_zip_entries', []):
            source_kind = row.get('source_kind', 'source')
            if source_kind == 'compiled_collector':
                src = compiled_collector
            else:
                src = source_dir / row['source']
            arc = Path(top_level) / row['zip_path']
            zf.write(src, arc.as_posix())
            emitted_files.append({'source_kind': source_kind, 'source': str(src), 'zip_path': row['zip_path']})

    report = {
        'success': True,
        'stage': 'complete',
        'steps': steps,
        'zip_path': str(zip_path),
        'bundle_name': bundle_name,
        'bundle_version': version,
        'top_level_folder': top_level,
        'file_count': len(emitted_files),
        'emitted_files': emitted_files,
        'retained_supporting_asset_path': manifest.get('retained_supporting_asset_path'),
    }
    write_report(output_dir, report)
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
