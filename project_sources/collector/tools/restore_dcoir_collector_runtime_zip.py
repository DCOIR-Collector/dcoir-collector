#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
import tempfile
import zipfile
from pathlib import Path

SCRIPT_SUFFIXES = ('.ps1.txt', '.psm1.txt', '.psd1.txt', '.cmd.txt', '.bat.txt')

def strip_terminal_txt(name: str) -> str:
    for suffix in SCRIPT_SUFFIXES:
        if name.endswith(suffix):
            return name[:-4]
    if name.endswith('.txt'):
        return name[:-4]
    return name

def zip_directory_contents(source_dir: Path, zip_path: Path) -> None:
    with zipfile.ZipFile(zip_path, 'w', compression=zipfile.ZIP_DEFLATED) as zf:
        for path in sorted(source_dir.rglob('*')):
            if path.is_file():
                zf.write(path, path.relative_to(source_dir).as_posix())

def write_report(output_dir: Path, report: dict) -> None:
    report_path = output_dir / 'restore_dcoir_collector_runtime_zip_report.json'
    report_path.write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report, indent=2))

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--delivery-package-zip', required=True)
    ap.add_argument('--base-runtime-zip', required=True)
    ap.add_argument('--output-dir', required=True)
    ap.add_argument('--output-name', default='DCOIR_Collector_runtime_for_harness.zip')
    args = ap.parse_args()

    delivery_zip = Path(args.delivery_package_zip).resolve()
    base_zip = Path(args.base_runtime_zip).resolve()
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    if not delivery_zip.exists():
        write_report(output_dir, {'success': False, 'stage': 'input_check', 'error': f'delivery package zip not found: {delivery_zip}'})
        return 1
    if not base_zip.exists():
        write_report(output_dir, {'success': False, 'stage': 'input_check', 'error': f'base runtime zip not found: {base_zip}'})
        return 1

    with tempfile.TemporaryDirectory(prefix='dcoir_delivery_') as delivery_tmp, tempfile.TemporaryDirectory(prefix='dcoir_base_') as base_tmp:
        delivery_root = Path(delivery_tmp)
        base_root = Path(base_tmp)

        with zipfile.ZipFile(delivery_zip, 'r') as zf:
            zf.extractall(delivery_root)
        with zipfile.ZipFile(base_zip, 'r') as zf:
            zf.extractall(base_root)

        restored = []
        for path in sorted(delivery_root.rglob('*')):
            if not path.is_file():
                continue
            restored_name = strip_terminal_txt(path.name)
            if restored_name == path.name:
                continue
            dest = base_root / restored_name
            shutil.copy2(path, dest)
            restored.append({'from': str(path.relative_to(delivery_root)), 'to': restored_name})

        output_zip = output_dir / args.output_name
        if output_zip.exists():
            output_zip.unlink()

        zip_directory_contents(base_root, output_zip)

    report = {
        'success': True,
        'stage': 'complete',
        'delivery_package_zip': str(delivery_zip),
        'base_runtime_zip': str(base_zip),
        'output_zip': str(output_zip),
        'restored_files': restored,
        'restored_file_count': len(restored),
        'notes': [
            'This bridge restores transport-safe delivery filenames back to native runtime names for harness testing.',
            'It overlays the restored collector and harness files onto the retained tool-bearing runtime zip contents.'
        ]
    }
    write_report(output_dir, report)
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
