#!/usr/bin/env python3
"""Create strict DCOIR repo-layout and GitHub-primary bootstrap bundles."""

from __future__ import annotations

import argparse
import json
import shutil
import zipfile
from pathlib import Path
from typing import Any

SKILL_ROOT = Path(__file__).resolve().parent.parent
MAPPING_PATH = SKILL_ROOT / 'references' / 'source_mapping.json'
DISCOVERY_CONTRACT_REL = Path('dcoir_skills/project_discovery_contract.json')


def load_mapping() -> dict[str, Any]:
    return json.loads(MAPPING_PATH.read_text(encoding='utf-8'))


def load_discovery_contract(source_dir: Path) -> dict[str, Any]:
    contract_path = source_dir / DISCOVERY_CONTRACT_REL
    if not contract_path.exists():
        return {}
    return json.loads(contract_path.read_text(encoding='utf-8'))


def apply_discovery_contract(mapping: dict[str, Any], discovery_contract: dict[str, Any]) -> dict[str, Any]:
    runtime = dict(mapping)
    if discovery_contract.get('control_file_roles'):
        runtime['control_file_roles'] = discovery_contract['control_file_roles']
    active = discovery_contract.get('active_surface_paths', {})
    required = list(runtime.get('required_repo_mode_entries', []))
    for key in ('manifest', 'change_log'):
        value = active.get(key)
        if value and value not in required:
            required.append(value)
    runtime['required_repo_mode_entries'] = required
    runtime['_runtime_repository_name'] = discovery_contract.get('repository', {}).get('name', 'malwaredevil/dcoir-collector')
    return runtime


def resolve_role_file(source_dir: Path, candidates: list[str]) -> str | None:
    for candidate in candidates:
        if (source_dir / candidate).exists():
            return candidate
    return None


def resolve_required_control_files(source_dir: Path, mapping: dict[str, Any]) -> tuple[dict[str, str], list[str]]:
    resolved: dict[str, str] = {}
    missing_roles: list[str] = []
    for role, candidates in mapping['control_file_roles'].items():
        hit = resolve_role_file(source_dir, candidates)
        if hit is None:
            missing_roles.append(role)
        else:
            resolved[role] = hit
    return resolved, missing_roles


def ensure_clean_dir(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)


def copy_entry(source_dir: Path, rel_path: str, dest_root: Path, emitted: list[str]) -> None:
    src = source_dir / rel_path
    dst = dest_root / rel_path
    if src.is_file():
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        emitted.append(rel_path)
    elif src.is_dir():
        if dst.exists():
            shutil.rmtree(dst)
        shutil.copytree(src, dst, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
        for path in sorted(dst.rglob('*')):
            if path.is_file():
                emitted.append(str(path.relative_to(dest_root)))


def zip_dir(root_dir: Path, zip_path: Path, relative_to: Path) -> None:
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        for file_path in sorted(root_dir.rglob('*')):
            if file_path.is_file():
                zf.write(file_path, file_path.relative_to(relative_to))


def verify_project_gate(source_dir: Path, mapping: dict[str, Any]) -> tuple[bool, list[str], dict[str, Any]]:
    errors: list[str] = []
    details: dict[str, Any] = {}

    resolved_control, missing_roles = resolve_required_control_files(source_dir, mapping)
    details['resolved_control_files'] = resolved_control
    details['missing_control_roles'] = missing_roles
    if missing_roles:
        errors.append('missing required DCOIR control-plane roles')

    missing_required_entries = sorted(
        entry for entry in mapping.get('required_repo_mode_entries', []) if not (source_dir / entry).exists()
    )
    details['missing_required_repo_mode_entries'] = missing_required_entries
    if missing_required_entries:
        errors.append('one or more required current repo-mode entries are missing from the source directory')

    missing_repo_roots = sorted(
        root for root in mapping.get('repo_mode_include_roots', [])
        if root in {'knowledge', 'project_sources', 'project_settings', 'supporting_assets'} and not (source_dir / root).exists()
    )
    details['missing_expected_roots'] = missing_repo_roots
    if missing_repo_roots:
        errors.append('one or more required current roots are missing from the source directory')

    return len(errors) == 0, errors, details


def build_repo_bundle(source_dir: Path, output_dir: Path, mapping: dict[str, Any]) -> dict[str, Any]:
    repo_root = output_dir / 'repo_build' / 'DCOIR_Project'
    ensure_clean_dir(repo_root.parent)
    emitted: list[str] = []
    for rel_path in mapping.get('repo_mode_include_roots', []):
        if (source_dir / rel_path).exists():
            copy_entry(source_dir, rel_path, repo_root, emitted)
    repo_zip = output_dir / 'DCOIR_Project_repo_bundle.zip'
    zip_dir(repo_root, repo_zip, repo_root.parent)
    checks = {
        'repo_guide_present': (repo_root / 'README.md').exists(),
        'project_sources_present': (repo_root / 'project_sources').exists(),
        'knowledge_present': (repo_root / 'knowledge').exists(),
        'dcoir_skills_present': (repo_root / 'dcoir_skills').exists(),
        'project_settings_present': (repo_root / 'project_settings').exists(),
        'supporting_assets_present': (repo_root / 'supporting_assets').exists(),
        'collector_present': (repo_root / 'project_sources' / 'DCOIR_Collector.ps1').exists(),
        'harness_ps1_present': (repo_root / 'project_sources' / 'run_DCOIR_Tests.ps1').exists(),
        'manifest_present': (repo_root / 'project_sources' / 'CP-01_DCOIR_Version_Manifest.txt').exists(),
        'change_log_present': (repo_root / 'project_sources' / 'CP-02_DCOIR_Change_Log.txt').exists(),
    }
    return {
        'mode': 'repo',
        'build_root': str(repo_root),
        'zip_path': str(repo_zip),
        'emitted': emitted,
        'checks': checks,
    }


def build_update_bundle(source_dir: Path, output_dir: Path, mapping: dict[str, Any]) -> dict[str, Any]:
    bundle_root = output_dir / 'update_build'
    ensure_clean_dir(bundle_root)
    included: list[str] = []
    for rel_path in mapping.get('update_mode_include_roots', []):
        if (source_dir / rel_path).exists():
            copy_entry(source_dir, rel_path, bundle_root, included)

    release_notes = bundle_root / 'release_notes'
    release_notes.mkdir(parents=True, exist_ok=True)
    instructions = f"""RELEASE_INSTRUCTIONS.txt

This bundle was generated by the dcoir-repo-packager skill.

Purpose
- GitHub-primary bootstrap refresh bundle for the DCOIR Project workspace.

Operator actions
- Update the Project settings content from the included settings file or files.
- Upload retained supporting assets from supporting_assets/ only when the release calls for them.
- Do not upload readable governed text mirrors from project_sources/, knowledge/, or dcoir_skills/ into Project space.
- Resume from Project Instructions first, then use the GitHub connector against {mapping.get('_runtime_repository_name', 'malwaredevil/dcoir-collector')}.
- Treat GitHub as the sole readable working source.

Notes
- This bundle does not decide promotions or authority.
- The current no-duplicate-readable-source rule is assumed.
"""
    (release_notes / 'RELEASE_INSTRUCTIONS.txt').write_text(instructions, encoding='utf-8')
    included.append('release_notes/RELEASE_INSTRUCTIONS.txt')

    update_zip = output_dir / 'DCOIR_Project_bootstrap_bundle.zip'
    zip_dir(bundle_root, update_zip, bundle_root)
    checks = {
        'project_settings_present': (bundle_root / 'project_settings').exists(),
        'supporting_assets_present': (bundle_root / 'supporting_assets').exists(),
        'release_instructions_present': (release_notes / 'RELEASE_INSTRUCTIONS.txt').exists(),
    }
    return {
        'mode': 'update',
        'build_root': str(bundle_root),
        'zip_path': str(update_zip),
        'included': included,
        'checks': checks,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description='Create strict DCOIR repo and bootstrap bundles.')
    parser.add_argument('--source-dir', default='/mnt/data', help='Directory containing current DCOIR files.')
    parser.add_argument('--output-dir', required=True, help='Output directory for build artifacts.')
    parser.add_argument('--mode', choices=['repo', 'update', 'both'], default='repo')
    args = parser.parse_args()

    source_dir = Path(args.source_dir).resolve()
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    base_mapping = load_mapping()
    discovery_contract = load_discovery_contract(source_dir)
    mapping = apply_discovery_contract(base_mapping, discovery_contract)
    success, errors, gate_details = verify_project_gate(source_dir, mapping)
    report: dict[str, Any] = {
        'success': success,
        'mode': args.mode,
        'source_dir': str(source_dir),
        'output_dir': str(output_dir),
        'gate_details': gate_details,
        'errors': errors,
        'outputs': [],
    }

    if success:
        if args.mode in {'repo', 'both'}:
            report['outputs'].append(build_repo_bundle(source_dir, output_dir, mapping))
        if args.mode in {'update', 'both'}:
            report['outputs'].append(build_update_bundle(source_dir, output_dir, mapping))

    report_path = output_dir / 'packager_report.json'
    report_path.write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report, indent=2))
    print(f'[OK] wrote {report_path}')
    return 0 if success else 1


if __name__ == '__main__':
    raise SystemExit(main())
