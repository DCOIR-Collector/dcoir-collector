#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, List

MANIFEST_NAME = 'Gemini_Bundle_Source_Manifest.json'
AGENT_DIR = '01_GEMINI_AGENT_BUILD'
QUICK_START = '00_START_HERE/Gemini_Build_Quick_Start.md.txt'

SCENARIOS = {
    'GeminiCollectorArtifactInterpretation': {
        'description': 'The stored Gemini source should explicitly acknowledge collector artifact interpretation, upload summary driven review, and narrower artifact-first upload behavior.',
        'all_markers': ['collector artifact', 'upload summary'],
        'any_marker_groups': [
            ['attachment budget manifest', 'collection scope', 'targeted collection plan', 'representative final_artifacts'],
        ],
    },
    'GeminiIOCEnrichmentTrigger': {
        'description': 'The stored Gemini source should make mixed-format IOC intake and downstream tool routing explicit.',
        'all_markers': ['ioc', 'csv', 'pdf', 'docx'],
        'any_marker_groups': [
            ['kql', 'es/ql', 'osquery', 'response action', 'collector action'],
        ],
    },
    'GeminiOutputContractConsistency': {
        'description': 'The stored Gemini source should preserve the singular triage command contract and avoid vague filler or non-contract drift.',
        'all_markers': ['singular triage command'],
        'any_marker_groups': [
            ['starter prompt 1', 'starter prompt 2', 'starter prompt 3'],
            ['operator', 'analyst'],
        ],
    },
    'GeminiOutputLeakageAndDuplicateSuppression': {
        'description': 'The stored Gemini source should explicitly block malformed preamble text, internal state leakage, duplicate final sections, and alternate draft spillover.',
        'all_markers': [
            'malformed preamble',
            'duplicate final sections',
            'routing state',
            'exactly one final analyst-facing draft',
        ],
        'any_marker_groups': [
            ['planner payloads', 'hidden diagnostics', 'yaml', 'json'],
            ['alternate drafts', 'repeated near-identical section pairs', 'single clean final response'],
        ],
    },
    'GeminiStagedExecutionAndGroundedBoundary': {
        'description': 'The stored Gemini source should preserve decide-then-execute-then-narrate behavior and bounded grounded-source-family wording.',
        'all_markers': [
            'decide then execute then narrate',
            'progress or planner wording is not proof of execution',
            'uploaded files, connector-backed enterprise retrieval, public web grounding, custom search, or returned runtime tool results',
            'not verified from configured sources',
        ],
        'any_marker_groups': [
            ['requested action', 'planned action', 'executed action', 'returned result'],
            ['connector and indexing limits', 'searchable-text extraction limits', 'file-size or indexing ceilings'],
        ],
    },
    'GeminiSecurityProductNegativeControl': {
        'description': 'The stored Gemini source should preserve false-positive-aware handling for benign or dual-use security-product behavior.',
        'all_markers': ['false-positive-aware', 'security product'],
        'any_marker_groups': [
            ['benign', 'false positive', 'uncertainty', 'known benign'],
        ],
    },
    'GeminiRepeatedSessionConsistency': {
        'description': 'The stored Gemini source should preserve session-state awareness and repeatable behavior across repeated runs.',
        'all_markers': ['session', 'operator', 'analyst'],
        'any_marker_groups': [
            ['state', 'current', 'resume', 'repeatable', 'continuity'],
        ],
    },
    'GeminiUSBViolationsReportComposer': {
        'description': 'The stored Gemini source should preserve the weekly USB violations report workflow, conservative parsing, Stuttgart date-window handling, SNOW-prefix classification, and NIPR/SIPR split output rules.',
        'all_markers': ['usb violations', 'stuttgart', 'last friday', 'this friday', 'snow ticket', 'incn', 'incs', 'nipr', 'sipr', 'on-site', 'off-site/vpn', 'plaintext'],
        'any_marker_groups': [
            ['last week', "last week's"],
            ['weekly usb violations', 'recipient', 'message draft'],
        ],
    },
}


def load_manifest(source_root: Path) -> Dict:
    return json.loads((source_root / MANIFEST_NAME).read_text(encoding='utf-8'))


def gather_text(paths: List[Path]) -> str:
    parts: List[str] = []
    for path in paths:
        if path.exists() and path.is_file():
            parts.append(path.read_text(encoding='utf-8', errors='ignore').lower())
    return '\n'.join(parts)


def rel_posix(path: Path, source_root: Path) -> str:
    return path.relative_to(source_root).as_posix()


def evaluate_scenario(combined_text: str, config: Dict[str, object]) -> Dict[str, object]:
    all_markers = list(config.get('all_markers', []))
    any_marker_groups = list(config.get('any_marker_groups', []))
    missing_all = [marker for marker in all_markers if marker not in combined_text]
    group_results: List[Dict[str, object]] = []
    for group in any_marker_groups:
        present = [marker for marker in group if marker in combined_text]
        group_results.append({
            'expected_any_of': group,
            'present': present,
            'passed': len(present) > 0,
        })
    success = len(missing_all) == 0 and all(group['passed'] for group in group_results)
    return {
        'success': success,
        'description': config.get('description'),
        'missing_all_markers': missing_all,
        'group_results': group_results,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--source-root', required=True)
    ap.add_argument('--output-dir', required=True)
    args = ap.parse_args()

    source_root = Path(args.source_root).resolve()
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    manifest = load_manifest(source_root)
    topology = manifest.get('topology', {})

    source_paths: List[Path] = []
    source_paths.append(source_root / QUICK_START)
    if topology.get('prime_agent_file'):
        source_paths.append(source_root / topology['prime_agent_file'])
    for rel in topology.get('sub_agent_files', []):
        source_paths.append(source_root / rel)
    repo_root = source_root.parent.parent.parent
    for rel in manifest.get('knowledge_attachment_sources', []):
        source_paths.append(repo_root / rel)

    discovered_files = sorted({path.as_posix() for path in source_paths if path.exists()})
    combined_text = gather_text(source_paths)

    scenario_results: Dict[str, object] = {}
    errors: List[str] = []
    for name, config in SCENARIOS.items():
        result = evaluate_scenario(combined_text, config)
        scenario_results[name] = result
        if not result['success']:
            errors.append(f'{name} markers did not satisfy the required scenario expectations')

    report = {
        'success': len(errors) == 0,
        'source_root': str(source_root),
        'bundle_name': manifest.get('bundle_name'),
        'bundle_version': manifest.get('bundle_version'),
        'topology_source': topology.get('topology_source_of_truth', 'missing'),
        'scenario_source_files': discovered_files,
        'scenario_count': len(SCENARIOS),
        'scenario_results': scenario_results,
        'errors': errors,
    }
    report_path = output_dir / 'validate_dcoir_gemini_behavior_scenarios_report.json'
    report_path.write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report, indent=2))
    return 0 if report['success'] else 1


if __name__ == '__main__':
    raise SystemExit(main())