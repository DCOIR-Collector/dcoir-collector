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


SCHEMA = "dcoir.ops.apply_patch_request.v1"
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
class PatchRequest:
    schema: str
    request_id: str
    mode: str
    target_branch: str
    target_path: str
    patch_path: str
    expected_patch_sha256: str
    allowed_roots: tuple[str, ...]
    expected_target_blob_sha: str | None = None
    expected_current_sha256: str | None = None
    expected_new_sha256: str | None = None
    commit_message: str = DEFAULT_COMMIT
    allow_default_branch: bool = False
    default_branch_reason: str = ""
    allow_workflow_changes: bool = False
    workflow_change_reason: str = ""


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


def validate_target_path(request: PatchRequest) -> None:
    target = request.target_path
    if any(target == prefix.rstrip("/") or target.startswith(prefix) for prefix in BLOCKED_TARGET_PREFIXES):
        raise RequestError(f"target_path is blocked for ops patch requests: {target}")
    if not path_under(target, request.allowed_roots):
        raise RequestError(f"target_path is outside allowed_roots: {target}")
    if target.startswith(".github/workflows/") and not request.allow_workflow_changes:
        raise RequestError("workflow targets require allow_workflow_changes=true and workflow_change_reason")
    if request.allow_workflow_changes and not request.workflow_change_reason.strip():
        raise RequestError("allow_workflow_changes=true requires workflow_change_reason")


def request_dir_from_path(repo: pathlib.Path, request_path: pathlib.Path, request_id: str) -> pathlib.Path:
    try:
        rel = request_path.resolve().relative_to((repo / "ops/requests/apply_patch").resolve())
    except ValueError as exc:
        raise RequestError("request file must live under ops/requests/apply_patch/<request_id>/request.json") from exc
    if rel.parts != (request_id, "request.json"):
        raise RequestError("request file path must be ops/requests/apply_patch/<request_id>/request.json")
    return request_path.parent


def load_request(repo: pathlib.Path, request_path: pathlib.Path, default_branch: str) -> PatchRequest:
    data = json.loads(request_path.read_text(encoding="utf-8"))
    if data.get("schema") != SCHEMA:
        raise RequestError(f"schema must be {SCHEMA}")
    request_id = validate_request_id(require_string(data.get("request_id"), field="request_id"))
    allowed_roots = validate_roots(data.get("allowed_roots"))
    target_branch = validate_branch(
        repo,
        require_string(data.get("target_branch"), field="target_branch"),
        default_branch,
        optional_bool(data.get("allow_default_branch"), field="allow_default_branch"),
        optional_string(data.get("default_branch_reason"), field="default_branch_reason") or "",
    )
    target_path = normalize_repo_path(require_string(data.get("target_path"), field="target_path"), field="target_path")
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
    mode = optional_string(data.get("mode", "dry-run"), field="mode") or "dry-run"
    if mode not in {"dry-run", "apply"}:
        raise RequestError("mode must be dry-run or apply")
    commit_message = (optional_string(data.get("commit_message", DEFAULT_COMMIT), field="commit_message") or DEFAULT_COMMIT).strip() or DEFAULT_COMMIT
    if "\n" in commit_message or "\r" in commit_message:
        raise RequestError("commit_message must be a single line")
    request = PatchRequest(
        schema=SCHEMA,
        request_id=request_id,
        mode=mode,
        target_branch=target_branch,
        target_path=target_path,
        patch_path=patch_path,
        expected_patch_sha256=expected_patch_sha256,
        allowed_roots=allowed_roots,
        expected_target_blob_sha=optional_string(data.get("expected_target_blob_sha"), field="expected_target_blob_sha"),
        expected_current_sha256=optional_string(data.get("expected_current_sha256"), field="expected_current_sha256"),
        expected_new_sha256=optional_string(data.get("expected_new_sha256"), field="expected_new_sha256"),
        commit_message=commit_message,
        allow_default_branch=optional_bool(data.get("allow_default_branch"), field="allow_default_branch"),
        default_branch_reason=optional_string(data.get("default_branch_reason"), field="default_branch_reason") or "",
        allow_workflow_changes=optional_bool(data.get("allow_workflow_changes"), field="allow_workflow_changes"),
        workflow_change_reason=optional_string(data.get("workflow_change_reason"), field="workflow_change_reason") or "",
    )
    validate_target_path(request)
    if not (request.expected_target_blob_sha or request.expected_current_sha256):
        raise RequestError("expected_target_blob_sha or expected_current_sha256 is required")
    if request.expected_target_blob_sha and not re.fullmatch(r"[0-9a-f]{40}", request.expected_target_blob_sha):
        raise RequestError("expected_target_blob_sha must be a 40-character git blob SHA")
    for field in ("expected_current_sha256", "expected_new_sha256"):
        digest = getattr(request, field)
        if digest is not None and not re.fullmatch(r"[0-9a-f]{64}", str(digest).lower()):
            raise RequestError(f"{field} must be a SHA-256 hex digest")
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


def extract_patch_paths(patch_text: str) -> set[str]:
    paths: set[str] = set()
    for line in patch_text.splitlines():
        if line.startswith(("--- ", "+++ ")):
            if line[4:].strip().split("\t", 1)[0] == "/dev/null":
                raise RequestError("patch must not create or delete the target file")
            token = patch_path_token(line[4:])
            if token:
                paths.add(token)
        elif line.startswith("diff --git "):
            try:
                parts = shlex.split(line)
            except ValueError:
                continue
            for token in parts[2:4]:
                parsed = patch_path_token(token)
                if parsed:
                    paths.add(parsed)
    return paths


def validate_patch_text(patch_text: str, request: PatchRequest) -> None:
    if "\x00" in patch_text:
        raise RequestError("patch contains NUL bytes")
    for marker in FORBIDDEN_PATCH_MARKERS:
        if marker in patch_text:
            raise RequestError(f"patch contains forbidden marker: {marker.strip()}")
    paths = extract_patch_paths(patch_text)
    if paths != {request.target_path}:
        raise RequestError(f"patch must touch only target_path {request.target_path}; found {sorted(paths)}")


def prepare_patch(repo: pathlib.Path, request: PatchRequest) -> bytes:
    patch_file = repo / request.patch_path
    patch_bytes = patch_file.read_bytes()
    actual = sha256_bytes(patch_bytes)
    if actual != request.expected_patch_sha256:
        raise RequestError(f"patch SHA-256 mismatch: expected {request.expected_patch_sha256}, got {actual}")
    patch_text = patch_bytes.decode("utf-8")
    validate_patch_text(patch_text, request)
    return patch_bytes


def checkout_target(repo: pathlib.Path, branch: str, *, local_only: bool) -> None:
    if not local_only:
        refspec = f"refs/heads/{branch}:refs/remotes/origin/{branch}"
        run(["git", "fetch", "--no-tags", "origin", refspec], cwd=repo)
        run(["git", "checkout", "-B", "ops-apply-patch-target", f"origin/{branch}"], cwd=repo)
    else:
        run(["git", "checkout", branch], cwd=repo)


def validate_current_target(repo: pathlib.Path, request: PatchRequest) -> None:
    target = repo / request.target_path
    if not target.is_file():
        raise RequestError(f"target_path is missing or not a file on target branch: {request.target_path}")
    blob_sha = git_blob_sha(repo, request.target_path)
    if not blob_sha:
        raise RequestError(f"target_path is not tracked on target branch: {request.target_path}")
    if request.expected_target_blob_sha and blob_sha != request.expected_target_blob_sha:
        raise RequestError(f"target blob mismatch for {request.target_path}: expected {request.expected_target_blob_sha}, got {blob_sha}")
    if request.expected_current_sha256:
        current_sha = sha256_file(target)
        if current_sha != request.expected_current_sha256:
            raise RequestError(f"target SHA-256 mismatch for {request.target_path}: expected {request.expected_current_sha256}, got {current_sha}")


def apply_patch(repo: pathlib.Path, patch_bytes: bytes, request: PatchRequest, *, dry_run: bool) -> None:
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
    changed = run(["git", "diff", "--name-only", "--", request.target_path], cwd=repo).stdout.splitlines()
    if changed != [request.target_path]:
        raise RequestError(f"patch changed unexpected paths: {changed}")
    if not (repo / request.target_path).is_file():
        raise RequestError("patch must leave target_path as an existing file")
    if request.expected_new_sha256:
        actual_new = sha256_file(repo / request.target_path)
        if actual_new != request.expected_new_sha256:
            raise RequestError(f"new target SHA-256 mismatch: expected {request.expected_new_sha256}, got {actual_new}")
    ensure_git_identity(repo)
    run(["git", "add", "--", request.target_path], cwd=repo)
    run(["git", "commit", "-m", request.commit_message], cwd=repo)
    commit_sha = run(["git", "rev-parse", "HEAD"], cwd=repo).stdout.strip()
    if not (local_only or no_push):
        run(["git", "push", "origin", f"HEAD:refs/heads/{request.target_branch}"], cwd=repo)
    return commit_sha


def write_report(report_dir: pathlib.Path, result: dict[str, Any]) -> None:
    report_dir.mkdir(parents=True, exist_ok=True)
    (report_dir / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    lines = ["# Ops apply-patch report", ""]
    for key in ("result", "request_id", "mode", "target_branch", "target_path", "commit_sha", "message"):
        if key in result and result[key] is not None:
            lines.append(f"- {key}: `{result[key]}`")
    (report_dir / "workflow_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def apply_request(args: argparse.Namespace) -> int:
    repo = pathlib.Path(args.repo).resolve()
    request_path = (repo / args.request).resolve() if not pathlib.Path(args.request).is_absolute() else pathlib.Path(args.request).resolve()
    report_dir = pathlib.Path(args.report_dir).resolve() if args.report_dir else None
    result: dict[str, Any] = {
        "result": "failure",
        "request_id": None,
        "mode": None,
        "target_branch": None,
        "target_path": None,
        "commit_sha": None,
    }
    try:
        request = load_request(repo, request_path, args.default_branch)
        patch_bytes = prepare_patch(repo, request)
        result.update(
            {
                "result": "success",
                "request_id": request.request_id,
                "mode": request.mode,
                "target_branch": request.target_branch,
                "target_path": request.target_path,
            }
        )
        checkout_target(repo, request.target_branch, local_only=args.local_only)
        validate_current_target(repo, request)
        dry_run = request.mode == "dry-run"
        apply_patch(repo, patch_bytes, request, dry_run=dry_run)
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
    prepare_patch(repo, request)
    print(json.dumps({"result": "success", "request_id": request.request_id, "target_path": request.target_path}, sort_keys=True))
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
