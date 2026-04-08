#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


def run_step(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, text=True, capture_output=True)


def write_report(output_dir: Path, report: dict) -> None:
    report_path = output_dir / 'build_dcoir_gemini_release_report.json'
    report_path.write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report, indent=2))


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
    repo_root = source_root.parent.parent

    sync_script = script_root / 'sync_dcoir_gemini_knowledge_attachments.py'
    validate_script = script_root / 'validate_dcoir_gemini_bundle.py'
    compile_script = script_root / 'compile_dcoir_gemini_bundle.py'

    steps = []

    sync_cmd = [sys.executable, str(sync_script), '--repo-root', str(repo_root), '--source-root', str(source_root), '--output-dir', str(output_dir)]
    sync_proc = run_step(sync_cmd)
    steps.append({
        'name': 'sync_knowledge_attachments',
        'cmd': sync_cmd,
        'returncode': sync_proc.returncode,
        'stdout': sync_proc.stdout,
        'stderr': sync_proc.stderr,
    })
    if sync_proc.returncode != 0:
        write_report(output_dir, {'success': False, 'stage': 'sync_knowledge_attachments', 'steps': steps})
        return 1

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
            write_report(output_dir, {'success': False, 'stage': 'validate', 'steps': steps})
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
    write_report(output_dir, {'success': success, 'stage': 'complete' if success else 'compile', 'steps': steps})
    return 0 if success else 1


if __name__ == '__main__':
    raise SystemExit(main())
