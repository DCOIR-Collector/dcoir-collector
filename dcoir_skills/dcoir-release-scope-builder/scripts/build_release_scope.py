#!/usr/bin/env python3
from __future__ import annotations
import argparse


def choose_scope(targets: list[str]) -> tuple[str, str]:
    joined = ' '.join(targets).lower()
    if any(x in joined for x in ['manifest', 'change_log', 'layout', 'collector', 'prompt', 'rename', 'structural']):
        return 'full-refresh', 'structural, runtime, or project-source-affecting change detected'
    if any(x in joined for x in ['repo', 'local test', 'local-only']):
        return 'repo-layout', 'request is centered on local execution or testing'
    if any(x.startswith('dcoir-') for x in targets):
        return 'targeted-skill-update', 'helper-skill-only change detected with no broader source scope claimed'
    return 'bounded-review', 'scope is not broad enough for automatic full-refresh but needs explicit review'


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--changed-target', action='append', default=[])
    args = ap.parse_args()
    scope, reason = choose_scope(args.changed_target)
    print(f'scope: {scope}')
    print(f'reason: {reason}')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
