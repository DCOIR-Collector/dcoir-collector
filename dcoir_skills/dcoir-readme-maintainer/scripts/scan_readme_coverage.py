#!/usr/bin/env python3
"""Scan a repository for README coverage and simple broken local README links."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Iterable

README_NAME = "README.md"
MARKDOWN_LINK_RE = re.compile(r"\[[^\]]+\]\(([^)]+)\)")


def is_local_link(target: str) -> bool:
    lowered = target.lower()
    return not (
        lowered.startswith("http://")
        or lowered.startswith("https://")
        or lowered.startswith("mailto:")
        or lowered.startswith("#")
    )


def major_directories(root: Path) -> Iterable[Path]:
    for child in sorted(root.iterdir()):
        if not child.is_dir():
            continue
        if child.name.startswith("."):
            continue
        if child.name in {"__pycache__", "node_modules", ".git"}:
            continue
        yield child


def resolve_link(readme_path: Path, raw_target: str) -> Path:
    target = raw_target.split("#", 1)[0]
    return (readme_path.parent / target).resolve()


def scan(root: Path) -> dict:
    report: dict = {
        "root": str(root.resolve()),
        "major_directories_missing_readme": [],
        "readmes_scanned": [],
        "broken_local_links": [],
    }

    for directory in major_directories(root):
        if not (directory / README_NAME).exists():
            report["major_directories_missing_readme"].append(directory.name)

    for readme_path in sorted(root.rglob(README_NAME)):
        report["readmes_scanned"].append(str(readme_path.relative_to(root)))
        text = readme_path.read_text(encoding="utf-8")
        for raw_target in MARKDOWN_LINK_RE.findall(text):
            if not is_local_link(raw_target):
                continue
            resolved = resolve_link(readme_path, raw_target)
            if not resolved.exists():
                report["broken_local_links"].append(
                    {
                        "readme": str(readme_path.relative_to(root)),
                        "target": raw_target,
                    }
                )

    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("repo_root", help="Path to the repository root to scan")
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON instead of a markdown-style summary.",
    )
    args = parser.parse_args()

    root = Path(args.repo_root).resolve()
    if not root.exists() or not root.is_dir():
        raise SystemExit(f"Repository root does not exist or is not a directory: {root}")

    report = scan(root)

    if args.json:
        print(json.dumps(report, indent=2))
        return 0

    print("# README Coverage Report")
    print()
    print(f"Repository root: `{report['root']}`")
    print()
    print("## Major directories missing README")
    if report["major_directories_missing_readme"]:
        for name in report["major_directories_missing_readme"]:
            print(f"- `{name}/`")
    else:
        print("- none")
    print()
    print("## Broken local README links")
    if report["broken_local_links"]:
        for item in report["broken_local_links"]:
            print(f"- `{item['readme']}` -> `{item['target']}`")
    else:
        print("- none")
    print()
    print("## READMEs scanned")
    for path in report["readmes_scanned"]:
        print(f"- `{path}`")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
