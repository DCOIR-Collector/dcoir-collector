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
JOB_USES_RE = re.compile(r"^  [A-Za-z0-9_-]+:\s*\n(?:    .*\n)*?    uses:\s*(\./\.github/workflows/[^\s#]+)", re.MULTILINE)
PERMISSION_ORDER = {"none": 0, "read": 1, "write": 2}
DOUBLE_QUOTED_EXPRESSION_LITERAL_RE = re.compile(r"\$\{\{[^}]*\|\|\s*\"[^\"]*\"[^}]*\}\}")
BARE_INPUT_FORWARD_RE = re.compile(r"\$\{\{\s*inputs\.[A-Za-z0-9_-]+\s*\}\}")


def strip_quotes(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]
    return value


def parse_workflow_call_contract(path: Path) -> tuple[set[str], set[str]]:
    lines = path.read_text(encoding="utf-8").splitlines()
    inputs: set[str] = set()
    secrets: set[str] = set()
    in_workflow_call = False
    section: str | None = None
    section_indent = 0
    for line in lines:
        stripped = line.strip()
        indent = len(line) - len(line.lstrip(" "))
        if stripped == "workflow_call:":
            in_workflow_call = True
            section = None
            continue
        if not in_workflow_call:
            continue
        if stripped in {"inputs:", "secrets:"}:
            section = stripped[:-1]
            section_indent = indent
            continue
        if section and stripped and indent <= section_indent:
            section = None
        if section in {"inputs", "secrets"} and indent == section_indent + 2 and stripped.endswith(":"):
            name = stripped[:-1].strip().strip("'\"")
            if name != "{}":
                (inputs if section == "inputs" else secrets).add(name)
    return inputs, secrets


def collect_mapping_after(lines: list[str], start_index: int, key: str) -> set[str]:
    names: set[str] = set()
    key_indent: int | None = None
    for index in range(start_index, len(lines)):
        line = lines[index]
        stripped = line.strip()
        indent = len(line) - len(line.lstrip(" "))
        if key_indent is None:
            if stripped == f"{key}:":
                key_indent = indent
            continue
        if stripped and indent <= key_indent:
            break
        if indent == key_indent + 2 and ":" in stripped:
            names.add(stripped.split(":", 1)[0].strip().strip("'\""))
    return names


def collect_mapping_values_after(lines: list[str], start_index: int, key: str) -> dict[str, str]:
    values: dict[str, str] = {}
    key_indent: int | None = None
    for index in range(start_index, len(lines)):
        line = lines[index]
        stripped = line.strip()
        indent = len(line) - len(line.lstrip(" "))
        if key_indent is None:
            if stripped == f"{key}:":
                key_indent = indent
            continue
        if stripped and indent <= key_indent:
            break
        if indent == key_indent + 2 and ":" in stripped:
            name, value = stripped.split(":", 1)
            values[name.strip().strip("'\"")] = strip_quotes(value.strip())
    return values


def find_mapping_headers(lines: list[str], key: str) -> list[int]:
    return [index for index, line in enumerate(lines) if line.strip() == f"{key}:"]


def permission_satisfies(actual: str | None, required: str) -> bool:
    if actual is None:
        return False
    actual_normalized = strip_quotes(actual).lower()
    required_normalized = required.lower()
    if actual_normalized in {"read-all", "write-all"}:
        return permission_satisfies(actual_normalized.split("-", 1)[0], required_normalized)
    return PERMISSION_ORDER.get(actual_normalized, -1) >= PERMISSION_ORDER[required_normalized]


def required_permissions_for_text(text: str) -> dict[str, str]:
    required: dict[str, str] = {}

    def require(scope: str, level: str) -> None:
        current = required.get(scope)
        if current is None or PERMISSION_ORDER[level] > PERMISSION_ORDER[current]:
            required[scope] = level

    uses_external_wiki_push_token = "DCOIR_WIKI_PUSH_TOKEN" in text and "wiki_url" in text
    if (
        "Invoke-ChatGptReportPush.ps1" in text
        or (re.search(r"\bgit\s+push\b", text) and not uses_external_wiki_push_token)
    ):
        require("contents", "write")
    if re.search(r"\bgh\s+pr\s+merge\b", text):
        require("contents", "write")
        require("pull-requests", "write")
    if "actions/download-artifact@" in text or re.search(r"\bgh\s+run\s+download\b", text):
        require("actions", "read")
    return required


def declares_workflow_call_github_token_secret(text: str) -> bool:
    in_workflow_call = False
    in_secrets = False
    secrets_indent = 0
    for line in text.splitlines():
        stripped = line.strip()
        indent = len(line) - len(line.lstrip(" "))
        if stripped == "workflow_call:":
            in_workflow_call = True
            in_secrets = False
            continue
        if not in_workflow_call:
            continue
        if stripped == "secrets:":
            in_secrets = True
            secrets_indent = indent
            continue
        if in_secrets:
            if stripped and indent <= secrets_indent:
                in_secrets = False
            elif indent == secrets_indent + 2 and stripped.startswith("GITHUB_TOKEN:"):
                return True
    return False


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


def iter_all_workflow_files(repo_root: Path) -> list[Path]:
    workflow_dir = repo_root / WORKFLOW_DIR
    if not workflow_dir.exists():
        return []
    return sorted(
        path for path in workflow_dir.iterdir()
        if path.is_file() and path.suffix.lower() in {".yml", ".yaml"}
    )


def local_uses_refs(source_files: list[Path]) -> tuple[list[tuple[Path, int, str]], list[tuple[Path, int, str]], list[tuple[Path, int, str]]]:
    workflow_refs: list[tuple[Path, int, str]] = []
    action_refs: list[tuple[Path, int, str]] = []
    other_local_refs: list[tuple[Path, int, str]] = []
    for source_file in source_files:
        for line_no, line in enumerate(source_file.read_text(encoding="utf-8").splitlines(), start=1):
            match = USES_RE.match(line)
            if not match:
                continue
            ref = strip_quotes(match.group(1))
            if ref.startswith("./.github/workflows/"):
                workflow_refs.append((source_file, line_no, ref))
            elif ref.startswith("./.github/actions/"):
                action_refs.append((source_file, line_no, ref))
            elif ref.startswith("./"):
                other_local_refs.append((source_file, line_no, ref))
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
        if is_reusable_name:
            required_permissions = required_permissions_for_text(text)
            if required_permissions:
                lines = text.splitlines()
                top_permissions = collect_mapping_values_after(lines, 0, "permissions")
                for scope, level in sorted(required_permissions.items()):
                    if not permission_satisfies(top_permissions.get(scope), level):
                        actual = top_permissions.get(scope, "<missing>")
                        findings.append(
                            f"{workflow_rel}:1: reusable workflow uses write/read-capable operations "
                            f"but top-level permissions.{scope} is {actual}; expected at least {level}"
                        )
                for header_index in find_mapping_headers(lines, "permissions"):
                    indent = len(lines[header_index]) - len(lines[header_index].lstrip(" "))
                    if indent <= 0:
                        continue
                    permission_block = collect_mapping_values_after(lines, header_index, "permissions")
                    for scope, level in sorted(required_permissions.items()):
                        if not permission_satisfies(permission_block.get(scope), level):
                            actual = permission_block.get(scope, "<missing>")
                            findings.append(
                                f"{workflow_rel}:{header_index + 1}: job-level permissions.{scope} is {actual}; "
                                f"expected at least {level} because this reusable workflow uses write/read-capable operations"
                            )
        if DOUBLE_QUOTED_EXPRESSION_LITERAL_RE.search(text):
            findings.append(
                f"{workflow_rel}:1: GitHub expressions must use single-quoted string literals; "
                "double-quoted fallback literals can make the workflow invalid"
            )
        if "secrets.GITHUB_TOKEN" in text:
            findings.append(
                f"{workflow_rel}:1: do not pass or reference secrets.GITHUB_TOKEN explicitly in reusable workflow plumbing; "
                "use github.token inside the called workflow"
            )
        if declares_workflow_call_github_token_secret(text):
            findings.append(
                f"{workflow_rel}:1: reusable workflow callees must not declare GITHUB_TOKEN as an explicit workflow_call secret"
            )
        if not is_reusable_name and "uses: ./.github/workflows/" in text and BARE_INPUT_FORWARD_RE.search(text):
            findings.append(
                f"{workflow_rel}:1: entry workflow forwards bare inputs.* to a reusable workflow; "
                "multi-trigger callers must provide explicit non-dispatch fallbacks"
            )


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
        declared_inputs, declared_secrets = parse_workflow_call_contract(target)
        lines = source_path.read_text(encoding="utf-8").splitlines()
        passed_inputs = collect_mapping_after(lines, line_no - 1, "with")
        passed_secrets = collect_mapping_after(lines, line_no - 1, "secrets")
        for input_name in sorted(passed_inputs - declared_inputs):
            findings.append(f"{source_rel}:{line_no}: caller passes undeclared reusable-workflow input {input_name}: {ref}")
        for secret_name in sorted(passed_secrets - declared_secrets):
            findings.append(f"{source_rel}:{line_no}: caller passes undeclared reusable-workflow secret {secret_name}: {ref}")


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
    primary_workflow_files = iter_workflow_files()
    workflow_files = iter_all_workflow_files(repo_root)
    findings: list[str] = []
    if not workflow_files:
        findings.append(f"{WORKFLOW_DIR.as_posix()}:1: no workflow files found")
    else:
        check_reusable_workflows(repo_root, workflow_files, findings)
        action_metadata_files = iter_action_metadata_files(repo_root)
        workflow_refs, workflow_action_refs, workflow_other_local_refs = local_uses_refs(workflow_files)
        action_workflow_refs, action_refs, action_other_local_refs = local_uses_refs(action_metadata_files)
        action_refs = workflow_action_refs + action_refs
        check_local_workflow_calls(repo_root, workflow_refs, findings)
        check_local_action_calls(repo_root, action_refs, findings)
        check_action_definitions(repo_root, findings)
        for source_path, line_no, ref in action_workflow_refs:
            findings.append(
                f"{rel(source_path, repo_root)}:{line_no}: composite actions must not call reusable workflows: {ref}"
            )
        for source_path, line_no, ref in workflow_other_local_refs + action_other_local_refs:
            findings.append(
                f"{rel(source_path, repo_root)}:{line_no}: unsupported local uses target; "
                f"use ./.github/workflows/reusable-* or ./.github/actions/* only: {ref}"
            )

        for workflow_file in workflow_files:
            lines = workflow_file.read_text(encoding="utf-8").splitlines()
            checkout_seen = False
            for line_no, line in enumerate(lines, start=1):
                stripped = line.strip()
                if stripped.startswith("uses: actions/checkout@"):
                    checkout_seen = True
                if stripped.startswith("uses: ./.github/actions/") and not checkout_seen:
                    findings.append(
                        f"{rel(workflow_file, repo_root)}:{line_no}: local composite action is used before checkout"
                    )

    check_inventory(repo_root, findings)

    if findings:
        print("Reusable/composite contract audit failed:")
        for finding in findings:
            print(f"- {finding}")
        return 1

    action_metadata_files = iter_action_metadata_files(repo_root)
    workflow_refs, workflow_action_refs, _ = local_uses_refs(workflow_files)
    _, composite_action_refs, _ = local_uses_refs(action_metadata_files)
    action_refs = workflow_action_refs + composite_action_refs
    reusable_count = sum(1 for path in workflow_files if "workflow_call:" in path.read_text(encoding="utf-8"))
    action_definition_count = len(iter_action_metadata_files(repo_root))
    print(
        "Reusable/composite contract audit passed: "
        f"{len(primary_workflow_files)} primary workflows, "
        f"{reusable_count} reusable workflow definitions, "
        f"{len(workflow_refs)} local reusable workflow calls, "
        f"{action_definition_count} local action definitions, "
        f"{len(action_refs)} local action calls "
        f"({len(workflow_action_refs)} from workflows, {len(composite_action_refs)} from composite actions)."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
