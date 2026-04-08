#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, List

MANIFEST_NAME = 'Gemini_Bundle_Source_Manifest.json.txt'
REQUIRED_KNOWLEDGE = [
    'Knowledge - 01 - Overview and About.md.txt',
    'Knowledge - 02 - Elastic Quick Start.md.txt',
    'Knowledge - 03 - Local Test and Regression.md.txt',
    'Knowledge - 04 - Tier 1 Collect Runbook.md.txt',
    'Knowledge - 05 - Tier 2 Collect Runbook.md.txt',
    'Knowledge - 06 - Enrichment Actions.md.txt',
    'Knowledge - 07 - Artifact Review Guide.md.txt',
    'Knowledge - 08 - Troubleshooting.md.txt',
    'Knowledge - 09 - FAQ.md.txt',
    'Knowledge - 10 - AI Prompt and Agent Design.md.txt',
    'Knowledge - 11 - IOC Enrichment and Public Sources.md.txt',
]
VISIBILITY_CHECKS = {
    'collector_artifact_interpretation_visibility': ['collector', 'artifact'],
    'collector_pivot_visibility': ['collector', 'pivot'],
    'ioc_ownership_visibility': ['ioc'],
    'false_positive_aware_security_product_behavior': ['false positive', 'security product'],
    'operator_state_awareness_visibility': ['operator', 'analyst'],
}
AGENT_DIR = '01_GEMINI_AGENT_BUILD'
KNOWLEDGE_DIR = '02_PRIME_AGENT_ATTACHMENTS'


def load_manifest(source_root: Path) -> Dict:
    return json.loads((source_root / MANIFEST_NAME).read_text(encoding='utf-8'))


def gather_text(paths: List[Path]) -> str:
    parts: List[str] = []
    for path in paths:
        if path.exists() and path.is_file():
            try:
                parts.append(path.read_text(encoding='utf-8', errors='ignore').lower())
            except Exception:
                continue
    return '\n'.join(parts)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--source-root', required=True)
    ap.add_argument('--output-dir', required=True)
    args = ap.parse_args()

    source_root = Path(args.source_root).resolve()
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    manifest = load_manifest(source_root)
    errors: List[str] = []
    warnings: List[str] = []
    checks: Dict[str, object] = {}

    if manifest.get('source_strategy') != 'stored_source_compile':
        errors.append('source_strategy must be stored_source_compile for routine Gemini shipment')
    checks['source_strategy'] = manifest.get('source_strategy')

    required_files = manifest.get('required_files', [])
    missing_files = [rel for rel in required_files if not (source_root / rel).exists()]
    checks['required_files_present'] = len(missing_files) == 0
    checks['missing_required_files'] = missing_files
    if missing_files:
        errors.append('missing required files: ' + ', '.join(missing_files))

    operator_files = [source_root / rel for rel in required_files if rel != MANIFEST_NAME]
    non_txt = [str(p.relative_to(source_root)) for p in operator_files if p.exists() and p.suffix != '.txt']
    checks['operator_facing_txt_suffixes'] = len(non_txt) == 0
    checks['non_txt_operator_files'] = non_txt
    if non_txt:
        warnings.append('some operator-facing files do not end with .txt: ' + ', '.join(non_txt))

    knowledge_root = source_root / KNOWLEDGE_DIR
    missing_knowledge = [name for name in REQUIRED_KNOWLEDGE if not (knowledge_root / name).exists()]
    checks['approved_knowledge_attachment_set_present'] = len(missing_knowledge) == 0
    checks['missing_knowledge_files'] = missing_knowledge
    if missing_knowledge:
        errors.append('missing required knowledge attachment files: ' + ', '.join(missing_knowledge))

    agent_text = gather_text(sorted((source_root / AGENT_DIR).glob('*.txt')))
    for key, needles in VISIBILITY_CHECKS.items():
        present = all(needle in agent_text for needle in needles)
        checks[key] = present
        if not present:
            warnings.append(f'visibility check did not find all markers for {key}: {needles}')

    success = len(errors) == 0
    report = {
        'success': success,
        'source_root': str(source_root),
        'bundle_name': manifest.get('bundle_name'),
        'bundle_version': manifest.get('bundle_version'),
        'checks': checks,
        'warnings': warnings,
        'errors': errors,
    }
    report_path = output_dir / 'validate_dcoir_gemini_bundle_report.json'
    report_path.write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report, indent=2))
    return 0 if success else 1


if __name__ == '__main__':
    raise SystemExit(main())
