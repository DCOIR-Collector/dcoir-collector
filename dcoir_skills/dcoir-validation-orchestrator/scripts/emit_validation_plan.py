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

SCENARIOS = {
    'end-to-end-repo-workflow': ['workflow entry points', 'handoff boundaries', 'generated artifact checks', 'representative happy-path execution', 'key failure-gate checks'],
    'edge-case-and-failure-gate': ['expected failure signatures', 'negative fixtures', 'stop conditions', 'recovery checks'],
    'skill-deep-dive': ['representative trigger coverage', 'script execution checks', 'stale-instruction review', 'governance alignment checks', 'code-hygiene follow-ups'],
    'docs-readme-knowledge-alignment': ['cross-link checks', 'inventory alignment checks', 'authority-boundary checks', 'surface usefulness checks'],
    'packager-live-project-validation': ['required roots and files', 'emitted tree checks', 'no-duplicate-readable-source checks', 'bootstrap-safety checks'],
    'session-memory-pre-push-contract': ['pre-push flush/manicure checks', 'staged governed update checks', 'todo synchronization checks', 'post-push cleanup checks', 'loss-boundary statement'],
}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--phase', required=True, choices=sorted(PHASES))
    ap.add_argument('--scenario', action='append', default=[])
    ap.add_argument('--changed-target', action='append', default=[])
    ap.add_argument('--campaign-scope', default='')
    ap.add_argument('--countdown', action='append', default=[])
    ap.add_argument('--output', required=False)
    args = ap.parse_args()

    scenarios = args.scenario or ['end-to-end-repo-workflow']
    targets = args.changed_target or ['unspecified bounded target']
    lines = ['# DCOIR Validation Plan', '', '## Phase', '', args.phase, '', '## Changed targets', '']
    for t in targets:
        lines.append(f'- {t}')
    if args.campaign_scope:
        lines.extend(['', '## Campaign scope', '', f'- {args.campaign_scope}'])
    lines.extend(['', '## Required phase sections', ''])
    for item in PHASES[args.phase]:
        lines.append(f'- {item}')
    lines.extend(['', '## Scenario overlays', ''])
    for scenario in scenarios:
        lines.append(f'### {scenario}')
        for item in SCENARIOS.get(scenario, ['bounded scenario review']):
            lines.append(f'- {item}')
        lines.append('')
    lines.extend(['## Default testing posture', '', '- use deep regression when the target is testable', '- verify emitted artifacts, not just exit status'])
    if args.countdown:
        lines.extend(['', '## Deferred review counters', ''])
        for item in args.countdown:
            lines.append(f'- {item}')
    text = '\n'.join(lines) + '\n'
    if args.output:
        Path(args.output).write_text(text, encoding='utf-8')
    print(text)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
