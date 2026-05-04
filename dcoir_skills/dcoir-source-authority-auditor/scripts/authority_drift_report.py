#!/usr/bin/env python3
"""Create DCOIR authority drift reports in Markdown and JSON."""
from __future__ import annotations
import argparse, json, re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

FAMILY_KEYWORDS = [
    ('schema_assumption_drift', ['schema','field','table','Skill State Registry','Plan Tasks','Plan Checkpoints','Retained Repo Manifest']),
    ('github_promoted_history_drift', ['github todo','CP-01','CP-02','promoted history','T99']),
    ('skill_instruction_drift', ['skill','SKILL.md','helper']),
    ('project_attachment_drift', ['attachment','Project Instructions','CP-00']),
    ('delete_queue_dependency_drift', ['Delete Queue','delete','deletion','dependency']),
    ('connector_failure_drift', ['connector','timeout','failed','error']),
]

def load_input(args) -> Dict[str, Any]:
    if args.input_json:
        with open(args.input_json, 'r', encoding='utf-8') as f: data = json.load(f)
    else:
        data = {
            'task': args.task or '', 'symptoms': args.symptom or [], 'sources': args.source or [],
            'expected_authority': args.expected_authority or '', 'observed_drift': args.observed_drift or '',
            'affected_surfaces': args.affected_surface or [], 'recommended_fix': args.recommended_fix or '',
            'operator_decision_needed': bool(args.operator_decision_needed)
        }
    for k in ['symptoms','sources','affected_surfaces']:
        if isinstance(data.get(k), str): data[k] = [data[k]]
        if data.get(k) is None: data[k] = []
    return data

def classify(data: Dict[str, Any]) -> Dict[str, str]:
    text = ' '.join([str(data.get('task','')), str(data.get('expected_authority','')), str(data.get('observed_drift','')), ' '.join(data.get('symptoms',[])), ' '.join(data.get('sources',[]))])
    family = 'startup_authority_conflict'
    for fam, keys in FAMILY_KEYWORDS:
        if any(k.lower() in text.lower() for k in keys): family = fam; break
    severity = 'warning'
    critical_terms = ['delete', 'destructive', 'overwrite', 'secret', 'token', 'schema migration']
    high_terms = ['conflict', 'missing', 'stale', 'retired', 'wrong source', 'duplicate']
    low = text.lower()
    if any(t in low for t in critical_terms): severity = 'critical'
    elif any(t in low for t in high_terms): severity = 'high'
    return {'drift_family': family, 'severity': severity}

def repair_prompt(report: Dict[str, Any]) -> str:
    return f"""Re-anchor in AFRICOM_SOC_IR / DCOIR. Airtable is live operational authority; GitHub is governed source/readback/promoted history only when source tasks require it. Analyze and repair this authority drift without creating duplicate Work Items or trusting old GitHub todo files as live queue authority.\n\nTriggering task: {report['task']}\nObserved symptom: {'; '.join(report['symptoms'])}\nSources already checked: {'; '.join(report['sources'])}\nExpected current authority: {report['expected_authority']}\nObserved drift/conflict: {report['observed_drift']}\nAffected surfaces: {'; '.join(report['affected_surfaces'])}\nRecommended repair lane: {report['recommended_fix']}\n\nOutput the smallest safe repair plan and, if files/skills must change, provide the appropriate DCOIR skill bundle, Project attachment bundle, or GitHub Desktop bundle."""

def render_md(report: Dict[str, Any]) -> str:
    def bullets(items): return '\n'.join(f'- {x}' for x in items) if items else '- none recorded'
    return f"""# DCOIR Authority Drift Report\n\n- Report key: `{report['report_key']}`\n- Created at: `{report['created_at']}`\n- Severity: `{report['severity']}`\n- Drift family: `{report['drift_family']}`\n\n## Triggering task\n{report['task'] or 'not recorded'}\n\n## Observed symptoms\n{bullets(report['symptoms'])}\n\n## Sources consulted\n{bullets(report['sources'])}\n\n## Expected current authority\n{report['expected_authority'] or 'not recorded'}\n\n## Observed drift or conflict\n{report['observed_drift'] or 'not recorded'}\n\n## Affected surfaces\n{bullets(report['affected_surfaces'])}\n\n## Recommended repair lane\n{report['recommended_fix'] or 'not recorded'}\n\n## Safe next move\nUse the smallest repair lane that updates the stale authority surface and preserves Airtable-first operational authority. Do not perform destructive Airtable cleanup outside the Delete Queue workflow.\n\n## Paste-ready repair prompt\n```text\n{report['repair_prompt']}\n```\n"""

def create(args):
    data = load_input(args); meta = classify(data)
    now = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    key_src = re.sub(r'[^a-zA-Z0-9]+','-', (data.get('task') or 'authority-drift').strip()).strip('-').lower()[:50] or 'authority-drift'
    report = {'report_key': f'DRIFT-{now}-{key_src}', 'created_at': datetime.now(timezone.utc).isoformat(), **data, **meta}
    report['repair_prompt'] = repair_prompt(report)
    out = Path(args.output_dir); out.mkdir(parents=True, exist_ok=True)
    json_path = out / 'dcoir_authority_drift_report.json'
    md_path = out / 'dcoir_authority_drift_report.md'
    json_path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding='utf-8')
    md_path.write_text(render_md(report), encoding='utf-8')
    print(json.dumps({'report_json': str(json_path), 'report_markdown': str(md_path), 'severity': report['severity'], 'drift_family': report['drift_family']}, indent=2))

def main():
    p=argparse.ArgumentParser(); sub=p.add_subparsers(dest='cmd', required=True)
    c=sub.add_parser('create'); c.add_argument('--input-json'); c.add_argument('--task'); c.add_argument('--symptom', action='append'); c.add_argument('--source', action='append'); c.add_argument('--expected-authority'); c.add_argument('--observed-drift'); c.add_argument('--affected-surface', action='append'); c.add_argument('--recommended-fix'); c.add_argument('--operator-decision-needed', action='store_true'); c.add_argument('--output-dir', required=True); c.set_defaults(func=create)
    args=p.parse_args(); args.func(args)
if __name__ == '__main__': main()
