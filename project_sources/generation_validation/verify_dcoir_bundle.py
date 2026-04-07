#!/usr/bin/env python3
from __future__ import annotations
import argparse
import json
from pathlib import Path

SAFE_PER_FILE_KB = 900
SAFE_TOTAL_KB = 1800

GEMINI_REQUIRED = [
    '00_START_HERE/README_FIRST.md.txt',
    '00_START_HERE/Gemini_Build_Quick_Start.md.txt',
    '00_START_HERE/Agent_Attachment_Map.md.txt',
    '01_GEMINI_AGENT_BUILD/Prime_Agent_DCOIR_Gemini_Orchestrator.md.txt',
    '01_GEMINI_AGENT_BUILD/Generated_DCOIR_Gemini_Agent_Index.md.txt',
]

STANDALONE_REQUIRED = [
    '00_START_HERE/README_FIRST.md.txt',
    '01_STANDALONE_PROMPT/AFRICOM_SOC_DCOIR_Standalone_Master_Prompt_Full_Assembly.txt',
]

KEY_PHRASES = {
    'collector_artifact': ['collector artifact', 'collect bundle', 'enrich bundle'],
    'collector_pivot': ['collector path', 'dcoir collection'],
    'ioc_ownership': ['ioc', 'public-source', 'osint'],
    'false_positive_branch': ['false positive', 'security product'],
    'singular_command': ['SINGULAR TRIAGE COMMAND'],
}


def kb(path: Path) -> int:
    return int((path.stat().st_size + 1023) / 1024)


def find_files(root: Path) -> list[Path]:
    return sorted([p for p in root.rglob('*') if p.is_file()])


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--bundle-root', required=True)
    ap.add_argument('--bundle-type', choices=['gemini','standalone'], required=True)
    ap.add_argument('--output-json', required=True)
    args = ap.parse_args()

    root = Path(args.bundle_root).resolve()
    files = find_files(root)
    rels = [str(p.relative_to(root)).replace('\\','/') for p in files]
    required = GEMINI_REQUIRED if args.bundle_type == 'gemini' else STANDALONE_REQUIRED

    missing = [r for r in required if r not in rels]
    txt_suffix_violations = [r for r in rels if ('README' in r or r.endswith('.md') or 'Agent_' in r or 'Prompt' in r) and not r.endswith('.txt')]

    phrase_hits = {k: False for k in KEY_PHRASES}
    for p in files:
        try:
            text = p.read_text(encoding='utf-8', errors='ignore').lower()
        except Exception:
            continue
        for key, terms in KEY_PHRASES.items():
            if any(term.lower() in text for term in terms):
                phrase_hits[key] = True

    upload_candidates = [p for p in files if p.suffix == '.txt']
    upload_sizes = [{'path': str(p.relative_to(root)).replace('\\','/'), 'size_kb': kb(p)} for p in upload_candidates]
    upload_total = sum(x['size_kb'] for x in upload_sizes)
    oversize = [x for x in upload_sizes if x['size_kb'] > SAFE_PER_FILE_KB]

    report = {
        'bundle_root': str(root),
        'bundle_type': args.bundle_type,
        'missing_required_files': missing,
        'txt_suffix_violations': txt_suffix_violations,
        'phrase_hits': phrase_hits,
        'safe_total_kb': SAFE_TOTAL_KB,
        'safe_per_file_kb': SAFE_PER_FILE_KB,
        'upload_total_kb': upload_total,
        'oversize_files': oversize,
        'pass': not missing and not txt_suffix_violations and not oversize and upload_total <= SAFE_TOTAL_KB and all(phrase_hits.values())
    }

    Path(args.output_json).write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report, indent=2))
    return 0 if report['pass'] else 1

if __name__ == '__main__':
    raise SystemExit(main())
