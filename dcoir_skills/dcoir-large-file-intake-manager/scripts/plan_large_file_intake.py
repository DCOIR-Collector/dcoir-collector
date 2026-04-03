#!/usr/bin/env python3
from __future__ import annotations
import argparse

PLAYBOOKS = {
    'too-large': 'use metadata-first triage and request the highest-value narrow excerpt next',
    'missing': 'pivot to the next best adjacent artifact or metadata source',
    'partial': 'analyze the present slice, state bounded confidence, then request the most decision-relevant missing slice',
}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--artifact-type', required=True)
    ap.add_argument('--file-status', required=True, choices=sorted(PLAYBOOKS))
    args = ap.parse_args()
    print(f'artifact_type: {args.artifact_type}')
    print(f'playbook: {PLAYBOOKS[args.file_status]}')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
