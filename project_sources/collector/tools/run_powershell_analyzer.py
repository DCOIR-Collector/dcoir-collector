#!/usr/bin/env python3
"""Run the DCOIR PowerShell analyzer contract.

The wrapper consumes the #261 PowerShell surface inventory, loads the
repository-owned analyzer settings file, runs PSScriptAnalyzer by default, and
normalizes findings into JSON/Markdown reports. It is deliberately strict about
plumbing failures so later workflow integration cannot turn a skipped analyzer
into a green check.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "dcoir_powershell_analyzer_report_v1"
ISSUE_NUMBER = 262
INVENTORY_SCHEMA_VERSION = "dcoir_powershell_surface_inventory_v1"
BASELINE_SCHEMA_VERSION = "dcoir_powershell_analyzer_baseline_v1"
DEFAULT_INVENTORY = Path("project_sources/collector/powershell_surface_inventory.json")
DEFAULT_SETTINGS = Path("project_sources/collector/PSScriptAnalyzerSettings.psd1")
DEFAULT_JSON_OUTPUT = Path("project_sources/collector/powershell_analyzer_report.json")
DEFAULT_MARKDOWN_OUTPUT = Path("project_sources/collector/powershell_analyzer_report.md")
ANALYZABLE_SOURCE_TYPES = {".ps1", ".psm1", ".psd1", ".ps1xml", ".ps1.txt"}
PRIMARY_TARGET_CATEGORIES = {
    "collector_runtime_wrapper",
    "collector_runtime_source_part",
    "collector_harness_script",
    "collector_harness_source_part",
}
REQUIRED_POLICY_RULES = {
    "PSAvoidUsingPlainTextForPassword",
    "PSAvoidUsingConvertToSecureStringWithPlainText",
    "PSAvoidUsingInvokeExpression",
    "PSAvoidUsingWriteHost",
    "PSUseDeclaredVarsMoreThanAssignments",
    "PSUseShouldProcessForStateChangingFunctions",
}
SEVERITY_ORDER = {"information": 0, "warning": 1, "error": 2}


class AnalyzerContractError(Exception):
    """Raised for fail-closed analyzer wrapper errors."""


def relpath(path: Path, repo_root: Path) -> str:
    return path.resolve().relative_to(repo_root.resolve()).as_posix()


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def read_json(path: Path, label: str) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise AnalyzerContractError(f"{label} is missing: {path}") from exc
    except json.JSONDecodeError as exc:
        raise AnalyzerContractError(f"{label} is invalid JSON: {path}: {exc}") from exc
    except OSError as exc:
        raise AnalyzerContractError(f"{label} could not be read: {path}: {exc}") from exc


def read_text(path: Path, label: str) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise AnalyzerContractError(f"{label} is missing: {path}") from exc
    except OSError as exc:
        raise AnalyzerContractError(f"{label} could not be read: {path}: {exc}") from exc


def normalize_repo_path(value: str, repo_root: Path, target: dict[str, Any] | None = None) -> str:
    if not value:
        return str(target.get("path", "")) if target else ""
    candidate = Path(value)
    if candidate.is_absolute():
        try:
            return relpath(candidate, repo_root)
        except ValueError:
            analysis_path = str(target.get("analysis_path", "")) if target else ""
            if analysis_path and Path(analysis_path).resolve() == candidate.resolve():
                return str(target.get("path", ""))
            return candidate.as_posix()
    return candidate.as_posix()


def safe_relpath(path: Path, repo_root: Path) -> str:
    try:
        return relpath(path, repo_root)
    except ValueError:
        return path.as_posix()


def version_tuple(version: str) -> tuple[int, ...]:
    pieces = re.findall(r"\d+", version or "")
    return tuple(int(piece) for piece in pieces[:3])


def is_supported_powershell_version(version: str, minimum: str) -> bool:
    current = version_tuple(version)
    required = version_tuple(minimum)
    if not current or not required:
        return False
    while len(current) < len(required):
        current += (0,)
    return current >= required


def strip_powershell_comments(text: str) -> str:
    output: list[str] = []
    index = 0
    quote: str | None = None
    block_comment = False
    while index < len(text):
        char = text[index]
        next_char = text[index + 1] if index + 1 < len(text) else ""
        if block_comment:
            if char == "#" and next_char == ">":
                output.extend((" ", " "))
                block_comment = False
                index += 2
                continue
            output.append("\n" if char == "\n" else " ")
            index += 1
            continue
        if quote:
            output.append(char)
            if char == quote:
                if quote == "'" and next_char == "'":
                    output.append(next_char)
                    index += 2
                    continue
                if quote == '"' and index > 0 and text[index - 1] == "`":
                    index += 1
                    continue
                quote = None
            index += 1
            continue
        if char == "<" and next_char == "#":
            output.extend((" ", " "))
            block_comment = True
            index += 2
            continue
        if char == "#":
            while index < len(text) and text[index] != "\n":
                output.append(" ")
                index += 1
            continue
        if char in {"'", '"'}:
            quote = char
        output.append(char)
        index += 1
    return "".join(output)


def extract_outer_hashtable_body(text: str) -> str:
    start = text.find("@{")
    if start < 0:
        return ""
    index = start + 2
    output: list[str] = []
    quote: str | None = None
    depth = 1
    while index < len(text):
        char = text[index]
        next_char = text[index + 1] if index + 1 < len(text) else ""
        if quote:
            if char == quote:
                if quote == "'" and next_char == "'":
                    output.append(char)
                    output.append(next_char)
                    index += 2
                    continue
                if quote == '"' and index > 0 and text[index - 1] == "`":
                    output.append(char)
                    index += 1
                    continue
                quote = None
            output.append(char)
            index += 1
            continue
        if char in {"'", '"'}:
            quote = char
            output.append(char)
            index += 1
            continue
        if char in "([{":
            depth += 1
            output.append(char)
            index += 1
            continue
        if char in ")]}":
            depth -= 1
            if depth == 0:
                return "".join(output)
            output.append(char)
            index += 1
            continue
        output.append(char)
        index += 1
    return ""


def top_level_assignment_values(text: str) -> dict[str, list[str]]:
    assignments: dict[str, list[str]] = {}
    index = 0
    quote: str | None = None
    depth = 0
    while index < len(text):
        char = text[index]
        next_char = text[index + 1] if index + 1 < len(text) else ""
        if quote:
            if char == quote:
                if quote == "'" and next_char == "'":
                    index += 2
                    continue
                if quote == '"' and index > 0 and text[index - 1] == "`":
                    index += 1
                    continue
                quote = None
            index += 1
            continue
        if char in {"'", '"'}:
            quote = char
            index += 1
            continue
        if char in "([{":
            depth += 1
            index += 1
            continue
        if char in ")]}":
            depth = max(0, depth - 1)
            index += 1
            continue
        if depth == 0:
            match = re.match(r"\s*([A-Za-z_][A-Za-z0-9_]*)\s*=", text[index:])
            if match:
                key = match.group(1)
                value_start = index + match.end()
                value_index = value_start
                value_quote: str | None = None
                value_depth = 0
                while value_index < len(text):
                    value_char = text[value_index]
                    value_next = text[value_index + 1] if value_index + 1 < len(text) else ""
                    if value_quote:
                        if value_char == value_quote:
                            if value_quote == "'" and value_next == "'":
                                value_index += 2
                                continue
                            if value_quote == '"' and value_index > 0 and text[value_index - 1] == "`":
                                value_index += 1
                                continue
                            value_quote = None
                        value_index += 1
                        continue
                    if value_char in {"'", '"'}:
                        value_quote = value_char
                        value_index += 1
                        continue
                    if value_char in "([{":
                        value_depth += 1
                        value_index += 1
                        continue
                    if value_char in ")]}":
                        value_depth = max(0, value_depth - 1)
                        value_index += 1
                        continue
                    if value_depth == 0 and value_char == ";":
                        break
                    if (
                        value_depth == 0
                        and value_char == "\n"
                        and re.match(r"\s*[A-Za-z_][A-Za-z0-9_]*\s*=", text[value_index + 1 :])
                    ):
                        break
                    value_index += 1
                assignments.setdefault(key.casefold(), []).append(text[value_start:value_index].strip())
                index = value_index + 1 if value_index < len(text) and text[value_index] == ";" else value_index
                continue
        index += 1
    return assignments


def string_literals(text: str) -> list[str]:
    values: list[str] = []
    index = 0
    while index < len(text):
        char = text[index]
        if char not in {"'", '"'}:
            index += 1
            continue
        quote = char
        index += 1
        value: list[str] = []
        while index < len(text):
            current = text[index]
            next_char = text[index + 1] if index + 1 < len(text) else ""
            if current == quote:
                if quote == "'" and next_char == "'":
                    value.append("'")
                    index += 2
                    continue
                values.append("".join(value))
                index += 1
                break
            value.append(current)
            index += 1
    return values


def top_level_hashtable_keys(text: str) -> set[str]:
    keys: set[str] = set()
    index = 0
    quote: str | None = None
    depth = 0
    while index < len(text):
        char = text[index]
        next_char = text[index + 1] if index + 1 < len(text) else ""
        if quote:
            if char == quote:
                if quote == "'" and next_char == "'":
                    index += 2
                    continue
                if quote == '"' and index > 0 and text[index - 1] == "`":
                    index += 1
                    continue
                quote = None
            index += 1
            continue
        if char in {"'", '"'}:
            quote = char
            index += 1
            continue
        if char == "{":
            depth += 1
            index += 1
            continue
        if char == "}":
            depth = max(0, depth - 1)
            index += 1
            continue
        if depth == 1:
            match = re.match(r"\s*([A-Za-z][A-Za-z0-9_-]*)\s*=", text[index:])
            if match:
                keys.add(match.group(1))
                index += match.end()
                continue
        index += 1
    return keys


def validate_policy(settings_path: Path) -> dict[str, Any]:
    text = read_text(settings_path, "analyzer settings file")
    uncommented_text = strip_powershell_comments(text)
    settings_body = extract_outer_hashtable_body(uncommented_text)
    assignments = top_level_assignment_values(settings_body) if settings_body else {}
    errors: list[str] = []
    warnings: list[str] = []
    if not text.strip():
        errors.append(f"{settings_path}: analyzer settings file is empty")
    if not settings_body:
        errors.append(f"{settings_path}: analyzer settings file does not look like a PowerShell data file")
    if "DCOIR_POLICY_ID:" not in text:
        errors.append(f"{settings_path}: missing DCOIR_POLICY_ID comment")

    policy_values: dict[str, str] = {}
    for key, label in (("severity", "Severity"), ("includerules", "IncludeRules"), ("rules", "Rules")):
        values = assignments.get(key, [])
        if not values:
            errors.append(f"{settings_path}: missing {label} declaration")
            continue
        if len(values) > 1:
            errors.append(f"{settings_path}: duplicate top-level {label} declarations are not allowed")
        policy_values[label] = values[0]
    exclude_values = assignments.get("excluderules", [])
    if len(exclude_values) > 1:
        errors.append(f"{settings_path}: duplicate top-level ExcludeRules declarations are not allowed")
    exclude_rules_value = exclude_values[0] if exclude_values else ""

    severity_value = policy_values.get("Severity", "")
    include_rules_value = policy_values.get("IncludeRules", "")
    rules_value = policy_values.get("Rules", "")

    active_severities = {severity.strip() for severity in string_literals(severity_value)}
    include_rules = set(string_literals(include_rules_value))
    rules_keys = top_level_hashtable_keys(rules_value)
    missing_severities = sorted(severity for severity in {"Error", "Warning"} if severity not in active_severities)
    if missing_severities:
        errors.append(f"{settings_path}: missing active Severity entries: {', '.join(missing_severities)}")
    missing_include_rules = sorted(rule for rule in REQUIRED_POLICY_RULES if rule not in include_rules)
    missing_rules_keys = sorted(rule for rule in REQUIRED_POLICY_RULES if rule not in rules_keys)
    if missing_include_rules:
        errors.append(f"{settings_path}: missing active IncludeRules entries: {', '.join(missing_include_rules)}")
    if missing_rules_keys:
        errors.append(f"{settings_path}: missing active Rules keys: {', '.join(missing_rules_keys)}")

    exclude_rules = {rule.strip().casefold() for rule in string_literals(exclude_rules_value)}
    if "*" in exclude_rules:
        errors.append(f"{settings_path}: wildcard ExcludeRules are not allowed")
    if "ps*" in exclude_rules:
        errors.append(f"{settings_path}: broad PS* ExcludeRules are not allowed")

    if exclude_values:
        warnings.append(f"{settings_path}: ExcludeRules present; every exclusion must be reviewed and justified")

    if errors:
        raise AnalyzerContractError("; ".join(errors))
    return {
        "path": settings_path.as_posix(),
        "sha256": sha256_file(settings_path),
        "required_rules": sorted(REQUIRED_POLICY_RULES),
        "active_severities": sorted(active_severities),
        "active_include_rules": sorted(include_rules),
        "active_rule_keys": sorted(rules_keys),
        "warnings": warnings,
        "exclusions_declared": bool(exclude_values),
    }


def load_inventory(repo_root: Path, inventory_path: Path) -> dict[str, Any]:
    inventory = read_json(inventory_path, "PowerShell surface inventory")
    if not isinstance(inventory, dict):
        raise AnalyzerContractError("PowerShell surface inventory must be a JSON object")
    if inventory.get("schema_version") != INVENTORY_SCHEMA_VERSION:
        raise AnalyzerContractError(
            "PowerShell surface inventory schema mismatch: "
            f"expected {INVENTORY_SCHEMA_VERSION}, got {inventory.get('schema_version')!r}"
        )
    validation = inventory.get("validation")
    if not isinstance(validation, dict) or validation.get("success") is not True:
        raise AnalyzerContractError("PowerShell surface inventory validation is not successful")
    surfaces = inventory.get("surfaces")
    if not isinstance(surfaces, list):
        raise AnalyzerContractError("PowerShell surface inventory is missing surfaces[]")
    if not surfaces:
        raise AnalyzerContractError("PowerShell surface inventory contains no surfaces")
    if not inventory_path.exists():
        raise AnalyzerContractError(f"PowerShell surface inventory is missing: {inventory_path}")
    return inventory


def selected_target_paths(values: list[str]) -> set[str] | None:
    if not values:
        return None
    return {Path(value).as_posix() for value in values}


def safe_inventory_path(value: Any) -> str:
    raw = scalar(value)
    if not raw:
        raise AnalyzerContractError("inventory surface path is empty")
    if "\\" in raw:
        raise AnalyzerContractError(f"{raw}: inventory path must use repo-relative POSIX separators")
    candidate = Path(raw)
    if candidate.is_absolute():
        raise AnalyzerContractError(f"{raw}: inventory path must be repo-relative")
    if any(part == ".." for part in candidate.parts):
        raise AnalyzerContractError(f"{raw}: inventory path must not contain parent traversal")
    normalized = candidate.as_posix()
    if normalized in {"", "."}:
        raise AnalyzerContractError("inventory surface path is empty")
    return normalized


def is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


def build_target_sets(
    repo_root: Path,
    inventory: dict[str, Any],
    only_paths: set[str] | None,
    temp_root: Path,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[str]]:
    errors: list[str] = []
    targets: list[dict[str, Any]] = []
    skipped_surfaces: list[dict[str, Any]] = []
    inventory_paths: set[str] = set()

    for surface in inventory["surfaces"]:
        if not isinstance(surface, dict):
            errors.append("PowerShell surface inventory contains a non-object surface entry")
            continue
        raw_path = scalar(surface.get("path"))
        try:
            path = safe_inventory_path(raw_path)
        except AnalyzerContractError as exc:
            errors.append(str(exc))
            inventory_paths.add(raw_path)
            continue
        inventory_paths.add(path)
        decision = str(surface.get("inclusion_decision", ""))
        source_type = str(surface.get("source_type", ""))
        if only_paths is not None and path not in only_paths:
            continue
        if decision != "include":
            skipped_surfaces.append(
                {
                    "path": path,
                    "category": surface.get("category"),
                    "source_type": source_type,
                    "decision": decision,
                    "reason": surface.get("decision_reason", ""),
                }
            )
            continue
        if source_type not in ANALYZABLE_SOURCE_TYPES:
            skipped_surfaces.append(
                {
                    "path": path,
                    "category": surface.get("category"),
                    "source_type": source_type,
                    "decision": "unsupported_source_type",
                    "reason": "Included inventory surface has no direct analyzer source type.",
                }
            )
            errors.append(f"{path}: included inventory surface has unsupported source type {source_type!r}")
            continue

        absolute_path = repo_root / path
        if not is_relative_to(absolute_path, repo_root):
            errors.append(f"{path}: inventory path resolves outside repo root")
            continue
        if not absolute_path.exists():
            errors.append(f"{path}: intended analyzer target is missing")
            continue
        if absolute_path.is_dir():
            errors.append(f"{path}: intended analyzer target is a directory")
            continue
        if absolute_path.stat().st_size == 0:
            errors.append(f"{path}: intended analyzer target is empty")
            continue
        actual_sha256 = sha256_file(absolute_path)
        inventory_sha256 = scalar(surface.get("sha256")).strip()
        if inventory_sha256 and inventory_sha256 != actual_sha256:
            errors.append(f"{path}: inventory sha256 does not match current file content")
            continue

        analysis_path = absolute_path
        if source_type == ".ps1.txt":
            staged = temp_root / path
            staged = staged.with_name(staged.name + ".ps1")
            if not is_relative_to(staged, temp_root):
                errors.append(f"{path}: staged analyzer path resolves outside temp root")
                continue
            staged.parent.mkdir(parents=True, exist_ok=True)
            staged.write_text(absolute_path.read_text(encoding="utf-8", errors="ignore"), encoding="utf-8")
            analysis_path = staged

        targets.append(
            {
                "path": path,
                "absolute_path": str(absolute_path),
                "analysis_path": str(analysis_path),
                "category": surface.get("category"),
                "source_type": source_type,
                "sha256": actual_sha256,
                "line_count": surface.get("line_count"),
                "size_bytes": surface.get("size_bytes"),
            }
        )

    if only_paths is not None:
        missing_requested = sorted(path for path in only_paths if path not in inventory_paths)
        for path in missing_requested:
            errors.append(f"{path}: requested target path is not present in the #261 inventory")

    if not targets:
        errors.append("Analyzer intended target set is empty")
    if not any(target["category"] in PRIMARY_TARGET_CATEGORIES for target in targets):
        errors.append("Analyzer intended target set has no collector or harness source surfaces")
    return targets, skipped_surfaces, errors


def make_request(settings_path: Path, target: dict[str, Any]) -> dict[str, Any]:
    return {
        "settings_path": str(settings_path),
        "target": {
            "path": target["path"],
            "absolute_path": target["absolute_path"],
            "analysis_path": target["analysis_path"],
            "category": target["category"],
            "source_type": target["source_type"],
            "sha256": target["sha256"],
        },
    }


def psscriptanalyzer_script() -> str:
    return r"""
$ErrorActionPreference = 'Stop'
$requestJson = [Console]::In.ReadToEnd()
$request = $requestJson | ConvertFrom-Json
Import-Module PSScriptAnalyzer -ErrorAction Stop
$module = Get-Module PSScriptAnalyzer
$rawFindings = @(Invoke-ScriptAnalyzer -Path $request.target.analysis_path -Settings $request.settings_path -ErrorAction Stop)
$findings = @(
  foreach ($finding in $rawFindings) {
    $recommendedFix = ''
    if ($finding.PSObject.Properties.Name -contains 'SuggestedCorrections' -and $finding.SuggestedCorrections) {
      $recommendedFix = ($finding.SuggestedCorrections | Select-Object -First 1 | ForEach-Object { $_.Description }) -join '; '
    }
    [pscustomobject]@{
      path = $finding.ScriptPath
      line = $finding.Line
      column = $finding.Column
      symbol = $finding.ScriptName
      rule_name = $finding.RuleName
      severity = $finding.Severity.ToString()
      observed_problem = $finding.Message
      recommended_fix = $recommendedFix
    }
  }
)
[pscustomobject]@{
  analyzer_name = 'PSScriptAnalyzer'
  analyzer_version = $module.Version.ToString()
  powershell_engine = $PSVersionTable.PSEdition
  powershell_version = $PSVersionTable.PSVersion.ToString()
  target_path = $request.target.path
  analyzed = $true
  findings = $findings
} | ConvertTo-Json -Depth 8
"""


def analyzer_command(args: argparse.Namespace) -> tuple[list[str], str]:
    if args.analyzer_command:
        return args.analyzer_command, "custom_json_command"
    pwsh = shutil.which("pwsh")
    if not pwsh:
        raise AnalyzerContractError("analyzer tool missing: pwsh was not found on PATH")
    return [pwsh, "-NoProfile", "-NonInteractive", "-Command", psscriptanalyzer_script()], "psscriptanalyzer_pwsh"


def run_analyzer_command(
    command: list[str],
    command_kind: str,
    request: dict[str, Any],
    timeout_seconds: int,
) -> dict[str, Any]:
    try:
        completed = subprocess.run(
            command,
            input=json.dumps(request),
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            check=False,
        )
    except FileNotFoundError as exc:
        raise AnalyzerContractError(f"analyzer tool missing: {command[0]}") from exc
    except subprocess.TimeoutExpired as exc:
        raise AnalyzerContractError(
            f"analyzer timeout after {timeout_seconds} seconds for {request['target']['path']}"
        ) from exc
    except OSError as exc:
        raise AnalyzerContractError(f"analyzer launch failed for {request['target']['path']}: {exc}") from exc

    if completed.returncode != 0:
        stderr = completed.stderr.strip()[-2000:]
        raise AnalyzerContractError(
            f"analyzer crash for {request['target']['path']} with exit {completed.returncode}: {stderr}"
        )
    try:
        response = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise AnalyzerContractError(f"analyzer returned invalid JSON for {request['target']['path']}: {exc}") from exc
    if not isinstance(response, dict):
        raise AnalyzerContractError(f"analyzer response for {request['target']['path']} is not a JSON object")
    response["command_kind"] = command_kind
    return response


def scalar(value: Any) -> str:
    if value is None:
        return ""
    return str(value)


def integer_or_none(value: Any) -> int | None:
    if value in (None, ""):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def normalize_finding(raw: dict[str, Any], target: dict[str, Any], repo_root: Path) -> dict[str, Any]:
    path = normalize_repo_path(
        scalar(raw.get("path") or raw.get("ScriptPath") or target["path"]),
        repo_root,
        target,
    )
    finding = {
        "path": path,
        "line": integer_or_none(raw.get("line") or raw.get("Line")),
        "column": integer_or_none(raw.get("column") or raw.get("Column")),
        "symbol": scalar(raw.get("symbol") or raw.get("ScriptName") or raw.get("Extent")),
        "rule_name": scalar(raw.get("rule_name") or raw.get("RuleName") or raw.get("rule") or raw.get("check_name")),
        "severity": scalar(raw.get("severity") or raw.get("Severity")),
        "observed_problem": scalar(raw.get("observed_problem") or raw.get("Message") or raw.get("message")),
        "recommended_fix": scalar(raw.get("recommended_fix") or raw.get("RecommendedFix") or raw.get("recommendation")),
        "target_path": target["path"],
        "target_sha256": target["sha256"],
        "suppressed_by_baseline": False,
    }
    missing = [
        key
        for key in ("path", "rule_name", "severity", "observed_problem")
        if not finding[key]
    ]
    if missing:
        raise AnalyzerContractError(
            f"{target['path']}: analyzer finding is missing required normalized fields: {', '.join(missing)}"
        )
    fingerprint_payload = {
        "path": finding["path"],
        "line": finding["line"],
        "column": finding["column"],
        "rule_name": finding["rule_name"],
        "severity": finding["severity"],
        "observed_problem": finding["observed_problem"],
        "target_sha256": finding["target_sha256"],
    }
    finding["fingerprint"] = sha256_text(json.dumps(fingerprint_payload, sort_keys=True, separators=(",", ":")))
    return finding


def normalize_response(response: dict[str, Any], target: dict[str, Any], repo_root: Path, minimum_ps_version: str) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    if response.get("analyzed") is not True or response.get("skipped") is True:
        reason = response.get("skipped_reason") or response.get("reason") or "no reason supplied"
        raise AnalyzerContractError(f"{target['path']}: intended analyzer target was skipped: {reason}")

    analyzer_name = scalar(response.get("analyzer_name") or response.get("AnalyzerName"))
    analyzer_version = scalar(response.get("analyzer_version") or response.get("AnalyzerVersion"))
    powershell_engine = scalar(response.get("powershell_engine") or response.get("PowerShellEngine"))
    powershell_version = scalar(response.get("powershell_version") or response.get("PowerShellVersion"))
    if not analyzer_name:
        raise AnalyzerContractError(f"{target['path']}: analyzer response missing analyzer_name")
    if not analyzer_version:
        raise AnalyzerContractError(f"{target['path']}: analyzer response missing analyzer_version")
    if not powershell_engine:
        raise AnalyzerContractError(f"{target['path']}: analyzer response missing powershell_engine")
    if not powershell_version:
        raise AnalyzerContractError(f"{target['path']}: analyzer response missing powershell_version")
    if not is_supported_powershell_version(powershell_version, minimum_ps_version):
        raise AnalyzerContractError(
            f"{target['path']}: unsupported PowerShell version {powershell_version}; minimum is {minimum_ps_version}"
        )

    response_target = scalar(response.get("target_path") or response.get("TargetPath"))
    if not response_target:
        raise AnalyzerContractError(f"{target['path']}: analyzer response missing target_path")
    if normalize_repo_path(response_target, repo_root, target) != target["path"]:
        raise AnalyzerContractError(
            f"{target['path']}: analyzer response target mismatch: {response_target}"
        )

    raw_findings = response.get("findings", [])
    if raw_findings is None:
        raw_findings = []
    if not isinstance(raw_findings, list):
        raise AnalyzerContractError(f"{target['path']}: analyzer findings must be a list")
    findings: list[dict[str, Any]] = []
    for raw in raw_findings:
        if not isinstance(raw, dict):
            raise AnalyzerContractError(f"{target['path']}: analyzer finding is not a JSON object")
        findings.append(normalize_finding(raw, target, repo_root))

    metadata = {
        "target_path": target["path"],
        "analyzer_name": analyzer_name,
        "analyzer_version": analyzer_version,
        "powershell_engine": powershell_engine,
        "powershell_version": powershell_version,
        "command_kind": response.get("command_kind"),
        "finding_count": len(findings),
    }
    return metadata, findings


def portable_target(target: dict[str, Any]) -> dict[str, Any]:
    return {
        "path": target["path"],
        "category": target["category"],
        "source_type": target["source_type"],
        "sha256": target["sha256"],
        "line_count": target["line_count"],
        "size_bytes": target["size_bytes"],
        "staged_for_analysis": target["source_type"] == ".ps1.txt",
        "analysis_input_kind": "temporary_ps1_copy" if target["source_type"] == ".ps1.txt" else "source_file",
    }


def load_baseline(path: Path | None) -> dict[str, Any] | None:
    if path is None:
        return None
    baseline = read_json(path, "PowerShell analyzer baseline")
    if not isinstance(baseline, dict):
        raise AnalyzerContractError("PowerShell analyzer baseline must be a JSON object")
    if baseline.get("schema_version") != BASELINE_SCHEMA_VERSION:
        raise AnalyzerContractError(
            "PowerShell analyzer baseline schema mismatch: "
            f"expected {BASELINE_SCHEMA_VERSION}, got {baseline.get('schema_version')!r}"
        )
    suppressions = baseline.get("suppressions", [])
    if not isinstance(suppressions, list):
        raise AnalyzerContractError("PowerShell analyzer baseline suppressions must be a list")
    seen_suppressions: set[tuple[str, str, str]] = set()
    for suppression in suppressions:
        if not isinstance(suppression, dict):
            raise AnalyzerContractError("PowerShell analyzer baseline suppression must be an object")
        for key in ("path", "rule_name", "reason", "fingerprint"):
            if not scalar(suppression.get(key)).strip():
                raise AnalyzerContractError(f"PowerShell analyzer baseline suppression missing {key}")
        suppression_key = (
            scalar(suppression["path"]),
            scalar(suppression["rule_name"]),
            scalar(suppression["fingerprint"]),
        )
        if suppression_key in seen_suppressions:
            raise AnalyzerContractError(
                "PowerShell analyzer baseline duplicate suppression for "
                f"{suppression_key[0]} {suppression_key[1]} {suppression_key[2]}"
            )
        seen_suppressions.add(suppression_key)
        expected_count = suppression.get("expected_match_count", 1)
        if not isinstance(expected_count, int) or expected_count < 1:
            raise AnalyzerContractError(
                "PowerShell analyzer baseline suppression expected_match_count must be a positive integer"
            )
    return baseline


def apply_baseline(findings: list[dict[str, Any]], baseline: dict[str, Any] | None) -> list[str]:
    if baseline is None:
        return []
    errors: list[str] = []
    for suppression in baseline.get("suppressions", []):
        suppression_path = scalar(suppression["path"])
        suppression_rule = scalar(suppression["rule_name"])
        suppression_fingerprint = scalar(suppression["fingerprint"])
        expected_count = int(suppression.get("expected_match_count", 1))
        matches = [
            finding
            for finding in findings
            if finding["path"] == suppression_path and finding["rule_name"] == suppression_rule
            and finding["fingerprint"] == suppression_fingerprint
        ]
        if len(matches) != expected_count:
            errors.append(
                "suppressed-rule mismatch: "
                f"{suppression_path} {suppression_rule} {suppression_fingerprint} "
                f"matched {len(matches)} analyzer findings, expected {expected_count}"
            )
            continue
        for finding in matches:
            finding["suppressed_by_baseline"] = True
            finding["baseline_reason"] = suppression["reason"]
    return errors


def baseline_metadata(
    baseline: dict[str, Any] | None,
    baseline_path: Path | None,
    repo_root: Path,
    findings: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    findings = findings or []
    return {
        "path": safe_relpath(baseline_path, repo_root) if baseline_path else None,
        "schema_version": baseline.get("schema_version") if baseline else None,
        "suppression_count": len(baseline.get("suppressions", [])) if baseline else 0,
        "matched_suppression_count": len([finding for finding in findings if finding["suppressed_by_baseline"]]),
        "suppression_keys": [
            {
                "path": scalar(suppression.get("path")),
                "rule_name": scalar(suppression.get("rule_name")),
                "fingerprint": scalar(suppression.get("fingerprint")),
                "expected_match_count": suppression.get("expected_match_count", 1),
            }
            for suppression in (baseline.get("suppressions", []) if baseline else [])
        ],
    }


def severity_at_or_above(severity: str, threshold: str) -> bool:
    return SEVERITY_ORDER.get(severity.casefold(), 99) >= SEVERITY_ORDER.get(threshold.casefold(), 1)


def expected_finding_errors(findings: list[dict[str, Any]], args: argparse.Namespace) -> list[str]:
    errors: list[str] = []
    if args.expect_finding_rule:
        matches = [
            finding
            for finding in findings
            if finding["rule_name"] == args.expect_finding_rule
            and (not args.expect_finding_path or finding["path"] == args.expect_finding_path)
        ]
        if not matches:
            path_text = f" at {args.expect_finding_path}" if args.expect_finding_path else ""
            errors.append(f"expected analyzer finding {args.expect_finding_rule}{path_text} was not produced")
    if args.expect_no_findings:
        unsuppressed = [finding for finding in findings if not finding["suppressed_by_baseline"]]
        if unsuppressed:
            errors.append(f"expected no unsuppressed analyzer findings, found {len(unsuppressed)}")
    return errors


def render_markdown(report: dict[str, Any]) -> str:
    summary = report["summary"]
    validation = report["validation"]
    lines = [
        "# DCOIR PowerShell Analyzer Report",
        "",
        f"- Schema: `{report['schema_version']}`",
        f"- Issue: `#{report['issue']}`",
        f"- Analyzer: `{report['analyzer']['name']}` `{report['analyzer']['version']}`",
        f"- PowerShell: `{report['powershell']['engine']}` `{report['powershell']['version']}`",
        f"- Settings: `{report['settings']['path']}`",
        f"- Inventory: `{report['inventory']['path']}`",
        f"- JSON artifact: `{report['outputs']['json']}`",
        f"- Validation: `{'pass' if validation['success'] else 'fail'}`",
        "",
        "## Summary",
        "",
        "| Metric | Count |",
        "| --- | ---: |",
        f"| Intended targets | {summary['target_count']} |",
        f"| Analyzed targets | {summary['analyzed_count']} |",
        f"| Skipped intended targets | {summary['skipped_target_count']} |",
        f"| Reference/excluded surfaces | {summary['reference_or_excluded_surface_count']} |",
        f"| Findings | {summary['finding_count']} |",
        f"| Baseline-suppressed findings | {summary['suppressed_finding_count']} |",
        f"| Unsuppressed findings | {summary['unsuppressed_finding_count']} |",
        "",
        "## Findings",
        "",
    ]
    findings = report["findings"]
    if findings:
        lines.extend(["| Path | Line | Severity | Rule | Problem | Recommended Fix |", "| --- | ---: | --- | --- | --- | --- |"])
        for finding in findings:
            line = finding["line"] if finding["line"] is not None else ""
            suppressed = " (baseline-suppressed)" if finding["suppressed_by_baseline"] else ""
            problem = str(finding["observed_problem"]).replace("|", "\\|")
            fix = str(finding["recommended_fix"] or "").replace("|", "\\|")
            lines.append(
                f"| `{finding['path']}` | {line} | `{finding['severity']}{suppressed}` | "
                f"`{finding['rule_name']}` | {problem} | {fix} |"
            )
    else:
        lines.append("No analyzer findings were reported.")

    lines.extend(["", "## Validation Findings", ""])
    if validation["errors"]:
        lines.append("Errors:")
        lines.extend(f"- {error}" for error in validation["errors"])
    else:
        lines.append("- No validation errors.")
    if validation["warnings"]:
        lines.extend(["", "Warnings:"])
        lines.extend(f"- {warning}" for warning in validation["warnings"])
    lines.append("")
    return "\n".join(lines)


def write_outputs(repo_root: Path, report: dict[str, Any], json_output: Path, markdown_output: Path) -> None:
    json_path = repo_root / json_output
    markdown_path = repo_root / markdown_output
    try:
        json_path.parent.mkdir(parents=True, exist_ok=True)
        markdown_path.parent.mkdir(parents=True, exist_ok=True)
        json_text = json.dumps(report, indent=2) + "\n"
        json_path.write_text(json_text, encoding="utf-8")
        markdown_path.write_text(render_markdown(report), encoding="utf-8")
    except (TypeError, OSError) as exc:
        raise AnalyzerContractError(f"report write failure: {exc}") from exc
    for label, path in (("JSON", json_path), ("Markdown", markdown_path)):
        if not path.exists() or path.stat().st_size == 0:
            raise AnalyzerContractError(f"missing output: {label} report was not written to {path}")


def empty_report(
    *,
    args: argparse.Namespace,
    repo_root: Path,
    inventory_path: Path,
    settings_path: Path,
    json_output: Path,
    markdown_output: Path,
    errors: list[str],
    warnings: list[str],
) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "issue": ISSUE_NUMBER,
        "source_of_truth": "#261 powershell_surface_inventory.json",
        "analyzer": {
            "name": "not_run",
            "version": "not_run",
            "command_kind": "not_run",
            "observed_versions": [],
        },
        "powershell": {
            "engine": "not_run",
            "version": "not_run",
            "minimum_version": args.minimum_powershell_version,
            "observed_versions": [],
        },
        "settings": {
            "path": safe_relpath(settings_path, repo_root),
            "sha256": sha256_file(settings_path) if settings_path.exists() and settings_path.is_file() else None,
            "required_rules": sorted(REQUIRED_POLICY_RULES),
            "active_severities": [],
            "active_include_rules": [],
            "active_rule_keys": [],
            "warnings": [],
            "exclusions_declared": False,
        },
        "inventory": {
            "path": safe_relpath(inventory_path, repo_root),
            "schema_version": None,
            "sha256": sha256_file(inventory_path) if inventory_path.exists() and inventory_path.is_file() else None,
            "inventory_total_surfaces": None,
        },
        "baseline": baseline_metadata(None, Path(args.baseline_json).resolve() if args.baseline_json else None, repo_root),
        "summary": {
            "target_count": 0,
            "analyzed_count": 0,
            "skipped_target_count": 0,
            "reference_or_excluded_surface_count": 0,
            "finding_count": 0,
            "suppressed_finding_count": 0,
            "unsuppressed_finding_count": 0,
        },
        "targets": [],
        "skipped_surfaces": [],
        "findings": [],
        "validation": {
            "success": False,
            "errors": errors,
            "warnings": warnings,
        },
        "outputs": {
            "json": json_output.as_posix(),
            "markdown": markdown_output.as_posix(),
        },
    }


def build_report(args: argparse.Namespace) -> tuple[dict[str, Any] | None, list[str], list[str]]:
    repo_root = Path(args.repo_root).resolve()
    inventory_path = (repo_root / args.inventory).resolve()
    settings_path = (repo_root / args.settings).resolve()
    baseline_path = Path(args.baseline_json).resolve() if args.baseline_json else None
    json_output = Path(args.json_output)
    markdown_output = Path(args.markdown_output)
    errors: list[str] = []
    warnings: list[str] = []

    try:
        policy = validate_policy(settings_path)
        policy["path"] = relpath(settings_path, repo_root)
        warnings.extend(policy["warnings"])
        inventory = load_inventory(repo_root, inventory_path)
        baseline = load_baseline(baseline_path)
        command, command_kind = analyzer_command(args)
    except AnalyzerContractError as exc:
        errors = [str(exc)]
        return empty_report(
            args=args,
            repo_root=repo_root,
            inventory_path=inventory_path,
            settings_path=settings_path,
            json_output=json_output,
            markdown_output=markdown_output,
            errors=errors,
            warnings=warnings,
        ), errors, warnings

    with tempfile.TemporaryDirectory(prefix="dcoir-ps-analyzer-") as temp:
        temp_root = Path(temp)
        targets, skipped_surfaces, target_errors = build_target_sets(
            repo_root=repo_root,
            inventory=inventory,
            only_paths=selected_target_paths(args.target_path),
            temp_root=temp_root,
        )
        errors.extend(target_errors)

        analyzed_targets: list[dict[str, Any]] = []
        all_findings: list[dict[str, Any]] = []
        analyzer_metadata: list[dict[str, Any]] = []
        if not errors:
            for target in targets:
                try:
                    response = run_analyzer_command(
                        command,
                        command_kind,
                        make_request(settings_path, target),
                        args.timeout_seconds,
                    )
                    metadata, findings = normalize_response(
                        response,
                        target,
                        repo_root,
                        args.minimum_powershell_version,
                    )
                    analyzed_targets.append(portable_target(target))
                    analyzer_metadata.append(metadata)
                    all_findings.extend(findings)
                except AnalyzerContractError as exc:
                    errors.append(str(exc))
                    break

        errors.extend(apply_baseline(all_findings, baseline if "baseline" in locals() else None))
        errors.extend(expected_finding_errors(all_findings, args))

        unsuppressed_findings = [finding for finding in all_findings if not finding["suppressed_by_baseline"]]
        blocking_findings = [
            finding
            for finding in unsuppressed_findings
            if severity_at_or_above(finding["severity"], args.fail_on_severity)
        ]
        if blocking_findings and not args.allow_findings:
            errors.append(
                f"unsuppressed analyzer findings at or above {args.fail_on_severity}: {len(blocking_findings)}"
            )

        metadata_first = analyzer_metadata[0] if analyzer_metadata else {}
        analyzer_versions = sorted(
            {
                f"{metadata.get('analyzer_name')} {metadata.get('analyzer_version')}"
                for metadata in analyzer_metadata
                if metadata.get("analyzer_name") and metadata.get("analyzer_version")
            }
        )
        powershell_versions = sorted(
            {
                f"{metadata.get('powershell_engine')} {metadata.get('powershell_version')}"
                for metadata in analyzer_metadata
                if metadata.get("powershell_engine") and metadata.get("powershell_version")
            }
        )
        if len(analyzer_versions) > 1:
            errors.append("analyzer version changed across targets: " + ", ".join(analyzer_versions))
        if len(powershell_versions) > 1:
            errors.append("PowerShell engine/version changed across targets: " + ", ".join(powershell_versions))
        skipped_target_count = max(0, len(targets) - len(analyzed_targets))
        if skipped_target_count:
            errors.append(f"partial scan: {skipped_target_count} intended targets were not analyzed")

        report = {
            "schema_version": SCHEMA_VERSION,
            "issue": ISSUE_NUMBER,
            "source_of_truth": "#261 powershell_surface_inventory.json",
            "analyzer": {
                "name": metadata_first.get("analyzer_name", "not_run"),
                "version": metadata_first.get("analyzer_version", "not_run"),
                "command_kind": command_kind,
                "observed_versions": analyzer_versions,
            },
            "powershell": {
                "engine": metadata_first.get("powershell_engine", "not_run"),
                "version": metadata_first.get("powershell_version", "not_run"),
                "minimum_version": args.minimum_powershell_version,
                "observed_versions": powershell_versions,
            },
            "settings": policy,
            "inventory": {
                "path": relpath(inventory_path, repo_root),
                "schema_version": inventory.get("schema_version"),
                "sha256": sha256_file(inventory_path),
                "inventory_total_surfaces": inventory.get("summary", {}).get("total_surfaces"),
            },
            "baseline": baseline_metadata(baseline if "baseline" in locals() else None, baseline_path, repo_root, all_findings),
            "summary": {
                "target_count": len(targets),
                "analyzed_count": len(analyzed_targets),
                "skipped_target_count": skipped_target_count,
                "reference_or_excluded_surface_count": len(skipped_surfaces),
                "finding_count": len(all_findings),
                "suppressed_finding_count": len(all_findings) - len(unsuppressed_findings),
                "unsuppressed_finding_count": len(unsuppressed_findings),
            },
            "targets": analyzed_targets,
            "skipped_surfaces": skipped_surfaces,
            "findings": all_findings,
            "validation": {
                "success": not errors,
                "errors": errors,
                "warnings": warnings,
            },
            "outputs": {
                "json": json_output.as_posix(),
                "markdown": markdown_output.as_posix(),
            },
        }
        return report, errors, warnings


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the DCOIR PowerShell analyzer contract")
    parser.add_argument("--repo-root", default=".", help="Repository root")
    parser.add_argument("--inventory", default=DEFAULT_INVENTORY.as_posix(), help="PowerShell surface inventory JSON")
    parser.add_argument("--settings", default=DEFAULT_SETTINGS.as_posix(), help="PSScriptAnalyzer settings file")
    parser.add_argument("--json-output", default=DEFAULT_JSON_OUTPUT.as_posix(), help="JSON report output path")
    parser.add_argument("--markdown-output", default=DEFAULT_MARKDOWN_OUTPUT.as_posix(), help="Markdown report output path")
    parser.add_argument("--analyzer-command", action="append", default=[], help="Custom JSON analyzer command token; repeat for args")
    parser.add_argument("--target-path", action="append", default=[], help="Inventory path to analyze; may be repeated")
    parser.add_argument("--baseline-json", help="Optional analyzer baseline JSON")
    parser.add_argument("--timeout-seconds", type=int, default=60, help="Analyzer timeout per target")
    parser.add_argument("--minimum-powershell-version", default="5.1", help="Minimum supported PowerShell version")
    parser.add_argument("--fail-on-severity", default="Warning", choices=["Information", "Warning", "Error"], help="Finding severity threshold")
    parser.add_argument("--allow-findings", action="store_true", help="Write reports without failing on unsuppressed findings")
    parser.add_argument("--expect-finding-rule", help="Require at least one finding with this rule name")
    parser.add_argument("--expect-finding-path", help="When expecting a finding, require this path")
    parser.add_argument("--expect-no-findings", action="store_true", help="Fail if unsuppressed findings are present")
    parser.add_argument("--no-write", action="store_true", help="Do not write report files")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report, errors, _warnings = build_report(args)
    if report is not None and not args.no_write:
        try:
            write_outputs(Path(args.repo_root).resolve(), report, Path(args.json_output), Path(args.markdown_output))
        except AnalyzerContractError as exc:
            errors.append(str(exc))
    if report is None:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    print(json.dumps(report["summary"], indent=2))
    for error in errors:
        print(error, file=sys.stderr)
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
