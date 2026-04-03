#!/usr/bin/env python3
from __future__ import annotations
import argparse
from pathlib import Path

PHASES = {
    'pre-live': ['blocking gates', 'smoke checks', 'deep-regression set', 'evidence collection', 'live-readiness criteria'],
    'post-patch': ['reproduce original failure', 'patch verification', 'rerun deep-regression set', 'spillover regression', 'restored-readiness criteria'],
    'failed-run': ['capture failure evidence', 'isolate changed surface', 'targeted re-test', 'expanded regression around failure', 'recovery gate'],
    'routine': ['drift checks', 'representative regression subset', 'artifact verification', 'status note'],
}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--phase', required=True, choices=sorted(PHASES))
    ap.add_argument('--changed-target', action='append', default=[])
    ap.add_argument('--output', required=False)
    args = ap.parse_args()
    lines = ['# DCOIR Validation Plan', '', '## Phase', '', args.phase, '', '## Changed targets', '']
    targets = args.changed_target or ['unspecified bounded target']
    for t in targets:
        lines.append(f'- {t}')
    lines.extend(['', '## Required sections', ''])
    for item in PHASES[args.phase]:
        lines.append(f'- {item}')
    lines.extend(['', '## Default testing posture', '', '- use deep regression when the target is testable', '- verify emitted artifacts, not just exit status'])
    text = '\n'.join(lines) + '\n'
    if args.output:
        Path(args.output).write_text(text, encoding='utf-8')
    print(text)
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
