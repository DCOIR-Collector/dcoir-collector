#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_ROOT = SCRIPT_DIR.parent
RULES_PATH = SKILL_ROOT / "references" / "impact_rules.json"
OUTPUT_MD = "dcoir_change_impact_report.md"
OUTPUT_JSON = "dcoir_change_impact_report.json"


class ImpactError(RuntimeError):
    pass



def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")



def load_rules() -> Dict[str, Any]:
    return json.loads(RULES_PATH.read_text(encoding="utf-8"))



def resolve_control_files(source_dir: Path, roles: Dict[str, List[str]]) -> Dict[str, str]:
    resolved: Dict[str, str] = {}
    missing: List[str] = []
    for role, candidates in roles.items():
        hit = None
        for candidate in candidates:
            if (source_dir / candidate).exists():
                hit = candidate
                break
        if hit:
            resolved[role] = hit
        else:
            missing.append(role)
    if missing:
        raise ImpactError("impact analysis refused: missing required control-plane role(s): " + ", ".join(missing))
    return resolved



def parse_current_prose_manifest(manifest_text: str, sections: Dict[str, str]) -> Dict[str, List[str]]:
    data = {value: [] for value in sections.values()}
    heading = None
    for raw in manifest_text.splitlines():
        line = raw.strip()
        if not line:
            continue
        if line in {'Current control plane', 'Current repo guide', 'Current collector files', 'Current task-memory bank', 'Current next work item'}:
            heading = line
            continue
        if line.startswith('- '):
            payload = line[2:].strip()
            if payload.lower() == 'none currently tracked in the authoritative working set.':
                continue
            value = payload.split(':', 1)[1].strip() if ':' in payload else payload
            if heading in {'Current control plane', 'Current repo guide', 'Current collector files'}:
                data['governed_github_readable_sources'].append(value)
            elif heading == 'Current task-memory bank':
                if value.startswith('knowledge/'):
                    data['governed_knowledge_sources'].append(value)
                else:
                    data['governed_github_readable_sources'].append(value)
    return data


def parse_manifest_current_files(manifest_text: str, sections: Dict[str, str]) -> Dict[str, List[str]]:
    data = {value: [] for value in sections.values()}
    current: Optional[str] = None
    for raw in manifest_text.splitlines():
        line = raw.strip()
        if line in sections:
            current = sections[line]
            continue
        if current and line.isupper() and not line.startswith('-'):
            current = None
            continue
        if current and line.startswith('- '):
            payload = line[2:].strip()
            if payload.lower() == 'none currently tracked in the authoritative working set.':
                continue
            if ':' in payload:
                _, value = payload.split(':', 1)
                data[current].append(value.strip())
            else:
                data[current].append(payload)
    if any(data.values()):
        return data
    return parse_current_prose_manifest(manifest_text, sections)



def target_variants(target: str) -> List[str]:
    stripped = target.strip()
    variants = [stripped]
    basename = Path(stripped).name
    if basename not in variants:
        variants.append(basename)
    return variants



def matches_target(target: str, matcher: Dict[str, Any]) -> bool:
    variants = target_variants(target)
    for variant in variants:
        for exact in matcher.get('exact', []):
            if variant == exact:
                return True
        for prefix in matcher.get('prefix', []):
            if variant.startswith(prefix):
                return True
        for pattern in matcher.get('regex', []):
            if re.match(pattern, variant):
                return True
    return False



def packaging_rank(value: str, ordering: List[str]) -> int:
    try:
        return ordering.index(value)
    except ValueError:
        return -1



def unique_preserve(items: List[str]) -> List[str]:
    out: List[str] = []
    seen = set()
    for item in items:
        if item not in seen:
            out.append(item)
            seen.add(item)
    return out



def classify_targets(targets: List[str], rules: Dict[str, Any]) -> List[Dict[str, Any]]:
    results: List[Dict[str, Any]] = []
    for target in targets:
        matched_rule = None
        for rule in rules['rules']:
            if matches_target(target, rule.get('match', {})):
                matched_rule = rule
                break
        if not matched_rule:
            raise ImpactError(f'no impact rule matched target: {target}')
        if matched_rule.get('id') == 'fallback-unknown-target':
            raise ImpactError(
                f'unknown target requires manual classification before impact analysis can proceed: {target}'
            )
        results.append({'target': target, 'rule': matched_rule})
    return results



def build_current_known(manifest_data: Dict[str, List[str]]) -> set[str]:
    current_known: set[str] = set()
    for section, items in manifest_data.items():
        for item in items:
            if '*' in item:
                current_known.add(item)
                continue
            current_known.add(item)
            current_known.add(Path(item).name)
    return current_known



def target_in_current_working_set(target: str, current_known: set[str]) -> bool:
    for variant in target_variants(target):
        if variant in current_known:
            return True
        if 'knowledge/*.md' in current_known and variant.startswith('knowledge/') and variant.endswith('.md'):
            return True
    return False



def build_analysis(source_dir: Path, changed_targets: List[str]) -> Dict[str, Any]:
    rules = load_rules()
    resolved = resolve_control_files(source_dir, rules['control_file_roles'])
    manifest_name = resolved['manifest']
    manifest_data = parse_manifest_current_files(
        read_text(source_dir / manifest_name),
        rules['manifest_sections'],
    )

    current_known = build_current_known(manifest_data)
    classifications = classify_targets(changed_targets, rules)

    required_refresh: List[str] = []
    conditional_review: List[str] = []
    deep_regression: List[str] = []
    skill_impacts: List[str] = []
    reasons: List[str] = []
    warnings: List[str] = []
    packaging = 'none'
    packaging_order = rules['packaging_priority']

    for item in classifications:
        target = item['target']
        rule = item['rule']
        required_refresh.extend(rule.get('required_refresh', []))
        conditional_review.extend(rule.get('conditional_review', []))
        deep_regression.extend(rule.get('deep_regression', []))
        skill_impacts.extend(rule.get('skill_impacts', []))
        reasons.append(f"{target}: {rule['reason']}")
        if packaging_rank(rule.get('packaging', 'none'), packaging_order) > packaging_rank(packaging, packaging_order):
            packaging = rule.get('packaging', 'none')
        if not target.startswith('dcoir-') and not target_in_current_working_set(target, current_known):
            warnings.append(f'Target not present in the current manifest working set: {target}')

    modular_prompt_changed = any(matches_target(t, {'exact': [
        'PP-01_System_Prompt_v1_0_1.txt',
        'PP-02_Output_Schema_v1_0_0.txt',
        'PP-03_Baseline_Triage_Prompt_v1_0_0.txt',
        'PP-04_Enrichment_Review_Prompt_v0_1_1.txt',
        'PP-05_Retrieved_Artifact_Review_Prompt_v0_1_1.txt',
        'PP-06_Final_Case_Synthesis_Prompt_v0_1_1.txt',
        'PP-07_Agent_Guardrails_v1_0_0.txt',
        'project_sources/PP-01_System_Prompt_v1_0_1.txt',
        'project_sources/PP-02_Output_Schema_v1_0_0.txt',
        'project_sources/PP-03_Baseline_Triage_Prompt_v1_0_0.txt',
        'project_sources/PP-04_Enrichment_Review_Prompt_v0_1_1.txt',
        'project_sources/PP-05_Retrieved_Artifact_Review_Prompt_v0_1_1.txt',
        'project_sources/PP-06_Final_Case_Synthesis_Prompt_v0_1_1.txt',
        'project_sources/PP-07_Agent_Guardrails_v1_0_0.txt',
    ]}) for t in changed_targets)
    combined_master_changed = any(matches_target(t, {'prefix': [
        'PP-08_Combined_Analyst_Facing_Master_Prompt_',
        'project_sources/PP-08_Combined_Analyst_Facing_Master_Prompt_',
    ]}) for t in changed_targets)
    if combined_master_changed and not modular_prompt_changed:
        warnings.append('Direct PP-08 change detected without accompanying modular PP-01 through PP-07 change. Review whether the true source change belongs in the modular prompt-pack.')

    if any(t.startswith('dcoir-') for t in changed_targets):
        deep_regression.append('production-readiness gate: deep regression required before live use and after every patch')

    stop_conditions = [
        'Stop if the manifest or change log cannot be resolved.',
        'Stop if a changed target is unknown and the classification materially affects authority, packaging, or the live release set.',
        'Stop if packaging assumptions drift beyond the current layout spec.',
        'Stop if deep regression surfaces a failure in a skill, script, bundle generator, or runtime output path.',
    ]

    return {
        'analysis_status': 'success',
        'resolved_control_files': resolved,
        'changed_targets': changed_targets,
        'current_manifest_sources': manifest_data,
        'required_refresh': unique_preserve(required_refresh),
        'conditional_review': unique_preserve(conditional_review),
        'deep_regression': unique_preserve(deep_regression),
        'skill_impacts': unique_preserve(skill_impacts),
        'packaging_recommendation': packaging,
        'reasoning': reasons,
        'warnings': unique_preserve(warnings),
        'stop_conditions': stop_conditions,
    }



def render_markdown(payload: Dict[str, Any]) -> str:
    lines: List[str] = []
    lines.append('# DCOIR Change Impact Report')
    lines.append('')
    lines.append(f"- Analysis status: {payload['analysis_status']}")
    lines.append(f"- Packaging recommendation: {payload['packaging_recommendation']}")
    lines.append('')
    lines.append('## Change summary')
    lines.append('')
    if payload.get('error'):
        lines.append(f"- Error: {payload['error']}")
    for reason in payload.get('reasoning', []):
        lines.append(f'- {reason}')
    lines.append('')
    lines.append('## Directly changed targets')
    lines.append('')
    for target in payload.get('changed_targets', []):
        lines.append(f'- {target}')
    lines.append('')
    lines.append('## Required refresh set')
    lines.append('')
    for item in payload.get('required_refresh', []):
        lines.append(f'- {item}')
    lines.append('')
    lines.append('## Conditional review set')
    lines.append('')
    for item in payload.get('conditional_review', []):
        lines.append(f'- {item}')
    lines.append('')
    lines.append('## Deep-regression test set')
    lines.append('')
    for item in payload.get('deep_regression', []):
        lines.append(f'- {item}')
    lines.append('')
    lines.append('## Skill impacts')
    lines.append('')
    for item in payload.get('skill_impacts', []):
        lines.append(f'- {item}')
    lines.append('')
    lines.append('## Stop conditions and warnings')
    lines.append('')
    for item in payload.get('stop_conditions', []):
        lines.append(f'- {item}')
    for item in payload.get('warnings', []):
        lines.append(f'- Warning: {item}')
    lines.append('')
    return '\n'.join(lines)



def main() -> int:
    parser = argparse.ArgumentParser(description='Analyze DCOIR downstream change impact.')
    parser.add_argument('--source-dir', required=True)
    parser.add_argument('--output-dir', required=True)
    parser.add_argument('--changed-target', action='append', dest='changed_targets', required=True)
    args = parser.parse_args()

    source_dir = Path(args.source_dir).resolve()
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        analysis = build_analysis(source_dir, args.changed_targets)
    except ImpactError as exc:
        analysis = {
            'analysis_status': 'failure',
            'error': str(exc),
            'changed_targets': args.changed_targets,
            'required_refresh': [],
            'conditional_review': [],
            'deep_regression': [],
            'skill_impacts': [],
            'packaging_recommendation': 'none',
            'reasoning': [],
            'warnings': [],
            'stop_conditions': [str(exc)],
        }

    md_path = output_dir / OUTPUT_MD
    json_path = output_dir / OUTPUT_JSON
    md_path.write_text(render_markdown(analysis), encoding='utf-8')
    json_path.write_text(json.dumps(analysis, indent=2), encoding='utf-8')
    print(render_markdown(analysis))
    print(f'[OK] wrote {md_path}')
    print(f'[OK] wrote {json_path}')
    return 0 if analysis['analysis_status'] == 'success' else 1


if __name__ == '__main__':
    raise SystemExit(main())
