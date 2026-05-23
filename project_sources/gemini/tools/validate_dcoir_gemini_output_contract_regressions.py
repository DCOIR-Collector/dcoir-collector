#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path
from typing import Dict, List

FIXTURE_REL = 'fixtures/gemini_output_contract_regression_cases.json'
MANIFEST_NAME = 'Gemini_Bundle_Source_Manifest.json'
FIRST_SECTION_PATTERN = re.compile(r'(?im)^\s*##\s+(bluf|executive summary)\s*$')
HEADER_PATTERN = re.compile(r'(?im)^\s*##\s+(.+?)\s*$')
BLOCKED_TERMS = [
    'readiness_confirmed',
    'enterprise_web_search_status',
    'missing_minimum_evidence',
    'routing_state',
    'planner_payloads',
    'handoff',
    'normalized evidence',
    'candidate_datasets',
    'output-composer',
    'command planning state',
]


def load_manifest(source_root: Path) -> Dict[str, object]:
    return json.loads((source_root / MANIFEST_NAME).read_text(encoding='utf-8'))


def load_fixtures(script_root: Path) -> Dict[str, object]:
    return json.loads((script_root / FIXTURE_REL).read_text(encoding='utf-8'))


def text_before_first_required_section(text: str) -> str:
    match = FIRST_SECTION_PATTERN.search(text)
    if not match:
        return text.strip()
    return text[:match.start()].strip()


def extract_headers(text: str) -> List[str]:
    return [match.group(1).strip().lower() for match in HEADER_PATTERN.finditer(text)]


def analyze_response(text: str) -> Dict[str, object]:
    lowered = text.lower()
    findings: List[str] = []
    details: Dict[str, object] = {}

    preamble = text_before_first_required_section(text)
    if preamble:
        findings.append('malformed_preamble')
        details['preamble_excerpt'] = preamble[:400]

    matched_terms = [term for term in BLOCKED_TERMS if term in lowered]
    if matched_terms:
        findings.append('internal_state_leakage')
        details['matched_internal_terms'] = matched_terms

    scaffold_markers = [marker for marker in ('```yaml', '```json') if marker in lowered]
    if scaffold_markers:
        findings.append('yaml_or_json_scaffold')
        details['matched_scaffold_markers'] = scaffold_markers

    headers = extract_headers(text)
    duplicate_headers = sorted(name for name, count in Counter(headers).items() if count > 1)
    if duplicate_headers:
        findings.append('duplicate_final_sections')
        details['duplicate_headers'] = duplicate_headers

    findings = sorted(set(findings))
    return {
        'accepted': len(findings) == 0,
        'findings': findings,
        'details': details,
    }


def evaluate_case(case: Dict[str, object]) -> Dict[str, object]:
    result = analyze_response(str(case['response']))
    expected = str(case['expected']).lower()
    must_trigger = list(case.get('must_trigger', []))
    errors: List[str] = []

    if expected == 'accept' and not result['accepted']:
        errors.append('control case was rejected unexpectedly')
    if expected == 'reject' and result['accepted']:
        errors.append('negative case was accepted unexpectedly')

    missing_required_findings = [name for name in must_trigger if name not in result['findings']]
    if missing_required_findings:
        errors.append('missing expected findings: ' + ', '.join(missing_required_findings))

    return {
        'id': case['id'],
        'description': case.get('description'),
        'expected': expected,
        'must_trigger': must_trigger,
        'accepted': result['accepted'],
        'findings': result['findings'],
        'details': result['details'],
        'success': len(errors) == 0,
        'errors': errors,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--source-root', required=True)
    ap.add_argument('--output-dir', required=True)
    args = ap.parse_args()

    script_root = Path(__file__).resolve().parent
    source_root = Path(args.source_root).resolve()
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    manifest = load_manifest(source_root)
    fixtures = load_fixtures(script_root)
    case_results = [evaluate_case(case) for case in fixtures.get('cases', [])]
    errors = [f"{case['id']}: {'; '.join(case['errors'])}" for case in case_results if not case['success']]

    report = {
        'success': len(errors) == 0,
        'source_root': str(source_root),
        'bundle_name': manifest.get('bundle_name'),
        'bundle_version': manifest.get('bundle_version'),
        'fixture_path': str((script_root / FIXTURE_REL).resolve()),
        'fixture_family': fixtures.get('fixture_family'),
        'issue': fixtures.get('issue'),
        'source_basis': fixtures.get('source_basis', []),
        'case_count': len(case_results),
        'case_results': case_results,
        'errors': errors,
    }
    report_path = output_dir / 'validate_dcoir_gemini_output_contract_regressions_report.json'
    report_path.write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report, indent=2))
    return 0 if report['success'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
