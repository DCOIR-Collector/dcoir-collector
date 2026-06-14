#!/usr/bin/env python3
"""Inventory loading and target selection for PowerShell analyzer runs."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from powershell_analyzer_contract import (
    ANALYZABLE_SOURCE_TYPES,
    AnalyzerContractError,
    INVENTORY_SCHEMA_VERSION,
    PRIMARY_TARGET_CATEGORIES,
    read_json,
    scalar,
    sha256_line_ending_stable_file,
)

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
        actual_sha256 = sha256_line_ending_stable_file(absolute_path)
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
