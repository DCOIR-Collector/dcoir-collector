#!/usr/bin/env python3
"""Discovery, classification, and dependency expansion for PowerShell surfaces."""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path
from typing import Any

from powershell_surface_inventory_common import (
    HARNESS_GENERATED_OUTPUT,
    HARNESS_PARTS_ROOT,
    MANIFEST_PATH,
    REQUIRED_SURFACE_PROFILE_SUPPLEMENTS_PATH,
    REQUIRED_SURFACE_PROFILES_PATH,
    archive_temp_vendor_like,
    file_facts,
    fixture_like,
    generated_like,
    has_prefix,
    is_ignored_discovery_path,
    is_powershell_file,
    is_workflow_yaml,
    make_surface,
    path_is_dir_inside_repo,
    path_is_file_inside_repo,
    path_parts,
    path_resolves_inside_repo,
    repo_file_exists,
    staging_like,
)
from powershell_surface_inventory_workflow_yaml import extract_workflow_snippets, workflow_yaml_shape_error

def classify_surface(repo_root: Path, rel: str, exists: bool = True) -> dict[str, Any] | None:
    if is_workflow_yaml(rel):
        if not exists:
            return make_surface(
                repo_root,
                rel,
                "missing_changed_workflow_surface",
                "missing",
                "fail",
                "Changed workflow/action YAML path is missing from the working tree.",
                exists,
            )
        workflow_error = workflow_yaml_shape_error(repo_root, rel)
        if workflow_error:
            return make_surface(
                repo_root,
                rel,
                "invalid_workflow_surface",
                "invalid",
                "fail",
                workflow_error,
                exists,
            )
        snippets = extract_workflow_snippets(repo_root, rel) if exists else []
        if not snippets:
            return None
        markers = sorted({snippet["line_start"] for snippet in snippets})
        return make_surface(
            repo_root,
            rel,
            "workflow_embedded_powershell",
            "workflow_embedded",
            "reference",
            "Workflow or composite-action YAML embeds PowerShell and needs later snippet-aware handling.",
            exists,
            markers,
            snippets,
        )

    if not is_powershell_file(rel):
        return None

    if not exists:
        return make_surface(
            repo_root,
            rel,
            "missing_changed_powershell_surface",
            "missing",
            "fail",
            "Changed PowerShell-relevant path is missing from the working tree.",
            exists,
        )

    if rel == "project_sources/collector/source/DCOIR_Collector.ps1":
        return make_surface(
            repo_root,
            rel,
            "collector_runtime_wrapper",
            "source",
            "include",
            "Collector runtime wrapper is a primary maintained PowerShell surface.",
            exists,
        )

    if has_prefix(rel, "project_sources/collector/source/parts"):
        return make_surface(
            repo_root,
            rel,
            "collector_runtime_source_part",
            "source",
            "include",
            "Collector runtime source part is primary maintained PowerShell source.",
            exists,
        )

    if has_prefix(rel, "project_sources/collector/harness/source/parts"):
        return make_surface(
            repo_root,
            rel,
            "collector_harness_source_part",
            "source_part",
            "include",
            "Collector harness source part is primary maintained PowerShell source.",
            exists,
        )

    if rel == HARNESS_GENERATED_OUTPUT.as_posix() or generated_like(rel):
        return make_surface(
            repo_root,
            rel,
            "generated_or_assembled_output",
            "generated",
            "reference",
            "Generated or assembled output is covered as parity/reference evidence, not source truth.",
            exists,
        )

    if has_prefix(rel, "project_sources/collector/harness"):
        return make_surface(
            repo_root,
            rel,
            "collector_harness_script",
            "source",
            "include",
            "Collector harness script is a primary maintained PowerShell surface.",
            exists,
        )

    if has_prefix(rel, "project_sources/collector/tools"):
        return make_surface(
            repo_root,
            rel,
            "collector_validation_tooling",
            "tooling",
            "include",
            "Collector validation/tooling script is maintained repo PowerShell.",
            exists,
        )

    if rel == "project_sources/collector/PSScriptAnalyzerSettings.psd1":
        return make_surface(
            repo_root,
            rel,
            "collector_validation_tooling",
            "tooling",
            "include",
            "Repository-owned PowerShell analyzer policy is maintained validation tooling.",
            exists,
        )

    if staging_like(rel):
        return make_surface(
            repo_root,
            rel,
            "staging_artifact",
            "staging",
            "exclude",
            "ChatGPT staging scripts are historical execution artifacts, not maintained source.",
            exists,
        )

    if archive_temp_vendor_like(rel):
        return make_surface(
            repo_root,
            rel,
            "archive_temp_vendor_artifact",
            "excluded_artifact",
            "exclude",
            "Archive, temp, or vendor path is not a maintained PowerShell validation target.",
            exists,
        )

    if fixture_like(rel):
        return make_surface(
            repo_root,
            rel,
            "fixture_or_example",
            "fixture",
            "reference",
            "Fixture/example PowerShell is inventoried separately from maintained source targets.",
            exists,
        )

    if has_prefix(rel, ".github/actions") or has_prefix(rel, ".github/pester") or has_prefix(rel, ".github/scripts"):
        return make_surface(
            repo_root,
            rel,
            "github_workflow_support_script",
            "tooling",
            "include",
            "GitHub workflow support script is maintained repo PowerShell.",
            exists,
        )

    if has_prefix(rel, "operator_tools"):
        return make_surface(
            repo_root,
            rel,
            "operator_tooling",
            "tooling",
            "include",
            "Operator tooling PowerShell is maintained repo tooling.",
            exists,
        )

    if has_prefix(rel, "project_sources/validation") or has_prefix(rel, "scripts"):
        return make_surface(
            repo_root,
            rel,
            "validation_tooling",
            "tooling",
            "include",
            "Validation PowerShell is maintained repo tooling.",
            exists,
        )

    return make_surface(
        repo_root,
        rel,
        "unclassified_powershell_surface",
        "unknown",
        "fail",
        "PowerShell-relevant path has no inventory category.",
        exists,
    )


def git_tracked_files(repo_root: Path) -> list[str] | None:
    try:
        completed = subprocess.run(
            ["git", "-C", str(repo_root), "ls-files", "-z"],
            capture_output=True,
            text=False,
            timeout=30,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if completed.returncode != 0:
        return None
    paths = [path.decode("utf-8", errors="ignore") for path in completed.stdout.split(b"\0") if path]
    return sorted(path for path in paths if not is_ignored_discovery_path(path))


def filesystem_files(repo_root: Path) -> list[str]:
    files: list[str] = []
    for path in repo_root.rglob("*"):
        if not path_resolves_inside_repo(path, repo_root):
            continue
        if not path.is_file():
            continue
        try:
            rel = path.relative_to(repo_root).as_posix()
        except (OSError, ValueError):
            continue
        if is_ignored_discovery_path(rel):
            continue
        files.append(rel)
    return sorted(files)


def discover_repo_files(repo_root: Path) -> tuple[list[str], str]:
    tracked = git_tracked_files(repo_root)
    if tracked is not None:
        return tracked, "git ls-files -z"
    return filesystem_files(repo_root), "filesystem recursive scan fallback"


def normalize_changed_files(values: list[str], repo_root: Path) -> list[str]:
    normalized: list[str] = []
    root = repo_root.resolve()
    for value in values:
        raw = value.strip()
        if not raw:
            raise ValueError("Changed-file input must not be blank")
        slash_path = raw.replace("\\", "/")
        path_parts = tuple(part for part in slash_path.split("/") if part)
        if slash_path.startswith("/") or Path(raw).is_absolute() or re.match(r"^[A-Za-z]:", slash_path) is not None:
            raise ValueError(f"Changed-file input must be repo-relative: {value}")
        if ".." in path_parts:
            raise ValueError(f"Changed-file input must not traverse parents: {value}")
        candidate = root / Path(slash_path)
        try:
            repo_relative = candidate.resolve().relative_to(root)
        except (OSError, RuntimeError, ValueError) as exc:
            raise ValueError(f"Changed-file input resolves outside repo root: {value}") from exc
        rel = repo_relative.as_posix()
        if not rel or rel == ".":
            raise ValueError(f"Changed-file input must name a file under repo root: {value}")
        normalized.append(rel)
    return sorted(dict.fromkeys(normalized))


def load_changed_files_from(path: Path) -> list[str]:
    if not path.is_file():
        raise ValueError(f"Changed-files input is missing: {path}")
    try:
        records = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise ValueError(f"Changed-files input could not be read: {path}: {exc}") from exc
    return records if records else [""]


def load_manifest(repo_root: Path) -> dict[str, Any] | None:
    path = repo_root / MANIFEST_PATH
    if not path_is_file_inside_repo(path, repo_root):
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    return data if isinstance(data, dict) else None


def manifest_error(repo_root: Path) -> str | None:
    path = repo_root / MANIFEST_PATH
    if not path_is_file_inside_repo(path, repo_root):
        return f"Collector runtime manifest is missing: {MANIFEST_PATH.as_posix()}"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return f"Invalid JSON in collector runtime manifest {MANIFEST_PATH.as_posix()}: {exc}"
    if not isinstance(data, dict):
        return f"Collector runtime manifest must be a JSON object: {MANIFEST_PATH.as_posix()}"
    path_errors = collector_manifest_path_errors(repo_root)
    if path_errors:
        return "; ".join(path_errors)
    return None


def normalize_manifest_surface_path(value: str, repo_root: Path, field_name: str) -> tuple[str | None, str | None]:
    raw = value.strip()
    if not raw:
        return None, f"Collector runtime manifest {field_name} must not be blank"
    slash_path = raw.replace("\\", "/")
    if Path(slash_path).is_absolute():
        return None, f"Collector runtime manifest {field_name} must be repo-relative, not absolute: {value}"
    if re.match(r"^[A-Za-z]:", slash_path) is not None:
        return None, f"Collector runtime manifest {field_name} must not be drive-qualified: {value}"
    path = Path(slash_path)
    if ".." in path.parts:
        return None, f"Collector runtime manifest {field_name} must not traverse parents: {value}"
    normalized = slash_path
    while normalized.startswith("./"):
        normalized = normalized[2:]
    path = Path(normalized)
    if not normalized or normalized == ".":
        return None, f"Collector runtime manifest {field_name} must name a file under repo root: {value}"
    if ".." in path.parts:
        return None, f"Collector runtime manifest {field_name} must not traverse parents: {value}"
    root = repo_root.resolve()
    try:
        rel = (root / path).resolve().relative_to(root).as_posix()
    except (OSError, RuntimeError, ValueError):
        return None, f"Collector runtime manifest {field_name} resolves outside repo root: {value}"
    if not rel or rel == ".":
        return None, f"Collector runtime manifest {field_name} must name a file under repo root: {value}"
    return rel, None


def collector_manifest_path_entries(repo_root: Path) -> tuple[list[str], list[str]]:
    manifest = load_manifest(repo_root)
    if not manifest:
        return [], []
    paths: list[str] = []
    errors: list[str] = []

    def append_path(value: str, field_name: str) -> None:
        rel, error = normalize_manifest_surface_path(value, repo_root, field_name)
        if error is not None:
            errors.append(error)
        elif rel is not None:
            paths.append(rel)

    wrapper = manifest.get("collector_wrapper_source")
    if isinstance(wrapper, str):
        append_path(wrapper, "collector_wrapper_source")
    part_files = manifest.get("collector_part_files", [])
    if isinstance(part_files, list):
        for index, path in enumerate(part_files):
            if isinstance(path, str):
                append_path(path, f"collector_part_files[{index}]")
    return sorted(dict.fromkeys(paths)), errors


def collector_manifest_path_errors(repo_root: Path) -> list[str]:
    _paths, errors = collector_manifest_path_entries(repo_root)
    return errors


def collector_manifest_paths(repo_root: Path) -> list[str]:
    paths, _errors = collector_manifest_path_entries(repo_root)
    return paths


def harness_source_part_paths(repo_root: Path) -> list[str]:
    root = repo_root / HARNESS_PARTS_ROOT
    if not path_is_dir_inside_repo(root, repo_root):
        return []
    paths: list[str] = []
    for path in root.glob("*.ps1.txt"):
        if not path_resolves_inside_repo(path, repo_root):
            continue
        if not path.is_file():
            continue
        try:
            paths.append(path.relative_to(repo_root).as_posix())
        except (OSError, ValueError):
            continue
    return sorted(paths)


def required_profile_control_path(rel: str) -> bool:
    if rel in {
        REQUIRED_SURFACE_PROFILES_PATH.as_posix(),
        REQUIRED_SURFACE_PROFILE_SUPPLEMENTS_PATH.as_posix(),
    }:
        return True
    return has_prefix(
        rel,
        REQUIRED_SURFACE_PROFILE_SUPPLEMENTS_PATH.parent.as_posix(),
    ) and rel.endswith(".json")


def validate_required_profile_map(data: object, label: str) -> tuple[dict[str, list[str]], str | None]:
    if not isinstance(data, dict):
        return {}, f"Required surface profile must be a JSON object: {label}"
    profiles: dict[str, list[str]] = {}
    for profile_name, paths in data.items():
        if not isinstance(paths, list):
            return {}, f"Required surface profile {profile_name!r} must be a JSON list"
        normalized: list[str] = []
        for index, candidate in enumerate(paths):
            if not isinstance(candidate, str):
                return {}, f"Required surface profile {profile_name!r}[{index}] must be a string"
            normalized.append(candidate)
        profiles[str(profile_name)] = normalized
    return profiles, None


def merge_required_profile_paths(profiles: dict[str, list[str]], additions: dict[str, list[str]]) -> None:
    for profile_name, paths in additions.items():
        merged = profiles.setdefault(profile_name, [])
        seen = set(merged)
        for path in paths:
            if path not in seen:
                merged.append(path)
                seen.add(path)


def load_required_profile_json(repo_root: Path, rel: str, label: str) -> tuple[object | None, str | None]:
    path = repo_root / rel
    if not path_is_file_inside_repo(path, repo_root):
        return None, f"Required surface profile file missing: {rel}"
    try:
        return json.loads(path.read_text(encoding="utf-8")), None
    except json.JSONDecodeError as exc:
        return None, f"Invalid JSON in {label}: {exc}"


def load_required_profile_supplements(repo_root: Path) -> tuple[dict[str, list[str]], str | None]:
    manifest_rel = REQUIRED_SURFACE_PROFILE_SUPPLEMENTS_PATH.as_posix()
    manifest_path = repo_root / manifest_rel
    if not path_is_file_inside_repo(manifest_path, repo_root):
        return {}, None
    manifest, error = load_required_profile_json(
        repo_root,
        manifest_rel,
        f"required surface profile supplement manifest {manifest_rel}",
    )
    if error is not None:
        return {}, error
    if not isinstance(manifest, dict):
        return {}, f"Required surface profile supplement manifest must be a JSON object: {manifest_rel}"
    supplements = manifest.get("supplements")
    if not isinstance(supplements, list) or not all(isinstance(path, str) for path in supplements):
        return {}, f"Required surface profile supplement manifest must define a list of supplement paths: {manifest_rel}"

    profiles: dict[str, list[str]] = {}
    for rel in supplements:
        path = Path(rel)
        if path.is_absolute() or ".." in path.parts or re.match(r"^[A-Za-z]:", rel.replace("\\", "/")):
            return {}, f"Required surface profile supplement path must be repo-relative: {rel}"
        data, error = load_required_profile_json(
            repo_root,
            rel,
            f"required surface profile supplement {rel}",
        )
        if error is not None:
            return {}, error
        supplement_profiles, error = validate_required_profile_map(data, rel)
        if error is not None:
            return {}, error
        merge_required_profile_paths(profiles, supplement_profiles)
    return profiles, None


def read_required_profiles(repo_root: Path) -> tuple[dict[str, list[str]], str | None]:
    base_rel = REQUIRED_SURFACE_PROFILES_PATH.as_posix()
    base_path = repo_root / base_rel
    if not path_is_file_inside_repo(base_path, repo_root):
        return {}, None
    try:
        data = json.loads(base_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return {}, f"Invalid JSON in required surface profile {base_rel}: {exc}"
    profiles, error = validate_required_profile_map(data, base_rel)
    if error is not None:
        return {}, error
    supplements, error = load_required_profile_supplements(repo_root)
    if error is not None:
        return {}, error
    merge_required_profile_paths(profiles, supplements)
    return profiles, None


def read_required_profile_harness_paths(repo_root: Path) -> tuple[list[str], str | None]:
    profiles, error = read_required_profiles(repo_root)
    if error is not None:
        return [], error
    expected: set[str] = set()
    for paths in profiles.values():
        for candidate in paths:
            if has_prefix(candidate, HARNESS_PARTS_ROOT.as_posix()) and candidate.endswith(".ps1.txt"):
                expected.add(candidate)
    return sorted(expected), None


def required_profile_harness_paths(repo_root: Path) -> list[str]:
    paths, _ = read_required_profile_harness_paths(repo_root)
    return paths


def expand_changed_files(repo_root: Path, changed_files: list[str]) -> tuple[list[str], dict[str, Any]]:
    normalized = normalize_changed_files(changed_files, repo_root)
    expanded: set[str] = set(normalized)
    rules: list[dict[str, Any]] = []
    for rel in normalized:
        added: list[str] = []
        if rel == MANIFEST_PATH.as_posix():
            added = collector_manifest_paths(repo_root)
        elif rel == "project_sources/collector/harness/assemble_run_DCOIR_Tests.ps1":
            added = harness_source_part_paths(repo_root)
        elif required_profile_control_path(rel):
            added = harness_source_part_paths(repo_root)
        elif is_workflow_yaml(rel):
            added = [rel]
        if added:
            expanded.update(added)
            rules.append({"changed_path": rel, "rule": "dependency_expansion", "added_paths": added})
    return sorted(expanded), {
        "input_paths": normalized,
        "expanded_paths": sorted(expanded),
        "rules": rules,
        "boundary": "Dependency expansion covers collector manifest paths, harness assembler source parts, and PowerShell-bearing workflow/action YAML. Other changed paths are classified directly.",
    }


def append_missing_authoritative_surfaces(repo_root: Path, surfaces: list[dict[str, Any]]) -> None:
    existing = {entry["path"] for entry in surfaces}
    for rel in collector_manifest_paths(repo_root):
        if rel not in existing and not repo_file_exists(repo_root, rel):
            surfaces.append(
                make_surface(
                    repo_root,
                    rel,
                    "missing_authoritative_surface",
                    "missing",
                    "fail",
                    "Collector runtime manifest references this PowerShell surface, but the file is missing.",
                    False,
                )
            )


def collect_surfaces(repo_root: Path, changed_files: list[str] | None = None) -> tuple[list[dict[str, Any]], str, dict[str, Any] | None]:
    discovered, source = discover_repo_files(repo_root)
    dependency_expansion = None
    if changed_files is not None:
        candidates, dependency_expansion = expand_changed_files(repo_root, changed_files)
    else:
        candidates = discovered
    surfaces: list[dict[str, Any]] = []
    for rel in candidates:
        exists = repo_file_exists(repo_root, rel)
        if changed_files is not None and not exists and not (is_powershell_file(rel) or is_workflow_yaml(rel)):
            continue
        surface = classify_surface(repo_root, rel, exists)
        if surface is not None:
            surfaces.append(surface)
    if changed_files is None:
        append_missing_authoritative_surfaces(repo_root, surfaces)
    return sorted(surfaces, key=lambda entry: entry["path"]), source, dependency_expansion


__all__ = [
    "classify_surface",
    "git_tracked_files",
    "filesystem_files",
    "discover_repo_files",
    "normalize_changed_files",
    "load_changed_files_from",
    "load_manifest",
    "manifest_error",
    "normalize_manifest_surface_path",
    "collector_manifest_path_entries",
    "collector_manifest_path_errors",
    "collector_manifest_paths",
    "harness_source_part_paths",
    "required_profile_control_path",
    "validate_required_profile_map",
    "merge_required_profile_paths",
    "load_required_profile_json",
    "load_required_profile_supplements",
    "read_required_profiles",
    "read_required_profile_harness_paths",
    "required_profile_harness_paths",
    "expand_changed_files",
    "append_missing_authoritative_surfaces",
    "collect_surfaces",
]
