#!/usr/bin/env python3
"""Build a bounded manifest for DCOIR artifact intake.

This script lists file metadata without reading file contents. It supports
folders and zip archives. It is intentionally conservative to reduce timeout
risk during first-pass intake.
"""
from __future__ import annotations

import argparse
import json
import os
from collections import Counter
from pathlib import Path
from zipfile import ZipFile, BadZipFile

PRIORITY_TERMS = (
    "fail", "failure", "failed", "error", "stderr", "summary", "junit",
    "pytest", "test-results", "coverage", "sarif", "workflow", "action",
    "collector", "gemini", "prompt", "skill.md", "manifest", "readme",
)

SKIP_DIR_TERMS = (
    "node_modules", ".git", ".venv", "venv", "__pycache__", "dist", "build",
    ".mypy_cache", ".pytest_cache", ".tox", "target",
)


def ext_for(name: str) -> str:
    suffix = Path(name).suffix.lower()
    return suffix if suffix else "[no extension]"


def priority_score(name: str) -> int:
    lower = name.lower()
    score = sum(10 for term in PRIORITY_TERMS if term in lower)
    if lower.endswith((".log", ".txt", ".md", ".json", ".xml", ".sarif")):
        score += 3
    if any(part in SKIP_DIR_TERMS for part in lower.split("/")):
        score -= 20
    return score


def classify(rows: list[dict]) -> tuple[str, list[str]]:
    names = "\n".join(row["path"].lower() for row in rows[:5000])
    classes = []
    if any(term in names for term in ("workflow", "actions", "junit", "pytest", "coverage", "sarif", "##[error]")):
        classes.append("github-actions-artifact")
    if "skill.md" in names:
        classes.append("skill-package")
    if any(term in names for term in ("dcoir_collector", "dcoir-collector", "collector", "retrieved", "endpoint")):
        classes.append("collector-output")
    if any(term in names for term in ("gemini", "prompt-pack", "sub-agent", "parent-agent")):
        classes.append("gemini-or-prompt-pack")
    if any(term in names for term in (".github/workflows", "project_sources/", "dcoir_skills/", "knowledge/")):
        classes.append("repo-snapshot")
    if not classes:
        return "unknown-mixed", []
    return classes[0], classes[1:]


def manifest_zip(path: Path, max_rows: int) -> tuple[list[dict], int]:
    with ZipFile(path) as zf:
        infos = zf.infolist()
        rows = []
        for info in infos:
            if info.is_dir():
                continue
            rows.append({
                "path": info.filename,
                "size": info.file_size,
                "compressed_size": info.compress_size,
                "extension": ext_for(info.filename),
                "priority_score": priority_score(info.filename),
            })
    return rows[:max_rows], len(rows)


def manifest_dir(path: Path, max_rows: int) -> tuple[list[dict], int]:
    rows = []
    total = 0
    for root, dirs, files in os.walk(path):
        dirs[:] = [d for d in dirs if d not in SKIP_DIR_TERMS]
        for file_name in files:
            total += 1
            full = Path(root) / file_name
            rel = full.relative_to(path).as_posix()
            try:
                size = full.stat().st_size
            except OSError:
                size = None
            if len(rows) < max_rows:
                rows.append({
                    "path": rel,
                    "size": size,
                    "extension": ext_for(rel),
                    "priority_score": priority_score(rel),
                })
    return rows, total


def build_manifest(input_path: Path, max_rows: int) -> dict:
    if not input_path.exists():
        raise FileNotFoundError(str(input_path))
    if input_path.is_dir():
        rows, total = manifest_dir(input_path, max_rows)
        source_type = "directory"
    elif input_path.suffix.lower() == ".zip":
        try:
            rows, total = manifest_zip(input_path, max_rows)
        except BadZipFile as exc:
            raise ValueError(f"not a valid zip archive: {input_path}") from exc
        source_type = "zip"
    else:
        size = input_path.stat().st_size
        rows = [{
            "path": input_path.name,
            "size": size,
            "extension": ext_for(input_path.name),
            "priority_score": priority_score(input_path.name),
        }]
        total = 1
        source_type = "single-file"

    ext_counts = Counter(row["extension"] for row in rows)
    largest = sorted(rows, key=lambda r: (r.get("size") or 0), reverse=True)[:20]
    candidates = sorted(rows, key=lambda r: (r["priority_score"], -(r.get("size") or 0)), reverse=True)[:20]
    primary, secondary = classify(rows)
    return {
        "input": str(input_path),
        "source_type": source_type,
        "total_files_estimate": total,
        "manifest_rows_returned": len(rows),
        "primary_class": primary,
        "secondary_classes": secondary,
        "extension_histogram": ext_counts.most_common(20),
        "largest_files": largest,
        "candidate_files": candidates,
        "rows": rows,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a bounded DCOIR artifact manifest")
    parser.add_argument("input", help="file, folder, or zip archive to inspect")
    parser.add_argument("--output", help="write manifest JSON to this path")
    parser.add_argument("--max-rows", type=int, default=250)
    args = parser.parse_args()

    manifest = build_manifest(Path(args.input), args.max_rows)
    data = json.dumps(manifest, indent=2, sort_keys=True)
    if args.output:
        Path(args.output).write_text(data, encoding="utf-8")
    print(data)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
