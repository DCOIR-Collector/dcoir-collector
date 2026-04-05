#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

TOP_LEVEL_STRUCTURAL = {
    'project_sources/',
    'knowledge/',
    'supporting_assets/',
    'project_settings/',
    'release_notes/'
}
CONTROL_PLANE_NAMES = {
    'cp-01_dcoir_version_manifest.txt',
    'cp-02_dcoir_change_log.txt',
    'doc-01_africom_soc_ir_project_setup_and_workflow.txt',
    'doc-03_dcoir_repository_layout_spec_v1_0_0.txt'
}


def classify(name: str) -> str:
    lowered = name.lower()
    if not lowered:
        return 'generic'
    if lowered.startswith('dcoir_skills/') or lowered.startswith('dcoir-'):
        return 'skill'
    if any(lowered.startswith(prefix) for prefix in TOP_LEVEL_STRUCTURAL):
        return 'repo_surface'
    if Path(lowered).name in CONTROL_PLANE_NAMES or 'layout' in lowered or 'structural' in lowered:
        return 'control_plane'
    if lowered.endswith('.zip') or lowered.startswith('supporting_assets/'):
        return 'supporting_asset'
    return 'repo_readable'


def map_impact(data):
    old = data.get('old_name', '').strip()
    new = data.get('new_name', '').strip()
    categories = {classify(old), classify(new)}

    impacted = ['change_log', 'docs', 'tests']
    repo_posture = 'github_desktop_manual_repo_update_bundle'
    skill_posture = 'none'

    if 'skill' in categories:
        impacted.extend(['skills', 'skill_packages', 'routing_note', 'parity_surfaces'])
        skill_posture = 'targeted_skill_update'
    if 'repo_surface' in categories:
        impacted.extend(['readmes', 'routing_note', 'bundle_mappings'])
    if 'supporting_asset' in categories:
        impacted.extend(['supporting_assets', 'bundle_mappings'])
    if 'control_plane' in categories:
        impacted.extend(['manifest', 'control_plane', 'handoff'])
        repo_posture = 'full_refresh_project_upload'
    if 'repo_readable' in categories and repo_posture != 'full_refresh_project_upload':
        impacted.extend(['governed_repo_readable_sources'])

    impacted = sorted(dict.fromkeys(impacted))
    stop_conditions = [
        'stop if current control-plane files still point at the retired name after the patch',
        'stop if README or routing surfaces would remain stale after the rename',
        'stop if a generated artifact is renamed without updating its modular source of truth'
    ]
    if skill_posture != 'none' and repo_posture == 'github_desktop_manual_repo_update_bundle':
        recommended = 'github_desktop_manual_repo_update_bundle + targeted_skill_update'
    elif skill_posture != 'none' and repo_posture == 'full_refresh_project_upload':
        recommended = 'full_refresh_project_upload + targeted_skill_update'
    else:
        recommended = repo_posture

    return {
        'old_name': old,
        'new_name': new,
        'impacted_areas': impacted,
        'recommended_repo_posture': repo_posture,
        'recommended_skill_posture': skill_posture,
        'default_release_posture': recommended,
        'deeper_regression_required': True,
        'stop_conditions': stop_conditions
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--input-json', required=True)
    ap.add_argument('--output-json', required=True)
    args = ap.parse_args()
    out = map_impact(json.loads(Path(args.input_json).read_text(encoding='utf-8')))
    p = Path(args.output_json)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(out, indent=2), encoding='utf-8')
    print(json.dumps(out, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
