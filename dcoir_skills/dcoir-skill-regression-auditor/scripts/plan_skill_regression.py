#!/usr/bin/env python3
from __future__ import annotations
import argparse


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--skill', action='append', default=[])
    ap.add_argument('--campaign', default='')
    args = ap.parse_args()
    skills = args.skill or ['unspecified-dcoir-skill']
    campaign = args.campaign.strip()

    print('# DCOIR Skill Regression Plan')
    print()
    print('## Skills')
    for s in skills:
        print(f'- {s}')
    print()

    if campaign:
        print('## Campaign context')
        print(f'- {campaign}')
        print()

    print('## Required suites')
    for item in [
        'package validation',
        'success path',
        'failure gate',
        'artifact verification',
        'post-patch rerun of failing case',
    ]:
        print(f'- {item}')
    print()

    print('## Recommended fixtures')
    fixture_items = [
        'current-workspace success fixture',
        'current-control-plane narrative-manifest fixture',
        'missing-control-plane fixture',
    ]
    if any('regression-auditor' in s for s in skills):
        fixture_items.append('helper-memory read-write fixture')
    for item in fixture_items:
        print(f'- {item}')
    print()

    print('## Campaign sequencing')
    if any('regression-auditor' in s for s in skills):
        print('- This skill is the test harness for later `dcoir-*` skill checks, so validate it before using it as evidence on the other skills.')
    else:
        print('- If this work is part of a broader helper-skill campaign, confirm `dcoir-skill-regression-auditor` has already been validated first.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
