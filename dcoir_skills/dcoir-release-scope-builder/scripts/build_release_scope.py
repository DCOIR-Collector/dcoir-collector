#!/usr/bin/env python3
# skill-marker: updated-skill|20260425T071800Z|T2.3-airtable-first-skill-repair|source-update|dcoir-release-scope-builder|build_release_scope.py
from __future__ import annotations
import argparse


def choose_scope(targets: list[str]) -> tuple[str, str]:
    lowered = [t.lower() for t in targets]
    joined = ' '.join(lowered)
    skill_targets = [t for t in targets if t.startswith('dcoir-')]
    non_skill_targets = [t for t in targets if not t.startswith('dcoir-')]

    if any(x in joined for x in ['repo', 'local test', 'local-only']):
        return 'repo-layout-local-testing', 'request is centered on local execution or testing'

    if any(x in joined for x in ['project upload', 'full refresh upload', 'supporting_assets/', 'Airtable Operator Preferences', 'structural', 'rename']):
        return 'full-refresh-project-upload', 'broader project-upload or structural change detected'

    if non_skill_targets:
        return 'github-desktop-manual-repo-update', 'current governed repo-readable change detected in the GitHub-primary working line'

    if len(skill_targets) > 1:
        return 'batched-skill-update-wave', 'multiple compatible helper-skill changes detected'

    if len(skill_targets) == 1:
        return 'targeted-skill-update', 'single helper-skill-only change detected'

    return 'bounded-review', 'scope is not broad enough for automatic class selection and needs explicit review'


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
