#!/usr/bin/env python3
"""Build the DCOIR skill parity manifest from repo skill source trees."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path
from typing import Any


SKIP_DIRS = {".git", "__pycache__", ".pytest_cache", ".mypy_cache"}
SKIP_FILES = {".DS_Store"}


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def iter_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for path in root.rglob("*"):
        if any(part in SKIP_DIRS for part in path.relative_to(root).parts):
            continue
        if path.is_file() and path.name not in SKIP_FILES:
            files.append(path)
    return sorted(files, key=lambda p: p.relative_to(root).as_posix())


def build_skill_entry(skill_dir: Path) -> dict[str, Any]:
    files = iter_files(skill_dir)
    file_entries: list[dict[str, Any]] = []
    tree_lines: list[str] = []
    total_bytes = 0

    for file_path in files:
        rel = file_path.relative_to(skill_dir).as_posix()
        digest = sha256_file(file_path)
        size = file_path.stat().st_size
        total_bytes += size
        file_entries.append({"path": rel, "sha256": digest, "size_bytes": size})
        tree_lines.append(f"{rel}\t{digest}")

    tree_blob = ("\n".join(tree_lines) + ("\n" if tree_lines else "")).encode("utf-8")
    return {
        "source_root": skill_dir.name,
        "source_tree_hash": sha256_bytes(tree_blob),
        "release_zip_name": f"{skill_dir.name}.zip",
        "release_zip_hash": "",
        "status": "verified",
        "file_count": len(file_entries),
        "total_bytes": total_bytes,
        "files": file_entries,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skills-root", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--skill-prefix", default="dcoir-")
    parser.add_argument("--baseline-origin", default="repo_source")
    parser.add_argument("--contract", default="")
    parser.add_argument("--project", default="AFRICOM_SOC_IR / DCOIR")
    args = parser.parse_args()

    skills_root = Path(args.skills_root)
    if not skills_root.is_dir():
        raise SystemExit(f"skills root does not exist: {skills_root}")

    skills: dict[str, Any] = {}
    for child in sorted(skills_root.iterdir(), key=lambda p: p.name):
        if not child.is_dir():
            continue
        if not child.name.startswith(args.skill_prefix):
            continue
        if not (child / "SKILL.md").is_file():
            continue
        skills[child.name] = build_skill_entry(child)

    generated_at = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    manifest: dict[str, Any] = {
        "schema_version": 1,
        "project": args.project,
        "generated_at_utc": generated_at,
        "baseline_origin": args.baseline_origin,
        "hash_policy": {
            "file_hash": "sha256",
            "tree_hash": "sha256 over sorted path\\tsha256 lines",
            "zip_hash": "sha256",
            "zip_hash_role": "secondary package/install check",
        },
        "skills": skills,
    }

    contract_path = Path(args.contract) if args.contract else None
    if contract_path and contract_path.is_file():
        manifest["contract"] = {
            "path": contract_path.as_posix(),
            "sha256": sha256_file(contract_path),
            "size_bytes": contract_path.stat().st_size,
        }

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(manifest, indent=2, sort_keys=False) + "\n", encoding="utf-8")
    print(f"Wrote {output} with {len(skills)} skills")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
