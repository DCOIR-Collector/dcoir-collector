#!/usr/bin/env python3
from __future__ import annotations
import argparse


def ordered_skills(skills: list[str]) -> list[str]:
    unique = []
    seen = set()
    for skill in skills:
        if skill not in seen:
            unique.append(skill)
            seen.add(skill)
    if 'dcoir-skill-regression-auditor' in seen:
        unique = ['dcoir-skill-regression-auditor'] + [s for s in unique if s != 'dcoir-skill-regression-auditor']
    return unique


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--skill', action='append', default=[])
    ap.add_argument('--campaign', default='')
    args = ap.parse_args()
    skills = ordered_skills(args.skill or ['unspecified-dcoir-skill'])
    campaign = args.campaign.strip()

    print('# DCOIR Skill Regression Plan')
    print()
    print('## Skills in scope')
    for s in skills:
        print(f'- {s}')
    print()

    if campaign:
        print('## Campaign context')
        print(f'- {campaign}')
        print()

    print('## Execution order')
    for idx, skill in enumerate(skills, start=1):
        if idx == 1 and skill == 'dcoir-skill-regression-auditor':
            print(f'- {idx}. {skill} (self-first validation because it is the campaign harness)')
        else:
            print(f'- {idx}. {skill}')
    print()

    print('## Required suites by skill')
    for skill in skills:
        print(f'### {skill}')
        for item in [
            'preventive bytecode-suppression step where practical',
            'package hygiene cleanup step',
            'package validation',
            'package cleanliness check',
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
        'package hygiene cleanup fixture',
        'package cleanliness fixture',
    ]
    if any('regression-auditor' in s for s in skills):
        fixture_items.append('helper-memory read-write fixture')
    for item in fixture_items:
        print(f'- {item}')
    print()

    print('## Grouped campaign readiness summary')
    print('- Every materially changed skill must have an explicit regression result or a plainly bounded untested reason.')
    print('- The campaign is not ready merely because all packages validate.')
    print('- If a grouped repo batch is planned, keep one grouped regression bundle with per-skill evidence and stop reasons.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
