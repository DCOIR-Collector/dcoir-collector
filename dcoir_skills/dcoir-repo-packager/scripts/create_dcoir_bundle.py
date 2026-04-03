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
MAPPING_PATH = SKILL_ROOT / "references" / "source_mapping.json"



def load_mapping() -> dict[str, Any]:
    with MAPPING_PATH.open('r', encoding='utf-8') as f:
        return json.load(f)



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



def parse_current_prose_manifest(text: str) -> dict[str, list[str]]:
    data = {
        'governed_github_readable_sources': [],
        'governed_knowledge_sources': [],
        'governed_settings_mirrors': [],
        'supporting_assets': [],
    }
    heading = None
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        if line in {'Current control plane', 'Current repo guide', 'Current collector files', 'Current task-memory bank', 'Current next work item'}:
            heading = line
            continue
        if line.startswith('- '):
            payload = line[2:].strip()
            value = payload.split(':', 1)[1].strip() if ':' in payload else payload
            if heading in {'Current control plane', 'Current repo guide', 'Current collector files'}:
                data['governed_github_readable_sources'].append(value)
            elif heading == 'Current task-memory bank':
                if value.startswith('knowledge/'):
                    data['governed_knowledge_sources'].append(value)
                else:
                    data['governed_github_readable_sources'].append(value)
    return data


def parse_manifest_sections(text: str, section_names: dict[str, str]) -> dict[str, list[str]]:
    data = {value: [] for value in section_names.values()}
    current = None
    for raw in text.splitlines():
        line = raw.strip()
        if line in section_names:
            current = section_names[line]
            continue
        if current and line.isupper() and not line.startswith('-'):
            current = None
            continue
        if current and line.startswith('- '):
            payload = line[2:].strip()
            if ':' in payload:
                _, value = payload.split(':', 1)
                data[current].append(value.strip())
            else:
                data[current].append(payload)
    if any(data.values()):
        return data
    return parse_current_prose_manifest(text)



def ensure_clean_dir(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)



def copy_file(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)



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
        return False, errors, details

    manifest_name = resolved_control['manifest']
    manifest_text = (source_dir / manifest_name).read_text(encoding='utf-8')
    manifest_data = parse_manifest_sections(manifest_text, mapping['manifest_sections'])
    prose_manifest_mode = ('Current control plane' in manifest_text and 'Current collector files' in manifest_text)

    current_readable = sorted(manifest_data.get('governed_github_readable_sources', []))
    current_knowledge = sorted(manifest_data.get('governed_knowledge_sources', []))
    current_settings = sorted(manifest_data.get('governed_settings_mirrors', []))
    current_assets = sorted(manifest_data.get('supporting_assets', []))

    expected_readable = sorted(mapping.get('expected_governed_github_readable_sources', []))
    expected_settings = sorted(mapping.get('expected_governed_settings_mirrors', []))
    expected_knowledge = sorted(mapping.get('expected_governed_knowledge_sources', ['knowledge/*.md']))
    expected_assets = sorted(mapping.get('expected_supporting_assets', []))

    if not current_readable:
        current_readable = expected_readable
    if not current_settings:
        current_settings = expected_settings
    if not current_assets:
        current_assets = expected_assets
    if not current_knowledge:
        current_knowledge = expected_knowledge

    details['manifest_current_readable_sources'] = current_readable
    details['manifest_current_knowledge_sources'] = current_knowledge
    details['manifest_current_settings_mirrors'] = current_settings
    details['manifest_current_supporting_assets'] = current_assets
    details['expected_readable_sources'] = expected_readable
    details['expected_settings_mirrors'] = expected_settings
    details['expected_supporting_assets'] = expected_assets

    if prose_manifest_mode:
        details['manifest_mode'] = 'current_prose'
        current_readable = expected_readable
        current_settings = expected_settings
        current_assets = expected_assets
        current_knowledge = expected_knowledge
        details['manifest_current_readable_sources'] = current_readable
        details['manifest_current_knowledge_sources'] = current_knowledge
        details['manifest_current_settings_mirrors'] = current_settings
        details['manifest_current_supporting_assets'] = current_assets
    else:
        details['manifest_mode'] = 'sectioned_or_legacy'
        if current_readable != expected_readable:
            errors.append('manifest current readable source list does not match packaged mapping rules')
        if expected_settings and current_settings != expected_settings:
            errors.append('manifest current settings mirror list does not match packaged mapping rules')
        if current_knowledge != expected_knowledge:
            errors.append('manifest knowledge working-set rule drifted beyond current packager assumptions')
        if expected_assets and current_assets != expected_assets:
            errors.append('manifest supporting-asset list does not match packaged mapping rules')

    required_files = expected_readable + current_settings + current_assets
    missing_files = sorted(f for f in required_files if not (source_dir / f).exists())
    knowledge_dir = source_dir / 'knowledge'
    details['missing_expected_files'] = missing_files
    details['knowledge_dir_present'] = knowledge_dir.exists()
    details['knowledge_md_count'] = len(list(knowledge_dir.glob('*.md'))) if knowledge_dir.exists() else 0
    if missing_files:
        errors.append('one or more expected current files are missing from the source directory')
    if not knowledge_dir.exists():
        errors.append('knowledge directory is missing from the source directory')

    return len(errors) == 0, errors, details



def build_repo_bundle(source_dir: Path, output_dir: Path, gate_details: dict[str, Any]) -> dict[str, Any]:
    repo_root = output_dir / 'repo_build' / 'DCOIR_Project'
    ensure_clean_dir(repo_root.parent)

    emitted: list[str] = []
    for rel_path in gate_details.get('manifest_current_readable_sources', []):
        dst = repo_root / rel_path
        copy_file(source_dir / rel_path, dst)
        emitted.append(str(dst.relative_to(repo_root)))
    for rel_path in gate_details.get('manifest_current_settings_mirrors', []):
        dst = repo_root / rel_path
        copy_file(source_dir / rel_path, dst)
        emitted.append(str(dst.relative_to(repo_root)))
    for rel_path in gate_details.get('manifest_current_supporting_assets', []):
        dst = repo_root / rel_path
        copy_file(source_dir / rel_path, dst)
        emitted.append(str(dst.relative_to(repo_root)))
    knowledge_dir = source_dir / 'knowledge'
    if knowledge_dir.exists():
        for path in sorted(knowledge_dir.glob('*.md')):
            dst = repo_root / 'knowledge' / path.name
            copy_file(path, dst)
            emitted.append(str(dst.relative_to(repo_root)))

    repo_zip = output_dir / 'DCOIR_Project_repo_bundle.zip'
    zip_dir(repo_root, repo_zip, repo_root.parent)
    checks = {
        'project_sources_present': (repo_root / 'project_sources').exists(),
        'knowledge_present': (repo_root / 'knowledge').exists(),
        'project_settings_present': (repo_root / 'project_settings').exists(),
        'supporting_assets_present': (repo_root / 'supporting_assets').exists(),
        'repo_guide_present': (repo_root / 'README.md').exists(),
        'collector_present': (repo_root / 'project_sources' / 'DCOIR_Collector.ps1').exists(),
        'harness_ps1_present': (repo_root / 'project_sources' / 'run_DCOIR_Tests.ps1').exists(),
        'todo_index_present': (repo_root / 'project_sources' / 'LOG-01_DCOIR_Todo_Index.txt').exists(),
    }
    return {
        'mode': 'repo',
        'build_root': str(repo_root),
        'zip_path': str(repo_zip),
        'emitted': emitted,
        'checks': checks,
    }



def build_update_bundle(source_dir: Path, output_dir: Path, mapping: dict[str, Any], gate_details: dict[str, Any]) -> dict[str, Any]:
    bundle_root = output_dir / 'update_build'
    ensure_clean_dir(bundle_root)
    project_settings = bundle_root / 'project_settings'
    supporting_assets = bundle_root / 'supporting_assets'
    release_notes = bundle_root / 'release_notes'

    included: list[str] = []
    if mapping.get('update_bundle_include_settings', True):
        project_settings.mkdir(parents=True, exist_ok=True)
        for rel_path in gate_details.get('manifest_current_settings_mirrors', []):
            dst = bundle_root / rel_path
            copy_file(source_dir / rel_path, dst)
            included.append(str(dst.relative_to(bundle_root)))
    if mapping.get('update_bundle_include_supporting_assets', True):
        supporting_assets.mkdir(parents=True, exist_ok=True)
        for rel_path in gate_details.get('manifest_current_supporting_assets', []):
            dst = bundle_root / rel_path
            copy_file(source_dir / rel_path, dst)
            included.append(str(dst.relative_to(bundle_root)))

    release_notes.mkdir(parents=True, exist_ok=True)
    instructions = """RELEASE_INSTRUCTIONS.txt

This bundle was generated by the dcoir-repo-packager skill.

Purpose
- GitHub-primary bootstrap refresh bundle for the DCOIR Project workspace.

Operator actions
- Update the Project settings content from the included settings file.
- Upload retained supporting assets from supporting_assets/ only when the release calls for them.
- Do not upload readable governed text mirrors from project_sources/ or knowledge/ into Project space.
- Resume from Project Instructions first, then use the GitHub connector against malwaredevil/dcoir-collector.
- Treat GitHub as the sole readable working source.

Notes
- This bundle does not decide promotions or authority.
- The current no-duplicate-readable-source rule is assumed.
"""
    (release_notes / 'RELEASE_INSTRUCTIONS.txt').write_text(instructions, encoding='utf-8')

    update_zip = output_dir / 'DCOIR_Project_bootstrap_bundle.zip'
    zip_dir(bundle_root, update_zip, bundle_root)
    checks = {
        'project_settings_present': project_settings.exists(),
        'supporting_assets_present': supporting_assets.exists(),
        'release_instructions_present': (release_notes / 'RELEASE_INSTRUCTIONS.txt').exists(),
        'project_settings_count': len(gate_details.get('manifest_current_settings_mirrors', [])),
        'supporting_asset_count': len(gate_details.get('manifest_current_supporting_assets', [])),
    }
    return {
        'mode': 'update',
        'build_root': str(bundle_root),
        'zip_path': str(update_zip),
        'included': included + ['release_notes/RELEASE_INSTRUCTIONS.txt'],
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

    mapping = load_mapping()
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
            report['outputs'].append(build_repo_bundle(source_dir, output_dir, gate_details))
        if args.mode in {'update', 'both'}:
            report['outputs'].append(build_update_bundle(source_dir, output_dir, mapping, gate_details))

    report_path = output_dir / 'packager_report.json'
    report_path.write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report, indent=2))
    print(f'[OK] wrote {report_path}')
    return 0 if success else 1


if __name__ == '__main__':
    raise SystemExit(main())
