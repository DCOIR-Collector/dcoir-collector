#!/usr/bin/env python3
from __future__ import annotations
import argparse, json
from pathlib import Path

def review(data):
    missing=[]
    if not data.get('control_plane_clear'): missing.append('control_plane_clear')
    if not data.get('changed_set_identified'): missing.append('changed_set_identified')
    if data.get('testable') and not data.get('deep_regression_passed'): missing.append('deep_regression_passed')
    if data.get('release_instructions_required') and not data.get('release_instructions_present'): missing.append('release_instructions_present')
    if not data.get('downstream_refreshes_resolved'): missing.append('downstream_refreshes_resolved')

    packaging = data.get('packaging_posture')
    if packaging == 'batched-skill-update-wave':
        if not data.get('all_changed_skills_regression_covered'):
            missing.append('all_changed_skills_regression_covered')
        if not data.get('batched_skill_bundle_present'):
            missing.append('batched_skill_bundle_present')
    if packaging == 'github-desktop-manual-repo-update':
        if not data.get('repo_update_bundle_present'):
            missing.append('repo_update_bundle_present')
        if data.get('commit_summary_required') and not data.get('commit_summary_present'):
            missing.append('commit_summary_present')
        if data.get('delivery_instructions_required') and not data.get('delivery_instructions_present'):
            missing.append('delivery_instructions_present')
    if data.get('package_cleanliness_required') and not data.get('package_cleanliness_passed'):
        missing.append('package_cleanliness_passed')

    if missing:
        status='not_ready'
        reason='blocking readiness gaps remain'
    elif data.get('warnings'):
        status='ready_with_conditions'
        reason='ready but operator should review non-blocking warnings'
    else:
        status='ready'
        reason='required readiness conditions satisfied'
    return {'status':status,'reason':reason,'missing':missing,'warnings':data.get('warnings',[])}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--input-json',required=True); ap.add_argument('--output-json',required=True); args=ap.parse_args()
    data=json.loads(Path(args.input_json).read_text())
    out=review(data); p=Path(args.output_json); p.parent.mkdir(parents=True, exist_ok=True); p.write_text(json.dumps(out, indent=2)); print(json.dumps(out, indent=2)); return 0 if out['status']!='not_ready' else 1
if __name__=='__main__': raise SystemExit(main())
