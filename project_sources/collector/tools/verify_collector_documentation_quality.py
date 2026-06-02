#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path
from typing import Iterable

DEFAULT_INCLUDE_PATTERNS = [
    "project_sources/collector/source/DCOIR_Collector.ps1",
    "project_sources/collector/harness/run_DCOIR_Tests.ps1",
    "project_sources/collector/source/parts/*.ps1",
]

DEFAULT_EXCLUDE_SUBSTRINGS = [
    "/generation_validation/out_",
    "\\generation_validation\\out_",
]

FILE_HELP_TOKENS = [".SYNOPSIS", ".DESCRIPTION", "FILE NAME:", "DESCRIPTION:"]
FUNCTION_HELP_TOKENS = [".SYNOPSIS", ".DESCRIPTION", "FUNCTION NAME:", "DESCRIPTION:", "INPUT:", "OUTPUT:"]
KNOWLEDGE_INDEX_PATH = "DCOIR_KNOWLEDGE_INDEX.md"
INDEX_REFERENCE_PREFIXES = (
    "knowledge/",
    "project_sources/gemini/bundle_source/",
)


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


def extract_adjacent_help_block(lines: list[str], lineno: int) -> str:
    idx = lineno - 2
    while idx >= 0 and not lines[idx].strip():
        idx -= 1

    if idx < 0 or "#>" not in lines[idx]:
        return ""

    end_idx = idx
    idx -= 1
    while idx >= 0:
        if "<#" in lines[idx]:
            start_idx = idx
            return "\n".join(lines[start_idx:end_idx + 1])
        if re.match(r"^\s*function\s+[A-Za-z0-9_-]+", lines[idx]):
            return ""
        idx -= 1
    return ""


def has_help_near_function(lines: list[str], lineno: int) -> bool:
    block = extract_adjacent_help_block(lines, lineno)
    if not block:
        return False
    return any(token in block for token in FUNCTION_HELP_TOKENS)


def extract_function_name_from_help(block: str) -> str:
    m = re.search(r"(?im)^\s*(?:\.)?FUNCTION NAME\s*:?\s*$\s*^\s*([A-Za-z0-9_-]+)\s*$", block)
    if m:
        return m.group(1)
    m = re.search(r"(?im)^\s*(?:\.)?FUNCTION NAME\s*:?\s*([A-Za-z0-9_-]+)\s*$", block)
    return m.group(1) if m else ""


def function_help_blocks(lines: list[str]) -> list[dict]:
    blocks: list[dict] = []
    idx = 0
    while idx < len(lines):
        if "<#" not in lines[idx]:
            idx += 1
            continue
        start_idx = idx
        idx += 1
        while idx < len(lines) and "#>" not in lines[idx]:
            idx += 1
        if idx >= len(lines):
            break
        end_idx = idx
        block = "\n".join(lines[start_idx:end_idx + 1])
        expected = extract_function_name_from_help(block)
        if expected:
            next_idx = end_idx + 1
            while next_idx < len(lines) and not lines[next_idx].strip():
                next_idx += 1
            next_line = lines[next_idx].rstrip() if next_idx < len(lines) else ""
            actual = function_name(next_line) if re.match(r"^\s*function\s+[A-Za-z0-9_-]+", next_line, re.IGNORECASE) else ""
            blocks.append({
                "expected_function_name": expected,
                "line": start_idx + 1,
                "adjacent_line": next_idx + 1 if next_idx < len(lines) else None,
                "adjacent_signature": next_line.strip(),
                "adjacent_function_name": actual,
                "is_adjacent_to_matching_function": actual.lower() == expected.lower(),
            })
        idx += 1
    return blocks


def analyze_file(path: Path, repo_root: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    funcs = function_lines(text)

    documented = []
    undocumented = []
    help_blocks = function_help_blocks(lines)
    misattached = [block for block in help_blocks if not block["is_adjacent_to_matching_function"]]
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
        "misattached_function_help_block_count": len(misattached),
        "misattached_function_help_blocks": misattached,
    }


def discover_knowledge_index_references(repo_root: Path) -> list[dict]:
    index_path = repo_root / KNOWLEDGE_INDEX_PATH
    if not index_path.exists():
        return []

    text = index_path.read_text(encoding="utf-8")
    references: list[dict] = []
    for match in re.finditer(r"`([^`]+)`", text):
        raw = match.group(1).strip()
        if not raw.startswith(INDEX_REFERENCE_PREFIXES):
            continue
        if "*" in raw:
            continue
        normalized = raw.replace("\\", "/")
        references.append({
            "path": normalized,
            "exists": (repo_root / normalized).exists(),
        })
    return references


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
    knowledge_index_references = discover_knowledge_index_references(repo_root)
    missing_knowledge_index_references = [row["path"] for row in knowledge_index_references if not row["exists"]]

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
    misattached_function_help_rows = [
        {
            "path": row["path"],
            "misattached_function_help_block_count": row["misattached_function_help_block_count"],
            "misattached_function_help_blocks_sample": row["misattached_function_help_blocks"][:25],
        }
        for row in analyses
        if row["misattached_function_help_block_count"] > 0
    ]

    should_fail = False
    findings: list[str] = []

    if args.fail_on_missing_file_help and missing_file_help:
        should_fail = True
        findings.append("One or more PowerShell source files with functions are missing file-level help.")
    if args.fail_on_undocumented_functions and undocumented_function_rows:
        should_fail = True
        findings.append("One or more PowerShell source files contain undocumented functions.")
    if args.fail_on_undocumented_functions and misattached_function_help_rows:
        should_fail = True
        findings.append("One or more PowerShell source files contain function help blocks that are not adjacent to the named function.")
    if missing_knowledge_index_references:
        should_fail = True
        findings.append("DCOIR_KNOWLEDGE_INDEX.md references missing governed knowledge or Gemini source paths.")

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
            "misattached_function_help_file_count": len(misattached_function_help_rows),
            "misattached_function_help_rows": misattached_function_help_rows,
            "knowledge_index_reference_count": len(knowledge_index_references),
            "missing_knowledge_index_reference_count": len(missing_knowledge_index_references),
            "missing_knowledge_index_references": missing_knowledge_index_references,
        },
        "policy": {
            "fail_on_missing_file_help": args.fail_on_missing_file_help,
            "fail_on_undocumented_functions": args.fail_on_undocumented_functions,
            "fail_on_missing_knowledge_index_references": True,
        },
        "status": "FAIL" if should_fail else "PASS",
        "findings": findings,
    }

    output_path = Path(args.output_json).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, indent=2), encoding="utf-8")

    print(f"DOCUMENTATION_AUDIT_STATUS={result['status']}")
    print(f"OUTPUT_JSON={output_path}")
    if missing_file_help:
        print("MISSING_FILE_HELP_FILES=")
        for path in missing_file_help:
            print(f"  - {path}")
    if undocumented_function_rows:
        print("UNDOCUMENTED_FUNCTION_ROWS=")
        for row in undocumented_function_rows:
            print(f"  - {row['path']} ({row['undocumented_function_count']})")
            for fn in row['undocumented_functions_sample']:
                print(f"      * {fn['name']} line {fn['line']}")
    if misattached_function_help_rows:
        print("MISATTACHED_FUNCTION_HELP_ROWS=")
        for row in misattached_function_help_rows:
            print(f"  - {row['path']} ({row['misattached_function_help_block_count']})")
            for block in row['misattached_function_help_blocks_sample']:
                print(f"      * {block['expected_function_name']} help line {block['line']} adjacent to {block['adjacent_signature']}")
    if missing_knowledge_index_references:
        print("MISSING_KNOWLEDGE_INDEX_REFERENCES=")
        for path in missing_knowledge_index_references:
            print(f"  - {path}")

    return 1 if should_fail else 0


if __name__ == "__main__":
    raise SystemExit(main())
