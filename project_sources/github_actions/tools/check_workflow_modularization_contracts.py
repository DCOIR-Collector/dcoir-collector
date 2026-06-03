#!/usr/bin/env python3
"""Audit issue #194 workflow modularization contracts."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

WORKFLOW_DIR = Path(".github/workflows")
ACTION_DIR = Path(".github/actions")
CONTRACT_PATH = Path("project_sources/github_actions/workflow_modularization_contracts.json")
INVENTORY_PATH = Path("project_sources/github_actions/workflow_inventory.json")
REPORTER_PATH = Path(".github/workflows/chatgpt-workflow-run-reporter.yml")

REQUIRED_CONTRACT_FIELDS = [
    "file",
    "family",
    "contract_family",
    "target_architecture",
    "migration_status",
    "risk",
    "rollback",
    "acceptance_evidence",
]

ALLOWED_MIGRATION_STATUS = {"planned", "foundation", "active", "intentionally-inline"}
ALLOWED_RISK = {"low", "medium", "high"}
GENERIC_REUSABLE_NAMES = {"reusable.yml", "reusable-workflow.yml", "shared.yml", "common.yml", "generic.yml"}
REQUIRED_HEADER_MARKERS = [
    "# DCOIR WORKFLOW OPERATOR NOTES",
    "# Workflow key:",
    "# Purpose:",
    "# Use when:",
    "# Do not use when:",
    "# Trigger model:",
    "# Required inputs:",
    "# Required secrets/config:",
    "# Runtime dependencies:",
    "# Expected outputs/readback:",
    "# Safety notes:",
    "# Maintenance notes:",
    "# Authority routing:",
]


def iter_workflow_files() -> list[Path]:
    if not WORKFLOW_DIR.exists():
        return []
    return sorted(
        path for path in WORKFLOW_DIR.iterdir()
        if path.is_file() and path.suffix.lower() in {".yml", ".yaml"}
    )


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def ensure_exists(findings: list[str], path: Path) -> bool:
    if path.exists():
        return True
    findings.append(f"{path}:1: required workflow modularization surface is missing")
    return False


def check_contract_registry(findings: list[str], contracts: dict[str, Any], workflow_files: list[Path]) -> None:
    expected_count = contracts.get("existing_workflow_count")
    if expected_count != len(workflow_files):
        findings.append(
            f"{CONTRACT_PATH}:1: existing_workflow_count is {expected_count}, but {len(workflow_files)} workflow files were found"
        )

    required_families = set(contracts.get("required_contract_families", []))
    workflow_contracts = contracts.get("workflow_contracts", [])
    if not isinstance(workflow_contracts, list):
        findings.append(f"{CONTRACT_PATH}:1: workflow_contracts must be a list")
        return

    actual_files = {path.as_posix() for path in workflow_files}
    contracted_files: set[str] = set()
    contracted_families: set[str] = set()

    for index, entry in enumerate(workflow_contracts, start=1):
        if not isinstance(entry, dict):
            findings.append(f"{CONTRACT_PATH}:workflow_contracts[{index}]: entry must be an object")
            continue
        for field in REQUIRED_CONTRACT_FIELDS:
            if not entry.get(field):
                findings.append(f"{CONTRACT_PATH}:workflow_contracts[{index}]: missing required field {field}")
        file_name = entry.get("file")
        if file_name:
            contracted_files.add(file_name)
            if file_name not in actual_files:
                findings.append(f"{CONTRACT_PATH}:workflow_contracts[{index}]: contract references missing workflow {file_name}")
        family = entry.get("contract_family")
        if family:
            contracted_families.add(family)
        status = entry.get("migration_status")
        if status and status not in ALLOWED_MIGRATION_STATUS:
            findings.append(f"{CONTRACT_PATH}:workflow_contracts[{index}]: unsupported migration_status {status}")
        risk = entry.get("risk")
        if risk and risk not in ALLOWED_RISK:
            findings.append(f"{CONTRACT_PATH}:workflow_contracts[{index}]: unsupported risk {risk}")

    for missing_file in sorted(actual_files - contracted_files):
        findings.append(f"{CONTRACT_PATH}:1: workflow missing modularization contract: {missing_file}")
    for missing_family in sorted(required_families - contracted_families):
        findings.append(f"{CONTRACT_PATH}:1: required contract family is not mapped by any workflow: {missing_family}")


def check_inventory(findings: list[str], contracts: dict[str, Any], workflow_files: list[Path]) -> None:
    if not ensure_exists(findings, INVENTORY_PATH):
        return
    inventory = load_json(INVENTORY_PATH)
    workflows = inventory.get("workflows", [])
    if len(workflows) != len(workflow_files):
        findings.append(f"{INVENTORY_PATH}:1: inventory has {len(workflows)} workflows, expected {len(workflow_files)}")
    expected_files = {path.as_posix() for path in workflow_files}
    inventoried_files = {entry.get("file") for entry in workflows if isinstance(entry, dict)}
    for missing_file in sorted(expected_files - inventoried_files):
        findings.append(f"{INVENTORY_PATH}:1: workflow missing from generated inventory: {missing_file}")
    contract_by_file = {entry["file"]: entry for entry in contracts.get("workflow_contracts", []) if isinstance(entry, dict) and entry.get("file")}
    for entry in workflows:
        if not isinstance(entry, dict):
            continue
        file_name = entry.get("file")
        contract = contract_by_file.get(file_name, {})
        for field in ("contract_family", "migration_status", "risk"):
            if entry.get(field) != contract.get(field):
                findings.append(f"{INVENTORY_PATH}:1: inventory field {field} is stale for {file_name}")


def check_reusable_workflows(findings: list[str], workflow_files: list[Path]) -> None:
    for path in workflow_files:
        text = path.read_text(encoding="utf-8")
        if "workflow_call:" not in text:
            continue
        if not path.name.startswith("reusable-"):
            findings.append(f"{path}:1: reusable workflow filename must start with reusable-")
        if path.name in GENERIC_REUSABLE_NAMES:
            findings.append(f"{path}:1: generic reusable workflow filename is not allowed")
        if re.search(r"secrets:\s*inherit", text):
            findings.append(f"{path}:1: broad secrets inheritance is not allowed without explicit approval/readback")
        for required in ("inputs:", "outputs:", "permissions:"):
            if required not in text:
                findings.append(f"{path}:1: reusable workflow is missing visible {required.rstrip(':')} contract")


def check_workflow_headers(findings: list[str], workflow_files: list[Path]) -> None:
    for path in workflow_files:
        text = path.read_text(encoding="utf-8")
        if "workflow_call:" in text:
            continue
        header = "\n".join(text.splitlines()[:45])
        for marker in REQUIRED_HEADER_MARKERS:
            if marker not in header:
                findings.append(f"{path}:1: missing workflow operator header marker: {marker}")


def check_reporter_allowlist(findings: list[str], contracts: dict[str, Any]) -> None:
    if not ensure_exists(findings, REPORTER_PATH):
        return
    lines = REPORTER_PATH.read_text(encoding="utf-8").splitlines()
    allowlist: set[str] = set()
    in_workflows = False
    workflows_indent = 0
    for line in lines:
        stripped = line.strip()
        if stripped == "workflows:":
            in_workflows = True
            workflows_indent = len(line) - len(line.lstrip())
            continue
        if in_workflows:
            indent = len(line) - len(line.lstrip())
            if stripped and indent <= workflows_indent:
                break
            if stripped.startswith("- "):
                allowlist.add(stripped[2:].strip().strip("'\""))
    for entry in contracts.get("workflow_contracts", []):
        if not isinstance(entry, dict):
            continue
        file_name = entry.get("file")
        if not file_name:
            continue
        path = Path(file_name)
        if not path.exists():
            continue
        workflow_name = None
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.startswith("name:"):
                workflow_name = line.split(":", 1)[1].strip().strip("'\"")
                break
        if not workflow_name or workflow_name == "chatgpt-workflow-run-reporter":
            continue
        if entry.get("migration_status") in {"planned", "foundation", "active"} and workflow_name not in allowlist:
            findings.append(f"{REPORTER_PATH}:1: reporter allowlist missing workflow name from contract registry: {workflow_name}")


def check_composite_actions(findings: list[str]) -> None:
    if not ACTION_DIR.exists():
        return
    for child in sorted(ACTION_DIR.iterdir()):
        if not child.is_dir():
            continue
        action_file = child / "action.yml"
        if not action_file.exists():
            findings.append(f"{child}:1: composite action directory missing action.yml")
            continue
        text = action_file.read_text(encoding="utf-8")
        if "runs:" not in text or "using: composite" not in text:
            findings.append(f"{action_file}:1: action.yml must declare runs using composite")
        if "Compensating evidence" not in text:
            findings.append(f"{action_file}:1: composite action must document compensating evidence for reduced caller log granularity")
        if re.search(r"secrets\.", text):
            findings.append(f"{action_file}:1: composite action must not directly reference secrets.*")
        forbidden_terms = ["rm -rf", "git push", "gh pr merge"]
        for term in forbidden_terms:
            if term in text:
                findings.append(f"{action_file}:1: composite action contains safety-sensitive command text: {term}")


def main() -> int:
    findings: list[str] = []
    if not ensure_exists(findings, CONTRACT_PATH):
        print("Workflow modularization contract audit failed:")
        for finding in findings:
            print(f"- {finding}")
        return 1

    workflow_files = iter_workflow_files()
    contracts = load_json(CONTRACT_PATH)
    check_contract_registry(findings, contracts, workflow_files)
    check_inventory(findings, contracts, workflow_files)
    check_reusable_workflows(findings, workflow_files)
    check_workflow_headers(findings, workflow_files)
    check_reporter_allowlist(findings, contracts)
    check_composite_actions(findings)

    if findings:
        print("Workflow modularization contract audit failed:")
        for finding in findings:
            print(f"- {finding}")
        return 1

    print(
        "Workflow modularization contract audit passed for "
        f"{len(workflow_files)} workflow files and "
        f"{len(contracts.get('workflow_contracts', []))} contracts."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
