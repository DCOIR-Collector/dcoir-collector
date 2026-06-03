#!/usr/bin/env python3
"""Audit local reusable workflow and composite action contracts.

This is intentionally a contract scaffold. It validates the current baseline and
will catch unsafe partial migrations when later issue #194 slices introduce
`workflow_call` workflows or `.github/actions` composite actions.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

from build_workflow_inventory import (
    DEFAULT_JSON_OUTPUT,
    DEFAULT_MARKDOWN_OUTPUT,
    build_inventory,
    check_outputs,
    iter_workflow_files,
)

WORKFLOW_DIR = Path(".github/workflows")
ACTION_DIR = Path(".github/actions")
EXPECTED_PRIMARY_WORKFLOW_COUNT = 29

USES_RE = re.compile(r"^\s*uses:\s*([^\s#]+)", re.IGNORECASE)
COMPOSITE_USING_RE = re.compile(r"^\s*using:\s*['\"]?composite['\"]?\s*$", re.IGNORECASE | re.MULTILINE)


def strip_quotes(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]
    return value


def rel(path: Path, repo_root: Path) -> str:
    if path.is_absolute():
        return path.relative_to(repo_root).as_posix()
    return path.as_posix()


def iter_action_metadata_files(repo_root: Path) -> list[Path]:
    action_dir = repo_root / ACTION_DIR
    if not action_dir.exists():
        return []
    return sorted(
        path for path in action_dir.rglob("*")
        if path.is_file() and path.name.lower() in {"action.yml", "action.yaml"}
    )


def local_uses_refs(workflow_files: list[Path]) -> tuple[list[tuple[Path, int, str]], list[tuple[Path, int, str]], list[tuple[Path, int, str]]]:
    workflow_refs: list[tuple[Path, int, str]] = []
    action_refs: list[tuple[Path, int, str]] = []
    other_local_refs: list[tuple[Path, int, str]] = []
    for workflow_file in workflow_files:
        for line_no, line in enumerate(workflow_file.read_text(encoding="utf-8").splitlines(), start=1):
            match = USES_RE.match(line)
            if not match:
                continue
            ref = strip_quotes(match.group(1))
            if ref.startswith("./.github/workflows/"):
                workflow_refs.append((workflow_file, line_no, ref))
            elif ref.startswith("./.github/actions/"):
                action_refs.append((workflow_file, line_no, ref))
            elif ref.startswith("./"):
                other_local_refs.append((workflow_file, line_no, ref))
    return workflow_refs, action_refs, other_local_refs


def check_inventory(repo_root: Path, findings: list[str]) -> None:
    inventory = build_inventory()
    findings.extend(check_outputs(inventory, repo_root / DEFAULT_JSON_OUTPUT, repo_root / DEFAULT_MARKDOWN_OUTPUT))


def check_reusable_workflows(repo_root: Path, workflow_files: list[Path], findings: list[str]) -> None:
    primary_workflows = [path for path in workflow_files if not path.name.startswith("reusable-")]
    if len(primary_workflows) != EXPECTED_PRIMARY_WORKFLOW_COUNT:
        findings.append(
            f"{WORKFLOW_DIR.as_posix()}:1: expected {EXPECTED_PRIMARY_WORKFLOW_COUNT} primary workflows, "
            f"found {len(primary_workflows)}"
        )

    for workflow_file in workflow_files:
        text = workflow_file.read_text(encoding="utf-8")
        has_workflow_call = "workflow_call:" in text
        is_reusable_name = workflow_file.name.startswith("reusable-")
        workflow_rel = rel(workflow_file, repo_root)
        if has_workflow_call and not is_reusable_name:
            findings.append(f"{workflow_rel}:1: workflow_call definitions must use reusable-*.yml naming")
        if is_reusable_name and not has_workflow_call:
            findings.append(f"{workflow_rel}:1: reusable-* workflow file is missing on.workflow_call")
        if is_reusable_name and "pull_request:" in text:
            findings.append(f"{workflow_rel}:1: reusable workflow must not also define pull_request triggers")
        if is_reusable_name and "push:" in text:
            findings.append(f"{workflow_rel}:1: reusable workflow must not also define push triggers")


def check_local_workflow_calls(
    repo_root: Path,
    workflow_refs: list[tuple[Path, int, str]],
    findings: list[str],
) -> None:
    for source_path, line_no, ref in workflow_refs:
        target_ref = ref.split("@", 1)[0]
        target = repo_root / target_ref.removeprefix("./")
        source_rel = rel(source_path, repo_root)
        if not target.is_file():
            findings.append(f"{source_rel}:{line_no}: local reusable workflow target does not exist: {ref}")
            continue
        if not target.name.startswith("reusable-"):
            findings.append(f"{source_rel}:{line_no}: local workflow call target must be reusable-*.yml: {ref}")
        if "workflow_call:" not in target.read_text(encoding="utf-8"):
            findings.append(f"{source_rel}:{line_no}: local workflow call target is missing workflow_call: {ref}")


def check_local_action_calls(
    repo_root: Path,
    action_refs: list[tuple[Path, int, str]],
    findings: list[str],
) -> None:
    for source_path, line_no, ref in action_refs:
        target_ref = ref.split("@", 1)[0]
        target = repo_root / target_ref.removeprefix("./")
        source_rel = rel(source_path, repo_root)
        action_file = target / "action.yml"
        action_file_yaml = target / "action.yaml"
        if not action_file.is_file() and not action_file_yaml.is_file():
            findings.append(f"{source_rel}:{line_no}: local action target has no action.yml/action.yaml: {ref}")


def check_action_definitions(repo_root: Path, findings: list[str]) -> None:
    for action_file in iter_action_metadata_files(repo_root):
        text = action_file.read_text(encoding="utf-8")
        action_rel = rel(action_file, repo_root)
        if not COMPOSITE_USING_RE.search(text):
            findings.append(f"{action_rel}:1: .github/actions metadata must declare runs.using: composite")
        readme = action_file.parent / "README.md"
        if not readme.is_file():
            findings.append(f"{action_rel}:1: local composite action is missing sibling README.md contract notes")


def main() -> int:
    repo_root = Path(".").resolve()
    workflow_files = iter_workflow_files()
    findings: list[str] = []
    if not workflow_files:
        findings.append(f"{WORKFLOW_DIR.as_posix()}:1: no workflow files found")
    else:
        check_reusable_workflows(repo_root, workflow_files, findings)
        workflow_refs, action_refs, other_local_refs = local_uses_refs(workflow_files)
        check_local_workflow_calls(repo_root, workflow_refs, findings)
        check_local_action_calls(repo_root, action_refs, findings)
        check_action_definitions(repo_root, findings)
        for source_path, line_no, ref in other_local_refs:
            findings.append(
                f"{rel(source_path, repo_root)}:{line_no}: unsupported local uses target; "
                f"use ./.github/workflows/reusable-* or ./.github/actions/* only: {ref}"
            )

    check_inventory(repo_root, findings)

    if findings:
        print("Reusable/composite contract audit failed:")
        for finding in findings:
            print(f"- {finding}")
        return 1

    workflow_refs, action_refs, _ = local_uses_refs(workflow_files)
    reusable_count = sum(1 for path in workflow_files if "workflow_call:" in path.read_text(encoding="utf-8"))
    action_definition_count = len(iter_action_metadata_files(repo_root))
    print(
        "Reusable/composite contract audit passed: "
        f"{len([p for p in workflow_files if not p.name.startswith('reusable-')])} primary workflows, "
        f"{reusable_count} reusable workflow definitions, "
        f"{len(workflow_refs)} local reusable workflow calls, "
        f"{action_definition_count} local action definitions, "
        f"{len(action_refs)} local action calls."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
