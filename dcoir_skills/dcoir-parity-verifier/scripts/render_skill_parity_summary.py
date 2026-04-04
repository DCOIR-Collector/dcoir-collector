#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--manifest', required=True)
    ap.add_argument('--output', required=True)
    args = ap.parse_args()
    manifest = json.loads(Path(args.manifest).read_text(encoding='utf-8'))
    lines = [
        '# DCOIR Skill Parity Summary',
        '',
        f"- generated_at_utc: {manifest.get('generated_at_utc', '')}",
        f"- baseline_origin: {manifest.get('baseline_origin', '')}",
        '- canonical machine-readable source: `dcoir_skills/skill_parity_manifest.json`',
        '',
    ]
    for skill_name, data in sorted(manifest.get('skills', {}).items()):
        lines.extend([
            f'## {skill_name}',
            '',
            f"- source_tree_hash: `{data.get('source_tree_hash', '')}`",
            f"- release_zip_name: `{data.get('release_zip_name', '')}`",
            f"- release_zip_hash: `{data.get('release_zip_hash', '') or 'not-recorded'}`",
            f"- status: `{data.get('status', '')}`",
            f"- file_count: `{data.get('file_count', 0)}`",
            '',
        ])
        for row in data.get('files', []):
            lines.append(f"- `{row['path']}` — `{row['sha256']}`")
        lines.append('')
    output = Path(args.output).resolve()
    output.write_text('\n'.join(lines), encoding='utf-8')
    print(f'Wrote {output}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
