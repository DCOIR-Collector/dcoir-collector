#!/usr/bin/env python3
"""Validate required repo surfaces for named workflow profiles."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROFILE_PATH = Path("project_sources/github_actions/workflow_required_surface_profiles.json")


def load_profiles(repo_root: Path) -> dict[str, list[str]]:
    profile_file = repo_root / PROFILE_PATH
    if not profile_file.is_file():
        raise FileNotFoundError(f"Required surface profile file missing: {PROFILE_PATH.as_posix()}")
    try:
        data = json.loads(profile_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in {PROFILE_PATH.as_posix()}: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError(f"Profile file must be a JSON object: {PROFILE_PATH.as_posix()}")
    profiles: dict[str, list[str]] = {}
    for name, paths in data.items():
        if not isinstance(name, str) or not isinstance(paths, list) or not all(isinstance(p, str) for p in paths):
            raise ValueError(f"Profile {name!r} must map to a list of string paths")
        profiles[name] = paths
    return profiles


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", required=True, help="Required surface profile name")
    parser.add_argument("--repo-root", default=".", help="Repository root path")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    try:
        profiles = load_profiles(repo_root)
    except (FileNotFoundError, ValueError) as exc:
        print(exc, file=sys.stderr)
        return 1

    if args.profile not in profiles:
        available = ", ".join(sorted(profiles))
        print(
            f"Required surface profile not found: {args.profile}. Available profiles: {available}",
            file=sys.stderr,
        )
        return 1

    required_paths = profiles[args.profile]
    missing = [path for path in required_paths if not (repo_root / path).exists()]
    if missing:
        print(
            f"Missing required governed surfaces for profile {args.profile}: {', '.join(missing)}",
            file=sys.stderr,
        )
        return 1

    print(f"Required surface profile {args.profile} validated: {len(required_paths)} paths present.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
