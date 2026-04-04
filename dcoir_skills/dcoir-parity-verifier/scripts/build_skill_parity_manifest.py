#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Any

EXCLUDE_DIRS = {'__pycache__'}
EXCLUDE_SUFFIXES = {'.pyc'}
EXCLUDE_NAMES = {'.DS_Store'}


def load_contract(path: Path | None) -> dict[str, Any]:
    if path is None or not path.exists():
        return {}
    return json.loads(path.read_text(encoding='utf-8'))


def resolve_project_label(contract: dict[str, Any], explicit: str | None) -> str:
    if explicit:
        return explicit
    return contract.get('project', {}).get('label', 'current project not recorded')


def resolve_skill_prefix(contract: dict[str, Any], explicit: str | None) -> str:
    if explicit is not None:
        return explicit
    return contract.get('project', {}).get('skill_prefix', 'dcoir-')


def iter_skill_dirs(skills_root: Path, skill_prefix: str, include: set[str] | None) -> Iterable[Path]:
    for path in sorted(skills_root.iterdir()):
        if not path.is_dir():
            continue
        if include and path.name not in include:
            continue
        if skill_prefix and not path.name.startswith(skill_prefix):
            continue
        if not (path / 'SKILL.md').exists():
            continue
        yield path


def iter_files(skill_dir: Path):
    for path in sorted(skill_dir.rglob('*')):
        if not path.is_file():
            continue
        rel = path.relative_to(skill_dir)
        if any(part in EXCLUDE_DIRS for part in rel.parts):
            continue
        if path.name in EXCLUDE_NAMES or path.suffix in EXCLUDE_SUFFIXES:
            continue
        yield path, rel


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def tree_hash(file_rows: list[dict]) -> str:
    lines = [f"{row['path']}\t{row['sha256']}" for row in sorted(file_rows, key=lambda x: x['path'])]
    data = ('\n'.join(lines) + ('\n' if lines else '')).encode('utf-8')
    return sha256_bytes(data)


def build_manifest(skills_root: Path, zip_dir: Path | None, skill_prefix: str, include: set[str] | None, baseline_origin: str, project: str) -> dict:
    skills: dict[str, dict] = {}
    for skill_dir in iter_skill_dirs(skills_root, skill_prefix, include):
        file_rows: list[dict] = []
        total_bytes = 0
        for abs_path, rel_path in iter_files(skill_dir):
            size = abs_path.stat().st_size
            total_bytes += size
            file_rows.append({'path': rel_path.as_posix(), 'sha256': sha256_file(abs_path), 'size_bytes': size})
        zip_name = f"{skill_dir.name}.zip"
        zip_hash = ''
        if zip_dir and (zip_dir / zip_name).exists():
            zip_hash = sha256_file(zip_dir / zip_name)
        skills[skill_dir.name] = {
            'source_root': skill_dir.name,
            'source_tree_hash': tree_hash(file_rows),
            'release_zip_name': zip_name,
            'release_zip_hash': zip_hash,
            'status': 'bootstrap' if baseline_origin != 'repo_source' else 'verified',
            'file_count': len(file_rows),
            'total_bytes': total_bytes,
            'files': file_rows,
        }
    return {
        'schema_version': 1,
        'project': project,
        'generated_at_utc': datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
        'baseline_origin': baseline_origin,
        'hash_policy': {
            'file_hash': 'sha256',
            'tree_hash': 'sha256 over sorted path\\tsha256 lines',
            'zip_hash': 'sha256',
            'zip_hash_role': 'secondary package/install check',
        },
        'skills': skills,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--skills-root', required=True)
    ap.add_argument('--output', required=True)
    ap.add_argument('--zip-dir')
    ap.add_argument('--skill-prefix', default=None)
    ap.add_argument('--skill', action='append', default=[])
    ap.add_argument('--baseline-origin', default='repo_source')
    ap.add_argument('--contract')
    ap.add_argument('--project', default=None)
    args = ap.parse_args()
    contract = load_contract(Path(args.contract).resolve() if args.contract else None)
    manifest = build_manifest(
        Path(args.skills_root).resolve(),
        Path(args.zip_dir).resolve() if args.zip_dir else None,
        resolve_skill_prefix(contract, args.skill_prefix),
        set(args.skill) or None,
        args.baseline_origin,
        resolve_project_label(contract, args.project),
    )
    out = Path(args.output).resolve()
    out.write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
    print(f'Wrote {out}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
