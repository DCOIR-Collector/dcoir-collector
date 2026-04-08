#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


def run_step(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, text=True, capture_output=True)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--source-root', required=True)
    ap.add_argument('--output-dir', required=True)
    ap.add_argument('--version', default=None)
    ap.add_argument('--skip-validation', action='store_true')
    args = ap.parse_args()

    script_root = Path(__file__).resolve().parent
    source_root = Path(args.source_root).resolve()
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    validate_script = script_root / 'validate_dcoir_gemini_bundle.py'
    compile_script = script_root / 'compile_dcoir_gemini_bundle.py'

    steps = []

    if not args.skip_validation:
        validate_cmd = [sys.executable, str(validate_script), '--source-root', str(source_root), '--output-dir', str(output_dir)]
        validate_proc = run_step(validate_cmd)
        steps.append({
            'name': 'validate',
            'cmd': validate_cmd,
            'returncode': validate_proc.returncode,
            'stdout': validate_proc.stdout,
            'stderr': validate_proc.stderr,
        })
        if validate_proc.returncode != 0:
            report = {
                'success': False,
                'stage': 'validate',
                'steps': steps,
            }
            report_path = output_dir / 'build_dcoir_gemini_release_report.json'
            report_path.write_text(json.dumps(report, indent=2), encoding='utf-8')
            print(json.dumps(report, indent=2))
            return 1

    compile_cmd = [sys.executable, str(compile_script), '--source-root', str(source_root), '--output-dir', str(output_dir)]
    if args.version:
        compile_cmd.extend(['--version', args.version])
    compile_proc = run_step(compile_cmd)
    steps.append({
        'name': 'compile',
        'cmd': compile_cmd,
        'returncode': compile_proc.returncode,
        'stdout': compile_proc.stdout,
        'stderr': compile_proc.stderr,
    })

    success = compile_proc.returncode == 0
    report = {
        'success': success,
        'stage': 'complete' if success else 'compile',
        'steps': steps,
    }
    report_path = output_dir / 'build_dcoir_gemini_release_report.json'
    report_path.write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report, indent=2))
    return 0 if success else 1


if __name__ == '__main__':
    raise SystemExit(main())
