#!/usr/bin/env python3
"""Build the DCOIR GitHub workflow inventory and contract matrix.

This parser intentionally avoids external YAML dependencies so it can run in
the same minimal GitHub Actions environment as the existing workflow audits.
It extracts contract-relevant facts conservatively from workflow text and joins
them to the issue #194 modularization contract registry.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

WORKFLOW_DIR = Path(".github/workflows")
CONTRACT_PATH = Path("project_sources/github_actions/workflow_modularization_contracts.json")
DEFAULT_JSON_OUTPUT = Path("project_sources/github_actions/workflow_inventory.json")
DEFAULT_MARKDOWN_OUTPUT = Path("project_sources/github_actions/workflow_inventory.md")

SECRET_RE = re.compile(r"(?:secrets|vars)\.([A-Za-z_][A-Za-z0-9_]*)")
USES_RE = re.compile(r"^\s*uses:\s*([^\s#]+)", re.IGNORECASE)
SCRIPT_RE = re.compile(
    r"((?:\.github/scripts|project_sources/github_actions/tools|ops/tools|tools)/[A-Za-z0-9_./-]+\.(?:py|ps1|psm1|json))"
)
SCHEDULE_RE = re.compile(r"cron:\s*['\"]?([^'\"]+)")


def read_contracts() -> dict[str, Any]:
    return json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))


def iter_workflow_files() -> list[Path]:
    if not WORKFLOW_DIR.exists():
        return []
    return sorted(
        path for path in WORKFLOW_DIR.iterdir()
        if path.is_file() and path.suffix.lower() in {".yml", ".yaml"}
    )


def top_level_key(line: str) -> str | None:
    if not line or line.startswith((" ", "\t", "#")):
        return None
    if ":" not in line:
        return None
    return line.split(":", 1)[0].strip()


def scalar_after_colon(line: str) -> str | None:
    if ":" not in line:
        return None
    value = line.split(":", 1)[1].strip()
    if not value:
        return None
    return value.strip("'\"")


def collect_top_level_block(lines: list[str], key: str) -> list[str]:
    block: list[str] = []
    in_block = False
    for line in lines:
        current_key = top_level_key(line)
        if current_key == key:
            in_block = True
            block.append(line)
            continue
        if in_block and current_key is not None:
            break
        if in_block:
            block.append(line)
    return block


def collect_header(lines: list[str]) -> list[str]:
    header: list[str] = []
    for line in lines:
        if line.startswith("#") or not line.strip():
            header.append(line)
            continue
        break
    return header


def extract_header_field(header: list[str], field: str) -> str | None:
    marker = f"# {field}:"
    for index, line in enumerate(header):
        if line.strip() == marker:
            values: list[str] = []
            for follow in header[index + 1:]:
                stripped = follow.strip()
                if stripped.startswith("# - "):
                    values.append(stripped[4:].strip())
                    continue
                if stripped.startswith("#") and stripped.endswith(":"):
                    break
                if stripped and not stripped.startswith("#"):
                    break
            return "; ".join(values) if values else None
    return None


def extract_triggers(lines: list[str]) -> dict[str, Any]:
    block = collect_top_level_block(lines, "on")
    triggers: set[str] = set()
    schedules: list[str] = []
    if not block:
        return {"events": [], "schedules": []}
    first_value = scalar_after_colon(block[0])
    if first_value:
        if first_value.startswith("[") and first_value.endswith("]"):
            for item in first_value.strip("[]").split(","):
                candidate = item.strip().strip("'\"")
                if candidate:
                    triggers.add(candidate)
        else:
            triggers.add(first_value)
    for line in block[1:]:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if line.startswith("  ") and not line.startswith("    ") and stripped.startswith("- "):
            candidate = stripped[2:].split(":", 1)[0].strip()
            if candidate and candidate != "cron":
                triggers.add(candidate)
        elif line.startswith("  ") and not line.startswith("    ") and stripped.endswith(":"):
            candidate = stripped[:-1].strip()
            if candidate and candidate != "cron":
                triggers.add(candidate)
        elif line.startswith("  ") and not line.startswith("    ") and ":" in stripped:
            candidate = stripped.split(":", 1)[0].strip()
            if candidate and candidate != "cron":
                triggers.add(candidate)
        cron_match = SCHEDULE_RE.search(stripped)
        if cron_match:
            schedules.append(cron_match.group(1))
    return {"events": sorted(triggers), "schedules": sorted(set(schedules))}


def extract_permissions(lines: list[str]) -> dict[str, str] | str | None:
    block = collect_top_level_block(lines, "permissions")
    if not block:
        return None
    first_value = scalar_after_colon(block[0])
    if first_value:
        return first_value
    permissions: dict[str, str] = {}
    for line in block[1:]:
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or ":" not in stripped:
            continue
        name, value = stripped.split(":", 1)
        permissions[name.strip()] = value.strip().strip("'\"")
    return permissions or None


def extract_jobs(lines: list[str]) -> list[str]:
    block = collect_top_level_block(lines, "jobs")
    jobs: list[str] = []
    for line in block[1:]:
        if line.startswith("  ") and not line.startswith("    ") and ":" in line:
            key = line.strip().split(":", 1)[0]
            if key and not key.startswith(("-", "$")):
                jobs.append(key)
    return jobs


def extract_artifact_names(lines: list[str]) -> list[str]:
    artifacts: set[str] = set()
    for index, line in enumerate(lines):
        if "actions/upload-artifact" not in line and "actions/download-artifact" not in line:
            continue
        for follow in lines[index + 1:index + 12]:
            stripped = follow.strip()
            if stripped.startswith("name:"):
                value = stripped.split(":", 1)[1].strip().strip("'\"")
                if value:
                    artifacts.add(value)
                break
    return sorted(artifacts)


def classify_report_family(path: Path, text: str) -> str:
    if "chatgpt_staging/status_reports/repo-workflows/" in text:
        return "repo-workflows completed summary"
    if "latest_progress_marker.json" in text or "progress_history.jsonl" in text:
        return "live heartbeat"
    if "chatgpt-workflow-report-section" in text:
        return "chatgpt workflow report section"
    if "workflow_report.md" in text:
        return "standalone workflow report"
    if path.name.startswith("ops-"):
        return "central reporter only when applicable"
    return "none declared"


def workflow_entry(path: Path, contract_by_file: dict[str, dict[str, Any]]) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    header = collect_header(lines)
    contract = contract_by_file.get(path.as_posix(), {})
    uses = sorted({USES_RE.match(line).group(1).strip().strip("'\"") for line in lines if USES_RE.match(line)})
    scripts = sorted({match.group(1) for match in SCRIPT_RE.finditer(text)})
    secrets = sorted({match.group(1) for match in SECRET_RE.finditer(text)})
    trigger_info = extract_triggers(lines)
    return {
        "file": path.as_posix(),
        "workflow_name": next(
            (scalar_after_colon(line) for line in lines if top_level_key(line) == "name"),
            None,
        ),
        "operator_purpose": extract_header_field(header, "Purpose"),
        "trigger_events": trigger_info["events"],
        "schedules": trigger_info["schedules"],
        "permissions": extract_permissions(lines),
        "concurrency_declared": bool(collect_top_level_block(lines, "concurrency")),
        "jobs": extract_jobs(lines),
        "secrets_or_vars": secrets,
        "actions_used": uses,
        "artifact_names": extract_artifact_names(lines),
        "scripts_and_tools": scripts,
        "report_family": classify_report_family(path, text),
        "contract_family": contract.get("contract_family"),
        "target_architecture": contract.get("target_architecture"),
        "migration_status": contract.get("migration_status"),
        "risk": contract.get("risk"),
        "rollback": contract.get("rollback"),
        "acceptance_evidence": contract.get("acceptance_evidence"),
    }


def build_inventory() -> dict[str, Any]:
    contracts = read_contracts()
    contract_by_file = {
        entry["file"]: entry
        for entry in contracts.get("workflow_contracts", [])
    }
    workflows = [workflow_entry(path, contract_by_file) for path in iter_workflow_files()]
    return {
        "schema_version": "dcoir_workflow_inventory_v1",
        "governing_issue": contracts.get("governing_issue"),
        "existing_workflow_count_expected": contracts.get("existing_workflow_count"),
        "workflow_count": len(workflows),
        "contract_registry": CONTRACT_PATH.as_posix(),
        "workflows": workflows,
    }


def markdown_value(value: Any) -> str:
    if value is None or value == [] or value == {}:
        return "none"
    if isinstance(value, dict):
        return ", ".join(f"{key}:{item}" for key, item in value.items())
    if isinstance(value, list):
        return ", ".join(str(item) for item in value) or "none"
    return str(value)


def render_markdown(inventory: dict[str, Any]) -> str:
    lines = [
        "# DCOIR GitHub Workflow Inventory",
        "",
        f"- schema_version: `{inventory['schema_version']}`",
        f"- governing_issue: `#{inventory['governing_issue']}`",
        f"- workflow_count: `{inventory['workflow_count']}`",
        f"- contract_registry: `{inventory['contract_registry']}`",
        "",
        "This inventory is generated by `project_sources/github_actions/tools/build_workflow_inventory.py`.",
        "Regenerate it after workflow, reusable workflow, composite action, report, or workflow-tooling changes.",
        "",
        "| File | Workflow name | Triggers | Permissions | Secrets/vars | Report family | Contract family | Status | Risk |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for item in inventory["workflows"]:
        lines.append(
            "| {file} | {name} | {triggers} | {permissions} | {secrets} | {report} | {contract} | {status} | {risk} |".format(
                file=f"`{item['file']}`",
                name=markdown_value(item["workflow_name"]),
                triggers=markdown_value(item["trigger_events"]),
                permissions=markdown_value(item["permissions"]),
                secrets=markdown_value(item["secrets_or_vars"]),
                report=markdown_value(item["report_family"]),
                contract=markdown_value(item["contract_family"]),
                status=markdown_value(item["migration_status"]),
                risk=markdown_value(item["risk"]),
            )
        )
    lines.extend(["", "## Contract Matrix", ""])
    for item in inventory["workflows"]:
        lines.extend([
            f"### {item['file']}",
            "",
            f"- workflow_name: `{markdown_value(item['workflow_name'])}`",
            f"- jobs: `{markdown_value(item['jobs'])}`",
            f"- schedules: `{markdown_value(item['schedules'])}`",
            f"- concurrency_declared: `{item['concurrency_declared']}`",
            f"- artifact_names: `{markdown_value(item['artifact_names'])}`",
            f"- scripts_and_tools: `{markdown_value(item['scripts_and_tools'])}`",
            f"- target_architecture: {markdown_value(item['target_architecture'])}",
            f"- rollback: {markdown_value(item['rollback'])}",
            f"- acceptance_evidence: {markdown_value(item['acceptance_evidence'])}",
            "",
        ])
    return "\n".join(lines).rstrip() + "\n"


def write_outputs(inventory: dict[str, Any], json_output: Path, markdown_output: Path) -> None:
    json_output.write_text(json.dumps(inventory, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    markdown_output.write_text(render_markdown(inventory), encoding="utf-8")


def check_outputs(inventory: dict[str, Any], json_output: Path, markdown_output: Path) -> list[str]:
    findings: list[str] = []
    expected_json = json.dumps(inventory, indent=2, sort_keys=True) + "\n"
    expected_markdown = render_markdown(inventory)
    if not json_output.exists():
        findings.append(f"{json_output}:1: generated workflow inventory JSON is missing")
    elif json_output.read_text(encoding="utf-8") != expected_json:
        findings.append(f"{json_output}:1: generated workflow inventory JSON is stale; rerun build_workflow_inventory.py")
    if not markdown_output.exists():
        findings.append(f"{markdown_output}:1: generated workflow inventory Markdown is missing")
    elif markdown_output.read_text(encoding="utf-8") != expected_markdown:
        findings.append(f"{markdown_output}:1: generated workflow inventory Markdown is stale; rerun build_workflow_inventory.py")
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json-output", type=Path, default=DEFAULT_JSON_OUTPUT)
    parser.add_argument("--markdown-output", type=Path, default=DEFAULT_MARKDOWN_OUTPUT)
    parser.add_argument("--check", action="store_true", help="fail when generated outputs are missing or stale")
    args = parser.parse_args()

    inventory = build_inventory()
    if args.check:
        findings = check_outputs(inventory, args.json_output, args.markdown_output)
        if findings:
            print("Workflow inventory check failed:")
            for finding in findings:
                print(f"- {finding}")
            return 1
        print(f"Workflow inventory check passed for {inventory['workflow_count']} workflow files.")
        return 0

    write_outputs(inventory, args.json_output, args.markdown_output)
    print(f"Wrote workflow inventory for {inventory['workflow_count']} workflow files.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
