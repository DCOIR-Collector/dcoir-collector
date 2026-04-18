#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path
from typing import Iterable

DEFAULT_INCLUDE_PATTERNS = [
    "project_sources/DCOIR_Collector.ps1",
    "project_sources/run_DCOIR_Tests.ps1",
    "project_sources/collector_parts/*.ps1",
]

DEFAULT_EXCLUDE_SUBSTRINGS = [
    "/generation_validation/out_",
    "\\generation_validation\\out_",
]

FILE_HELP_TOKENS = [".SYNOPSIS", ".DESCRIPTION", "FILE NAME:", "DESCRIPTION:"]
FUNCTION_HELP_TOKENS = [".SYNOPSIS", ".DESCRIPTION", "FUNCTION NAME:", "DESCRIPTION:", "INPUT:", "OUTPUT:"]


def git_tracked_files(repo_root: Path) -> list[Path]:
    result = subprocess.run(
        ["git", "ls-files", "*.ps1", "*.psm1", "*.psd1"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=True,
    )
    return [repo_root / line.strip() for line in result.stdout.splitlines() if line.strip()]


def matches_any_glob(path: Path, repo_root: Path, patterns: Iterable[str]) -> bool:
    rel = path.relative_to(repo_root).as_posix()
    for pattern in patterns:
        if Path(rel).match(pattern):
            return True
    return False


def discover_target_files(repo_root: Path, include_patterns: list[str], exclude_substrings: list[str]) -> list[Path]:
    tracked = git_tracked_files(repo_root)
    selected = []
    for path in tracked:
        rel = path.relative_to(repo_root).as_posix()
        if any(token in rel for token in exclude_substrings):
            continue
        if matches_any_glob(path, repo_root, include_patterns):
            selected.append(path)
    return sorted(set(selected))


def detect_file_help(text: str) -> bool:
    head = text[:5000]
    if "<#" not in head or "#>" not in head:
        return False
    return any(token in head for token in FILE_HELP_TOKENS)


def function_lines(text: str) -> list[tuple[int, str]]:
    items: list[tuple[int, str]] = []
    for idx, line in enumerate(text.splitlines(), start=1):
        if re.match(r"^\s*function\s+[A-Za-z0-9_-]+", line):
            items.append((idx, line.rstrip()))
    return items


def function_name(raw: str) -> str:
    m = re.match(r"^\s*function\s+([A-Za-z0-9_-]+)", raw, re.IGNORECASE)
    return m.group(1) if m else raw.strip()


def has_help_near_function(lines: list[str], lineno: int) -> bool:
    window_start = max(0, lineno - 14)
    window = "\n".join(lines[window_start:lineno])
    if "<#" not in window or "#>" not in window:
        return False
    return any(token in window for token in FUNCTION_HELP_TOKENS)


def analyze_file(path: Path, repo_root: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    funcs = function_lines(text)

    documented = []
    undocumented = []
    for lineno, raw in funcs:
        entry = {
            "name": function_name(raw),
            "line": lineno,
            "signature": raw.strip(),
        }
        if has_help_near_function(lines, lineno):
            documented.append(entry)
        else:
            undocumented.append(entry)

    return {
        "path": path.relative_to(repo_root).as_posix(),
        "file_comment_help_present": detect_file_help(text),
        "function_count": len(funcs),
        "documented_function_count": len(documented),
        "undocumented_function_count": len(undocumented),
        "documented_functions": documented,
        "undocumented_functions": undocumented,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Auto-discover PowerShell source files and verify in-code documentation coverage.")
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--output-json", required=True)
    parser.add_argument("--fail-on-missing-file-help", action="store_true")
    parser.add_argument("--fail-on-undocumented-functions", action="store_true")
    parser.add_argument("--include", action="append", default=[])
    parser.add_argument("--exclude-substring", action="append", default=[])
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    include_patterns = args.include or DEFAULT_INCLUDE_PATTERNS
    exclude_substrings = args.exclude_substring or DEFAULT_EXCLUDE_SUBSTRINGS

    files = discover_target_files(repo_root, include_patterns, exclude_substrings)
    analyses = [analyze_file(path, repo_root) for path in files]

    missing_file_help = [row["path"] for row in analyses if row["function_count"] > 0 and not row["file_comment_help_present"]]
    undocumented_function_rows = [
        {
            "path": row["path"],
            "undocumented_function_count": row["undocumented_function_count"],
            "undocumented_functions_sample": row["undocumented_functions"][:25],
        }
        for row in analyses
        if row["undocumented_function_count"] > 0
    ]

    should_fail = False
    findings: list[str] = []

    if args.fail_on_missing_file_help and missing_file_help:
        should_fail = True
        findings.append("One or more PowerShell source files with functions are missing file-level help.")
    if args.fail_on_undocumented_functions and undocumented_function_rows:
        should_fail = True
        findings.append("One or more PowerShell source files contain undocumented functions.")

    result = {
        "repo_root": str(repo_root),
        "include_patterns": include_patterns,
        "exclude_substrings": exclude_substrings,
        "file_count": len(analyses),
        "files": analyses,
        "summary": {
            "missing_file_help_count": len(missing_file_help),
            "missing_file_help_files": missing_file_help,
            "undocumented_function_file_count": len(undocumented_function_rows),
            "undocumented_function_rows": undocumented_function_rows,
        },
        "policy": {
            "fail_on_missing_file_help": args.fail_on_missing_file_help,
            "fail_on_undocumented_functions": args.fail_on_undocumented_functions,
        },
        "status": "FAIL" if should_fail else "PASS",
        "findings": findings,
    }

    output_path = Path(args.output_json).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, indent=2), encoding="utf-8")

    print(f"DOCUMENTATION_AUDIT_STATUS={result['status']}")
    print(f"OUTPUT_JSON={output_path}")

    return 1 if should_fail else 0


if __name__ == "__main__":
    raise SystemExit(main())
