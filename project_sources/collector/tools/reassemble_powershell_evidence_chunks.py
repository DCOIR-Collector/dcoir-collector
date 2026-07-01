#!/usr/bin/env python3
"""Reassemble and validate connector-sized PowerShell evidence chunks.

The issue #349 / PR #350 chunk sidecar is intentionally additive: it makes the
generated PowerShell evidence reports small enough for connector-only reads and
writes, but it does not replace the canonical report files by itself. This tool
validates that sidecar without blurring those boundaries.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

DEFAULT_CHUNK_ROOT = Path("project_sources/collector/report_chunks/issue349_pr350_powershell_evidence")
ROOT_SCHEMA_VERSION = "dcoir_powershell_evidence_chunk_set_v1"
REPORT_MANIFEST_SCHEMA_VERSION = "dcoir_report_chunk_manifest_v1"
CHUNK_SCHEMA_VERSION = "dcoir_report_chunk_v1"


class ChunkValidationError(RuntimeError):
    """Raised when a chunk set cannot be safely reassembled."""


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def json_dumps(value: Any) -> str:
    return json.dumps(value, indent=2) + "\n"


def normalize_repo_path(value: str) -> str:
    slash_path = value.replace("\\", "/")
    while slash_path.startswith("./"):
        slash_path = slash_path[2:]
    return Path(slash_path).as_posix()


def is_absolute_repo_input(value: str) -> bool:
    raw = value.strip()
    slash_path = raw.replace("\\", "/")
    return (
        slash_path.startswith("/")
        or re.match(r"^[A-Za-z]:", slash_path) is not None
        or Path(raw).is_absolute()
    )


def safe_repo_path(value: Any, *, repo_root: Path, label: str) -> Path:
    if not isinstance(value, str) or not value.strip():
        raise ChunkValidationError(f"{label}: path must be a non-empty string")
    raw = value.strip()
    slash_path = raw.replace("\\", "/")
    raw_parts = tuple(part for part in slash_path.split("/") if part)
    rel = normalize_repo_path(raw)
    parts = Path(rel).parts
    if (
        not raw
        or is_absolute_repo_input(raw)
        or ".." in raw_parts
        or ".." in parts
        or Path(rel).is_absolute()
    ):
        raise ChunkValidationError(f"{label}: path must be repo-relative without traversal")
    path = repo_root / rel
    try:
        path.resolve().relative_to(repo_root.resolve())
    except (OSError, RuntimeError, ValueError) as exc:
        raise ChunkValidationError(f"{label}: path must resolve inside the repository root") from exc
    return path


def safe_sidecar_path(value: Any, *, repo_root: Path, chunk_root: Path, label: str) -> Path:
    path = safe_repo_path(value, repo_root=repo_root, label=label)
    try:
        path.resolve().relative_to(chunk_root.resolve())
    except (OSError, RuntimeError, ValueError) as exc:
        raise ChunkValidationError(f"{label}: path must resolve inside the chunk root") from exc
    return path


def relpath(path: Path, repo_root: Path) -> str:
    return path.resolve().relative_to(repo_root.resolve()).as_posix()


def read_json_file(path: Path, *, label: str) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ChunkValidationError(f"{label}: missing file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ChunkValidationError(f"{label}: invalid JSON: {path}: {exc}") from exc
    except OSError as exc:
        raise ChunkValidationError(f"{label}: could not read file: {path}: {exc}") from exc


def read_chunk_bytes(path: Path, *, label: str) -> bytes:
    try:
        return path.read_bytes()
    except FileNotFoundError as exc:
        raise ChunkValidationError(f"{label}: missing chunk file: {path}") from exc
    except OSError as exc:
        raise ChunkValidationError(f"{label}: could not read chunk file: {path}: {exc}") from exc


def pointer_parts(pointer: Any, *, label: str) -> list[str]:
    if not isinstance(pointer, str):
        raise ChunkValidationError(f"{label}: json_pointer must be a string")
    if pointer == "":
        return []
    if not pointer.startswith("/"):
        raise ChunkValidationError(f"{label}: json_pointer must be empty or start with '/'")
    return [part.replace("~1", "/").replace("~0", "~") for part in pointer.split("/")[1:]]


def require_mapping(value: Any, *, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ChunkValidationError(f"{label}: expected an object")
    return value


def require_list(value: Any, *, label: str) -> list[Any]:
    if not isinstance(value, list):
        raise ChunkValidationError(f"{label}: expected a list")
    return value


def require_int_field(
    value: dict[str, Any],
    key: str,
    *,
    label: str,
    minimum: int | None = None,
) -> int:
    field_value = value.get(key)
    if not isinstance(field_value, int):
        raise ChunkValidationError(f"{label}: {key} must be an integer")
    if minimum is not None and field_value < minimum:
        raise ChunkValidationError(f"{label}: {key} must be at least {minimum}")
    return field_value


def ensure_object_parent(document: dict[str, Any], pointer: str, *, label: str) -> tuple[dict[str, Any], str] | None:
    parts = pointer_parts(pointer, label=label)
    if not parts:
        return None
    current: Any = document
    for part in parts[:-1]:
        if not isinstance(current, dict):
            raise ChunkValidationError(f"{label}: parent path is not an object before /{part}")
        if part not in current:
            current[part] = {}
        elif not isinstance(current[part], dict):
            raise ChunkValidationError(f"{label}: parent path /{'/'.join(parts[:-1])} is not an object")
        current = current[part]
    if not isinstance(current, dict):
        raise ChunkValidationError(f"{label}: parent path is not an object")
    return current, parts[-1]


def set_json_value(document: dict[str, Any], pointer: str, value: Any, *, label: str, assigned: set[str]) -> Any:
    if pointer in assigned:
        raise ChunkValidationError(f"{label}: duplicate json_value pointer {pointer}")
    assigned.add(pointer)
    parent_info = ensure_object_parent(document, pointer, label=label)
    if parent_info is None:
        return value
    parent, key = parent_info
    if key in parent:
        raise ChunkValidationError(f"{label}: pointer {pointer} would overwrite an existing value")
    parent[key] = value
    return document


def merge_json_object_members(document: dict[str, Any], pointer: str, value: Any, *, label: str) -> dict[str, Any]:
    members = require_mapping(value, label=f"{label}: data")
    parts = pointer_parts(pointer, label=label)
    current: Any = document
    for part in parts:
        if not isinstance(current, dict):
            raise ChunkValidationError(f"{label}: parent path is not an object before /{part}")
        if part not in current:
            current[part] = {}
        elif not isinstance(current[part], dict):
            raise ChunkValidationError(f"{label}: pointer {pointer} targets a non-object")
        current = current[part]
    target = require_mapping(current, label=f"{label}: target")
    for key, member_value in members.items():
        if key in target:
            raise ChunkValidationError(f"{label}: duplicate object member {pointer}/{key}")
        target[key] = member_value
    return document


def apply_json_list_items(
    document: dict[str, Any],
    pointer: str,
    items: Any,
    *,
    label: str,
    item_start: Any,
    item_count: Any,
) -> dict[str, Any]:
    values = require_list(items, label=f"{label}: data")
    if not isinstance(item_start, int) or item_start < 0:
        raise ChunkValidationError(f"{label}: item_start must be a non-negative integer")
    if item_count != len(values):
        raise ChunkValidationError(f"{label}: item_count does not match data length")
    parent_info = ensure_object_parent(document, pointer, label=label)
    if parent_info is None:
        if item_start != 0:
            raise ChunkValidationError(f"{label}: root list item_start must be 0")
        return values  # type: ignore[return-value]
    parent, key = parent_info
    if key not in parent:
        parent[key] = []
    target = require_list(parent[key], label=f"{label}: target")
    if item_start != len(target):
        raise ChunkValidationError(
            f"{label}: list range for {pointer} has a gap or overlap; expected start {len(target)}, got {item_start}"
        )
    target.extend(values)
    return document


def validate_chunk_metadata(
    chunk: dict[str, Any],
    chunk_info: dict[str, Any],
    report_manifest: dict[str, Any],
    *,
    label: str,
) -> None:
    checks = {
        "schema_version": CHUNK_SCHEMA_VERSION,
        "chunk_kind": chunk_info.get("chunk_kind"),
        "report_id": report_manifest.get("report_id"),
        "source_report": report_manifest.get("source_report"),
        "source_sha256": report_manifest.get("source_sha256"),
    }
    for key, expected in checks.items():
        if chunk.get(key) != expected:
            raise ChunkValidationError(f"{label}: {key} mismatch: expected {expected!r}, got {chunk.get(key)!r}")
    if chunk_info.get("format") and chunk_info.get("format") != report_manifest.get("source_format"):
        raise ChunkValidationError(f"{label}: chunk format does not match report format")
    if "json_pointer" in chunk_info and chunk.get("json_pointer") != chunk_info.get("json_pointer"):
        raise ChunkValidationError(f"{label}: json_pointer mismatch")
    if "item_start" in chunk_info and chunk.get("item_start") != chunk_info.get("item_start"):
        raise ChunkValidationError(f"{label}: item_start mismatch")
    if "item_count" in chunk_info and chunk.get("item_count") != chunk_info.get("item_count"):
        raise ChunkValidationError(f"{label}: item_count mismatch")
    if "chunk_index" in chunk_info and chunk.get("chunk_index") != chunk_info.get("chunk_index"):
        raise ChunkValidationError(f"{label}: chunk_index mismatch")
    if "key_count" in chunk_info and chunk.get("key_count") != chunk_info.get("key_count"):
        raise ChunkValidationError(f"{label}: key_count mismatch")


def require_chunk_index(chunk: dict[str, Any], chunk_info: dict[str, Any], *, label: str) -> None:
    if "chunk_index" not in chunk_info or not isinstance(chunk_info["chunk_index"], int):
        raise ChunkValidationError(f"{label}: manifest entry must include integer chunk_index")
    if "chunk_index" not in chunk or not isinstance(chunk["chunk_index"], int):
        raise ChunkValidationError(f"{label}: chunk body must include integer chunk_index")


def require_key_count(chunk: dict[str, Any], chunk_info: dict[str, Any], *, label: str) -> None:
    if "key_count" not in chunk_info or not isinstance(chunk_info["key_count"], int):
        raise ChunkValidationError(f"{label}: manifest entry must include integer key_count")
    if "key_count" not in chunk or not isinstance(chunk["key_count"], int):
        raise ChunkValidationError(f"{label}: chunk body must include integer key_count")


def validate_report_manifest(
    report_manifest: Any,
    root_report: dict[str, Any],
    *,
    label: str,
) -> dict[str, Any]:
    manifest = require_mapping(report_manifest, label=label)
    expected_pairs = {
        "schema_version": REPORT_MANIFEST_SCHEMA_VERSION,
        "report_id": root_report.get("report_id"),
        "source_format": root_report.get("source_format"),
        "source_report": root_report.get("source_report"),
        "source_sha256": root_report.get("source_sha256"),
        "source_bytes": root_report.get("source_bytes"),
        "chunk_count": root_report.get("chunk_count"),
    }
    for key, expected in expected_pairs.items():
        if manifest.get(key) != expected:
            raise ChunkValidationError(f"{label}: {key} mismatch: expected {expected!r}, got {manifest.get(key)!r}")
    chunks = manifest.get("chunks")
    if not isinstance(chunks, list) or len(chunks) != manifest.get("chunk_count"):
        raise ChunkValidationError(f"{label}: chunks length does not match chunk_count")
    return manifest


def reassemble_markdown(
    report_manifest: dict[str, Any],
    *,
    repo_root: Path,
    chunk_root: Path,
) -> tuple[bytes, list[dict[str, Any]]]:
    output = bytearray()
    chunk_results: list[dict[str, Any]] = []
    seen_paths: set[str] = set()
    for index, chunk_info in enumerate(report_manifest["chunks"]):
        chunk_label = f"{report_manifest['source_report']} chunk {index}"
        chunk_info = require_mapping(chunk_info, label=chunk_label)
        if chunk_info.get("chunk_kind") != "markdown_section":
            raise ChunkValidationError(
                f"{chunk_label}: unsupported Markdown chunk kind {chunk_info.get('chunk_kind')!r}"
            )
        chunk_path = safe_sidecar_path(
            chunk_info.get("path"),
            repo_root=repo_root,
            chunk_root=chunk_root,
            label=chunk_label,
        )
        chunk_rel = relpath(chunk_path, repo_root)
        if chunk_rel in seen_paths:
            raise ChunkValidationError(f"{chunk_label}: duplicate chunk path {chunk_rel}")
        seen_paths.add(chunk_rel)
        raw = read_chunk_bytes(chunk_path, label=chunk_label)
        if chunk_info.get("bytes") != len(raw):
            raise ChunkValidationError(f"{chunk_label}: byte count mismatch")
        digest = sha256_bytes(raw)
        if chunk_info.get("sha256") != digest:
            raise ChunkValidationError(f"{chunk_label}: sha256 mismatch")
        output.extend(raw)
        chunk_results.append({"path": chunk_rel, "sha256": digest, "bytes": len(raw), "status": "pass"})
    return bytes(output), chunk_results


def reassemble_json_text_slices(
    report_manifest: dict[str, Any],
    *,
    repo_root: Path,
    chunk_root: Path,
) -> tuple[bytes, Any, list[dict[str, Any]]]:
    if report_manifest.get("reassembly_mode") != "byte_exact_text_slices":
        raise ChunkValidationError(
            f"{report_manifest['source_report']}: json_text_slice reports require "
            "reassembly_mode 'byte_exact_text_slices'"
        )
    output = bytearray()
    chunk_results: list[dict[str, Any]] = []
    seen_paths: set[str] = set()
    expected_offset = 0
    for index, chunk_info in enumerate(report_manifest["chunks"]):
        chunk_label = f"{report_manifest['source_report']} chunk {index}"
        chunk_info = require_mapping(chunk_info, label=chunk_label)
        if chunk_info.get("chunk_kind") != "json_text_slice":
            raise ChunkValidationError(
                f"{chunk_label}: json_text_slice reports cannot mix chunk kind {chunk_info.get('chunk_kind')!r}"
            )
        if chunk_info.get("format") != report_manifest.get("source_format"):
            raise ChunkValidationError(f"{chunk_label}: chunk format does not match report format")
        chunk_index = require_int_field(chunk_info, "chunk_index", label=chunk_label, minimum=0)
        if chunk_index != index:
            raise ChunkValidationError(f"{chunk_label}: chunk_index must match manifest order")
        byte_start = require_int_field(chunk_info, "byte_start", label=chunk_label, minimum=0)
        byte_end = require_int_field(chunk_info, "byte_end", label=chunk_label, minimum=0)
        if byte_start != expected_offset:
            raise ChunkValidationError(
                f"{chunk_label}: byte range has a gap or overlap; expected start {expected_offset}, got {byte_start}"
            )
        if byte_end <= byte_start:
            raise ChunkValidationError(f"{chunk_label}: byte_end must be greater than byte_start")
        chunk_path = safe_sidecar_path(
            chunk_info.get("path"),
            repo_root=repo_root,
            chunk_root=chunk_root,
            label=chunk_label,
        )
        chunk_rel = relpath(chunk_path, repo_root)
        if chunk_rel in seen_paths:
            raise ChunkValidationError(f"{chunk_label}: duplicate chunk path {chunk_rel}")
        seen_paths.add(chunk_rel)
        raw = read_chunk_bytes(chunk_path, label=chunk_label)
        if chunk_info.get("bytes") != len(raw):
            raise ChunkValidationError(f"{chunk_label}: byte count mismatch")
        if byte_end - byte_start != len(raw):
            raise ChunkValidationError(f"{chunk_label}: byte range length does not match chunk bytes")
        digest = sha256_bytes(raw)
        if chunk_info.get("sha256") != digest:
            raise ChunkValidationError(f"{chunk_label}: sha256 mismatch")
        output.extend(raw)
        expected_offset = byte_end
        chunk_results.append(
            {
                "path": chunk_rel,
                "sha256": digest,
                "bytes": len(raw),
                "byte_start": byte_start,
                "byte_end": byte_end,
                "status": "pass",
            }
        )

    if expected_offset != report_manifest.get("source_bytes"):
        raise ChunkValidationError(
            f"{report_manifest['source_report']}: text-slice bytes do not cover source_bytes"
        )
    reconstructed_bytes = bytes(output)
    try:
        document = json.loads(reconstructed_bytes.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ChunkValidationError(f"{report_manifest['source_report']}: reassembled JSON is invalid: {exc}") from exc
    return reconstructed_bytes, document, chunk_results


def reassemble_json(
    report_manifest: dict[str, Any],
    *,
    repo_root: Path,
    chunk_root: Path,
) -> tuple[bytes, Any, list[dict[str, Any]]]:
    chunk_infos = [
        require_mapping(chunk_info, label=f"{report_manifest['source_report']} chunk {index}")
        for index, chunk_info in enumerate(report_manifest["chunks"])
    ]
    text_slice_count = sum(1 for chunk_info in chunk_infos if chunk_info.get("chunk_kind") == "json_text_slice")
    if text_slice_count:
        if text_slice_count != len(chunk_infos):
            raise ChunkValidationError(
                f"{report_manifest['source_report']}: json_text_slice chunks cannot be mixed with semantic JSON chunks"
            )
        report_manifest = dict(report_manifest)
        report_manifest["chunks"] = chunk_infos
        return reassemble_json_text_slices(report_manifest, repo_root=repo_root, chunk_root=chunk_root)

    document: Any = {}
    assigned_values: set[str] = set()
    chunk_results: list[dict[str, Any]] = []
    seen_paths: set[str] = set()
    for index, chunk_info in enumerate(chunk_infos):
        chunk_label = f"{report_manifest['source_report']} chunk {index}"
        chunk_path = safe_sidecar_path(
            chunk_info.get("path"),
            repo_root=repo_root,
            chunk_root=chunk_root,
            label=chunk_label,
        )
        chunk_rel = relpath(chunk_path, repo_root)
        if chunk_rel in seen_paths:
            raise ChunkValidationError(f"{chunk_label}: duplicate chunk path {chunk_rel}")
        seen_paths.add(chunk_rel)
        raw = read_chunk_bytes(chunk_path, label=chunk_label)
        if chunk_info.get("bytes") != len(raw):
            raise ChunkValidationError(f"{chunk_label}: byte count mismatch")
        digest = sha256_bytes(raw)
        if chunk_info.get("sha256") != digest:
            raise ChunkValidationError(f"{chunk_label}: sha256 mismatch")
        try:
            chunk = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ChunkValidationError(f"{chunk_label}: invalid JSON chunk: {exc}") from exc
        chunk = require_mapping(chunk, label=chunk_label)
        validate_chunk_metadata(chunk, chunk_info, report_manifest, label=chunk_label)
        kind = chunk.get("chunk_kind")
        pointer = chunk.get("json_pointer")
        if kind == "json_value":
            if not isinstance(document, dict):
                raise ChunkValidationError(f"{chunk_label}: root document is not an object")
            document = set_json_value(document, pointer, chunk.get("data"), label=chunk_label, assigned=assigned_values)
        elif kind == "json_object_members":
            require_chunk_index(chunk, chunk_info, label=chunk_label)
            require_key_count(chunk, chunk_info, label=chunk_label)
            members = require_mapping(chunk.get("data"), label=f"{chunk_label}: data")
            if "key_count" in chunk and chunk["key_count"] != len(members):
                raise ChunkValidationError(f"{chunk_label}: key_count does not match data length")
            if not isinstance(document, dict):
                raise ChunkValidationError(f"{chunk_label}: root document is not an object")
            document = merge_json_object_members(document, pointer, members, label=chunk_label)
        elif kind == "json_list_items":
            require_chunk_index(chunk, chunk_info, label=chunk_label)
            if not isinstance(document, dict):
                raise ChunkValidationError(f"{chunk_label}: root document is not an object")
            document = apply_json_list_items(
                document,
                pointer,
                chunk.get("data"),
                label=chunk_label,
                item_start=chunk.get("item_start"),
                item_count=chunk.get("item_count"),
            )
        else:
            raise ChunkValidationError(f"{chunk_label}: unsupported JSON chunk kind {kind!r}")
        chunk_results.append({"path": chunk_rel, "sha256": digest, "bytes": len(raw), "status": "pass"})
    text = json_dumps(document)
    return text.encode("utf-8"), document, chunk_results


def compare_canonical(
    *,
    repo_root: Path,
    report_manifest: dict[str, Any],
    reconstructed_bytes: bytes,
    reconstructed_document: Any | None,
) -> dict[str, Any]:
    source_path = safe_repo_path(
        report_manifest.get("source_report"),
        repo_root=repo_root,
        label="canonical source report",
    )
    if not source_path.exists():
        return {"checked": False, "status": "missing", "path": relpath(source_path, repo_root)}
    raw = source_path.read_bytes()
    exact_match = raw == reconstructed_bytes
    result: dict[str, Any] = {
        "checked": True,
        "path": relpath(source_path, repo_root),
        "bytes": len(raw),
        "sha256": sha256_bytes(raw),
        "source_sha256_match": sha256_bytes(raw) == report_manifest.get("source_sha256"),
        "exact_reconstruction_match": exact_match,
    }
    if report_manifest.get("source_format") == "json" and reconstructed_document is not None:
        try:
            result["semantic_reconstruction_match"] = json.loads(raw.decode("utf-8")) == reconstructed_document
        except (UnicodeDecodeError, json.JSONDecodeError):
            result["semantic_reconstruction_match"] = False
    result["status"] = "pass" if exact_match else "mismatch"
    return result


def validate_chunk_set(args: argparse.Namespace) -> tuple[dict[str, Any], dict[str, bytes]]:
    repo_root = Path(args.repo_root).resolve()
    chunk_root = safe_repo_path(args.chunk_root, repo_root=repo_root, label="chunk root")
    manifest_path = chunk_root / "manifest.json"
    try:
        manifest_path.resolve().relative_to(repo_root)
    except (OSError, RuntimeError, ValueError) as exc:
        raise ChunkValidationError("root manifest path must resolve inside the repository root") from exc
    root_manifest = require_mapping(read_json_file(manifest_path, label="root manifest"), label="root manifest")
    if root_manifest.get("schema_version") != ROOT_SCHEMA_VERSION:
        raise ChunkValidationError("root manifest: unsupported schema_version")
    if root_manifest.get("issue") != 349:
        raise ChunkValidationError("root manifest: issue must be 349")
    if root_manifest.get("pull_request") != 350:
        raise ChunkValidationError("root manifest: pull_request must be 350")
    reports = root_manifest.get("reports")
    if not isinstance(reports, list) or len(reports) != root_manifest.get("report_count"):
        raise ChunkValidationError("root manifest: report_count does not match reports length")

    results: list[dict[str, Any]] = []
    reconstructed_outputs: dict[str, bytes] = {}
    errors: list[str] = []
    warnings: list[str] = []
    seen_manifests: set[str] = set()
    seen_source_reports: set[str] = set()
    strict_source_hash = bool(args.strict_source_hash)
    compare_canonical_reports = bool(args.compare_canonical)
    require_canonical_parity = bool(args.require_canonical_parity)
    allow_lossy_json_order = bool(args.allow_lossy_json_order_reconstruction)
    actual_files = {relpath(path, repo_root) for path in chunk_root.rglob("*") if path.is_file()}
    expected_files = {relpath(manifest_path, repo_root)}
    if root_manifest.get("file_count") != len(actual_files):
        errors.append(
            "root manifest: "
            f"file_count {root_manifest.get('file_count')!r} does not match actual file count {len(actual_files)}"
        )
    top_level_files = root_manifest.get("top_level_files", [])
    if top_level_files is None:
        top_level_files = []
    if not isinstance(top_level_files, list):
        raise ChunkValidationError("root manifest: top_level_files must be a list when present")
    for index, entry_value in enumerate(top_level_files):
        entry = require_mapping(entry_value, label=f"top_level_files[{index}]")
        top_path = safe_sidecar_path(
            entry.get("path"),
            repo_root=repo_root,
            chunk_root=chunk_root,
            label=f"top_level_files[{index}]",
        )
        top_rel = relpath(top_path, repo_root)
        expected_files.add(top_rel)
        raw = read_chunk_bytes(top_path, label=f"top_level_files[{index}]")
        if entry.get("bytes") != len(raw):
            errors.append(f"{top_rel}: byte count does not match top_level_files entry")
        if entry.get("sha256") != sha256_bytes(raw):
            errors.append(f"{top_rel}: sha256 does not match top_level_files entry")

    for report_index, root_report_value in enumerate(reports):
        root_report = require_mapping(root_report_value, label=f"root report {report_index}")
        report_id = str(root_report.get("report_id"))
        source_report = root_report.get("source_report")
        if not isinstance(source_report, str) or not source_report.strip():
            raise ChunkValidationError(f"{report_id}: source_report must be a non-empty string")
        normalized_source_report = normalize_repo_path(source_report)
        if normalized_source_report in seen_source_reports:
            raise ChunkValidationError(f"{report_id}: duplicate source_report {normalized_source_report!r}")
        seen_source_reports.add(normalized_source_report)
        manifest_file = safe_sidecar_path(
            root_report.get("manifest_path"),
            repo_root=repo_root,
            chunk_root=chunk_root,
            label=f"{report_id} manifest",
        )
        manifest_rel = relpath(manifest_file, repo_root)
        if manifest_rel in seen_manifests:
            raise ChunkValidationError(f"{report_id}: duplicate report manifest path {manifest_rel}")
        seen_manifests.add(manifest_rel)
        report_manifest = validate_report_manifest(
            read_json_file(manifest_file, label=f"{report_id} manifest"),
            root_report,
            label=f"{report_id} manifest",
        )
        reconstructed_document: Any | None = None
        if report_manifest["source_format"] == "markdown":
            reconstructed_bytes, chunk_results = reassemble_markdown(
                report_manifest,
                repo_root=repo_root,
                chunk_root=chunk_root,
            )
        elif report_manifest["source_format"] == "json":
            reconstructed_bytes, reconstructed_document, chunk_results = reassemble_json(
                report_manifest,
                repo_root=repo_root,
                chunk_root=chunk_root,
            )
        else:
            raise ChunkValidationError(f"{report_id}: unsupported source_format {report_manifest['source_format']!r}")

        reconstructed_sha = sha256_bytes(reconstructed_bytes)
        source_sha_match = reconstructed_sha == report_manifest["source_sha256"]
        source_bytes_match = len(reconstructed_bytes) == report_manifest["source_bytes"]
        report_result: dict[str, Any] = {
            "report_id": report_id,
            "source_format": report_manifest["source_format"],
            "source_report": report_manifest["source_report"],
            "manifest_path": manifest_rel,
            "chunk_count": len(chunk_results),
            "chunk_integrity": "pass",
            "byte_exact": source_sha_match,
            "reconstructed_bytes": len(reconstructed_bytes),
            "reconstructed_sha256": reconstructed_sha,
            "source_bytes": report_manifest["source_bytes"],
            "source_sha256": report_manifest["source_sha256"],
            "source_bytes_match": source_bytes_match,
            "source_sha256_match": source_sha_match,
            "strict_source_hash_required_for_byte_readiness": not source_sha_match,
            "chunks": chunk_results,
        }
        if not source_bytes_match:
            errors.append(f"{report_manifest['source_report']}: reconstructed byte count does not match source_bytes")
        if not source_sha_match:
            message = (
                f"{report_manifest['source_report']}: reconstructed SHA-256 does not match source_sha256; "
                "for JSON this can indicate missing byte-order metadata in the sidecar schema"
            )
            if (
                allow_lossy_json_order
                and report_manifest["source_format"] == "json"
                and not strict_source_hash
            ):
                warnings.append(message)
            else:
                errors.append(message)
        if compare_canonical_reports:
            canonical_parity = compare_canonical(
                repo_root=repo_root,
                report_manifest=report_manifest,
                reconstructed_bytes=reconstructed_bytes,
                reconstructed_document=reconstructed_document,
            )
            report_result["canonical_parity"] = canonical_parity
            if canonical_parity.get("status") != "pass":
                message = (
                    f"{report_manifest['source_report']}: "
                    f"canonical parity status is {canonical_parity.get('status')}"
                )
                if require_canonical_parity:
                    errors.append(message)
                else:
                    warnings.append(message)
        if source_sha_match:
            reconstructed_outputs[normalize_repo_path(report_manifest["source_report"])] = reconstructed_bytes
        expected_files.add(manifest_rel)
        expected_files.update(chunk_result["path"] for chunk_result in chunk_results)
        results.append(report_result)

    missing_files = sorted(expected_files - actual_files)
    unexpected_files = sorted(actual_files - expected_files)
    if missing_files:
        errors.append(f"chunk sidecar is missing expected files: {missing_files}")
    if unexpected_files:
        errors.append(f"chunk sidecar has unexpected files: {unexpected_files}")

    chunk_integrity_success = not any(
        "canonical parity status" not in error and "reconstructed SHA-256 does not match source_sha256" not in error
        for error in errors
    )
    reconstruction_exact_success = all(report["byte_exact"] for report in results)
    canonical_parity_success = (
        all(report.get("canonical_parity", {}).get("status") == "pass" for report in results)
        if compare_canonical_reports
        else None
    )
    readiness_gaps: list[str] = []
    if not reconstruction_exact_success:
        readiness_gaps.append(
            "byte-exact source-hash validation is not clean; "
            "only --allow-lossy-json-order-reconstruction can downgrade this to a warning"
        )
    if compare_canonical_reports and not canonical_parity_success:
        readiness_gaps.append(
            "canonical reports do not match the reassembled chunk sidecar; "
            "sidecar validation is not canonical replacement"
        )
    if not compare_canonical_reports:
        readiness_gaps.append(
            "canonical reports were not compared; "
            "sidecar validation is not canonical replacement"
        )

    output = {
        "schema_version": "dcoir_powershell_evidence_chunk_validation_v1",
        "chunk_root": relpath(chunk_root, repo_root),
        "issue": root_manifest.get("issue"),
        "pull_request": root_manifest.get("pull_request"),
        "report_count": len(results),
        "strict_source_hash": strict_source_hash,
        "compare_canonical": compare_canonical_reports,
        "require_canonical_parity": require_canonical_parity,
        "allow_lossy_json_order_reconstruction": allow_lossy_json_order,
        "chunk_integrity_success": chunk_integrity_success,
        "reconstruction_exact_success": reconstruction_exact_success,
        "canonical_parity_success": canonical_parity_success,
        "readiness_gaps": readiness_gaps,
        "validation": {
            "success": not errors,
            "errors": errors,
            "warnings": warnings,
        },
        "reports": results,
    }
    return output, reconstructed_outputs


def write_outputs(outputs: dict[str, bytes], *, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    for source_report, data in outputs.items():
        rel = normalize_repo_path(source_report)
        out_path = output_dir / rel
        try:
            out_path.resolve().relative_to(output_dir.resolve())
        except (OSError, RuntimeError, ValueError) as exc:
            raise ChunkValidationError(f"write output path escapes output directory: {source_report}") from exc
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_bytes(data)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", default=".", help="Repository root containing the chunk sidecar.")
    parser.add_argument(
        "--chunk-root",
        default=DEFAULT_CHUNK_ROOT.as_posix(),
        help="Repo-relative chunk sidecar root.",
    )
    parser.add_argument(
        "--strict-source-hash",
        action="store_true",
        help="Fail when reconstructed bytes do not match the manifest source_sha256.",
    )
    parser.add_argument(
        "--allow-lossy-json-order-reconstruction",
        action="store_true",
        help="Permit JSON source-hash mismatches as warnings when chunk values reassemble but byte order differs.",
    )
    parser.add_argument(
        "--compare-canonical",
        action="store_true",
        help="Compare reconstructed outputs with canonical report files when they exist.",
    )
    parser.add_argument(
        "--require-canonical-parity",
        action="store_true",
        help="Fail when --compare-canonical finds missing or mismatched canonical reports.",
    )
    parser.add_argument(
        "--write-output-dir",
        default="",
        help="Optional directory for reconstructed outputs. Does not overwrite canonical report paths.",
    )
    parser.add_argument(
        "--json-output",
        default="",
        help="Optional path for the validation report JSON.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        report, outputs = validate_chunk_set(args)
        if args.write_output_dir:
            if not report["validation"]["success"]:
                raise ChunkValidationError("refusing to write reconstructed outputs because validation did not succeed")
            write_outputs(outputs, output_dir=Path(args.write_output_dir).resolve())
        rendered = json_dumps(report)
        if args.json_output:
            output_path = Path(args.json_output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(rendered, encoding="utf-8")
        else:
            sys.stdout.write(rendered)
        return 0 if report["validation"]["success"] else 1
    except ChunkValidationError as exc:
        error_report = {
            "schema_version": "dcoir_powershell_evidence_chunk_validation_v1",
            "validation": {"success": False, "errors": [str(exc)], "warnings": []},
        }
        sys.stdout.write(json_dumps(error_report))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
