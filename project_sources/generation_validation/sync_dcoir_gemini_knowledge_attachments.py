#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import List, Dict

MAPPINGS = [
    ('knowledge/Knowledge - 01 - Overview and About.md', '02_PRIME_AGENT_ATTACHMENTS/Knowledge - 01 - Overview and About.md.txt'),
    ('knowledge/Knowledge - 02 - Elastic Quick Start.md', '02_PRIME_AGENT_ATTACHMENTS/Knowledge - 02 - Elastic Quick Start.md.txt'),
    ('knowledge/Knowledge - 03 - Local Test and Regression.md', '02_PRIME_AGENT_ATTACHMENTS/Knowledge - 03 - Local Test and Regression.md.txt'),
    ('knowledge/Knowledge - 04 - Tier 1 Collect Runbook.md', '02_PRIME_AGENT_ATTACHMENTS/Knowledge - 04 - Tier 1 Collect Runbook.md.txt'),
    ('knowledge/Knowledge - 05 - Tier 2 Collect Runbook.md', '02_PRIME_AGENT_ATTACHMENTS/Knowledge - 05 - Tier 2 Collect Runbook.md.txt'),
    ('knowledge/Knowledge - 06 - Enrichment Actions.md', '02_PRIME_AGENT_ATTACHMENTS/Knowledge - 06 - Enrichment Actions.md.txt'),
    ('knowledge/Knowledge - 07 - Artifact Review Guide.md', '02_PRIME_AGENT_ATTACHMENTS/Knowledge - 07 - Artifact Review Guide.md.txt'),
    ('knowledge/Knowledge - 08 - Troubleshooting.md', '02_PRIME_AGENT_ATTACHMENTS/Knowledge - 08 - Troubleshooting.md.txt'),
    ('knowledge/Knowledge - 09 - FAQ.md', '02_PRIME_AGENT_ATTACHMENTS/Knowledge - 09 - FAQ.md.txt'),
    ('knowledge/Knowledge - 10 - AI Prompt and Agent Design.md', '02_PRIME_AGENT_ATTACHMENTS/Knowledge - 10 - AI Prompt and Agent Design.md.txt'),
    ('knowledge/Knowledge - 11 - IOC Enrichment and Public Sources.md', '02_PRIME_AGENT_ATTACHMENTS/Knowledge - 11 - IOC Enrichment and Public Sources.md.txt'),
]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--repo-root', required=True)
    ap.add_argument('--source-root', required=True)
    ap.add_argument('--output-dir', required=True)
    ap.add_argument('--check-only', action='store_true')
    args = ap.parse_args()

    repo_root = Path(args.repo_root).resolve()
    source_root = Path(args.source_root).resolve()
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    errors: List[str] = []
    changed: List[str] = []
    unchanged: List[str] = []
    missing_sources: List[str] = []

    for source_rel, target_rel in MAPPINGS:
        source_path = repo_root / source_rel
        target_path = source_root / target_rel
        if not source_path.exists():
            missing_sources.append(source_rel)
            continue
        target_path.parent.mkdir(parents=True, exist_ok=True)
        source_text = source_path.read_text(encoding='utf-8')
        if not source_text.endswith('
'):
            source_text += '
'
        current_text = target_path.read_text(encoding='utf-8') if target_path.exists() else None
        if current_text != source_text:
            if not args.check_only:
                target_path.write_text(source_text, encoding='utf-8')
            changed.append(target_rel)
        else:
            unchanged.append(target_rel)

    if missing_sources:
        errors.append('missing maintained knowledge source files: ' + ', '.join(missing_sources))

    report = {
        'success': len(errors) == 0,
        'repo_root': str(repo_root),
        'source_root': str(source_root),
        'check_only': args.check_only,
        'changed_files': changed,
        'unchanged_files': unchanged,
        'missing_source_files': missing_sources,
        'errors': errors,
    }
    report_path = output_dir / 'sync_dcoir_gemini_knowledge_attachments_report.json'
    report_path.write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report, indent=2))
    return 0 if len(errors) == 0 else 1

if __name__ == '__main__':
    raise SystemExit(main())
