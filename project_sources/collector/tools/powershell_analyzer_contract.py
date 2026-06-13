#!/usr/bin/env python3
"""Shared constants and helpers for the DCOIR PowerShell analyzer."""
from __future__ import annotations

import hashlib
import json
import re
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

def severity_at_or_above(severity: str, threshold: str) -> bool:
    return SEVERITY_ORDER.get(severity.casefold(), 99) >= SEVERITY_ORDER.get(threshold.casefold(), 1)
