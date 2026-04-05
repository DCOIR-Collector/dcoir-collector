#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import tempfile
import zipfile
from pathlib import Path

EXCLUDE_DIRS = {'__pycache__'}
EXCLUDE_SUFFIXES = {'.pyc'}
EXCLUDE_NAMES = {'.DS_Store'}


def is_runtime_residue_name(rel_name: str) -> bool:
    rel_path = Path(rel_name)
    return any(part in EXCLUDE_DIRS for part in rel_path.parts) or rel_path.suffix in EXCLUDE_SUFFIXES or rel_path.name in EXCLUDE_NAMES


def scan_zip_runtime_residue(zip_file: zipfile.ZipFile) -> list[str]:
    residue = []
    for info in zip_file.infolist():
        if info.is_dir():
            continue
        if is_runtime_residue_name(info.filename):
            residue.append(info.filename)
    return sorted(residue)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def iter_files(root: Path):
    for path in sorted(root.rglob('*')):
        if not path.is_file():
            continue
        rel = path.relative_to(root)
        if any(part in EXCLUDE_DIRS for part in rel.parts):
            continue
        if path.name in EXCLUDE_NAMES or path.suffix in EXCLUDE_SUFFIXES:
            continue
        yield rel.as_posix(), path


def build_rows(root: Path):
    rows = []
    for rel, path in iter_files(root):
        rows.append({'path': rel, 'sha256': sha256_file(path), 'size_bytes': path.stat().st_size})
    return rows


def tree_hash(rows: list[dict]) -> str:
    lines = [f"{row['path']}\t{row['sha256']}" for row in sorted(rows, key=lambda x: x['path'])]
    return sha256_bytes(('\n'.join(lines) + ('\n' if lines else '')).encode('utf-8'))


def verify_dir(manifest_entry: dict, root: Path) -> dict:
    expected = {row['path']: row['sha256'] for row in manifest_entry.get('files', [])}
    actual_rows = build_rows(root)
    actual = {row['path']: row['sha256'] for row in actual_rows}
    missing = sorted(set(expected) - set(actual))
    extra = sorted(set(actual) - set(expected))
    mismatches = sorted(path for path in set(expected) & set(actual) if expected[path] != actual[path])
    actual_tree_hash = tree_hash(actual_rows)
    status = 'match' if not missing and not extra and not mismatches and actual_tree_hash == manifest_entry.get('source_tree_hash', '') else 'mismatch'
    return {
        'status': status,
        'expected_tree_hash': manifest_entry.get('source_tree_hash', ''),
        'actual_tree_hash': actual_tree_hash,
        'missing_files': missing,
        'extra_files': extra,
        'hash_mismatches': mismatches,
    }


def verify_zip(manifest_entry: dict, zip_path: Path) -> dict:
    zip_hash = sha256_file(zip_path)
    with tempfile.TemporaryDirectory() as td:
        with zipfile.ZipFile(zip_path) as zf:
            runtime_residue_entries = scan_zip_runtime_residue(zf)
            zf.extractall(td)
        extracted = Path(td)
        skill_dirs = [p for p in extracted.iterdir() if p.is_dir() and (p / 'SKILL.md').exists()]
        root = skill_dirs[0] if skill_dirs else extracted
        result = verify_dir(manifest_entry, root)
        result['parity_status'] = result['status']
        result['runtime_residue_entries'] = runtime_residue_entries
        result['package_cleanliness_status'] = 'clean' if not runtime_residue_entries else 'contaminated'
        result['expected_zip_hash'] = manifest_entry.get('release_zip_hash', '')
        result['actual_zip_hash'] = zip_hash
        result['zip_hash_status'] = 'match' if manifest_entry.get('release_zip_hash', '') and manifest_entry.get('release_zip_hash', '') == zip_hash else 'secondary-check-only'
        if runtime_residue_entries:
            result['status'] = 'contaminated'
        return result


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--manifest', required=True)
    ap.add_argument('--skill', action='append', default=[])
    ap.add_argument('--skills-root')
    ap.add_argument('--zip-dir')
    ap.add_argument('--output-md', required=True)
    ap.add_argument('--output-json')
    args = ap.parse_args()

    manifest = json.loads(Path(args.manifest).read_text(encoding='utf-8'))
    skill_names = args.skill or sorted(manifest.get('skills', {}).keys())
    results = {'skills': {}}
    overall = 'match'
    for skill_name in skill_names:
        entry = manifest['skills'][skill_name]
        skill_result: dict[str, dict] = {}
        if args.skills_root:
            skill_dir = Path(args.skills_root) / skill_name
            if skill_dir.exists():
                skill_result['source_tree'] = verify_dir(entry, skill_dir)
            else:
                skill_result['source_tree'] = {'status': 'missing', 'missing_root': str(skill_dir)}
        if args.zip_dir:
            zip_path = Path(args.zip_dir) / entry.get('release_zip_name', f'{skill_name}.zip')
            if zip_path.exists():
                skill_result['zip_package'] = verify_zip(entry, zip_path)
            else:
                skill_result['zip_package'] = {'status': 'missing', 'missing_zip': str(zip_path)}
        for lane in skill_result.values():
            if lane.get('status') not in {'match', 'secondary-check-only'}:
                overall = 'mismatch'
        results['skills'][skill_name] = skill_result

    lines = ['# DCOIR Skill Parity Verification', '', f'- overall_status: {overall}', '']
    for skill_name, skill_result in results['skills'].items():
        lines.extend([f'## {skill_name}', ''])
        for lane_name, lane in skill_result.items():
            lines.append(f"- {lane_name}: {lane.get('status', 'unknown')}")
            for key in ['missing_root', 'missing_zip', 'expected_tree_hash', 'actual_tree_hash', 'expected_zip_hash', 'actual_zip_hash', 'zip_hash_status']:
                if lane.get(key):
                    lines.append(f"  - {key}: {lane[key]}")
            for key in ['missing_files', 'extra_files', 'hash_mismatches']:
                if lane.get(key):
                    lines.append(f'  - {key}:')
                    for item in lane[key]:
                        lines.append(f'    - {item}')
        lines.append('')

    output_md = Path(args.output_md).resolve()
    output_md.write_text('\n'.join(lines), encoding='utf-8')
    if args.output_json:
        Path(args.output_json).write_text(json.dumps(results, indent=2) + '\n', encoding='utf-8')
    print(f'Wrote {output_md}')
    return 0 if overall == 'match' else 1


if __name__ == '__main__':
    raise SystemExit(main())
