#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_ROOT = SCRIPT_DIR.parent
PACKAGED_CONTRACT_PATH = SKILL_ROOT / "references" / "project_discovery_contract.json"
REPO_CONTRACT_PATH = Path("dcoir_skills/project_discovery_contract.json")

def load_project_contract(source_dir: Path) -> dict[str, Any]:
    repo_contract = source_dir / REPO_CONTRACT_PATH
    candidate = repo_contract if repo_contract.exists() else PACKAGED_CONTRACT_PATH
    return json.loads(candidate.read_text(encoding="utf-8"))

REQUIRED_MARKERS = [
    "STATUS",
    "RUN_ID",
    "SESSION_STATUS",
    "NEXT_GET_FILE",
    "NEXT_OPTIONS",
    "CLEANUP_COMMAND",
    "DELETE_SCRIPT_COMMAND",
    "NEXT_QUICK_COMMANDS",
]


def sha256_text(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def parse_suite_names(test_ps1_text: str) -> List[str]:
    m = re.search(r"\[ValidateSet\((.*?)\)\]", test_ps1_text, re.DOTALL)
    if not m:
        return []
    raw = m.group(1)
    return [part.strip().strip('"\'') for part in raw.split(",") if part.strip()]


def find_output_markers(text: str) -> Dict[str, List[int]]:
    result: Dict[str, List[int]] = {}
    for marker in REQUIRED_MARKERS:
        positions = []
        for i, line in enumerate(text.splitlines(), start=1):
            if marker in line:
                positions.append(i)
        result[marker] = positions
    return result


def extract_cleanup_commands(text: str) -> Dict[str, Optional[str]]:
    values: Dict[str, Optional[str]] = {
        "cleanup_command": None,
        "delete_script_command": None,
        "next_get_file_example": None,
    }
    patterns = {
        "cleanup_command": r"CLEANUP_COMMAND=execute --command \"([^\"]+)\"",
        "delete_script_command": r"DELETE_SCRIPT_COMMAND=execute --command \"([^\"]+)\"",
        "next_get_file_example": r"NEXT_GET_FILE=([^\"\n]+\"[^\"]+\")",
    }
    for key, pattern in patterns.items():
        m = re.search(pattern, text)
        if m:
            values[key] = m.group(1)
    return values


def build_code_blocks(suites: List[str], extracted: Dict[str, Optional[str]]) -> Dict[str, str]:
    blocks: Dict[str, str] = {}
    for suite in suites:
        blocks[f"powershell_harness_{suite.lower()}"] = (
            f'powershell.exe -NoProfile -ExecutionPolicy Bypass -File ".\run_DCOIR_Tests.ps1" -Suite {suite}'
        )
    if extracted.get("cleanup_command"):
        blocks["collector_cleanup_command"] = extracted["cleanup_command"] or ""
    if extracted.get("delete_script_command"):
        blocks["collector_delete_script_command"] = extracted["delete_script_command"] or ""
    return blocks


def build_source_record(path: Path, runtime_name: Optional[str] = None) -> Dict[str, object]:
    return {
        "path": str(path),
        "filename": path.name,
        "exists": path.exists(),
        "sha256": sha256_text(path) if path.exists() else None,
        "bytes": path.stat().st_size if path.exists() else None,
        "runtime_name": runtime_name,
    }


def detect_file_help(text: str) -> bool:
    head = text[:4000]
    if "<#" not in head or "#>" not in head:
        return False
    return any(token in head for token in [".SYNOPSIS", ".DESCRIPTION", ".PARAMETER", ".EXAMPLE"])


def find_function_lines(text: str) -> List[tuple[int, str]]:
    items: List[tuple[int, str]] = []
    for idx, line in enumerate(text.splitlines(), start=1):
        if re.match(r"^\s*function\s+[A-Za-z0-9_-]+", line):
            items.append((idx, line.strip()))
    return items


def extract_function_name(line: str) -> str:
    m = re.match(r"^function\s+([A-Za-z0-9_-]+)", line, re.IGNORECASE)
    return m.group(1) if m else line


def function_help_map(text: str) -> Dict[str, Dict[str, object]]:
    lines = text.splitlines()
    functions = find_function_lines(text)
    result: Dict[str, Dict[str, object]] = {}
    for lineno, raw in functions:
        name = extract_function_name(raw)
        window_start = max(0, lineno - 12)
        window = "\n".join(lines[window_start:lineno])
        has_help = "<#" in window and ".SYNOPSIS" in window and "#>" in window
        result[name] = {"line": lineno, "has_help": has_help}
    return result


def documentation_health(collector_text: str) -> Dict[str, object]:
    func_map = function_help_map(collector_text)
    documented = [name for name, meta in func_map.items() if meta["has_help"]]
    undocumented = [name for name, meta in func_map.items() if not meta["has_help"]]
    return {
        "file_comment_help_present": detect_file_help(collector_text),
        "function_count": len(func_map),
        "documented_function_count": len(documented),
        "undocumented_function_count": len(undocumented),
        "documented_functions": documented[:25],
        "undocumented_functions_sample": undocumented[:25],
    }


def build_repair_candidates(runtime_alias_ok: bool, harness_targets_runtime_alias: bool, marker_status: Dict[str, str], doc_health: Dict[str, object]) -> List[Dict[str, str]]:
    candidates: List[Dict[str, str]] = []
    if not runtime_alias_ok or not harness_targets_runtime_alias:
        candidates.append({
            "type": "code",
            "target": "collector alias or harness alias path",
            "reason": "Runtime alias rules are not fully aligned between manifest, layout, and harness mirrors.",
        })
    missing_markers = [k for k, v in marker_status.items() if v != "present"]
    if missing_markers:
        candidates.append({
            "type": "code",
            "target": "collector output contract",
            "reason": f"Missing output-contract markers: {', '.join(missing_markers)}.",
        })
    if not doc_health.get("file_comment_help_present"):
        candidates.append({
            "type": "documentation",
            "target": "collector file-level comment-based help",
            "reason": "Primary entry-point script lacks file-level comment-based help.",
        })
    if int(doc_health.get("undocumented_function_count", 0)) > 0:
        candidates.append({
            "type": "documentation",
            "target": "collector function maintenance cues",
            "reason": "One or more functions lack nearby comment-based help or concise maintenance cues.",
        })
    return candidates


def main() -> None:
    parser = argparse.ArgumentParser(description="Static audit for the DCOIR collector source line.")
    parser.add_argument("--collector", required=True)
    parser.add_argument("--tests-ps1", required=True)
    parser.add_argument("--tests-cmd")
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--layout-spec", required=True)
    parser.add_argument("--change-log")
    parser.add_argument("--todo-log")
    parser.add_argument("--rollback")
    parser.add_argument("--json-out")
    args = parser.parse_args()

    collector = Path(args.collector).resolve()
    tests_ps1 = Path(args.tests_ps1).resolve()
    tests_cmd = Path(args.tests_cmd).resolve() if args.tests_cmd else None
    manifest = Path(args.manifest).resolve()
    layout_spec = Path(args.layout_spec).resolve()
    change_log = Path(args.change_log).resolve() if args.change_log else None
    todo_log = Path(args.todo_log).resolve() if args.todo_log else None
    rollback = Path(args.rollback).resolve() if args.rollback else None

    collector_text = read_text(collector)
    tests_ps1_text = read_text(tests_ps1)
    tests_cmd_text = read_text(tests_cmd) if tests_cmd and tests_cmd.exists() else ""
    manifest_text = read_text(manifest)
    layout_text = read_text(layout_spec)

    suites = parse_suite_names(tests_ps1_text)
    markers = find_output_markers(collector_text)
    extracted = extract_cleanup_commands(collector_text)
    code_blocks = build_code_blocks(suites, extracted)

    contract = load_project_contract(manifest.parent.parent)
    alias_contract = contract.get('collector_runtime_alias_contract', {})
    runtime_alias_ok = all(token in manifest_text for token in alias_contract.get('manifest_required_strings', [])) and any(token in layout_text for token in alias_contract.get('layout_any_strings', []))

    runtime_alias = alias_contract.get('harness_runtime_alias', r'.\DCOIR_Collector.ps1')
    harness_targets_runtime_alias = runtime_alias in tests_ps1_text or runtime_alias in tests_cmd_text

    output_contract_status = {
        marker: ("present" if positions else "missing")
        for marker, positions in markers.items()
    }
    doc_health = documentation_health(collector_text)
    repair_candidates = build_repair_candidates(runtime_alias_ok, harness_targets_runtime_alias, output_contract_status, doc_health)

    findings = [
        "Static audit completed against the current readable collector and harness sources.",
        "Use runtime alias, output-contract, and documentation-health results to decide whether execution or repair can proceed confidently.",
    ]
    if not doc_health.get("file_comment_help_present"):
        findings.append("Collector file-level comment-based help is currently absent in the readable source.")

    result = {
        "skill_intent": "dcoir-collector-qa static audit",
        "sources": {
            "collector": build_source_record(collector, runtime_name="DCOIR_Collector.ps1"),
            "tests_ps1": build_source_record(tests_ps1, runtime_name="run_DCOIR_Tests.ps1"),
            "manifest": build_source_record(manifest),
            "layout_spec": build_source_record(layout_spec),
            "change_log": build_source_record(change_log) if change_log and change_log.exists() else None,
            "todo_log": build_source_record(todo_log) if todo_log and todo_log.exists() else None,
            "rollback": build_source_record(rollback) if rollback and rollback.exists() else None,
        },
        "runtime_alias": {
            "expected_runtime_filename": "DCOIR_Collector.ps1",
            "manifest_and_layout_support_alias": runtime_alias_ok,
            "harness_targets_runtime_alias": harness_targets_runtime_alias,
        },
        "harness": {
            "suite_names": suites,
        },
        "output_contract": {
            "marker_status": output_contract_status,
            "marker_line_numbers": markers,
            "extracted_examples": extracted,
        },
        "documentation_health": doc_health,
        "repair_candidates": repair_candidates,
        "maintenance_code_blocks": code_blocks,
        "known_failure_lane": {
            "name": "gemini-collector-transcript-error",
            "status": "placeholder-pending-exact-excerpt",
            "details": "Project memory preserves that a DCOIR_Collector.ps1 execution error occurred during Gemini collector testing under the GitHub-primary workflow; convert this lane into a concrete replay fixture when the exact failing excerpt is recovered.",
        },
        "findings": findings,
    }

    output = json.dumps(result, indent=2)
    if args.json_out:
        Path(args.json_out).write_text(output, encoding="utf-8")
    else:
        print(output)


if __name__ == "__main__":
    main()
