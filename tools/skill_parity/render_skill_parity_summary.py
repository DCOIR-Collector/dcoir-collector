#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--manifest', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()

    manifest_path = Path(args.manifest)
    data = json.loads(manifest_path.read_text(encoding='utf-8'))
    skills = data.get('skills', {})

    lines = [
        '# DCOIR Skill Parity Summary',
        '',
        f"- Project: {data.get('project', '')}",
        f"- Generated at UTC: {data.get('generated_at_utc', '')}",
        f"- Baseline origin: {data.get('baseline_origin', '')}",
        f"- Skill count: {len(skills)}",
        '',
        '| Skill | Status | Files | Bytes | Source tree hash |',
        '|---|---:|---:|---:|---|',
    ]
    for name in sorted(skills):
        info = skills[name]
        lines.append(f"| `{name}` | {info.get('status', '')} | {info.get('file_count', 0)} | {info.get('total_bytes', 0)} | `{info.get('source_tree_hash', '')}` |")

    lines += [
        '',
        '## Notes',
        '',
        '- This summary is generated from repo source under `dcoir_skills/`.',
        '- Only directories beginning with `dcoir-` and containing `SKILL.md` are included.',
        '- `skill_parity_manifest.json` is the canonical machine-readable surface.',
    ]
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print(f'Wrote {output} with {len(skills)} skills')
    return 0


raise SystemExit(main())
