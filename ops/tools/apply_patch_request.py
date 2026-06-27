#!/usr/bin/env python3
"""Validate and apply one governed ops patch request."""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import re
import shlex
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from typing import Any


SCHEMA_V1 = "dcoir.ops.apply_patch_request.v1"
SCHEMA_V2 = "dcoir.ops.apply_patch_request.v2"
SCHEMA = SCHEMA_V1
SAFE_ID_RE = re.compile(r"^[A-Za-z0-9._-]+$")
DEFAULT_COMMIT = "Apply governed ops patch request"
BOT_USER_NAME = "github-actions[bot]"
BOT_USER_EMAIL = "41898282+github-actions[bot]@users.noreply.github.com"
BLOCKED_TARGET_PREFIXES = (
    ".git/",
    "chatgpt_staging/",
    "ops/requests/",
    "ops/reports/",
)
FORBIDDEN_PATCH_MARKERS = (
    "GIT binary patch",
    "Binary files ",
    "rename from ",
    "rename to ",
    "copy from ",
    "copy to ",
    "new file mode ",
    "deleted file mode ",
    "old mode ",
    "new mode ",
    "similarity index ",
    "dissimilarity index ",
)


class RequestError(RuntimeError):
    """Raised when a request violates the apply-patch contract."""


@dataclass(frozen=True)
class TargetSpec:
    path: str
    allowed_roots: tuple[str, ...]
    expected_target_blob_sha: str | None = None
    expected_current_sha256: str | None = None
    expected_new_sha256: str | None = None


@dataclass(frozen=True)
class PatchRequest:
    schema: str
    request_id: str
    mode: str
    operation: str
    target_branch: str
    patch_path: str
    expected_patch_sha256: str
    targets: tuple[TargetSpec, ...]
    commit_message: str = DEFAULT_COMMIT
    allow_default_branch: bool = False
    default_branch_reason: str = ""
    allow_workflow_changes: bool = False
    workflow_change_reason: str = ""

    @property
    def target_paths(self) -> tuple[str, ...]:
        return tuple(target.path for target in self.targets)

    @property
    def target_path(self) -> str | None:
        return self.targets[0].path if len(self.targets) == 1 else None


def run(cmd: list[str], *, cwd: pathlib.Path, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=cwd, check=check, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: pathlib.Path) -> str:
    return sha256_bytes(path.read_bytes())


def require_string(value: Any, *, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise RequestError(f"{field} is required")
    return value


def optional_string(value: Any, *, field: str) -> str | None:
    if value is None or value == "":
        return None
    if not isinstance(value, str):
        raise RequestError(f"{field} must be a string")
    return value


def optional_bool(value: Any, *, field: str, default: bool = False) -> bool:
    if value is None:
        return default
    if not isinstance(value, bool):
        raise RequestError(f"{field} must be a boolean")
    return value


def git_blob_sha(repo: pathlib.Path, target_path: str) -> str:
    proc = run(["git", "ls-files", "-s", "--", target_path], cwd=repo)
    parts = proc.stdout.split()
    return parts[1] if len(parts) > 1 else ""


def normalize_repo_path(value: str, *, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise RequestError(f"{field} is required")
    if "\\" in value:
        raise RequestError(f"{field} must use forward slashes: {value}")
    p = pathlib.PurePosixPath(value.strip())
    if p.is_absolute() or ".." in p.parts or str(p) in {"", "."}:
        raise RequestError(f"{field} must be a safe repo-relative path: {value}")
    return p.as_posix()


def validate_request_id(value: str) -> str:
    if not isinstance(value, str) or not SAFE_ID_RE.match(value):
        raise RequestError("request_id must contain only letters, numbers, dot, underscore, and hyphen")
    return value


def validate_branch(repo: pathlib.Path, branch: str, default_branch: str, allow_default: bool, reason: str) -> str:
    if not isinstance(branch, str) or not branch.strip():
        raise RequestError("target_branch is required")
    candidate = branch.strip()
    if candidate.startswith(("refs/", "origin/")):
        raise RequestError("target_branch must be a branch name, not a refspec or remote-tracking name")
    if any(token in candidate for token in ("..", "@{", "\\", ":", "~", "^", "?", "*", "[")):
        raise RequestError(f"target_branch contains unsupported ref syntax: {candidate}")
    if candidate.startswith("/") or candidate.endswith("/") or "//" in candidate:
        raise RequestError(f"target_branch must be a safe branch name: {candidate}")
    check = subprocess.run(
        ["git", "check-ref-format", "--branch", candidate],
        cwd=repo,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if check.returncode != 0:
        raise RequestError(f"target_branch is not a valid git branch name: {candidate}")
    if candidate == default_branch and not allow_default:
        raise RequestError("target_branch is the default branch; set allow_default_branch with a reason to permit this")
    if allow_default and candidate == default_branch and not reason.strip():
        raise RequestError("allow_default_branch=true requires default_branch_reason")
    return candidate


def validate_roots(raw: Any) -> tuple[str, ...]:
    if not isinstance(raw, list) or not raw:
        raise RequestError("allowed_roots must be a non-empty list")
    roots: list[str] = []
    for item in raw:
        if not isinstance(item, str):
            raise RequestError("allowed_roots[] must be a string")
        root = normalize_repo_path(item, field="allowed_roots[]").rstrip("/")
        if not root or root == ".":
            raise RequestError("allowed_roots must not include repo root")
        roots.append(root)
    return tuple(sorted(set(roots)))


def path_under(path: str, roots: tuple[str, ...]) -> bool:
    return any(path == root or path.startswith(root + "/") for root in roots)


def validate_target_path(target: TargetSpec, request: PatchRequest) -> None:
    path = target.path
    if any(path == prefix.rstrip("/") or path.startswith(prefix) for prefix in BLOCKED_TARGET_PREFIXES):
        raise RequestError(f"target_path is blocked for ops patch requests: {path}")
    if not path_under(path, target.allowed_roots):
        raise RequestError(f"target_path is outside allowed_roots: {path}")
    if path.startswith(".github/workflows/") and not request.allow_workflow_changes:
        raise RequestError("workflow targets require allow_workflow_changes=true and workflow_change_reason")


def request_dir_from_path(repo: pathlib.Path, request_path: pathlib.Path, request_id: str) -> pathlib.Path:
    try:
        rel = request_path.resolve().relative_to((repo / "ops/requests/apply_patch").resolve())
    except ValueError as exc:
        raise RequestError("request file must live under ops/requests/apply_patch/<request_id>/request.json") from exc
    if rel.parts != (request_id, "request.json"):
        raise RequestError("request file path must be ops/requests/apply_patch/<request_id>/request.json")
    return request_path.parent


def validate_digest(value: str | None, *, field: str, length: int) -> None:
    if value is not None and not re.fullmatch(rf"[0-9a-f]{{{length}}}", value):
        raise RequestError(f"{field} must be a {length}-character hex digest")


def target_from_v1(data: dict[str, Any]) -> TargetSpec:
    target = TargetSpec(
        path=normalize_repo_path(require_string(data.get("target_path"), field="target_path"), field="target_path"),
        allowed_roots=validate_roots(data.get("allowed_roots")),
        expected_target_blob_sha=optional_string(data.get("expected_target_blob_sha"), field="expected_target_blob_sha"),
        expected_current_sha256=optional_string(data.get("expected_current_sha256"), field="expected_current_sha256"),
        expected_new_sha256=optional_string(data.get("expected_new_sha256"), field="expected_new_sha256"),
    )
    if not (target.expected_target_blob_sha or target.expected_current_sha256):
        raise RequestError("expected_target_blob_sha or expected_current_sha256 is required")
    validate_digest(target.expected_target_blob_sha, field="expected_target_blob_sha", length=40)
    validate_digest(target.expected_current_sha256, field="expected_current_sha256", length=64)
    validate_digest(target.expected_new_sha256, field="expected_new_sha256", length=64)
    return target


def target_from_v2(raw: Any, index: int) -> TargetSpec:
    if not isinstance(raw, dict):
        raise RequestError(f"targets[{index}] must be an object")
    target = TargetSpec(
        path=normalize_repo_path(require_string(raw.get("path"), field=f"targets[{index}].path"), field=f"targets[{index}].path"),
        allowed_roots=validate_roots(raw.get("allowed_roots")),
        expected_target_blob_sha=optional_string(raw.get("expected_target_blob_sha"), field=f"targets[{index}].expected_target_blob_sha"),
        expected_current_sha256=optional_string(raw.get("expected_current_sha256"), field=f"targets[{index}].expected_current_sha256"),
        expected_new_sha256=optional_string(raw.get("expected_new_sha256"), field=f"targets[{index}].expected_new_sha256"),
    )
    if not (target.expected_target_blob_sha or target.expected_current_sha256):
        raise RequestError(f"targets[{index}] requires expected_target_blob_sha or expected_current_sha256")
    validate_digest(target.expected_target_blob_sha, field=f"targets[{index}].expected_target_blob_sha", length=40)
    validate_digest(target.expected_current_sha256, field=f"targets[{index}].expected_current_sha256", length=64)
    validate_digest(target.expected_new_sha256, field=f"targets[{index}].expected_new_sha256", length=64)
    return target


def load_request(repo: pathlib.Path, request_path: pathlib.Path, default_branch: str) -> PatchRequest:
    data = json.loads(request_path.read_text(encoding="utf-8"))
    schema = data.get("schema")
    if schema not in {SCHEMA_V1, SCHEMA_V2}:
        raise RequestError(f"schema must be {SCHEMA_V1} or {SCHEMA_V2}")
    request_id = validate_request_id(require_string(data.get("request_id"), field="request_id"))
    target_branch = validate_branch(
        repo,
        require_string(data.get("target_branch"), field="target_branch"),
        default_branch,
        optional_bool(data.get("allow_default_branch"), field="allow_default_branch"),
        optional_string(data.get("default_branch_reason"), field="default_branch_reason") or "",
    )
    patch_path = normalize_repo_path(require_string(data.get("patch_path"), field="patch_path"), field="patch_path")
    request_dir = request_dir_from_path(repo, request_path, request_id)
    expected_prefix = f"ops/requests/apply_patch/{request_id}/"
    if not patch_path.startswith(expected_prefix) or not patch_path.endswith((".patch", ".diff")):
        raise RequestError("patch_path must be a .patch or .diff file in the same request directory")
    if (repo / patch_path).resolve().parent != request_dir.resolve():
        raise RequestError("patch_path must be in the same request directory as request.json")
    expected_patch_sha256 = require_string(data.get("expected_patch_sha256"), field="expected_patch_sha256").lower()
    if not re.fullmatch(r"[0-9a-f]{64}", expected_patch_sha256):
        raise RequestError("expected_patch_sha256 must be a lowercase SHA-256 hex digest")
    if schema == SCHEMA_V1:
        mode = optional_string(data.get("mode", "dry-run"), field="mode") or "dry-run"
        if mode not in {"dry-run", "apply"}:
            raise RequestError("mode must be dry-run or apply")
        operation = mode
        targets = (target_from_v1(data),)
    else:
        mode = require_string(data.get("mode"), field="mode")
        if mode != "patch-set":
            raise RequestError('v2 mode must be "patch-set"')
        operation = optional_string(data.get("operation", "dry-run"), field="operation") or "dry-run"
        if operation not in {"dry-run", "apply"}:
            raise RequestError("operation must be dry-run or apply")
        raw_targets = data.get("targets")
        if not isinstance(raw_targets, list) or not raw_targets:
            raise RequestError("targets must be a non-empty list")
        targets = tuple(target_from_v2(raw, index) for index, raw in enumerate(raw_targets))
        seen: set[str] = set()
        for target in targets:
            if target.path in seen:
                raise RequestError(f"duplicate target path in targets: {target.path}")
            seen.add(target.path)
    commit_message = (optional_string(data.get("commit_message", DEFAULT_COMMIT), field="commit_message") or DEFAULT_COMMIT).strip() or DEFAULT_COMMIT
    if "\n" in commit_message or "\r" in commit_message:
        raise RequestError("commit_message must be a single line")
    request = PatchRequest(
        schema=schema,
        request_id=request_id,
        mode=mode,
        operation=operation,
        target_branch=target_branch,
        patch_path=patch_path,
        expected_patch_sha256=expected_patch_sha256,
        targets=targets,
        commit_message=commit_message,
        allow_default_branch=optional_bool(data.get("allow_default_branch"), field="allow_default_branch"),
        default_branch_reason=optional_string(data.get("default_branch_reason"), field="default_branch_reason") or "",
        allow_workflow_changes=optional_bool(data.get("allow_workflow_changes"), field="allow_workflow_changes"),
        workflow_change_reason=optional_string(data.get("workflow_change_reason"), field="workflow_change_reason") or "",
    )
    if request.allow_workflow_changes and not request.workflow_change_reason.strip():
        raise RequestError("allow_workflow_changes=true requires workflow_change_reason")
    for target in request.targets:
        validate_target_path(target, request)
    return request


def patch_path_token(raw: str) -> str | None:
    path = raw.strip()
    if not path or path == "/dev/null":
        return None
    if "\t" in path:
        path = path.split("\t", 1)[0]
    if path.startswith(("a/", "b/")):
        path = path[2:]
    return normalize_repo_path(path.strip('"'), field="patch path")


def extract_patch_paths(patch_text: str) -> dict[str, str]:
    paths: dict[str, str] = {}
    for line in patch_text.splitlines():
        if line.startswith(("--- ", "+++ ")):
            if line[4:].strip().split("\t", 1)[0] == "/dev/null":
                raise RequestError("patch must not create or delete the target file")
            token = patch_path_token(line[4:])
            if token:
                paths[token] = "modify"
        elif line.startswith("diff --git "):
            try:
                parts = shlex.split(line)
            except ValueError:
                continue
            for token in parts[2:4]:
                parsed = patch_path_token(token)
                if parsed:
                    paths[parsed] = "modify"
    return paths


def target_plan(target: TargetSpec, operation: str, request: PatchRequest) -> dict[str, Any]:
    root_policy = "pass" if path_under(target.path, target.allowed_roots) else "fail"
    if target.path.startswith(".github/workflows/"):
        workflow_policy = "explicitly_allowed" if request.allow_workflow_changes else "fail"
    else:
        workflow_policy = "not_workflow"
    return {
        "path": target.path,
        "operation": operation,
        "allowed_roots": list(target.allowed_roots),
        "root_policy_result": root_policy,
        "workflow_policy_result": workflow_policy,
        "expected_target_blob_sha": target.expected_target_blob_sha,
        "expected_current_sha256": target.expected_current_sha256,
        "expected_new_sha256": target.expected_new_sha256,
        "stale_base_result": "pending",
    }


def build_apply_plan(patch_text: str, request: PatchRequest) -> dict[str, Any]:
    if "\x00" in patch_text:
        raise RequestError("patch contains NUL bytes")
    for marker in FORBIDDEN_PATCH_MARKERS:
        if marker in patch_text:
            raise RequestError(f"patch contains forbidden marker: {marker.strip()}")
    paths = extract_patch_paths(patch_text)
    expected_paths = set(request.target_paths)
    found_paths = set(paths)
    if found_paths != expected_paths:
        if request.schema == SCHEMA_V1:
            raise RequestError(f"patch must touch only target_path {request.target_path}; found {sorted(found_paths)}")
        raise RequestError(f"patch paths must match targets; expected {sorted(expected_paths)}, found {sorted(found_paths)}")
    if request.schema == SCHEMA_V1 and len(found_paths) != 1:
        raise RequestError("v1 patch requests must touch exactly one target_path")
    branch_policy = "not_default_branch"
    if request.allow_default_branch:
        branch_policy = "explicitly_allowed" if request.default_branch_reason.strip() else "fail"
    return {
        "schema": request.schema,
        "request_id": request.request_id,
        "mode": request.mode,
        "operation": request.operation,
        "target_branch": request.target_branch,
        "patch_path": request.patch_path,
        "default_branch_policy_result": branch_policy,
        "allow_workflow_changes": request.allow_workflow_changes,
        "files": [target_plan(target, paths[target.path], request) for target in request.targets],
    }


def prepare_patch(repo: pathlib.Path, request: PatchRequest) -> tuple[bytes, dict[str, Any]]:
    patch_file = repo / request.patch_path
    patch_bytes = patch_file.read_bytes()
    actual = sha256_bytes(patch_bytes)
    if actual != request.expected_patch_sha256:
        raise RequestError(f"patch SHA-256 mismatch: expected {request.expected_patch_sha256}, got {actual}")
    patch_text = patch_bytes.decode("utf-8")
    return patch_bytes, build_apply_plan(patch_text, request)


def checkout_target(repo: pathlib.Path, branch: str, *, local_only: bool) -> None:
    if not local_only:
        refspec = f"refs/heads/{branch}:refs/remotes/origin/{branch}"
        run(["git", "fetch", "--no-tags", "origin", refspec], cwd=repo)
        run(["git", "checkout", "-B", "ops-apply-patch-target", f"origin/{branch}"], cwd=repo)
    else:
        run(["git", "checkout", branch], cwd=repo)


def plan_file_by_path(plan: dict[str, Any], path: str) -> dict[str, Any]:
    for item in plan.get("files", []):
        if item.get("path") == path:
            return item
    return {}


def validate_current_targets(repo: pathlib.Path, request: PatchRequest, plan: dict[str, Any]) -> None:
    for target_spec in request.targets:
        path = target_spec.path
        plan_file = plan_file_by_path(plan, path)
        target = repo / path
        if not target.is_file():
            if plan_file:
                plan_file["stale_base_result"] = "fail"
            raise RequestError(f"target_path is missing or not a file on target branch: {path}")
        blob_sha = git_blob_sha(repo, path)
        if plan_file:
            plan_file["current_target_blob_sha"] = blob_sha
        if not blob_sha:
            if plan_file:
                plan_file["stale_base_result"] = "fail"
            raise RequestError(f"target_path is not tracked on target branch: {path}")
        if target_spec.expected_target_blob_sha and blob_sha != target_spec.expected_target_blob_sha:
            if plan_file:
                plan_file["stale_base_result"] = "fail"
            raise RequestError(f"target blob mismatch for {path}: expected {target_spec.expected_target_blob_sha}, got {blob_sha}")
        current_sha = sha256_file(target)
        if plan_file:
            plan_file["current_sha256"] = current_sha
        if target_spec.expected_current_sha256 and current_sha != target_spec.expected_current_sha256:
            if plan_file:
                plan_file["stale_base_result"] = "fail"
            raise RequestError(f"target SHA-256 mismatch for {path}: expected {target_spec.expected_current_sha256}, got {current_sha}")
        if plan_file:
            plan_file["stale_base_result"] = "pass"


def apply_patch(repo: pathlib.Path, patch_bytes: bytes, *, dry_run: bool) -> None:
    with tempfile.NamedTemporaryFile(prefix="dcoir-ops-patch-", suffix=".patch", delete=False) as handle:
        handle.write(patch_bytes)
        temp_patch = pathlib.Path(handle.name)
    try:
        run(["git", "apply", "--check", "--", str(temp_patch)], cwd=repo)
        if not dry_run:
            run(["git", "apply", "--", str(temp_patch)], cwd=repo)
    finally:
        temp_patch.unlink(missing_ok=True)


def ensure_git_identity(repo: pathlib.Path) -> None:
    name = run(["git", "config", "--get", "user.name"], cwd=repo, check=False).stdout.strip()
    email = run(["git", "config", "--get", "user.email"], cwd=repo, check=False).stdout.strip()
    if not name:
        run(["git", "config", "user.name", BOT_USER_NAME], cwd=repo)
    if not email:
        run(["git", "config", "user.email", BOT_USER_EMAIL], cwd=repo)


def commit_and_push(repo: pathlib.Path, request: PatchRequest, *, local_only: bool, no_push: bool) -> str:
    expected = sorted(request.target_paths)
    changed = sorted(run(["git", "diff", "--name-only"], cwd=repo).stdout.splitlines())
    if changed != expected:
        raise RequestError(f"patch changed unexpected paths: {changed}")
    for target in request.targets:
        if not (repo / target.path).is_file():
            raise RequestError(f"patch must leave target_path as an existing file: {target.path}")
        if target.expected_new_sha256:
            actual_new = sha256_file(repo / target.path)
            if actual_new != target.expected_new_sha256:
                raise RequestError(f"new target SHA-256 mismatch for {target.path}: expected {target.expected_new_sha256}, got {actual_new}")
    ensure_git_identity(repo)
    run(["git", "add", "--", *request.target_paths], cwd=repo)
    run(["git", "commit", "-m", request.commit_message], cwd=repo)
    commit_sha = run(["git", "rev-parse", "HEAD"], cwd=repo).stdout.strip()
    if not (local_only or no_push):
        run(["git", "push", "origin", f"HEAD:refs/heads/{request.target_branch}"], cwd=repo)
    return commit_sha


def write_report(report_dir: pathlib.Path, result: dict[str, Any]) -> None:
    report_dir.mkdir(parents=True, exist_ok=True)
    (report_dir / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    lines = ["# Ops apply-patch report", ""]
    for key in ("result", "request_id", "schema", "mode", "operation", "target_branch", "target_path", "commit_sha", "message"):
        if key in result and result[key] is not None:
            lines.append(f"- {key}: `{result[key]}`")
    if result.get("target_paths"):
        lines.append("- target_paths:")
        for path in result["target_paths"]:
            lines.append(f"  - `{path}`")
    plan = result.get("apply_plan")
    if isinstance(plan, dict) and plan.get("files"):
        lines.extend(["", "## Apply plan", ""])
        for item in plan["files"]:
            lines.append(
                "- `{path}`: operation `{operation}`, root policy `{root}`, workflow policy `{workflow}`, stale-base `{stale}`".format(
                    path=item.get("path"),
                    operation=item.get("operation"),
                    root=item.get("root_policy_result"),
                    workflow=item.get("workflow_policy_result"),
                    stale=item.get("stale_base_result"),
                )
            )
    (report_dir / "workflow_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def apply_request(args: argparse.Namespace) -> int:
    repo = pathlib.Path(args.repo).resolve()
    request_path = (repo / args.request).resolve() if not pathlib.Path(args.request).is_absolute() else pathlib.Path(args.request).resolve()
    report_dir = pathlib.Path(args.report_dir).resolve() if args.report_dir else None
    result: dict[str, Any] = {
        "result": "failure",
        "request_id": None,
        "schema": None,
        "mode": None,
        "operation": None,
        "target_branch": None,
        "target_path": None,
        "target_paths": None,
        "commit_sha": None,
        "apply_plan": None,
    }
    try:
        request = load_request(repo, request_path, args.default_branch)
        patch_bytes, apply_plan = prepare_patch(repo, request)
        result.update(
            {
                "result": "success",
                "request_id": request.request_id,
                "schema": request.schema,
                "mode": request.mode,
                "operation": request.operation,
                "target_branch": request.target_branch,
                "target_path": request.target_path,
                "target_paths": list(request.target_paths),
                "apply_plan": apply_plan,
            }
        )
        checkout_target(repo, request.target_branch, local_only=args.local_only)
        validate_current_targets(repo, request, apply_plan)
        dry_run = request.operation == "dry-run"
        apply_patch(repo, patch_bytes, dry_run=dry_run)
        if dry_run:
            result["message"] = "patch passed validation and git apply --check; no commit was made"
        else:
            result["commit_sha"] = commit_and_push(repo, request, local_only=args.local_only, no_push=args.no_push)
            result["message"] = "patch applied, committed, and pushed" if not (args.local_only or args.no_push) else "patch applied and committed locally"
    except Exception as exc:
        result["result"] = "failure"
        result["message"] = str(exc)
        if report_dir:
            write_report(report_dir, result)
        raise
    if report_dir:
        write_report(report_dir, result)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


def validate_request(args: argparse.Namespace) -> int:
    repo = pathlib.Path(args.repo).resolve()
    request_path = (repo / args.request).resolve() if not pathlib.Path(args.request).is_absolute() else pathlib.Path(args.request).resolve()
    request = load_request(repo, request_path, args.default_branch)
    _, apply_plan = prepare_patch(repo, request)
    print(json.dumps({"result": "success", "request_id": request.request_id, "target_path": request.target_path, "target_paths": list(request.target_paths), "apply_plan": apply_plan}, sort_keys=True))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("validate", "apply"))
    parser.add_argument("--repo", default=".")
    parser.add_argument("--request", required=True)
    parser.add_argument("--default-branch", default="main")
    parser.add_argument("--report-dir")
    parser.add_argument("--local-only", action="store_true", help="Use the local target branch and do not fetch or push.")
    parser.add_argument("--no-push", action="store_true", help="Commit locally but do not push.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "validate":
            return validate_request(args)
        return apply_request(args)
    except (RequestError, subprocess.CalledProcessError, json.JSONDecodeError, UnicodeDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        if isinstance(exc, subprocess.CalledProcessError):
            if exc.stdout:
                print(exc.stdout, file=sys.stderr)
            if exc.stderr:
                print(exc.stderr, file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
